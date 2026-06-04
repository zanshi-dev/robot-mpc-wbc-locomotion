#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


SCENE = "assets/go1/scene.xml"
OUTPUT_CSV = "results/logs_sample/stage07_swing_foot_tracking_qp.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

CONTACT_MODES = {
    "trot_FR_RL": {"stance": ["FR", "RL"], "swing": ["FL", "RR"]},
    "trot_FL_RR": {"stance": ["FL", "RR"], "swing": ["FR", "RL"]},
}

SWING_DZ = 0.06
SWING_DX = 0.03
MAX_DQ = 0.35

W_SWING = 100.0
W_STANCE = 10.0
W_REG = 1e-4


def actuator_indices(model):
    dofs = []
    qadrs = []

    for act_id in range(model.nu):
        jid = int(model.actuator_trnid[act_id, 0])
        dofs.append(int(model.jnt_dofadr[jid]))
        qadrs.append(int(model.jnt_qposadr[jid]))

    return dofs, qadrs


def set_standing_pose(model, data):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0

    data.qpos[0:3] = [0.0, 0.0, 0.32]
    data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]

    for act_id in range(model.nu):
        jid = int(model.actuator_trnid[act_id, 0])
        qadr = int(model.jnt_qposadr[jid])
        data.qpos[qadr] = STANDING_Q_PER_LEG[act_id % 3]

    mujoco.mj_forward(model, data)

    site_ids = {}
    for leg in LEG_ORDER:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, leg)
        if sid < 0:
            raise RuntimeError(f"找不到 foot site: {leg}")
        site_ids[leg] = sid

    min_foot_z = min(float(data.site_xpos[site_ids[leg]][2]) for leg in LEG_ORDER)
    data.qpos[2] += 0.02 - min_foot_z

    mujoco.mj_forward(model, data)

    return site_ids


def leg_actuator_slice(leg):
    i = LEG_ORDER.index(leg)
    return slice(3 * i, 3 * i + 3)


def foot_jac_actuated(model, data, site_id, dofs):
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    return jacp[:, dofs]


def solve_mode(model, data, site_ids, dofs, mode_name, mode_cfg):
    n = 12

    H = W_REG * np.eye(n)
    g = np.zeros(n)

    swing_rows = []
    swing_targets = []

    for leg in mode_cfg["swing"]:
        J = foot_jac_actuated(model, data, site_ids[leg], dofs)
        dx_des = np.array([SWING_DX, 0.0, SWING_DZ])

        H += W_SWING * (J.T @ J)
        g += -W_SWING * (J.T @ dx_des)

        swing_rows.append(J)
        swing_targets.append(dx_des)

    for leg in mode_cfg["stance"]:
        sl = leg_actuator_slice(leg)
        S = np.zeros((3, n))
        S[:, sl] = np.eye(3)
        H += W_STANCE * (S.T @ S)

    P = sp.csc_matrix(2.0 * H)
    q = 2.0 * g

    A = sp.eye(n, format="csc")
    l = -MAX_DQ * np.ones(n)
    u = MAX_DQ * np.ones(n)

    solver = osqp.OSQP()
    solver.setup(P=P, q=q, A=A, l=l, u=u, verbose=False, polish=True)
    result = solver.solve()

    if result.x is None:
        raise RuntimeError(f"{mode_name} OSQP failed: {result.info.status}")

    dq = np.array(result.x)

    max_abs_dq = float(np.max(np.abs(dq)))
    swing_error_sq = 0.0
    swing_target_sq = 0.0
    max_swing_error = 0.0
    max_stance_dq = 0.0

    row = {
        "mode": mode_name,
        "osqp_status": result.info.status,
        "objective": f"{result.info.obj_val:.12f}",
        "swing_legs": ",".join(mode_cfg["swing"]),
        "stance_legs": ",".join(mode_cfg["stance"]),
        "swing_dx": SWING_DX,
        "swing_dz": SWING_DZ,
        "max_dq_limit": MAX_DQ,
        "w_swing": W_SWING,
        "w_stance": W_STANCE,
        "w_reg": W_REG,
        "max_abs_dq": f"{max_abs_dq:.12f}",
    }

    for leg in LEG_ORDER:
        sl = leg_actuator_slice(leg)
        dq_leg = dq[sl]

        row[f"{leg}_dq_hip"] = f"{dq_leg[0]:.12f}"
        row[f"{leg}_dq_thigh"] = f"{dq_leg[1]:.12f}"
        row[f"{leg}_dq_calf"] = f"{dq_leg[2]:.12f}"

        if leg in mode_cfg["stance"]:
            max_stance_dq = max(max_stance_dq, float(np.max(np.abs(dq_leg))))

        J = foot_jac_actuated(model, data, site_ids[leg], dofs)
        foot_delta = J @ dq

        row[f"{leg}_foot_dx"] = f"{foot_delta[0]:.12f}"
        row[f"{leg}_foot_dy"] = f"{foot_delta[1]:.12f}"
        row[f"{leg}_foot_dz"] = f"{foot_delta[2]:.12f}"

        if leg in mode_cfg["swing"]:
            target = np.array([SWING_DX, 0.0, SWING_DZ])
            err = foot_delta - target
            err_norm = float(np.linalg.norm(err))

            swing_error_sq += float(err @ err)
            swing_target_sq += float(target @ target)
            max_swing_error = max(max_swing_error, err_norm)

            row[f"{leg}_swing_error_norm"] = f"{err_norm:.12f}"
        else:
            row[f"{leg}_swing_error_norm"] = ""

    swing_error_norm = float(np.sqrt(swing_error_sq))
    swing_target_norm = float(np.sqrt(swing_target_sq))
    swing_relative_error = swing_error_norm / max(swing_target_norm, 1e-12)

    status_pass = result.info.status.lower() in ["solved", "solved inaccurate"]
    dq_pass = max_abs_dq <= MAX_DQ + 1e-9
    swing_pass = swing_relative_error < 0.25
    stance_pass = max_stance_dq < 0.05

    pass_test = bool(status_pass and dq_pass and swing_pass and stance_pass)

    row["swing_error_norm"] = f"{swing_error_norm:.12f}"
    row["swing_target_norm"] = f"{swing_target_norm:.12f}"
    row["swing_relative_error"] = f"{swing_relative_error:.12f}"
    row["max_swing_error"] = f"{max_swing_error:.12f}"
    row["max_stance_dq"] = f"{max_stance_dq:.12f}"
    row["dq_pass"] = str(dq_pass)
    row["swing_pass"] = str(swing_pass)
    row["stance_pass"] = str(stance_pass)
    row["pass"] = str(pass_test)

    return row


def main():
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, qadrs = actuator_indices(model)
    site_ids = set_standing_pose(model, data)

    rows = []

    for mode_name, mode_cfg in CONTACT_MODES.items():
        rows.append(
            solve_mode(
                model=model,
                data=data,
                site_ids=site_ids,
                dofs=dofs,
                mode_name=mode_name,
                mode_cfg=mode_cfg,
            )
        )

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Stage 7 swing foot tracking QP")
    all_pass = True

    for row in rows:
        all_pass = all_pass and (row["pass"] == "True")
        print(
            f"mode={row['mode']} "
            f"osqp_status={row['osqp_status']} "
            f"max_abs_dq={row['max_abs_dq']} "
            f"swing_error_norm={row['swing_error_norm']} "
            f"swing_relative_error={row['swing_relative_error']} "
            f"max_stance_dq={row['max_stance_dq']} "
            f"pass={row['pass']}"
        )

    print(f"all_pass={all_pass}")
    print(f"saved={OUTPUT_CSV}")

    if not all_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
