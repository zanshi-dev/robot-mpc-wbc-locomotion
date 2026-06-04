#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


SCENE = "assets/go1/scene.xml"
CONTACT_WBC_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
OUTPUT_CSV = "results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

CONTACT_MODES = {
    "trot_FR_RL": {
        "stance": ["FR", "RL"],
        "swing": ["FL", "RR"],
    },
    "trot_FL_RR": {
        "stance": ["FL", "RR"],
        "swing": ["FR", "RL"],
    },
}

CONTACT_SIGN = 1.0
MU = 0.6
TORQUE_LIMIT = 23.7
FZ_MAX = 300.0
QDD_LIMIT = 200.0

BASE_QDD_Z_REF = 0.2
SWING_ACC_REF = np.array([0.4, 0.0, 0.8], dtype=float)

W_BASE_Z_TASK = 100.0
W_BASE_OTHER = 1.0
W_SWING_ACC = 20.0
W_QDD_JOINT = 0.1
W_FORCE = 1e-2
W_TAU = 1.0

TORQUE_JUMP_NORM_WARN = 8.0
TORQUE_JUMP_MAX_WARN = 5.0


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


def read_contact_wbc_rows():
    with open(CONTACT_WBC_CSV, "r", newline="") as f:
        rows = list(csv.DictReader(f))

    out = {}
    for row in rows:
        mode = row.get("mode", "")
        if mode in CONTACT_MODES:
            out[mode] = row

    missing = [m for m in CONTACT_MODES if m not in out]
    if missing:
        raise RuntimeError(f"缺少这些 contact WBC mode: {missing}")

    return out


def get_first_existing(row, keys):
    for k in keys:
        if k in row and row[k] != "":
            return float(row[k])
    return None


def parse_tau(row):
    tau = []
    for leg in LEG_ORDER:
        for joint in JOINTS:
            keys = [
                f"{leg}_tau_{joint}",
                f"tau_{leg}_{joint}",
                f"{leg}_{joint}_tau",
            ]
            v = get_first_existing(row, keys)
            if v is None:
                raise RuntimeError(f"找不到 torque column: {keys}")
            tau.append(v)
    return np.array(tau, dtype=float)


def parse_force_or_fallback(model, row, mode):
    f = np.zeros(12)

    found_any = False
    for leg_i, leg in enumerate(LEG_ORDER):
        for comp_i, comp in enumerate(["fx", "fy", "fz"]):
            keys = [
                f"{leg}_{comp}",
                f"{leg}_f{comp[-1]}",
                f"{leg}_force_{comp[-1]}",
                f"{leg}_force_{comp}",
                f"force_{leg}_{comp}",
            ]
            v = get_first_existing(row, keys)
            if v is not None:
                f[3 * leg_i + comp_i] = v
                found_any = True

    if found_any:
        return f

    stance_legs = CONTACT_MODES[mode]["stance"]
    total_mass = float(np.sum(model.body_mass))
    total_weight = total_mass * abs(float(model.opt.gravity[2]))
    fz_each = total_weight / float(len(stance_legs))

    for leg in stance_legs:
        leg_i = LEG_ORDER.index(leg)
        f[3 * leg_i + 2] = fz_each

    return f


def foot_jacobian(model, data, site_id):
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    return jacp


def foot_jacobian_stack(model, data, site_ids, legs):
    return np.vstack([
        foot_jacobian(model, data, site_ids[leg])
        for leg in legs
    ])


def all_foot_jacobian_stack(model, data, site_ids):
    return np.vstack([
        foot_jacobian(model, data, site_ids[leg])
        for leg in LEG_ORDER
    ])


def mass_matrix(model, data):
    M = np.zeros((model.nv, model.nv))
    mujoco.mj_fullM(model, M, data.qM)
    return M


def selection_matrix(model, dofs):
    S_T = np.zeros((model.nv, model.nu))
    for act_id, dof in enumerate(dofs):
        S_T[dof, act_id] = 1.0
    return S_T


