#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


SCENE = "assets/go1/scene.xml"
CONTACT_WBC_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"

LOG_CSV = "results/logs_sample/stage07_online_full_wbc_step_loop_proto_log.csv"
SUMMARY_CSV = "results/logs_sample/stage07_online_full_wbc_step_loop_proto_summary.csv"

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

MODE_SEQUENCE = [
    ("trot_FR_RL", 200),
    ("trot_FL_RR", 200),
    ("trot_FR_RL", 200),
]

CONTACT_SIGN = 1.0
MU = 0.6
TORQUE_LIMIT = 23.7
FZ_MAX = 300.0
QDD_LIMIT = 200.0

# 在线原型先用保守 task scale，避免直接把离线 accel task 长时间积分放大。
BASE_QDD_Z_REF = 0.05
SWING_ACC_REF = np.array([0.10, 0.0, 0.20], dtype=float)

W_BASE_Z_TASK = 80.0
W_BASE_OTHER = 0.5
W_SWING_ACC = 10.0
W_QDD_JOINT = 0.2
W_FORCE = 1e-2
W_TAU = 1.0

KP_POSTURE = 60.0
KD_POSTURE = 2.0

RAMP_ALPHA = 0.20

MIN_Z_LIMIT = 0.22
MAX_ROLL_LIMIT = 0.20
MAX_PITCH_LIMIT = 0.20


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


def quat_to_roll_pitch(q):
    w, x, y, z = q

    roll = np.arctan2(
        2.0 * (w * x + y * z),
        1.0 - 2.0 * (x * x + y * y),
    )

    pitch = np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0))
    return float(roll), float(pitch)


def current_actuated_q(data, qadrs):
    return np.array([float(data.qpos[qadr]) for qadr in qadrs], dtype=float)


def current_actuated_qd(data, dofs):
    return np.array([float(data.qvel[dof]) for dof in dofs], dtype=float)


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


def solve_online_full_wbc(model, data, site_ids, dofs, mode, contact_row):
    mujoco.mj_forward(model, data)

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

    f_ref = parse_force_or_fallback(model, contact_row, mode)
    tau_ref = parse_tau(contact_row)

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
        polish=False,
        eps_abs=1e-5,
        eps_rel=1e-5,
        max_iter=5000,
    )

    result = solver.solve()

    if result.x is None:
        return None, {
            "osqp_status": result.info.status,
            "dyn_res_norm": np.nan,
            "stance_acc_res_norm": np.nan,
            "swing_acc_error_norm": np.nan,
            "base_qdd_z": np.nan,
            "max_abs_tau_wbc": np.nan,
        }

    x = np.array(result.x)
    qdd = x[qdd_off:qdd_off + nv]
    force = x[f_off:f_off + nf]
    tau = x[tau_off:tau_off + nu]

    dyn_res = M @ qdd + bias - S_T @ tau - CONTACT_SIGN * J_all.T @ force
    stance_res = J_stance @ qdd
    swing_res = J_swing @ qdd - swing_acc_ref_stack

    metrics = {
        "osqp_status": result.info.status,
        "dyn_res_norm": float(np.linalg.norm(dyn_res)),
        "stance_acc_res_norm": float(np.linalg.norm(stance_res)),
        "swing_acc_error_norm": float(np.linalg.norm(swing_res)),
        "base_qdd_z": float(qdd[2]),
        "max_abs_tau_wbc": float(np.max(np.abs(tau))),
    }

    return tau, metrics


