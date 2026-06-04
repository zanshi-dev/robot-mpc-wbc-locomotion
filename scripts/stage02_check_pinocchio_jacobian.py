from pathlib import Path

import mujoco
import numpy as np
import pinocchio as pin


MJCF_PATH = Path("assets/go1/scene.xml")
URDF_PATH = Path("assets/go1/urdf/go1.urdf")

FOOT_FRAMES = {
    "FR": "FR_foot",
    "FL": "FL_foot",
    "RR": "RR_foot",
    "RL": "RL_foot",
}


def mujoco_to_pin_qv(mj_qpos: np.ndarray, mj_qvel: np.ndarray):
    pin_q = np.zeros(19)
    pin_v = np.zeros(18)

    pin_q[0:3] = mj_qpos[0:3]
    pin_q[3:7] = np.array([mj_qpos[4], mj_qpos[5], mj_qpos[6], mj_qpos[3]])

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


def main():
    mj_model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    mj_data = mujoco.MjData(mj_model)
    mujoco.mj_forward(mj_model, mj_data)

    model = pin.buildModelFromUrdf(str(URDF_PATH), pin.JointModelFreeFlyer())
    data = model.createData()

    q, v = mujoco_to_pin_qv(mj_data.qpos, mj_data.qvel)

    pin.forwardKinematics(model, data, q, v)
    pin.computeJointJacobians(model, data, q)
    pin.updateFramePlacements(model, data)

    print("=== Pinocchio foot Jacobian check ===")
    print(f"model.nq = {model.nq}")
    print(f"model.nv = {model.nv}")

    for leg, frame_name in FOOT_FRAMES.items():
        fid = model.getFrameId(frame_name)

        # LOCAL_WORLD_ALIGNED gives a world-aligned 6 x nv frame Jacobian.
        J6 = pin.getFrameJacobian(
            model,
            data,
            fid,
            pin.ReferenceFrame.LOCAL_WORLD_ALIGNED,
        )

        J_pos = J6[:3, :]
        J_leg = J_pos[:, 6:18]

        rank = np.linalg.matrix_rank(J_pos)
        norm = np.linalg.norm(J_pos)

        print(f"\n{leg} {frame_name}")
        print(f"frame_id = {fid}")
        print(f"J6 shape = {J6.shape}")
        print(f"J_pos shape = {J_pos.shape}")
        print(f"J_leg block shape = {J_leg.shape}")
        print(f"J_pos rank = {rank}")
        print(f"J_pos norm = {norm:.6f}")
        print("J_pos[:, 6:18] =")
        print(J_leg)

    print("\nStage 2 Jacobian check finished.")


if __name__ == "__main__":
    main()
