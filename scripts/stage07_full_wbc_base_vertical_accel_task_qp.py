#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


SCENE = "assets/go1/scene.xml"
INPUT_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
OUTPUT_CSV = "results/logs_sample/stage07_full_wbc_base_vertical_accel_task_qp.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

CONTACT_MODES = {
    "all_stance": ["FR", "FL", "RR", "RL"],
    "trot_FR_RL": ["FR", "RL"],
    "trot_FL_RR": ["FL", "RR"],
}

CONTACT_SIGN = 1.0
MU = 0.6
TORQUE_LIMIT = 23.7
FZ_MAX = 300.0
QDD_LIMIT = 200.0

BASE_QDD_Z_REF = 0.2

W_BASE_Z_TASK = 100.0
W_BASE_OTHER = 1.0
W_QDD_JOINT = 0.1
W_FORCE = 1e-2
W_TAU = 1.0

DYN_RESIDUAL_TOL = 1e-6
STANCE_ACC_TOL = 1e-6
INACTIVE_FORCE_TOL = 1e-7
MIN_ACTIVE_FZ = 1.0
BASE_Z_TASK_ERROR_TOL = 0.03


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


def read_wbc_rows():
    with open(INPUT_CSV, "r", newline="") as f:
        rows = list(csv.DictReader(f))

    out = {}
    for row in rows:
        mode = row.get("mode", "")
        if mode in CONTACT_MODES:
            out[mode] = row

    missing = [m for m in CONTACT_MODES if m not in out]
    if missing:
        raise RuntimeError(f"缺少这些 mode 的 WBC 输入: {missing}")

    return out


def get_first_existing(row, keys):
    for k in keys:
        if k in row and row[k] != "":
            return float(row[k])
    return None


def parse_tau_ref(row):
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


def parse_force_ref_or_fallback(model, row, mode):
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

    active_legs = CONTACT_MODES[mode]
    total_mass = float(np.sum(model.body_mass))
    total_weight = total_mass * abs(float(model.opt.gravity[2]))
    fz_each = total_weight / float(len(active_legs))

    for leg in active_legs:
        leg_i = LEG_ORDER.index(leg)
        f[3 * leg_i + 2] = fz_each

    return f


def foot_jacobian(model, data, site_id):
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    return jacp


def foot_jacobian_stack(model, data, site_ids):
    return np.vstack([
        foot_jacobian(model, data, site_ids[leg])
        for leg in LEG_ORDER
    ])


