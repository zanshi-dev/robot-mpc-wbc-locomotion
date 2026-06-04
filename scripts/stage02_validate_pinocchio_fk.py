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

    # Base position.
    pin_q[0:3] = mj_qpos[0:3]

    # Quaternion conversion.
    # MuJoCo free joint qpos: [x, y, z, qw, qx, qy, qz]
    # Pinocchio free-flyer q: [x, y, z, qx, qy, qz, qw]
    pin_q[3:7] = np.array([
        mj_qpos[4],
        mj_qpos[5],
        mj_qpos[6],
        mj_qpos[3],
    ])

    # Actuated joint order.
    # MuJoCo order:     FR, FL, RR, RL
    # Pinocchio order: FL, FR, RL, RR
    pin_q[7:19] = np.concatenate([
        mj_qpos[10:13],  # FL
        mj_qpos[7:10],   # FR
        mj_qpos[16:19],  # RL
        mj_qpos[13:16],  # RR
    ])

    # Base velocity is kept as-is for this FK-only check.
    # Velocity convention will be checked before Jacobian velocity validation.
    pin_v[0:6] = mj_qvel[0:6]

    pin_v[6:18] = np.concatenate([
        mj_qvel[9:12],   # FL
        mj_qvel[6:9],    # FR
        mj_qvel[15:18],  # RL
        mj_qvel[12:15],  # RR
    ])

    return pin_q, pin_v


def main():
    if not MJCF_PATH.exists():
        raise FileNotFoundError(MJCF_PATH)
    if not URDF_PATH.exists():
        raise FileNotFoundError(URDF_PATH)

    mj_model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    mj_data = mujoco.MjData(mj_model)

    pin_model = pin.buildModelFromUrdf(str(URDF_PATH), pin.JointModelFreeFlyer())
    pin_data = pin_model.createData()

    mujoco.mj_forward(mj_model, mj_data)

    pin_q, pin_v = mujoco_to_pin_qv(mj_data.qpos, mj_data.qvel)

    print("=== MuJoCo -> Pinocchio actuated joint mapping ===")
    print("Pin FL <= MuJoCo FL: q[7:10]   <= qpos[10:13]")
    print("Pin FR <= MuJoCo FR: q[10:13]  <= qpos[7:10]")
    print("Pin RL <= MuJoCo RL: q[13:16]  <= qpos[16:19]")
    print("Pin RR <= MuJoCo RR: q[16:19]  <= qpos[13:16]")

    print("\n=== q/v dimension check ===")
    print(f"MuJoCo qpos shape: {mj_data.qpos.shape}")
    print(f"MuJoCo qvel shape: {mj_data.qvel.shape}")
    print(f"Pin q shape:       {pin_q.shape}")
    print(f"Pin v shape:       {pin_v.shape}")

    print("\n=== Base quaternion check ===")
    print(f"MuJoCo qpos[3:7] [qw qx qy qz] = {mj_data.qpos[3:7]}")
    print(f"Pin q[3:7]       [qx qy qz qw] = {pin_q[3:7]}")
    print(f"Pin q norm = {np.linalg.norm(pin_q[3:7]):.8f}")

    pin.forwardKinematics(pin_model, pin_data, pin_q, pin_v)
    pin.updateFramePlacements(pin_model, pin_data)

    print("\n=== Pinocchio foot positions in world frame ===")
    for leg, frame_name in FOOT_FRAMES.items():
        fid = pin_model.getFrameId(frame_name)
        pos = pin_data.oMf[fid].translation
        print(f"{leg} {frame_name:8s} frame_id={fid:2d} pos={pos}")

    print("\nStage 2 FK mapping script finished.")


if __name__ == "__main__":
    main()
