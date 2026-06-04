#!/usr/bin/env python3
import csv
import importlib.util
from pathlib import Path

import mujoco
import numpy as np


COMBINED_SCRIPT = "scripts/stage07_online_full_wbc_plus_swing_joint_tracking_proto.py"
OUTPUT_CSV = "results/logs_sample/stage07_online_full_wbc_plus_swing_joint_tracking_sweep.csv"

# 小规模优先：减少在线 WBC QP 重复运行成本。
WBC_TORQUE_SCALE_LIST = [0.0, 0.25, 0.50, 0.75]
SWING_PD_TORQUE_SCALE_LIST = [0.25, 0.50, 0.75]
TARGET_SCALE_LIST = [0.45, 0.60]

MIN_Z_LIMIT = 0.22
MAX_ROLL_LIMIT = 0.20
MAX_PITCH_LIMIT = 0.20
MAX_JOINT_ERROR_LIMIT = 0.08


def load_combined():
    spec = importlib.util.spec_from_file_location("combined_proto", COMBINED_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_case(mod, wbc_torque_scale, swing_pd_torque_scale, target_scale):
    wbc = mod.load_wbc()
    target_rows = mod.read_swing_targets()

    model = mujoco.MjModel.from_xml_path(wbc.SCENE)
    data = mujoco.MjData(model)

    contact_rows = wbc.read_contact_wbc_rows()
    dofs, qadrs = wbc.actuator_indices(model)
    site_ids = wbc.set_standing_pose(model, data)

    q_standing = wbc.current_actuated_q(data, qadrs)

    initial_z = float(data.qpos[2])
    min_z = initial_z
    max_z = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0

    max_tau_wbc_abs = 0.0
    max_tau_swing_pd_abs = 0.0
    max_tau_s = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0

    max_tau_wbcwing_pd_abs = 0.0
    max_tau_total_raw_abs = 0.0
    max_tau_total_abs = 0.0

    max_joint_error = 0.0
    max_swing_joint_error = 0.0
    max_stance_joint_error = 0.0

    max_cmd_step_jump_norm = 0.0
    max_cmd_step_jump_abs = 0.0

    max_dyn_res_norm = 0.0
    max_stance_acc_res_norm = 0.0
    max_swing_acc_error_norm = 0.0

    qp_fail_steps = 0
    saturation_steps = 0
    transition_count = 0

    tau_wbc_cmd = np.zeros(model.nu)
    tau_prev_total = np.zeros(model.nu)
    prev_mode = None

    mode_counts = {m: 0 for m in wbc.CONTACT_MODES}
    total_steps = min(wbc.TOTAL_STEPS, len(target_rows))

    for step in range(total_steps):
        sched = wbc.scheduler_mode(step)
        mode = sched["mode"]
        target = target_rows[step]

        if target["mode"] != mode:
            raise RuntimeError(
                f"mode mismatch at step={step}: scheduler={mode}, target={target['mode']}"
            )

        is_transition = prev_mode is not None and mode != prev_mode
        if is_transition:
            transition_count += 1
        prev_mode = mode
        mode_counts[mode] += 1

        tau_wbc, metrics = wbc.solve_online_full_wbc(
            model=model,
            data=data,
            site_ids=site_ids,
            dofs=dofs,
            mode=mode,
            contact_row=contact_rows[mode],
        )

        if tau_wbc is None:
            qp_fail_steps += 1
            tau_wbc = tau_wbc_cmd.copy()

        tau_wbc_cmd = (1.0 - wbc.RAMP_ALPHA) * tau_wbc_cmd + wbc.RAMP_ALPHA * tau_wbc
        tau_wbc_scaled = wbc_torque_scale * tau_wbc_cmd

        q_des_full = target["q_des"]
        q_des = q_standing + target_scale * (q_des_full - q_standing)

        q_now = wbc.current_actuated_q(data, qadrs)
        qd_now = wbc.current_actuated_qd(data, dofs)
        q_err = q_des - q_now

        tau_swing_pd_raw = mod.KP_SWING * q_err - mod.KD_SWING * qd_now
        tau_swing_pd_scaled = swing_pd_torque_scale * tau_swing_pd_raw

        tau_total_raw = tau_wbc_scaled + tau_swing_pd_scaled
        tau_total = np.clip(tau_total_raw, -mod.TORQUE_LIMIT, mod.TORQUE_LIMIT)

        saturated = bool(np.any(np.abs(tau_total_raw) > mod.TORQUE_LIMIT))
        saturation_steps += int(saturated)

        tau_jump = tau_total - tau_prev_total
        max_cmd_step_jump_norm = max(max_cmd_step_jump_norm, float(np.linalg.norm(tau_jump)))
        max_cmd_step_jump_abs = max(max_cmd_step_jump_abs, float(np.max(np.abs(tau_jump))))
        tau_prev_total = tau_total.copy()

        data.ctrl[:] = tau_total
        mujoco.mj_step(model, data)

        base_z = float(data.qpos[2])
        roll, pitch = wbc.quat_to_roll_pitch(data.qpos[3:7])

        min_z = min(min_z, base_z)
        max_z = max(max_z, base_z)
        max_abs_roll = max(max_abs_roll, abs(roll))
        max_abs_pitch = max(max_abs_pitch, abs(pitch))

        swing_legs = target["swing_legs"].split(",") if target["swing_legs"] else []
        stance_legs = target["stance_legs"].split(",") if target["stance_legs"] else []

        swing_indices = []
        stance_indices = []
        for leg_i, leg in enumerate(mod.LEG_ORDER):
            inds = [3 * leg_i + j for j in range(3)]
            if leg in swing_legs:
                swing_indices.extend(inds)
            if leg in stance_legs:
                stance_indices.extend(inds)

        step_joint_error = float(np.max(np.abs(q_err)))
        step_swing_joint_error = float(np.max(np.abs(q_err[swing_indices]))) if swing_indices else 0.0
        step_stance_joint_error = float(np.max(np.abs(q_err[stance_indices]))) if stance_indices else 0.0

        max_joint_error = max(max_joint_error, step_joint_error)
        max_swing_joint_error = max(max_swing_joint_error, step_swing_joint_error)
        max_stance_joint_error = max(max_stance_joint_error, step_stance_joint_error)

        max_tau_wbc_abs = max(max_tau_wbc_abs, float(np.max(np.abs(tau_wbc_scaled))))
        max_tau_swing_pd_abs = max(max_tau_swing_pd_abs, float(np.max(np.abs(tau_swing_pd_scaled))))
        max_tau_total_raw_abs = max(max_tau_total_raw_abs, float(np.max(np.abs(tau_total_raw))))
        max_tau_total_abs = max(max_tau_total_abs, float(np.max(np.abs(tau_total))))

        if np.isfinite(metrics["dyn_res_norm"]):
            max_dyn_res_norm = max(max_dyn_res_norm, metrics["dyn_res_norm"])
        if np.isfinite(metrics["stance_acc_res_norm"]):
            max_stance_acc_res_norm = max(max_stance_acc_res_norm, metrics["stance_acc_res_norm"])
        if np.isfinite(metrics["swing_acc_error_norm"]):
            max_swing_acc_error_norm = max(max_swing_acc_error_norm, metrics["swing_acc_error_norm"])

    final_z = float(data.qpos[2])
    final_roll, final_pitch = wbc.quat_to_roll_pitch(data.qpos[3:7])

    pass_test = (
        qp_fail_steps == 0
        and saturation_steps == 0
        and min_z > MIN_Z_LIMIT
        and max_abs_roll < MAX_ROLL_LIMIT
        and max_abs_pitch < MAX_PITCH_LIMIT
        and max_joint_error < MAX_JOINT_ERROR_LIMIT
    )

    pass_margin = (
        pass_test
        and min_z - MIN_Z_LIMIT > 0.02
        and MAX_ROLL_LIMIT - max_abs_roll > 0.01
        and MAX_PITCH_LIMIT - max_abs_pitch > 0.01
    )

    return {
        "wbc_torque_scale": wbc_torque_scale,
        "swing_pd_torque_scale": swing_pd_torque_scale,
        "target_scale": target_scale,
        "total_steps": total_steps,
        "transition_count": transition_count,
        "trot_FR_RL_steps": mode_counts["trot_FR_RL"],
        "trot_FL_RR_steps": mode_counts["trot_FL_RR"],
        "initial_z": f"{initial_z:.12f}",
        "final_z": f"{final_z:.12f}",
        "min_z": f"{min_z:.12f}",
        "max_z": f"{max_z:.12f}",
        "delta_z": f"{final_z - initial_z:.12f}",
        "final_roll": f"{final_roll:.12f}",
        "final_pitch": f"{final_pitch:.12f}",
        "max_abs_roll": f"{max_abs_roll:.12f}",
        "roll_margin_to_0p20": f"{MAX_ROLL_LIMIT - max_abs_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "pitch_margin_to_0p20": f"{MAX_PITCH_LIMIT - max_abs_pitch:.12f}",
        "z_margin_to_0p22": f"{min_z - MIN_Z_LIMIT:.12f}",
        "max_joint_error": f"{max_joint_error:.12f}",
        "max_swing_joint_error": f"{max_swing_joint_error:.12f}",
        "max_stance_joint_error": f"{max_stance_joint_error:.12f}",
        "max_tau_wbc_abs": f"{max_tau_wbc_abs:.12f}",
        "max_tau_swing_pd_abs": f"{max_tau_swing_pd_abs:.12f}",
        "max_tau_total_raw_abs": f"{max_tau_total_raw_abs:.12f}",
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


def rank_key(row):
    return (
        row["pass_margin"] != "True",
        row["pass"] != "True",
        float(row["max_joint_error"]),
        float(row["max_abs_roll"]),
        float(row["max_abs_pitch"]),
        float(row["max_tau_total_abs"]),
    )


def main():
    mod = load_combined()
    rows = []

    for wbc_torque_scale in WBC_TORQUE_SCALE_LIST:
        for swing_pd_torque_scale in SWING_PD_TORQUE_SCALE_LIST:
            for target_scale in TARGET_SCALE_LIST:
                row = run_case(
                    mod=mod,
                    wbc_torque_scale=wbc_torque_scale,
                    swing_pd_torque_scale=swing_pd_torque_scale,
                    target_scale=target_scale,
                )
                rows.append(row)

                print(
                    "case "
                    f"wbc_scale={wbc_torque_scale} "
                    f"swing_pd_scale={swing_pd_torque_scale} "
                    f"target_scale={target_scale} "
                    f"max_joint_error={row['max_joint_error']} "
                    f"max_abs_roll={row['max_abs_roll']} "
                    f"max_abs_pitch={row['max_abs_pitch']} "
                    f"max_tau_total_abs={row['max_tau_total_abs']} "
                    f"sat={row['saturation_steps']} "
                    f"pass={row['pass']} "
                    f"pass_margin={row['pass_margin']}"
                )

    ranked = sorted(rows, key=rank_key)
    recommended = ranked[0]

    for row in rows:
        row["recommended"] = str(row is recommended)

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    pass_cases = sum(1 for r in rows if r["pass"] == "True")
    pass_margin_cases = sum(1 for r in rows if r["pass_margin"] == "True")

    print("Stage 7 online full WBC plus swing joint tracking sweep")
    print(f"saved={OUTPUT_CSV}")
    print(f"num_cases={len(rows)}")
    print(f"pass_cases={pass_cases}")
    print(f"pass_margin_cases={pass_margin_cases}")
    print(
        "recommended "
        f"wbc_torque_scale={recommended['wbc_torque_scale']} "
        f"swing_pd_torque_scale={recommended['swing_pd_torque_scale']} "
        f"target_scale={recommended['target_scale']} "
        f"max_joint_error={recommended['max_joint_error']} "
        f"max_abs_roll={recommended['max_abs_roll']} "
        f"max_abs_pitch={recommended['max_abs_pitch']} "
        f"max_tau_total_abs={recommended['max_tau_total_abs']} "
        f"pass={recommended['pass']} "
        f"pass_margin={recommended['pass_margin']}"
    )

    if pass_cases == 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