def stance_jacobian_stack(model, data, site_ids, active_legs):
    return np.vstack([
        foot_jacobian(model, data, site_ids[leg])
        for leg in active_legs
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


def compute_tau_from_force_reference(model, data, site_ids, dofs, f_ref):
    J = foot_jacobian_stack(model, data, site_ids)
    tau_full = -J.T @ f_ref
    return tau_full[dofs]


def solve_mode(model, data, site_ids, dofs, row, mode):
    nv = model.nv
    nu = model.nu
    nf = 12
    nx = nv + nf + nu

    qdd_off = 0
    f_off = nv
    tau_off = nv + nf

    active_legs = CONTACT_MODES[mode]
    inactive_legs = [leg for leg in LEG_ORDER if leg not in active_legs]

    f_ref = parse_force_ref_or_fallback(model, row, mode)

    try:
        tau_ref = parse_tau_ref(row)
    except RuntimeError:
        tau_ref = compute_tau_from_force_reference(model, data, site_ids, dofs, f_ref)

    M = mass_matrix(model, data)
    bias = np.array(data.qfrc_bias, dtype=float).copy()
    J_all = foot_jacobian_stack(model, data, site_ids)
    J_stance = stance_jacobian_stack(model, data, site_ids, active_legs)
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

    P = sp.diags(2.0 * weights, format="csc")
    q = -2.0 * weights * x_ref

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
        return {
            "mode": mode,
            "osqp_status": result.info.status,
            "pass": "False",
            "reason": "no_solution",
        }

    x = np.array(result.x)
    qdd = x[qdd_off:qdd_off + nv]
    f = x[f_off:f_off + nf]
    tau = x[tau_off:tau_off + nu]

    dyn_res = M @ qdd + bias - S_T @ tau - CONTACT_SIGN * J_all.T @ f
    stance_acc_res = J_stance @ qdd

    base_z_task_error = float(qdd[2] - BASE_QDD_Z_REF)

    dyn_res_norm = float(np.linalg.norm(dyn_res))
    dyn_res_max_abs = float(np.max(np.abs(dyn_res)))
    stance_acc_res_norm = float(np.linalg.norm(stance_acc_res))
    stance_acc_res_max_abs = float(np.max(np.abs(stance_acc_res)))

    max_abs_tau = float(np.max(np.abs(tau)))
    max_abs_qdd = float(np.max(np.abs(qdd)))

    active_fz_values = []
    friction_margins = []
    inactive_force_norm_sq = 0.0

    for leg_i, leg in enumerate(LEG_ORDER):
        fx = float(f[3 * leg_i + 0])
        fy = float(f[3 * leg_i + 1])
        fz = float(f[3 * leg_i + 2])

        if leg in active_legs:
            active_fz_values.append(fz)
            friction_margins.append(MU * fz - abs(fx))
            friction_margins.append(MU * fz - abs(fy))
        else:
            inactive_force_norm_sq += fx * fx + fy * fy + fz * fz

    inactive_force_norm = float(np.sqrt(inactive_force_norm_sq))
    min_active_fz = float(min(active_fz_values)) if active_fz_values else 0.0
    min_friction_margin = float(min(friction_margins)) if friction_margins else 0.0

    tau_diff_norm = float(np.linalg.norm(tau - tau_ref))
    force_diff_norm = float(np.linalg.norm(f - f_ref))
    qdd_norm = float(np.linalg.norm(qdd))

    status_pass = result.info.status.lower() in ["solved", "solved inaccurate"]
    dyn_pass = dyn_res_norm < DYN_RESIDUAL_TOL
    stance_acc_pass = stance_acc_res_norm < STANCE_ACC_TOL
    base_z_task_pass = abs(base_z_task_error) < BASE_Z_TASK_ERROR_TOL
    torque_pass = max_abs_tau <= TORQUE_LIMIT + 1e-7
    fz_pass = min_active_fz > MIN_ACTIVE_FZ
    friction_pass = min_friction_margin >= -1e-7
    inactive_pass = inactive_force_norm < INACTIVE_FORCE_TOL

    pass_test = bool(
        status_pass
        and dyn_pass
        and stance_acc_pass
        and base_z_task_pass
        and torque_pass
        and fz_pass
        and friction_pass
        and inactive_pass
    )

    out = {
        "mode": mode,
        "contact_sign": CONTACT_SIGN,
        "osqp_status": result.info.status,
        "objective": f"{result.info.obj_val:.12f}",
        "active_legs": ",".join(active_legs),
        "inactive_legs": ",".join(inactive_legs),
        "nv": nv,
        "nu": nu,
        "num_vars": nx,
        "num_stance_acc_constraints": J_stance.shape[0],
        "mu": MU,
        "torque_limit": TORQUE_LIMIT,
        "base_qdd_z_ref": f"{BASE_QDD_Z_REF:.12f}",
        "base_qdd_x": f"{qdd[0]:.12f}",
        "base_qdd_y": f"{qdd[1]:.12f}",
        "base_qdd_z": f"{qdd[2]:.12f}",
        "base_qdd_roll": f"{qdd[3]:.12f}",
        "base_qdd_pitch": f"{qdd[4]:.12f}",
        "base_qdd_yaw": f"{qdd[5]:.12f}",
        "base_z_task_error": f"{base_z_task_error:.12e}",
        "dyn_res_norm": f"{dyn_res_norm:.12e}",
        "dyn_res_max_abs": f"{dyn_res_max_abs:.12e}",
        "stance_acc_res_norm": f"{stance_acc_res_norm:.12e}",
        "stance_acc_res_max_abs": f"{stance_acc_res_max_abs:.12e}",
        "max_abs_tau": f"{max_abs_tau:.12f}",
        "max_abs_qdd": f"{max_abs_qdd:.12f}",
        "qdd_norm": f"{qdd_norm:.12f}",
        "min_active_fz": f"{min_active_fz:.12f}",
        "min_friction_margin": f"{min_friction_margin:.12f}",
        "inactive_force_norm": f"{inactive_force_norm:.12e}",
        "tau_diff_norm": f"{tau_diff_norm:.12f}",
        "force_diff_norm": f"{force_diff_norm:.12f}",
        "status_pass": str(status_pass),
        "dyn_pass": str(dyn_pass),
        "stance_acc_pass": str(stance_acc_pass),
        "base_z_task_pass": str(base_z_task_pass),
        "torque_pass": str(torque_pass),
        "fz_pass": str(fz_pass),
        "friction_pass": str(friction_pass),
        "inactive_pass": str(inactive_pass),
        "pass": str(pass_test),
        "reason": "",
    }

    for leg_i, leg in enumerate(LEG_ORDER):
        out[f"{leg}_fx"] = f"{float(f[3 * leg_i + 0]):.12f}"
        out[f"{leg}_fy"] = f"{float(f[3 * leg_i + 1]):.12f}"
        out[f"{leg}_fz"] = f"{float(f[3 * leg_i + 2]):.12f}"

    for leg_i, leg in enumerate(LEG_ORDER):
        for joint_i, joint in enumerate(JOINTS):
            idx = 3 * leg_i + joint_i
            out[f"{leg}_tau_{joint}"] = f"{float(tau[idx]):.12f}"

    return out


def main():
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, _qadrs = actuator_indices(model)
    site_ids = set_standing_pose(model, data)
    wbc_rows = read_wbc_rows()

    rows = []

    for mode in CONTACT_MODES:
        rows.append(
            solve_mode(
                model=model,
                data=data,
                site_ids=site_ids,
                dofs=dofs,
                row=wbc_rows[mode],
                mode=mode,
            )
        )

    all_pass = all(r["pass"] == "True" for r in rows)

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

    print("Stage 7 full WBC base vertical accel task QP")
    print(f"saved={OUTPUT_CSV}")
    print(f"all_pass={all_pass}")

    for row in rows:
        print(
            f"mode={row['mode']} "
            f"osqp_status={row['osqp_status']} "
            f"base_qdd_z={row.get('base_qdd_z', 'nan')} "
            f"base_z_task_error={row.get('base_z_task_error', 'nan')} "
            f"dyn_res_norm={row.get('dyn_res_norm', 'nan')} "
            f"stance_acc_res_norm={row.get('stance_acc_res_norm', 'nan')} "
            f"max_abs_tau={row.get('max_abs_tau', 'nan')} "
            f"max_abs_qdd={row.get('max_abs_qdd', 'nan')} "
            f"min_active_fz={row.get('min_active_fz', 'nan')} "
            f"min_friction_margin={row.get('min_friction_margin', 'nan')} "
            f"pass={row['pass']}"
        )

    if not all_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