def main():
    contact_rows = read_contact_wbc_rows()

    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, qadrs = actuator_indices(model)
    site_ids = set_standing_pose(model, data)

    q_des = current_actuated_q(data, qadrs)

    initial_z = float(data.qpos[2])
    min_z = initial_z
    max_z = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0

    max_tau_pd_abs = 0.0
    max_tau_wbc_abs = 0.0
    max_tau_total_abs = 0.0
    max_cmd_step_jump_norm = 0.0
    max_cmd_step_jump_abs = 0.0

    max_dyn_res_norm = 0.0
    max_stance_acc_res_norm = 0.0
    max_swing_acc_error_norm = 0.0

    qp_fail_steps = 0
    saturation_steps = 0

    tau_cmd = np.zeros(model.nu)
    tau_prev_cmd = tau_cmd.copy()

    rows = []
    global_step = 0

    for segment_i, (mode, segment_steps) in enumerate(MODE_SEQUENCE):
        for segment_step in range(segment_steps):
            tau_wbc, metrics = solve_online_full_wbc(
                model=model,
                data=data,
                site_ids=site_ids,
                dofs=dofs,
                mode=mode,
                contact_row=contact_rows[mode],
            )

            if tau_wbc is None:
                qp_fail_steps += 1
                tau_wbc = tau_cmd.copy()

            tau_cmd = (1.0 - RAMP_ALPHA) * tau_cmd + RAMP_ALPHA * tau_wbc

            cmd_jump = tau_cmd - tau_prev_cmd
            max_cmd_step_jump_norm = max(
                max_cmd_step_jump_norm,
                float(np.linalg.norm(cmd_jump)),
            )
            max_cmd_step_jump_abs = max(
                max_cmd_step_jump_abs,
                float(np.max(np.abs(cmd_jump))),
            )
            tau_prev_cmd = tau_cmd.copy()

            q_now = current_actuated_q(data, qadrs)
            qd_now = current_actuated_qd(data, dofs)

            tau_pd = KP_POSTURE * (q_des - q_now) - KD_POSTURE * qd_now
            tau_total_raw = tau_pd + tau_cmd
            tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

            saturated = bool(np.any(np.abs(tau_total_raw) > TORQUE_LIMIT))
            saturation_steps += int(saturated)

            data.ctrl[:] = tau_total
            mujoco.mj_step(model, data)

            base_z = float(data.qpos[2])
            roll, pitch = quat_to_roll_pitch(data.qpos[3:7])

            min_z = min(min_z, base_z)
            max_z = max(max_z, base_z)
            max_abs_roll = max(max_abs_roll, abs(roll))
            max_abs_pitch = max(max_abs_pitch, abs(pitch))

            max_tau_pd_abs = max(max_tau_pd_abs, float(np.max(np.abs(tau_pd))))
            max_tau_wbc_abs = max(max_tau_wbc_abs, float(np.max(np.abs(tau_cmd))))
            max_tau_total_abs = max(max_tau_total_abs, float(np.max(np.abs(tau_total))))

            if np.isfinite(metrics["dyn_res_norm"]):
                max_dyn_res_norm = max(max_dyn_res_norm, metrics["dyn_res_norm"])
            if np.isfinite(metrics["stance_acc_res_norm"]):
                max_stance_acc_res_norm = max(max_stance_acc_res_norm, metrics["stance_acc_res_norm"])
            if np.isfinite(metrics["swing_acc_error_norm"]):
                max_swing_acc_error_norm = max(max_swing_acc_error_norm, metrics["swing_acc_error_norm"])

            rows.append({
                "step": global_step,
                "segment_i": segment_i,
                "segment_step": segment_step,
                "mode": mode,
                "time": f"{data.time:.9f}",
                "osqp_status": metrics["osqp_status"],
                "base_z": f"{base_z:.12f}",
                "roll": f"{roll:.12f}",
                "pitch": f"{pitch:.12f}",
                "base_qdd_z": f"{metrics['base_qdd_z']:.12f}",
                "dyn_res_norm": f"{metrics['dyn_res_norm']:.12e}",
                "stance_acc_res_norm": f"{metrics['stance_acc_res_norm']:.12e}",
                "swing_acc_error_norm": f"{metrics['swing_acc_error_norm']:.12e}",
                "tau_pd_max_abs": f"{float(np.max(np.abs(tau_pd))):.12f}",
                "tau_wbc_max_abs": f"{float(np.max(np.abs(tau_cmd))):.12f}",
                "tau_total_max_abs": f"{float(np.max(np.abs(tau_total))):.12f}",
                "cmd_step_jump_norm": f"{float(np.linalg.norm(cmd_jump)):.12f}",
                "cmd_step_jump_abs": f"{float(np.max(np.abs(cmd_jump))):.12f}",
                "saturated": str(saturated),
            })

            global_step += 1

    final_z = float(data.qpos[2])
    final_roll, final_pitch = quat_to_roll_pitch(data.qpos[3:7])

    pass_test = (
        qp_fail_steps == 0
        and min_z > MIN_Z_LIMIT
        and max_abs_roll < MAX_ROLL_LIMIT
        and max_abs_pitch < MAX_PITCH_LIMIT
        and saturation_steps == 0
    )

    pass_margin = (
        pass_test
        and min_z - MIN_Z_LIMIT > 0.02
        and MAX_ROLL_LIMIT - max_abs_roll > 0.01
        and MAX_PITCH_LIMIT - max_abs_pitch > 0.01
    )

    summary = {
        "mode_sequence": "->".join([m for m, _s in MODE_SEQUENCE]),
        "num_segments": len(MODE_SEQUENCE),
        "total_steps": global_step,
        "kp_posture": KP_POSTURE,
        "kd_posture": KD_POSTURE,
        "torque_limit": TORQUE_LIMIT,
        "base_qdd_z_ref": BASE_QDD_Z_REF,
        "swing_acc_ref_x": SWING_ACC_REF[0],
        "swing_acc_ref_y": SWING_ACC_REF[1],
        "swing_acc_ref_z": SWING_ACC_REF[2],
        "ramp_alpha": RAMP_ALPHA,
        "initial_z": f"{initial_z:.12f}",
        "final_z": f"{final_z:.12f}",
        "min_z": f"{min_z:.12f}",
        "max_z": f"{max_z:.12f}",
        "delta_z": f"{final_z - initial_z:.12f}",
        "final_roll": f"{final_roll:.12f}",
        "final_pitch": f"{final_pitch:.12f}",
        "max_abs_roll": f"{max_abs_roll:.12f}",
        "roll_margin_to_limit": f"{MAX_ROLL_LIMIT - max_abs_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "pitch_margin_to_limit": f"{MAX_PITCH_LIMIT - max_abs_pitch:.12f}",
        "z_margin_to_limit": f"{min_z - MIN_Z_LIMIT:.12f}",
        "max_tau_pd_abs": f"{max_tau_pd_abs:.12f}",
        "max_tau_wbc_abs": f"{max_tau_wbc_abs:.12f}",
        "max_tau_total_abs": f"{max_tau_total_abs:.12f}",
        "max_cmd_step_jump_norm": f"{max_cmd_step_jump_norm:.12f}",
        "max_cmd_step_jump_abs": f"{max_cmd_step_jump_abs:.12f}",
        "max_dyn_res_norm": f"{max_dyn_res_norm:.12e}",
        "max_stance_acc_res_norm": f"{max_stance_acc_res_norm:.12e}",
        "max_swing_acc_error_norm": f"{max_swing_acc_error_norm:.12e}",
        "qp_fail_steps": qp_fail_steps,
        "saturation_steps": saturation_steps,
        "pass": str(pass_test),
        "pass_margin": str(pass_margin),
    }

    Path(LOG_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(LOG_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print("Stage 7 online full WBC step loop proto")
    for k, v in summary.items():
        print(f"{k}={v}")

    print(f"saved_log={LOG_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
