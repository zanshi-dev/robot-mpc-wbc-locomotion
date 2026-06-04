from pathlib import Path

import mujoco
import numpy as np
import pinocchio as pin


MJCF_PATH = Path("assets/go1/scene.xml")
URDF_PATH = Path("assets/go1/urdf/go1.urdf")

PIN_FOOT_FRAMES = {
    "FR": "FR_foot",
    "FL": "FL_foot",
    "RR": "RR_foot",
    "RL": "RL_foot",
}

MJ_FOOT_GEOMS = {
    "FR": "FR",
    "FL": "FL",
    "RR": "RR",
    "RL": "RL",
}


def mujoco_to_pin_qv(mj_qpos: np.ndarray, mj_qvel: np.ndarray):
    pin_q = np.zeros(19)
    pin_v = np.zeros(18)

    # Base position.
    pin_q[0:3] = mj_qpos[0:3]

    # MuJoCo:     [x, y, z, qw, qx, qy, qz]
    # Pinocchio: [x, y, z, qx, qy, qz, qw]
    pin_q[3:7] = np.array([
        mj_qpos[4],
        mj_qpos[5],
        mj_qpos[6],
        mj_qpos[3],
    ])

    # MuJoCo joint order:     FR, FL, RR, RL
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


def get_mujoco_geom_position(model, data, geom_name):
    geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
    if geom_id < 0:
        raise RuntimeError(f"MuJoCo geom not found: {geom_name}")
    return data.geom_xpos[geom_id].copy()


def main():
    if not MJCF_PATH.exists():
        raise FileNotFoundError(MJCF_PATH)
    if not URDF_PATH.exists():
        raise FileNotFoundError(URDF_PATH)

    mj_model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    mj_data = mujoco.MjData(mj_model)
    mujoco.mj_forward(mj_model, mj_data)

    pin_model = pin.buildModelFromUrdf(str(URDF_PATH), pin.JointModelFreeFlyer())
    pin_data = pin_model.createData()

    pin_q, pin_v = mujoco_to_pin_qv(mj_data.qpos, mj_data.qvel)

    pin.forwardKinematics(pin_model, pin_data, pin_q, pin_v)
    pin.updateFramePlacements(pin_model, pin_data)

    print("=== MuJoCo-Pinocchio foot FK comparison ===")
    print("leg, mujoco_geom, pin_frame, mujoco_pos, pin_pos, error_norm")

    max_err = 0.0

    for leg in ["FR", "FL", "RR", "RL"]:
        mj_geom = MJ_FOOT_GEOMS[leg]
        pin_frame = PIN_FOOT_FRAMES[leg]

        mj_pos = get_mujoco_geom_position(mj_model, mj_data, mj_geom)

        frame_id = pin_model.getFrameId(pin_frame)
        if frame_id >= len(pin_model.frames):
            raise RuntimeError(f"Pinocchio frame not found: {pin_frame}")

        pin_pos = pin_data.oMf[frame_id].translation.copy()
        err = float(np.linalg.norm(mj_pos - pin_pos))
        max_err = max(max_err, err)

        print(
            f"{leg}, "
            f"{mj_geom}, "
            f"{pin_frame}, "
            f"mj={mj_pos}, "
            f"pin={pin_pos}, "
            f"err={err:.6f}"
        )

    print(f"\nmax_error = {max_err:.6f} m")

    if max_err < 0.03:
        print("PASS: FK alignment is within 3 cm at initial configuration.")
    elif max_err < 0.08:
        print("WARN: FK alignment is within 8 cm. Check foot geom center vs foot frame offset.")
    else:
        print("FAIL: FK alignment error is large. Check joint order, quaternion convention, or URDF/MJCF frame mismatch.")


if __name__ == "__main__":
    main()
