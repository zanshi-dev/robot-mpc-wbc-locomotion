import argparse
from pathlib import Path

import mujoco
import numpy as np
import pinocchio as pin


LEG_ORDER = ["FR", "FL", "RR", "RL"]
STAND_LEG_Q = np.array([0.0, 0.9, -1.8])

FOOT_GEOMS = {
    "FR": "FR",
    "FL": "FL",
    "RR": "RR",
    "RL": "RL",
}

PIN_FOOT_FRAMES = {
    "FR": "FR_foot",
    "FL": "FL_foot",
    "RR": "RR_foot",
    "RL": "RL_foot",
}

# MuJoCo actuated order: FR, FL, RR, RL.
MJ_ACT_SLICE = {
    "FR": slice(0, 3),
    "FL": slice(3, 6),
    "RR": slice(6, 9),
    "RL": slice(9, 12),
}

# Pinocchio actuated velocity/torque order: FL, FR, RL, RR.
PIN_ACT_SLICE = {
    "FL": slice(6, 9),
    "FR": slice(9, 12),
    "RL": slice(12, 15),
    "RR": slice(15, 18),
}


def build_standing_q():
    return np.tile(STAND_LEG_Q, 4)


def initialize_standing_pose(model, data, q_stand, desired_min_foot_z=0.02):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0

    # MuJoCo free-joint qpos: x, y, z, qw, qx, qy, qz.
    data.qpos[0:7] = np.array([0.0, 0.0, 0.35, 1.0, 0.0, 0.0, 0.0])
    data.qpos[7:19] = q_stand

    mujoco.mj_forward(model, data)

    foot_z = []
    for geom_name in LEG_ORDER:
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
        if gid < 0:
            raise RuntimeError(f"Cannot find foot geom: {geom_name}")
        foot_z.append(data.geom_xpos[gid, 2])

    min_foot_z = float(np.min(foot_z))
    data.qpos[2] += desired_min_foot_z - min_foot_z

    mujoco.mj_forward(model, data)


def compute_total_mass(model):
    return float(np.sum(np.asarray(model.body_mass)[1:]))


def mujoco_to_pin_q(mj_qpos):
    pin_q = np.zeros(19)

    pin_q[0:3] = mj_qpos[0:3]

    # MuJoCo:     x, y, z, qw, qx, qy, qz
    # Pinocchio: x, y, z, qx, qy, qz, qw
    pin_q[3:7] = np.array([
        mj_qpos[4],
        mj_qpos[5],
        mj_qpos[6],
        mj_qpos[3],
    ])

    # MuJoCo joint order:    FR, FL, RR, RL
    # Pinocchio joint order: FL, FR, RL, RR
    pin_q[7:19] = np.concatenate([
        mj_qpos[10:13],  # FL
        mj_qpos[7:10],   # FR
        mj_qpos[16:19],  # RL
        mj_qpos[13:16],  # RR
    ])

    return pin_q


def pin_tau_to_mujoco_order(pin_tau_act):
    # pin_tau_act is 12D in Pinocchio actuated order: FL, FR, RL, RR.
    # return 12D in MuJoCo actuated order: FR, FL, RR, RL.
    return np.concatenate([
        pin_tau_act[3:6],    # FR
        pin_tau_act[0:3],    # FL
        pin_tau_act[9:12],   # RR
        pin_tau_act[6:9],    # RL
    ])


def compute_mujoco_jt_force_torque(model, data, foot_forces):
    tau = np.zeros(12)

    for leg in LEG_ORDER:
        geom_id = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_GEOM,
            FOOT_GEOMS[leg],
        )
        if geom_id < 0:
            raise RuntimeError(f"Cannot find MuJoCo foot geom: {FOOT_GEOMS[leg]}")

        jacp = np.zeros((3, model.nv))
        jacr = np.zeros((3, model.nv))
        mujoco.mj_jacGeom(model, data, jacp, jacr, geom_id)

        mj_slice = MJ_ACT_SLICE[leg]
        full_col_slice = slice(6 + mj_slice.start, 6 + mj_slice.stop)

        j_leg = jacp[:, full_col_slice]
        f_leg = foot_forces[leg]

        tau[mj_slice] += j_leg.T @ f_leg

    return tau


