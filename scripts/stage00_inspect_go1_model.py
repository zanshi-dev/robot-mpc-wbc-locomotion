import argparse
from pathlib import Path

import mujoco


def obj_name(model, obj_type, obj_id):
    name = mujoco.mj_id2name(model, obj_type, obj_id)
    return name if name is not None else f"unnamed_{obj_id}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="assets/go1/go1.xml")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    model = mujoco.MjModel.from_xml_path(str(model_path))

    print("=== model dimensions ===")
    print(f"nq = {model.nq}")
    print(f"nv = {model.nv}")
    print(f"nu = {model.nu}")
    print(f"nbody = {model.nbody}")
    print(f"njnt = {model.njnt}")
    print(f"ngeom = {model.ngeom}")

    print("\n=== bodies ===")
    for i in range(model.nbody):
        print(f"[{i}] {obj_name(model, mujoco.mjtObj.mjOBJ_BODY, i)}")

    print("\n=== joints ===")
    for i in range(model.njnt):
        jname = obj_name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        qadr = model.jnt_qposadr[i]
        dadr = model.jnt_dofadr[i]
        print(f"[{i}] {jname:20s} qposadr={qadr:2d} dofadr={dadr:2d}")

    print("\n=== actuators ===")
    for i in range(model.nu):
        aname = obj_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
        trnid0 = model.actuator_trnid[i, 0]
        joint_name = obj_name(model, mujoco.mjtObj.mjOBJ_JOINT, trnid0)
        ctrl_min = model.actuator_ctrlrange[i, 0]
        ctrl_max = model.actuator_ctrlrange[i, 1]
        print(f"[{i}] {aname:12s} -> joint={joint_name:20s} ctrlrange=[{ctrl_min:.2f}, {ctrl_max:.2f}]")

    print("\n=== geoms ===")
    for i in range(model.ngeom):
        gname = obj_name(model, mujoco.mjtObj.mjOBJ_GEOM, i)
        body_id = model.geom_bodyid[i]
        body_name = obj_name(model, mujoco.mjtObj.mjOBJ_BODY, body_id)
        print(f"[{i}] {gname:20s} body={body_name}")

    print("\n=== base body candidates ===")
    candidates = ["trunk", "base", "body", "torso", "pelvis"]
    found = False
    for name in candidates:
        bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        if bid >= 0:
            print(f"candidate found: {name}, body_id={bid}")
            found = True

    if not found:
        print("No common base body name found. Use the body list above to select the trunk manually.")


if __name__ == "__main__":
    main()
