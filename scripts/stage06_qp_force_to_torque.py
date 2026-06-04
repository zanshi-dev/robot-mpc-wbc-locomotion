#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


SCENE = "assets/go1/scene.xml"
INPUT_CSV = "results/logs_sample/stage05_standing_contact_force_qp.csv"
OUTPUT_CSV = "results/logs_sample/stage06_qp_force_to_actuator_torque.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]
TORQUE_LIMIT = 23.7


def read_forces(path):
    forces = {}
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            leg = row["leg"].strip().upper()
            if leg in LEG_ORDER:
                forces[leg] = np.array(
                    [float(row["fx"]), float(row["fy"]), float(row["fz"])],
                    dtype=float,
                )

    missing = [leg for leg in LEG_ORDER if leg not in forces]
    if missing:
        raise RuntimeError(f"missing force rows for legs: {missing}")

    return forces


def name_or_empty(model, obj_type, idx):
    name = mujoco.mj_id2name(model, obj_type, idx)
    return "" if name is None else name


def find_foot_geom_or_body(model, leg):
    # Go1 Menagerie uses exact site/geom names: FR, FL, RR, RL.
    for obj_type, label, count in [
        (mujoco.mjtObj.mjOBJ_SITE, "site", model.nsite),
        (mujoco.mjtObj.mjOBJ_GEOM, "geom", model.ngeom),
        (mujoco.mjtObj.mjOBJ_BODY, "body", model.nbody),
    ]:
        exact_id = mujoco.mj_name2id(model, obj_type, leg)
        if exact_id >= 0:
            return label, exact_id, leg

        for i in range(count):
            name = name_or_empty(model, obj_type, i)
            if leg.lower() in name.lower():
                return label, i, name

    raise RuntimeError(f"cannot find foot site/geom/body for {leg}")

def foot_pos(data, target):
    label, idx, _ = target
    if label == "site":
        return np.array(data.site_xpos[idx], dtype=float)
    if label == "geom":
        return np.array(data.geom_xpos[idx], dtype=float)
    return np.array(data.xpos[idx], dtype=float)

def foot_jacobian(model, data, target):
    label, idx, _ = target
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))

    if label == "site":
        mujoco.mj_jacSite(model, data, jacp, jacr, idx)
    elif label == "geom":
        mujoco.mj_jacGeom(model, data, jacp, jacr, idx)
    else:
        mujoco.mj_jacBody(model, data, jacp, jacr, idx)

    return jacp

def set_standing_pose(model, data):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0

    data.qpos[0:3] = [0.0, 0.0, 0.32]
    data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]

    for act_id in range(model.nu):
        joint_id = int(model.actuator_trnid[act_id, 0])
        qadr = int(model.jnt_qposadr[joint_id])
        data.qpos[qadr] = STANDING_Q_PER_LEG[act_id % 3]

    mujoco.mj_forward(model, data)

    targets = {leg: find_foot_geom_or_body(model, leg) for leg in LEG_ORDER}
    min_z = min(foot_pos(data, targets[leg])[2] for leg in LEG_ORDER)
    data.qpos[2] += 0.02 - min_z

    mujoco.mj_forward(model, data)
    return targets


def actuator_dofs(model):
    dofs = []
    names = []
    for act_id in range(model.nu):
        joint_id = int(model.actuator_trnid[act_id, 0])
        dofs.append(int(model.jnt_dofadr[joint_id]))
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, act_id)
        names.append(name if name else f"actuator_{act_id}")
    return dofs, names


def main():
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"expected nu=12, got {model.nu}")

    forces = read_forces(INPUT_CSV)
    targets = set_standing_pose(model, data)
    dofs, actuator_names = actuator_dofs(model)

    tau_full = np.zeros(model.nv)

    for leg in LEG_ORDER:
        Jp = foot_jacobian(model, data, targets[leg])
        tau_full += Jp.T @ (-forces[leg])

    tau = tau_full[dofs]

    tau_norm = float(np.linalg.norm(tau))
    tau_max_abs = float(np.max(np.abs(tau)))
    torque_limit_pass = tau_max_abs <= TORQUE_LIMIT

    print("Stage 6 QP force -> actuator torque")
    print("sign_convention=actuator_tau = - J^T f_qp")
    print(f"tau_norm={tau_norm:.12f}")
    print(f"tau_max_abs={tau_max_abs:.12f}")
    print(f"torque_limit={TORQUE_LIMIT:.12f}")
    print(f"torque_limit_pass={torque_limit_pass}")

    for leg_i, leg in enumerate(LEG_ORDER):
        f = forces[leg]
        t = tau[3 * leg_i : 3 * leg_i + 3]
        print(
            f"{leg}: "
            f"force=[{f[0]: .9f}, {f[1]: .9f}, {f[2]: .9f}] "
            f"tau=[{t[0]: .9f}, {t[1]: .9f}, {t[2]: .9f}]"
        )

    row = {}

    for leg in LEG_ORDER:
        f = forces[leg]
        row[f"{leg}_fx"] = f"{f[0]:.12f}"
        row[f"{leg}_fy"] = f"{f[1]:.12f}"
        row[f"{leg}_fz"] = f"{f[2]:.12f}"

    for leg_i, leg in enumerate(LEG_ORDER):
        t = tau[3 * leg_i : 3 * leg_i + 3]
        for j_i, joint in enumerate(JOINTS):
            row[f"{leg}_tau_{joint}"] = f"{t[j_i]:.12f}"

    row["sign_convention"] = "actuator_tau = - J^T f_qp"
    row["tau_norm"] = f"{tau_norm:.12f}"
    row["tau_max_abs"] = f"{tau_max_abs:.12f}"
    row["torque_limit"] = f"{TORQUE_LIMIT:.12f}"
    row["torque_limit_pass"] = str(torque_limit_pass)

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    print(f"saved={OUTPUT_CSV}")

    if not torque_limit_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
