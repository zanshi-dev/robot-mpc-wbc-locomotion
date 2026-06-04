from pathlib import Path

import mujoco
import pinocchio as pin


MJCF_PATH = Path("assets/go1/scene.xml")
URDF_PATH = Path("assets/go1/urdf/go1.urdf")


def mj_name(model, obj_type, obj_id):
    name = mujoco.mj_id2name(model, obj_type, obj_id)
    return name if name is not None else f"unnamed_{obj_id}"


def main():
    if not MJCF_PATH.exists():
        raise FileNotFoundError(MJCF_PATH)
    if not URDF_PATH.exists():
        raise FileNotFoundError(URDF_PATH)

    mj_model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    pin_model = pin.buildModelFromUrdf(str(URDF_PATH), pin.JointModelFreeFlyer())

    print("=== Dimension check ===")
    print(f"MuJoCo:     nq={mj_model.nq}, nv={mj_model.nv}, nu={mj_model.nu}")
    print(f"Pinocchio: nq={pin_model.nq}, nv={pin_model.nv}")

    print("\n=== MuJoCo joint order ===")
    mj_hinge_joints = []
    for jid in range(mj_model.njnt):
        name = mj_name(mj_model, mujoco.mjtObj.mjOBJ_JOINT, jid)
        qadr = int(mj_model.jnt_qposadr[jid])
        dadr = int(mj_model.jnt_dofadr[jid])
        jtype = int(mj_model.jnt_type[jid])
        print(f"[{jid:02d}] {name:20s} qposadr={qadr:2d} dofadr={dadr:2d} type={jtype}")
        if qadr >= 7:
            mj_hinge_joints.append(name)

    print("\n=== Pinocchio joint order ===")
    pin_actuated_joints = []
    for jid, name in enumerate(pin_model.names):
        nq = int(pin_model.nqs[jid])
        nv = int(pin_model.nvs[jid])
        idx_q = int(pin_model.idx_qs[jid])
        idx_v = int(pin_model.idx_vs[jid])
        print(f"[{jid:02d}] {name:20s} idx_q={idx_q:2d} idx_v={idx_v:2d} nq={nq} nv={nv}")
        if idx_q >= 7 and nq == 1 and nv == 1:
            pin_actuated_joints.append(name)

    print("\n=== Actuated joint order comparison ===")
    print("MuJoCo:")
    for i, name in enumerate(mj_hinge_joints):
        print(f"  [{i:02d}] {name}")

    print("Pinocchio:")
    for i, name in enumerate(pin_actuated_joints):
        print(f"  [{i:02d}] {name}")

    print("\n=== Name-by-name comparison ===")
    same_order = True
    for i, (mj_name_i, pin_name_i) in enumerate(zip(mj_hinge_joints, pin_actuated_joints)):
        ok = mj_name_i == pin_name_i
        same_order = same_order and ok
        print(f"[{i:02d}] MuJoCo={mj_name_i:20s} Pinocchio={pin_name_i:20s} same={ok}")

    print(f"\nSame actuated joint order: {same_order}")

    print("\n=== Foot frame ids ===")
    for frame_name in ["FR_foot", "FL_foot", "RR_foot", "RL_foot"]:
        fid = pin_model.getFrameId(frame_name)
        print(f"{frame_name}: frame_id={fid}")


if __name__ == "__main__":
    main()