def solve_full_wbc_tau(model, data, site_ids, dofs, mode, contact_wbc_row):
    nv = model.nv
    nu = model.nu
    nf = 12
    nx = nv + nf + nu

    qdd_off = 0
    f_off = nv
    tau_off = nv + nf

    stance_legs = CONTACT_MODES[mode]["stance"]
    swing_legs = CONTACT_MODES[mode]["swing"]
    inactive_legs = swing_legs

    f_ref = parse_force_or_fallback(model, contact_wbc_row, mode)
    tau_ref = parse_tau(contact_wbc_row)

    M = mass_matrix(model, data)
    bias = np.array(data.qfrc_bias, dtype=float).copy()
    J_all = all_foot_jacobian_stack(model, data, site_ids)
    J_stance = foot_jacobian_stack(model, data, site_ids, stance_legs)
    J_swing = foot_jacobian_stack(model, data, site_ids, swing_legs)
    S_T = selection_matrix(model, dofs)

    weights = np.zeros(nx)
    x_ref = np.zeros(nx)

    weights[qdd_off:qdd_off + 6] = W_BASE_OTHER
    weights[qdd_off + 2] = W_BASE_Z_TASK
    x_ref[qdd_off + 2] = BASE_QDD_Z_REF

    weights[qdd_off + 6:qdd_off + nv] = W_QDD_JOINT

    weights[f_off:f_off + nf] = W_FORCE
    x_ref[f_off:f_off + nf] = f_ref

    weights[tau_off:tau_off + nu] = W_TAU
    x_ref[tau_off:tau_off + nu] = tau_ref

    H = np.diag(weights)
    g = -weights * x_ref

    swing_acc_ref_stack = np.tile(SWING_ACC_REF, len(swing_legs))
    H[:nv, :nv] += W_SWING_ACC * (J_swing.T @ J_swing)
    g[:nv] += -W_SWING_ACC * (J_swing.T @ swing_acc_ref_stack)

    P = sp.csc_matrix(2.0 * H)
    q = 2.0 * g

    A_blocks = []
    l_list = []
    u_list = []

    A_dyn = np.zeros((nv, nx))
    A_dyn[:, qdd_off:qdd_off + nv] = M
    A_dyn[:, f_off:f_off + nf] = -CONTACT_SIGN * J_all.T
    A_dyn[:, tau_off:tau_off + nu] = -S_T
    A_blocks.append(A_dyn)
    l_list.extend((-bias).tolist())
    u_list.extend((-bias).tolist())

    A_stance = np.zeros((J_stance.shape[0], nx))
    A_stance[:, qdd_off:qdd_off + nv] = J_stance
    A_blocks.append(A_stance)
    l_list.extend(np.zeros(J_stance.shape[0]).tolist())
    u_list.extend(np.zeros(J_stance.shape[0]).tolist())

    A_qdd = np.zeros((nv, nx))
    A_qdd[:, qdd_off:qdd_off + nv] = np.eye(nv)
    A_blocks.append(A_qdd)
    l_list.extend((-QDD_LIMIT * np.ones(nv)).tolist())
    u_list.extend((QDD_LIMIT * np.ones(nv)).tolist())

    A_tau = np.zeros((nu, nx))
    A_tau[:, tau_off:tau_off + nu] = np.eye(nu)
    A_blocks.append(A_tau)
    l_list.extend((-TORQUE_LIMIT * np.ones(nu)).tolist())
    u_list.extend((TORQUE_LIMIT * np.ones(nu)).tolist())

    for leg_i, leg in enumerate(LEG_ORDER):
        fx_i = f_off + 3 * leg_i + 0
        fy_i = f_off + 3 * leg_i + 1
        fz_i = f_off + 3 * leg_i + 2

        if leg in inactive_legs:
            for idx in [fx_i, fy_i, fz_i]:
                a = np.zeros(nx)
                a[idx] = 1.0
                A_blocks.append(a.reshape(1, -1))
                l_list.append(0.0)
                u_list.append(0.0)
            continue

        a = np.zeros(nx)
        a[fz_i] = 1.0
        A_blocks.append(a.reshape(1, -1))
        l_list.append(0.0)
        u_list.append(FZ_MAX)

        for sign in [1.0, -1.0]:
            a = np.zeros(nx)
            a[fx_i] = sign
            a[fz_i] = -MU
            A_blocks.append(a.reshape(1, -1))
            l_list.append(-np.inf)
            u_list.append(0.0)

            a = np.zeros(nx)
            a[fy_i] = sign
            a[fz_i] = -MU
            A_blocks.append(a.reshape(1, -1))
            l_list.append(-np.inf)
            u_list.append(0.0)

    A = sp.csc_matrix(np.vstack(A_blocks))
    l = np.array(l_list, dtype=float)
    u = np.array(u_list, dtype=float)

    solver = osqp.OSQP()
    solver.setup(
        P=P,
        q=q,
        A=A,
        l=l,
        u=u,
        verbose=False,
        polish=True,
        eps_abs=1e-8,
        eps_rel=1e-8,
        max_iter=30000,
    )

    result = solver.solve()

    if result.x is None:
        raise RuntimeError(f"{mode} full WBC QP failed: {result.info.status}")

    x = np.array(result.x)
    qdd = x[qdd_off:qdd_off + nv]
    force = x[f_off:f_off + nf]
    tau = x[tau_off:tau_off + nu]

    dyn_res = M @ qdd + bias - S_T @ tau - CONTACT_SIGN * J_all.T @ force
    stance_res = J_stance @ qdd
    swing_res = J_swing @ qdd - swing_acc_ref_stack

    return {
        "mode": mode,
        "status": result.info.status,
        "tau_full_wbc": tau,
        "tau_contact_wbc": tau_ref,
        "qdd": qdd,
        "force": force,
        "dyn_res_norm": float(np.linalg.norm(dyn_res)),
        "stance_acc_res_norm": float(np.linalg.norm(stance_res)),
        "swing_acc_error_norm": float(np.linalg.norm(swing_res)),
    }


