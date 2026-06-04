import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np


def obj_name(model, obj_type, obj_id):
    name = mujoco.mj_id2name(model, obj_type, obj_id)
    return name if name is not None else f"unnamed_{obj_id}"


def find_base_body(model, requested_name):
    if requested_name:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, requested_name)
        if body_id < 0:
            raise RuntimeError(f"Requested base body not found: {requested_name}")
        return body_id, requested_name

    candidates = ["trunk", "base", "body", "torso", "pelvis"]
    for name in candidates:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        if body_id >= 0:
            return body_id, name

    raise RuntimeError(
        "Cannot find base body automatically. "
        "Run scripts/stage00_inspect_go1_model.py and pass --base_body BODY_NAME."
    )


def print_model_summary(model):
    print("=== MuJoCo model summary ===")
    print(f"nq = {model.nq}")
    print(f"nv = {model.nv}")
    print(f"nu = {model.nu}")
    print(f"nbody = {model.nbody}")
    print(f"njnt = {model.njnt}")
    print(f"ngeom = {model.ngeom}")

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
        print(f"[{i}] {aname:12s} -> {joint_name}")


def contact_pairs(model, data):
    pairs = []
    for i in range(data.ncon):
        c = data.contact[i]
        g1 = obj_name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1)
        g2 = obj_name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2)
        pairs.append(f"{g1}<->{g2}")
    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="assets/stage00_minimal_leg.xml")
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--log", default="results/logs_sample/stage00_torque_log.csv")
    parser.add_argument("--base_body", default="")
    parser.add_argument("--torque_scale", type=float, default=1.0)
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    print_model_summary(model)

    if model.nu == 0:
        raise RuntimeError("model.nu == 0. No actuator found. Torque control cannot be tested.")

    base_id, base_name = find_base_body(model, args.base_body)
    print(f"\nUsing base body: {base_name}, body_id={base_id}")

    qpos0 = data.qpos.copy()
    qvel0 = data.qvel.copy()

    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "step",
            "time",
            "base_x",
            "base_y",
            "base_z",
            "qpos_norm",
            "qvel_norm",
            "ctrl_norm",
            "n_contact",
            "contact_pairs",
        ])

        for step in range(args.steps):
            t = data.time

            data.ctrl[:] = 0.0

            # Stage 0 only verifies torque write/read.
            # Use small sinusoidal torques on the first two actuators.
            data.ctrl[0] = args.torque_scale * np.sin(2.0 * np.pi * 1.0 * t)
            if model.nu > 1:
                data.ctrl[1] = 0.5 * args.torque_scale * np.cos(2.0 * np.pi * 1.0 * t)

            mujoco.mj_step(model, data)

            pairs = contact_pairs(model, data)

            writer.writerow([
                step,
                data.time,
                data.xpos[base_id, 0],
                data.xpos[base_id, 1],
                data.xpos[base_id, 2],
                float(np.linalg.norm(data.qpos - qpos0)),
                float(np.linalg.norm(data.qvel - qvel0)),
                float(np.linalg.norm(data.ctrl)),
                data.ncon,
                "|".join(pairs),
            ])

            if step % 200 == 0:
                print(
                    f"step={step:04d} "
                    f"time={data.time:.3f} "
                    f"base_pos={data.xpos[base_id].copy()} "
                    f"ctrl_norm={np.linalg.norm(data.ctrl):.4f} "
                    f"qpos_norm={np.linalg.norm(data.qpos - qpos0):.4f} "
                    f"qvel_norm={np.linalg.norm(data.qvel - qvel0):.4f} "
                    f"contacts={pairs}"
                )

    print(f"Log saved to: {log_path}")


if __name__ == "__main__":
    main()
