#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


SCENE = "assets/go1/scene.xml"
OUTPUT_CSV = "results/logs_sample/stage07_swing_trajectory_qp_k9.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

CONTACT_MODES = {
    "trot_FR_RL": {"stance": ["FR", "RL"], "swing": ["FL", "RR"]},
    "trot_FL_RR": {"stance": ["FL", "RR"], "swing": ["FR", "RL"]},
}

KNOTS = 9
TOTAL_DX = 0.03
CLEARANCE = 0.06
MAX_DQ = 0.12

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


def swing_target(k):
    phase_prev = k / KNOTS
    phase_now = (k + 1) / KNOTS

    x_prev = TOTAL_DX * phase_prev
    x_now = TOTAL_DX * phase_now

    z_prev = CLEARANCE * 4.0 * phase_prev * (1.0 - phase_prev)
    z_now = CLEARANCE * 4.0 * phase_now * (1.0 - phase_now)

    return np.array([x_now - x_prev, 0.0, z_now - z_prev])


def solve_knot(model, data, site_ids, dofs, mode_cfg, knot_i):
    n = 12

    H = W_REG * np.eye(n)
    g = np.zeros(n)

    target = swing_target(knot_i)

    for leg in mode_cfg["swing"]:
        J = foot_jac_actuated(model, data, site_ids[leg], dofs)

        H += W_SWING * (J.T @ J)
        g += -W_SWING * (J.T @ target)

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
        raise RuntimeError(f"OSQP failed at knot={knot_i}, status={result.info.status}")

    dq = np.array(result.x)

    return result, dq, target


def apply_dq(model, data, qadrs, dq):
    for act_id, qadr in enumerate(qadrs):
        data.qpos[qadr] += dq[act_id]
    mujoco.mj_forward(model, data)


def run_mode(mode_name, mode_cfg):
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, qadrs = actuator_indices(model)
    site_ids = set_standing_pose(model, data)

    rows = []

    mode_pass = True
    max_abs_dq_all = 0.0
    max_swing_error_all = 0.0
    max_stance_dq_all = 0.0
    swing_error_sq_total = 0.0
    swing_target_sq_total = 0.0

    for knot_i in range(KNOTS):
        result, dq, target = solve_knot(
            model=model,
            data=data,
            site_ids=site_ids,
            dofs=dofs,
            mode_cfg=mode_cfg,
            knot_i=knot_i,
        )

        max_abs_dq = float(np.max(np.abs(dq)))
        max_abs_dq_all = max(max_abs_dq_all, max_abs_dq)

        row = {
            "mode": mode_name,
            "knot": knot_i,
            "osqp_status": result.info.status,
            "objective": f"{result.info.obj_val:.12f}",
            "swing_legs": ",".join(mode_cfg["swing"]),
            "stance_legs": ",".join(mode_cfg["stance"]),
            "target_dx": f"{target[0]:.12f}",
            "target_dy": f"{target[1]:.12f}",
            "target_dz": f"{target[2]:.12f}",
            "max_dq_limit": MAX_DQ,
            "max_abs_dq": f"{max_abs_dq:.12f}",
        }

        max_stance_dq = 0.0
        max_swing_error = 0.0

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
                err = foot_delta - target
                err_norm = float(np.linalg.norm(err))

                max_swing_error = max(max_swing_error, err_norm)
                swing_error_sq_total += float(err @ err)
                swing_target_sq_total += float(target @ target)

                row[f"{leg}_swing_error_norm"] = f"{err_norm:.12f}"
            else:
                row[f"{leg}_swing_error_norm"] = ""

        max_swing_error_all = max(max_swing_error_all, max_swing_error)
        max_stance_dq_all = max(max_stance_dq_all, max_stance_dq)

        dq_pass = max_abs_dq <= MAX_DQ + 1e-9
        stance_pass = max_stance_dq < 0.02
        swing_pass = max_swing_error < 0.01
        knot_pass = (
            result.info.status.lower() in ["solved", "solved inaccurate"]
            and dq_pass
            and stance_pass
            and swing_pass
        )

        mode_pass = mode_pass and knot_pass

        row["max_swing_error"] = f"{max_swing_error:.12f}"
        row["max_stance_dq"] = f"{max_stance_dq:.12f}"
        row["dq_pass"] = str(dq_pass)
        row["stance_pass"] = str(stance_pass)
        row["swing_pass"] = str(swing_pass)
        row["pass"] = str(knot_pass)

        rows.append(row)

        apply_dq(model, data, qadrs, dq)

    swing_error_norm_total = float(np.sqrt(swing_error_sq_total))
    swing_target_norm_total = float(np.sqrt(swing_target_sq_total))
    swing_relative_error_total = swing_error_norm_total / max(swing_target_norm_total, 1e-12)

    for row in rows:
        row["mode_pass"] = str(mode_pass)
        row["mode_max_abs_dq"] = f"{max_abs_dq_all:.12f}"
        row["mode_max_swing_error"] = f"{max_swing_error_all:.12f}"
        row["mode_max_stance_dq"] = f"{max_stance_dq_all:.12f}"
        row["mode_swing_error_norm_total"] = f"{swing_error_norm_total:.12f}"
        row["mode_swing_relative_error_total"] = f"{swing_relative_error_total:.12f}"

    return rows


def main():
    all_rows = []

    for mode_name, mode_cfg in CONTACT_MODES.items():
        all_rows.extend(run_mode(mode_name, mode_cfg))

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    print("Stage 7 swing trajectory multi-knot QP")

    all_pass = True
    seen_modes = set()

    for row in all_rows:
        if row["mode"] not in seen_modes:
            seen_modes.add(row["mode"])
            all_pass = all_pass and (row["mode_pass"] == "True")
            print(
                f"mode={row['mode']} "
                f"mode_pass={row['mode_pass']} "
                f"mode_max_abs_dq={row['mode_max_abs_dq']} "
                f"mode_max_swing_error={row['mode_max_swing_error']} "
                f"mode_max_stance_dq={row['mode_max_stance_dq']} "
                f"mode_swing_relative_error_total={row['mode_swing_relative_error_total']}"
            )

    print(f"all_pass={all_pass}")
    print(f"saved={OUTPUT_CSV}")

    if not all_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
