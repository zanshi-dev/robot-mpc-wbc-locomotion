#!/usr/bin/env python3
import csv
import importlib.util
from pathlib import Path

import mujoco
import numpy as np


BASE_SCRIPT = "scripts/stage07_online_swing_joint_target_tracking_support_test.py"
OUTPUT_CSV = "results/logs_sample/stage07_online_swing_joint_tracking_stability_sweep.csv"

KP_LIST = [60.0, 80.0, 100.0]
KD_LIST = [2.0, 4.0, 6.0]
TARGET_SCALE_LIST = [0.60, 0.75, 0.90, 1.00]

MIN_Z_LIMIT = 0.22
MAX_ROLL_LIMIT = 0.20
MAX_PITCH_LIMIT = 0.20
MAX_JOINT_ERROR_LIMIT = 0.08


def load_base():
    spec = importlib.util.spec_from_file_location("swing_tracking_base", BASE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_case(base, kp, kd, target_scale):
    target_rows = base.read_targets()

    model = mujoco.MjModel.from_xml_path(base.SCENE)
    data = mujoco.MjData(model)

    dofs, qadrs = base.actuator_indices(model)
    base.set_standing_pose(model, data)

    q_standing = base.current_actuated_q(data, qadrs)

    initial_z = float(data.qpos[2])
    min_z = initial_z
    max_z = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0

    max_tau_raw_abs = 0.0
    max_tau_total_abs = 0.0
    max_joint_error = 0.0
    max_swing_joint_error = 0.0
    max_stance_joint_error = 0.0

    saturation_steps = 0

    for target in target_rows:
        q_des_full = target["q_des"]
        q_des = q_standing + target_scale * (q_des_full - q_standing)

        q_now = base.current_actuated_q(data, qadrs)
        qd_now = base.current_actuated_qd(data, dofs)

        q_err = q_des - q_now
        tau_raw = kp * q_err - kd * qd_now
        tau = np.clip(tau_raw, -base.TORQUE_LIMIT, base.TORQUE_LIMIT)

        saturated = bool(np.any(np.abs(tau_raw) > base.TORQUE_LIMIT))
        saturation_steps += int(saturated)

        data.ctrl[:] = tau
        mujoco.mj_step(model, data)

        base_z = float(data.qpos[2])
        roll, pitch = base.quat_to_roll_pitch(data.qpos[3:7])

        min_z = min(min_z, base_z)
        max_z = max(max_z, base_z)
        max_abs_roll = max(max_abs_roll, abs(roll))
        max_abs_pitch = max(max_abs_pitch, abs(pitch))

        swing_legs = target["swing_legs"].split(",") if target["swing_legs"] else []
        stance_legs = target["stance_legs"].split(",") if target["stance_legs"] else []

        swing_indices = []
        stance_indices = []
        for leg_i, leg in enumerate(base.LEG_ORDER):
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

        max_tau_raw_abs = max(max_tau_raw_abs, float(np.max(np.abs(tau_raw))))
        max_tau_total_abs = max(max_tau_total_abs, float(np.max(np.abs(tau))))

    final_z = float(data.qpos[2])
    final_roll, final_pitch = base.quat_to_roll_pitch(data.qpos[3:7])

    pass_test = (
        min_z > MIN_Z_LIMIT
        and max_abs_roll < MAX_ROLL_LIMIT
        and max_abs_pitch < MAX_PITCH_LIMIT
        and max_joint_error < MAX_JOINT_ERROR_LIMIT
        and saturation_steps == 0
    )

    pass_margin = (
        pass_test
        and min_z - MIN_Z_LIMIT > 0.02
        and MAX_ROLL_LIMIT - max_abs_roll > 0.01
        and MAX_PITCH_LIMIT - max_abs_pitch > 0.01
    )

    return {
        "kp": kp,
        "kd": kd,
        "target_scale": target_scale,
        "total_steps": len(target_rows),
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
        "max_tau_raw_abs": f"{max_tau_raw_abs:.12f}",
        "max_tau_total_abs": f"{max_tau_total_abs:.12f}",
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
    base = load_base()
    rows = []

    for kp in KP_LIST:
        for kd in KD_LIST:
            for target_scale in TARGET_SCALE_LIST:
                row = run_case(base, kp, kd, target_scale)
                rows.append(row)

                print(
                    "case "
                    f"kp={kp} "
                    f"kd={kd} "
                    f"target_scale={target_scale} "
                    f"max_joint_error={row['max_joint_error']} "
                    f"max_abs_roll={row['max_abs_roll']} "
                    f"max_abs_pitch={row['max_abs_pitch']} "
                    f"max_tau_total_abs={row['max_tau_total_abs']} "
                    f"saturation_steps={row['saturation_steps']} "
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

    print("Stage 7 online swing joint tracking stability sweep")
    print(f"saved={OUTPUT_CSV}")
    print(f"num_cases={len(rows)}")
    print(f"pass_cases={pass_cases}")
    print(f"pass_margin_cases={pass_margin_cases}")
    print(
        "recommended "
        f"kp={recommended['kp']} "
        f"kd={recommended['kd']} "
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