def main():
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, _qadrs = actuator_indices(model)
    site_ids = set_standing_pose(model, data)
    contact_rows = read_contact_wbc_rows()

    solved = {}
    for mode in CONTACT_MODES:
        solved[mode] = solve_full_wbc_tau(
            model=model,
            data=data,
            site_ids=site_ids,
            dofs=dofs,
            mode=mode,
            contact_wbc_row=contact_rows[mode],
        )

    rows = []

    for mode, item in solved.items():
        tau_full = item["tau_full_wbc"]
        tau_contact = item["tau_contact_wbc"]
        tau_diff = tau_full - tau_contact

        max_abs_tau = float(np.max(np.abs(tau_full)))
        torque_limit_pass = max_abs_tau <= TORQUE_LIMIT + 1e-9

        row = {
            "row_type": "mode",
            "mode": mode,
            "transition": "",
            "osqp_status": item["status"],
            "max_abs_tau_full_wbc": f"{max_abs_tau:.12f}",
            "max_abs_tau_contact_wbc": f"{float(np.max(np.abs(tau_contact))):.12f}",
            "tau_diff_norm_vs_contact_wbc": f"{float(np.linalg.norm(tau_diff)):.12f}",
            "tau_diff_max_abs_vs_contact_wbc": f"{float(np.max(np.abs(tau_diff))):.12f}",
            "dyn_res_norm": f"{item['dyn_res_norm']:.12e}",
            "stance_acc_res_norm": f"{item['stance_acc_res_norm']:.12e}",
            "swing_acc_error_norm": f"{item['swing_acc_error_norm']:.12e}",
            "jump_norm": "",
            "jump_max_abs": "",
            "need_smoothing": "",
            "torque_limit": TORQUE_LIMIT,
            "torque_limit_pass": str(torque_limit_pass),
            "pass": str(torque_limit_pass),
        }

        for leg_i, leg in enumerate(LEG_ORDER):
            for joint_i, joint in enumerate(JOINTS):
                idx = 3 * leg_i + joint_i
                row[f"{leg}_tau_{joint}"] = f"{float(tau_full[idx]):.12f}"

        rows.append(row)

    transitions = [
        ("trot_FR_RL", "trot_FL_RR"),
        ("trot_FL_RR", "trot_FR_RL"),
    ]

    for a, b in transitions:
        jump = solved[b]["tau_full_wbc"] - solved[a]["tau_full_wbc"]
        jump_norm = float(np.linalg.norm(jump))
        jump_max_abs = float(np.max(np.abs(jump)))
        need_smoothing = (
            jump_norm > TORQUE_JUMP_NORM_WARN
            or jump_max_abs > TORQUE_JUMP_MAX_WARN
        )

        rows.append({
            "row_type": "transition",
            "mode": "",
            "transition": f"{a}->{b}",
            "osqp_status": "",
            "max_abs_tau_full_wbc": "",
            "max_abs_tau_contact_wbc": "",
            "tau_diff_norm_vs_contact_wbc": "",
            "tau_diff_max_abs_vs_contact_wbc": "",
            "dyn_res_norm": "",
            "stance_acc_res_norm": "",
            "swing_acc_error_norm": "",
            "jump_norm": f"{jump_norm:.12f}",
            "jump_max_abs": f"{jump_max_abs:.12f}",
            "need_smoothing": str(need_smoothing),
            "torque_limit": TORQUE_LIMIT,
            "torque_limit_pass": "",
            "pass": str(not need_smoothing),
        })

    all_mode_pass = all(r["pass"] == "True" for r in rows if r["row_type"] == "mode")
    any_need_smoothing = any(
        r.get("need_smoothing") == "True"
        for r in rows
        if r["row_type"] == "transition"
    )

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = []
    for r in rows:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Stage 7 full WBC torque reconstruction check")
    print(f"saved={OUTPUT_CSV}")
    print(f"all_mode_pass={all_mode_pass}")
    print(f"any_need_smoothing={any_need_smoothing}")

    for r in rows:
        if r["row_type"] == "mode":
            print(
                f"mode={r['mode']} "
                f"max_abs_tau_full_wbc={r['max_abs_tau_full_wbc']} "
                f"tau_diff_norm_vs_contact_wbc={r['tau_diff_norm_vs_contact_wbc']} "
                f"tau_diff_max_abs_vs_contact_wbc={r['tau_diff_max_abs_vs_contact_wbc']} "
                f"torque_limit_pass={r['torque_limit_pass']}"
            )
        else:
            print(
                f"transition={r['transition']} "
                f"jump_norm={r['jump_norm']} "
                f"jump_max_abs={r['jump_max_abs']} "
                f"need_smoothing={r['need_smoothing']}"
            )

    if not all_mode_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
