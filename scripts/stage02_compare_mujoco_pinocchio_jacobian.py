from pathlib import Path

import mujoco
import numpy as np
import pinocchio as pin


MJCF_PATH = Path("assets/go1/scene.xml")
URDF_PATH = Path("assets/go1/urdf/go1.urdf")

FOOT_PAIRS = {
    "FR": ("FR", "FR_foot"),
    "FL": ("FL", "FL_foot"),
    "RR": ("RR", "RR_foot"),
    "RL": ("RL", "RL_foot"),
}


def mujoco_to_pin_qv(mj_qpos: np.ndarray, mj_qvel: np.ndarray):
    pin_q = np.zeros(19)
    pin_v = np.zeros(18)

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

    pin_v[0:6] = mj_qvel[0:6]

    pin_v[6:18] = np.concatenate([
        mj_qvel[9:12],   # FL
        mj_qvel[6:9],    # FR
        mj_qvel[15:18],  # RL
        mj_qvel[12:15],  # RR
    ])

    return pin_q, pin_v


def pin_actuated_jacobian_to_mujoco_order(pin_j_pos: np.ndarray):
    # Pinocchio actuator velocity columns:
    # FL: 6:9, FR: 9:12, RL: 12:15, RR: 15:18
    #
    # MuJoCo actuator velocity columns:
    # FR: 6:9, FL: 9:12, RR: 12:15, RL: 15:18
    return np.concatenate([
        pin_j_pos[:, 9:12],   # FR
        pin_j_pos[:, 6:9],    # FL
        pin_j_pos[:, 15:18],  # RR
        pin_j_pos[:, 12:15],  # RL
    ], axis=1)


def main():
    mj_model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    mj_data = mujoco.MjData(mj_model)
    mujoco.mj_forward(mj_model, mj_data)

    pin_model = pin.buildModelFromUrdf(str(URDF_PATH), pin.JointModelFreeFlyer())
    pin_data = pin_model.createData()

    pin_q, pin_v = mujoco_to_pin_qv(mj_data.qpos, mj_data.qvel)

    pin.forwardKinematics(pin_model, pin_data, pin_q, pin_v)
    pin.computeJointJacobians(pin_model, pin_data, pin_q)
    pin.updateFramePlacements(pin_model, pin_data)

    print("=== MuJoCo-Pinocchio foot Jacobian comparison ===")
    print("Compare only actuated joint columns.")
    print("MuJoCo order:     FR, FL, RR, RL")
    print("Pinocchio order:  FL, FR, RL, RR")
    print("Pinocchio columns are reordered to MuJoCo order before comparison.\n")

    max_err = 0.0

    for leg, (mj_geom_name, pin_frame_name) in FOOT_PAIRS.items():
        geom_id = mujoco.mj_name2id(mj_model, mujoco.mjtObj.mjOBJ_GEOM, mj_geom_name)
        if geom_id < 0:
            raise RuntimeError(f"MuJoCo foot geom not found: {mj_geom_name}")

        frame_id = pin_model.getFrameId(pin_frame_name)
        if frame_id >= len(pin_model.frames):
            raise RuntimeError(f"Pinocchio foot frame not found: {pin_frame_name}")

        mj_jacp = np.zeros((3, mj_model.nv))
        mj_jacr = np.zeros((3, mj_model.nv))
        mujoco.mj_jacGeom(mj_model, mj_data, mj_jacp, mj_jacr, geom_id)

        pin_j6 = pin.getFrameJacobian(
            pin_model,
            pin_data,
            frame_id,
            pin.ReferenceFrame.LOCAL_WORLD_ALIGNED,
        )
        pin_j_pos = pin_j6[:3, :]

        mj_act = mj_jacp[:, 6:18]
        pin_act_in_mj_order = pin_actuated_jacobian_to_mujoco_order(pin_j_pos)

        diff = mj_act - pin_act_in_mj_order
        err = float(np.linalg.norm(diff))
        max_abs = float(np.max(np.abs(diff)))
        max_err = max(max_err, err)

        print(f"{leg}")
        print(f"  MuJoCo geom: {mj_geom_name}, geom_id={geom_id}")
        print(f"  Pin frame:   {pin_frame_name}, frame_id={frame_id}")
        print(f"  mj_act shape:  {mj_act.shape}")
        print(f"  pin_act shape: {pin_act_in_mj_order.shape}")
        print(f"  error_norm = {err:.10f}")
        print(f"  max_abs_error = {max_abs:.10f}")
        print("  diff =")
        print(diff)

    print(f"\nmax_error_norm = {max_err:.10f}")

    if max_err < 1e-8:
        print("PASS: MuJoCo and Pinocchio actuated foot Jacobians match numerically.")
    elif max_err < 1e-5:
        print("PASS: Jacobian alignment is within numerical tolerance.")
    elif max_err < 1e-3:
        print("WARN: Small Jacobian mismatch. Check frame convention before using J^T f.")
    else:
        print("FAIL: Large Jacobian mismatch. Check joint order, frame choice, or reference frame convention.")


if __name__ == "__main__":
    main()
