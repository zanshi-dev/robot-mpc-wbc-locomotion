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
    pin_q[3:7] = np.array([
        mj_qpos[4],
        mj_qpos[5],
        mj_qpos[6],
        mj_qpos[3],
    ])

    pin_q[7:19] = np.concatenate([
        mj_qpos[10:13],  # FL
        mj_qpos[7:10],   # FR
        mj_qpos[16:19],  # RL
        mj_qpos[13:16],  # RR
    ])

    # At the initial upright configuration, this tests whether MuJoCo and
    # Pinocchio use compatible [linear, angular] base velocity convention.
    pin_v[0:6] = mj_qvel[0:6]

    pin_v[6:18] = np.concatenate([
        mj_qvel[9:12],   # FL
        mj_qvel[6:9],    # FR
        mj_qvel[15:18],  # RL
        mj_qvel[12:15],  # RR
    ])

    return pin_q, pin_v


def main():
    np.set_printoptions(precision=8, suppress=True)

    mj_model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    mj_data = mujoco.MjData(mj_model)

    mj_data.qvel[:] = 0.0

    # Base linear velocity + base angular velocity.
    mj_data.qvel[0:6] = np.array([0.10, -0.05, 0.03, 0.20, -0.10, 0.15])

    # Actuated joint velocities in MuJoCo order: FR, FL, RR, RL.
    mj_data.qvel[6:18] = np.array([
        0.10, -0.20, 0.30,
        -0.15, 0.25, -0.35,
        0.12, -0.22, 0.32,
        -0.18, 0.28, -0.38,
    ])

    mujoco.mj_forward(mj_model, mj_data)

    pin_model = pin.buildModelFromUrdf(str(URDF_PATH), pin.JointModelFreeFlyer())
    pin_data = pin_model.createData()

    pin_q, pin_v = mujoco_to_pin_qv(mj_data.qpos, mj_data.qvel)

    pin.forwardKinematics(pin_model, pin_data, pin_q, pin_v)
    pin.computeJointJacobians(pin_model, pin_data, pin_q)
    pin.updateFramePlacements(pin_model, pin_data)

    print("=== Full foot velocity comparison ===")
    print("This test includes floating-base velocity and actuated joint velocity.")
    print(f"MuJoCo qvel[0:6] = {mj_data.qvel[0:6]}")
    print(f"Pin v[0:6]       = {pin_v[0:6]}")
    print()

    max_err = 0.0

    for leg, (mj_geom_name, pin_frame_name) in FOOT_PAIRS.items():
        geom_id = mujoco.mj_name2id(mj_model, mujoco.mjtObj.mjOBJ_GEOM, mj_geom_name)
        frame_id = pin_model.getFrameId(pin_frame_name)

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

        # Reorder only actuated columns. Base columns remain 0:6.
        pin_j_full_in_mj_order = np.zeros((3, 18))
        pin_j_full_in_mj_order[:, 0:6] = pin_j_pos[:, 0:6]
        pin_j_full_in_mj_order[:, 6:18] = np.concatenate([
            pin_j_pos[:, 9:12],   # FR
            pin_j_pos[:, 6:9],    # FL
            pin_j_pos[:, 15:18],  # RR
            pin_j_pos[:, 12:15],  # RL
        ], axis=1)

        pin_v_in_mj_order = np.zeros(18)
        pin_v_in_mj_order[0:6] = pin_v[0:6]
        pin_v_in_mj_order[6:18] = np.concatenate([
            pin_v[9:12],    # FR
            pin_v[6:9],     # FL
            pin_v[15:18],   # RR
            pin_v[12:15],   # RL
        ])

        mj_vel = mj_jacp @ mj_data.qvel
        pin_vel = pin_j_full_in_mj_order @ pin_v_in_mj_order

        diff = mj_vel - pin_vel
        err = float(np.linalg.norm(diff))
        max_err = max(max_err, err)

        print(f"{leg}")
        print(f"  MuJoCo full foot vel:    {mj_vel}")
        print(f"  Pinocchio full foot vel: {pin_vel}")
        print(f"  diff:                    {diff}")
        print(f"  error_norm:              {err:.12f}")

    print(f"\nmax_full_velocity_error = {max_err:.12f}")

    if max_err < 1e-10:
        print("PASS: full foot velocity mapping matches numerically.")
    elif max_err < 1e-6:
        print("PASS: full foot velocity mapping is within tolerance.")
    else:
        print("WARN/FAIL: full velocity mismatch. Base velocity convention must be handled explicitly.")


if __name__ == "__main__":
    main()