def compute_pinocchio_jt_force_torque(pin_model, pin_data, pin_q, foot_forces):
    pin.forwardKinematics(pin_model, pin_data, pin_q)
    pin.computeJointJacobians(pin_model, pin_data, pin_q)
    pin.updateFramePlacements(pin_model, pin_data)

    # 12D in Pinocchio actuated order: FL, FR, RL, RR.
    tau_pin_act = np.zeros(12)

    for leg in LEG_ORDER:
        frame_id = pin_model.getFrameId(PIN_FOOT_FRAMES[leg])
        if frame_id >= len(pin_model.frames):
            raise RuntimeError(f"Cannot find Pinocchio foot frame: {PIN_FOOT_FRAMES[leg]}")

        j6 = pin.getFrameJacobian(
            pin_model,
            pin_data,
            frame_id,
            pin.ReferenceFrame.LOCAL_WORLD_ALIGNED,
        )
        j_pos = j6[:3, :]

        pin_slice_full = PIN_ACT_SLICE[leg]
        j_leg = j_pos[:, pin_slice_full]

        # Convert full Pinocchio actuated column slice to 12D actuated indexing.
        act_start = pin_slice_full.start - 6
        act_stop = pin_slice_full.stop - 6

        f_leg = foot_forces[leg]
        tau_pin_act[act_start:act_stop] += j_leg.T @ f_leg

    return pin_tau_to_mujoco_order(tau_pin_act)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="assets/go1/scene.xml")
    parser.add_argument("--urdf", default="assets/go1/urdf/go1.urdf")
    parser.add_argument("--force_scale", type=float, default=1.0)
    parser.add_argument("--sign", choices=["plus", "minus"], default="plus")
    args = parser.parse_args()

    np.set_printoptions(precision=8, suppress=True)

    model_path = Path(args.model)
    urdf_path = Path(args.urdf)

    if not model_path.exists():
        raise FileNotFoundError(model_path)
    if not urdf_path.exists():
        raise FileNotFoundError(urdf_path)

    mj_model = mujoco.MjModel.from_xml_path(str(model_path))
    mj_data = mujoco.MjData(mj_model)

    initialize_standing_pose(mj_model, mj_data, build_standing_q())

    mass = compute_total_mass(mj_model)
    g = abs(float(mj_model.opt.gravity[2]))
    mg = mass * g

    # Test force: equal upward force on four stance feet.
    # Convention here: f is the world-frame force applied at the foot/contact point
    # in the virtual-work mapping tau = J^T f.
    fz_each = args.force_scale * mg / 4.0
    sign = 1.0 if args.sign == "plus" else -1.0

    foot_forces = {
        leg: sign * np.array([0.0, 0.0, fz_each])
        for leg in LEG_ORDER
    }

    pin_model = pin.buildModelFromUrdf(str(urdf_path), pin.JointModelFreeFlyer())
    pin_data = pin_model.createData()
    pin_q = mujoco_to_pin_q(mj_data.qpos)

    tau_mj = compute_mujoco_jt_force_torque(
        mj_model,
        mj_data,
        foot_forces,
    )

    tau_pin = compute_pinocchio_jt_force_torque(
        pin_model,
        pin_data,
        pin_q,
        foot_forces,
    )

    diff = tau_mj - tau_pin

    print("=== Stage 6 Jacobian Transpose Torque Validation ===")
    print(f"model = {model_path}")
    print(f"urdf = {urdf_path}")
    print(f"mass = {mass:.6f} kg")
    print(f"gravity = {g:.6f}")
    print(f"mg = {mg:.6f} N")
    print(f"fz_each = {fz_each:.6f} N")
    print(f"sign convention = {args.sign}")
    print("tau convention in this script: tau = J^T f")
    print()

    print("Foot forces, world frame:")
    for leg in LEG_ORDER:
        print(f"  {leg}: {foot_forces[leg]}")
    print()

    print("tau_mujoco_order [FR, FL, RR, RL]:")
    print(tau_mj)
    print()

    print("tau_pinocchio_reordered_to_mujoco_order [FR, FL, RR, RL]:")
    print(tau_pin)
    print()

    print("diff = tau_mujoco - tau_pinocchio:")
    print(diff)
    print()

    print("Per-leg torque:")
    for leg in LEG_ORDER:
        s = MJ_ACT_SLICE[leg]
        print(
            f"  {leg}: "
            f"tau={tau_mj[s]}, "
            f"norm={np.linalg.norm(tau_mj[s]):.9f}, "
            f"max_abs={np.max(np.abs(tau_mj[s])):.9f}"
        )

    print()
    print(f"tau_shape = {tau_mj.shape}")
    print(f"tau_norm = {np.linalg.norm(tau_mj):.9f}")
    print(f"tau_max_abs = {np.max(np.abs(tau_mj)):.9f}")
    print(f"diff_norm = {np.linalg.norm(diff):.12f}")
    print(f"diff_max_abs = {np.max(np.abs(diff)):.12f}")

    if tau_mj.shape == (12,) and np.linalg.norm(diff) < 1e-8:
        print("PASS: MuJoCo and Pinocchio J^T f torque mapping match numerically.")
    else:
        print("WARN/FAIL: torque mapping mismatch. Check Jacobian frame, joint order, or sign convention.")


if __name__ == "__main__":
    main()
