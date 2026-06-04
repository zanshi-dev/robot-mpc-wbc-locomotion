#!/usr/bin/env python3
import csv
import importlib.util
from pathlib import Path

import mujoco
import numpy as np


PROTO_PATH = "scripts/stage07_online_full_wbc_with_scheduler_proto.py"
OUTPUT_CSV = "results/logs_sample/stage07_online_full_wbc_scheduler_stability_sweep.csv"

TOTAL_STEPS = 1200

PERIOD_STEPS_LIST = [400, 600]
RAMP_ALPHA_LIST = [0.10, 0.15, 0.20]
BASE_QDD_Z_REF_LIST = [0.03, 0.05]

STRICT_ROLL_TARGET = 0.12
ROLL_LIMIT = 0.20
PITCH_LIMIT = 0.20
MIN_Z_LIMIT = 0.22


def load_proto():
    spec = importlib.util.spec_from_file_location("online_full_wbc_proto", PROTO_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_case(proto, period_steps, ramp_alpha, base_qdd_z_ref):
    proto.TOTAL_STEPS = TOTAL_STEPS
    proto.PERIOD_STEPS = period_steps
    proto.HALF_PERIOD_STEPS = period_steps // 2
    proto.RAMP_ALPHA = ramp_alpha
    proto.BASE_QDD_Z_REF = base_qdd_z_ref

    contact_rows = proto.read_contact_wbc_rows()

    model = mujoco.MjModel.from_xml_path(proto.SCENE)
    data = mujoco.MjData(model)

    dofs, qadrs = proto.actuator_indices(model)
    site_ids = proto.set_standing_pose(model, data)

    q_des = proto.current_actuated_q(data, qadrs)

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
    transition_count = 0
    mode_counts = {m: 0 for m in proto.CONTACT_MODES}

    tau_cmd = np.zeros(model.nu)
    tau_prev_cmd = tau_cmd.copy()
    prev_mode = None

    for step in range(TOTAL_STEPS):
        sched = proto.scheduler_mode(step)
        mode = sched["mode"]

        if prev_mode is not None and mode != prev_mode:
            transition_count += 1
        prev_mode = mode
        mode_counts[mode] += 1

        tau_wbc, metrics = proto.solve_online_full_wbc(
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

        tau_cmd = (1.0 - ramp_alpha) * tau_cmd + ramp_alpha * tau_wbc

        cmd_jump = tau_cmd - tau_prev_cmd
        max_cmd_step_jump_norm = max(max_cmd_step_jump_norm, float(np.linalg.norm(cmd_jump)))
        max_cmd_step_jump_abs = max(max_cmd_step_jump_abs, float(np.max(np.abs(cmd_jump))))
        tau_prev_cmd = tau_cmd.copy()

        q_now = proto.current_actuated_q(data, qadrs)
        qd_now = proto.current_actuated_qd(data, dofs)

        tau_pd = proto.KP_POSTURE * (q_des - q_now) - proto.KD_POSTURE * qd_now
        tau_total_raw = tau_pd + tau_cmd
        tau_total = np.clip(tau_total_raw, -proto.TORQUE_LIMIT, proto.TORQUE_LIMIT)

        saturated = bool(np.any(np.abs(tau_total_raw) > proto.TORQUE_LIMIT))
        saturation_steps += int(saturated)

        data.ctrl[:] = tau_total
        mujoco.mj_step(model, data)

        base_z = float(data.qpos[2])
        roll, pitch = proto.quat_to_roll_pitch(data.qpos[3:7])

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

    final_z = float(data.qpos[2])
    final_roll, final_pitch = proto.quat_to_roll_pitch(data.qpos[3:7])

    pass_test = (
        qp_fail_steps == 0
        and saturation_steps == 0
        and min_z > MIN_Z_LIMIT
        and max_abs_roll < ROLL_LIMIT
        and max_abs_pitch < PITCH_LIMIT
    )

    strict_roll_pass = pass_test and max_abs_roll < STRICT_ROLL_TARGET

    return {
        "period_steps": period_steps,
        "half_period_steps": period_steps // 2,
        "ramp_alpha": ramp_alpha,
        "base_qdd_z_ref": base_qdd_z_ref,
        "total_steps": TOTAL_STEPS,
        "trot_FR_RL_steps": mode_counts["trot_FR_RL"],
        "trot_FL_RR_steps": mode_counts["trot_FL_RR"],
        "transition_count": transition_count,
        "initial_z": f"{initial_z:.12f}",
        "final_z": f"{final_z:.12f}",
        "min_z": f"{min_z:.12f}",
        "max_z": f"{max_z:.12f}",
        "delta_z": f"{final_z - initial_z:.12f}",
        "final_roll": f"{final_roll:.12f}",
        "final_pitch": f"{final_pitch:.12f}",
        "max_abs_roll": f"{max_abs_roll:.12f}",
        "roll_margin_to_0p20": f"{ROLL_LIMIT - max_abs_roll:.12f}",
        "roll_margin_to_0p12": f"{STRICT_ROLL_TARGET - max_abs_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "pitch_margin_to_0p20": f"{PITCH_LIMIT - max_abs_pitch:.12f}",
        "z_margin_to_0p22": f"{min_z - MIN_Z_LIMIT:.12f}",
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
        "strict_roll_pass": str(strict_roll_pass),
    }


def sort_key(row):
    return (
        row["strict_roll_pass"] != "True",
        row["pass"] != "True",
        float(row["max_abs_roll"]),
        float(row["max_abs_pitch"]),
        float(row["max_tau_total_abs"]),
    )


def main():
    proto = load_proto()

    rows = []

    for period_steps in PERIOD_STEPS_LIST:
        for ramp_alpha in RAMP_ALPHA_LIST:
            for base_qdd_z_ref in BASE_QDD_Z_REF_LIST:
                row = run_case(
                    proto=proto,
                    period_steps=period_steps,
                    ramp_alpha=ramp_alpha,
                    base_qdd_z_ref=base_qdd_z_ref,
                )
                rows.append(row)

                print(
                    "case "
                    f"period_steps={period_steps} "
                    f"ramp_alpha={ramp_alpha} "
                    f"base_qdd_z_ref={base_qdd_z_ref} "
                    f"max_abs_roll={row['max_abs_roll']} "
                    f"max_abs_pitch={row['max_abs_pitch']} "
                    f"max_tau_total_abs={row['max_tau_total_abs']} "
                    f"qp_fail_steps={row['qp_fail_steps']} "
                    f"saturation_steps={row['saturation_steps']} "
                    f"pass={row['pass']} "
                    f"strict_roll_pass={row['strict_roll_pass']}"
                )

    ranked = sorted(rows, key=sort_key)
    recommended = ranked[0]

    for r in rows:
        r["recommended"] = str(r is recommended)

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys())
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    pass_cases = sum(1 for r in rows if r["pass"] == "True")
    strict_roll_cases = sum(1 for r in rows if r["strict_roll_pass"] == "True")

    print("Stage 7 online full WBC scheduler stability sweep")
    print(f"saved={OUTPUT_CSV}")
    print(f"num_cases={len(rows)}")
    print(f"pass_cases={pass_cases}")
    print(f"strict_roll_cases={strict_roll_cases}")
    print(
        "recommended "
        f"period_steps={recommended['period_steps']} "
        f"ramp_alpha={recommended['ramp_alpha']} "
        f"base_qdd_z_ref={recommended['base_qdd_z_ref']} "
        f"max_abs_roll={recommended['max_abs_roll']} "
        f"max_abs_pitch={recommended['max_abs_pitch']} "
        f"max_tau_total_abs={recommended['max_tau_total_abs']} "
        f"pass={recommended['pass']} "
        f"strict_roll_pass={recommended['strict_roll_pass']}"
    )

    if pass_cases == 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
