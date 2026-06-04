#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


SCENE = "assets/go1/scene.xml"

OUTPUT_CSV = "results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv"
SUMMARY_CSV = "results/logs_sample/stage07_online_swing_trajectory_memory_proto_summary.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

DT = 0.002
TOTAL_STEPS = 1200
PERIOD_STEPS = 400
HALF_PERIOD_STEPS = PERIOD_STEPS // 2

STRIDE_X = 0.015
CLEARANCE_Z = 0.025

MIN_TARGET_Z = 0.015
MAX_TARGET_Z = 0.060

MAX_STEP_DELTA_NORM_WARN = 0.002
MAX_STEP_DELTA_Z_WARN = 0.0015

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


def scheduler_mode(step):
    phase_step = step % PERIOD_STEPS
    cycle_i = step // PERIOD_STEPS
    phase = phase_step / float(PERIOD_STEPS)

    if phase_step < HALF_PERIOD_STEPS:
        mode = "trot_FR_RL"
        mode_step = phase_step
        phase_in_mode = mode_step / float(HALF_PERIOD_STEPS)
    else:
        mode = "trot_FL_RR"
        mode_step = phase_step - HALF_PERIOD_STEPS
        phase_in_mode = mode_step / float(HALF_PERIOD_STEPS)

    return {
        "mode": mode,
        "cycle_i": cycle_i,
        "phase": phase,
        "phase_step": phase_step,
        "mode_step": mode_step,
        "phase_in_mode": phase_in_mode,
        "swing_progress": phase_in_mode,
    }


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

    nominal = {}
    for leg in LEG_ORDER:
        nominal[leg] = np.array(data.site_xpos[site_ids[leg]], dtype=float).copy()

    return site_ids, nominal


def smoothstep(s):
    return s * s * (3.0 - 2.0 * s)


def swing_target(lift_off_pos, touch_down_pos, progress):
    s = smoothstep(progress)
    target = (1.0 - s) * lift_off_pos + s * touch_down_pos
    target[2] +=  CLEARANCE_Z * np.sin(np.pi * progress)
    return target


def main():
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    _site_ids, nominal = set_standing_pose(model, data)

    rows = []

    prev_targets = {leg: nominal[leg].copy() for leg in LEG_ORDER}
    prev_leg_state = {leg: "stance" for leg in LEG_ORDER}

    lift_off_pos = {leg: nominal[leg].copy() for leg in LEG_ORDER}
    touch_down_pos = {leg: nominal[leg].copy() for leg in LEG_ORDER}

    max_step_delta_norm = 0.0
    max_step_delta_z = 0.0
    min_target_z = float("inf")
    max_target_z = -float("inf")

    transition_count = 0
    swing_start_count = 0
    prev_mode = None

    swing_samples = {leg: 0 for leg in LEG_ORDER}
    stance_samples = {leg: 0 for leg in LEG_ORDER}

    for step in range(TOTAL_STEPS):
        sched = scheduler_mode(step)
        mode = sched["mode"]
        progress = sched["swing_progress"]

        is_transition = prev_mode is not None and mode != prev_mode
        if is_transition:
            transition_count += 1
        prev_mode = mode

        stance_legs = CONTACT_MODES[mode]["stance"]
        swing_legs = CONTACT_MODES[mode]["swing"]

        target_by_leg = {}

        for leg in LEG_ORDER:
            state = "swing" if leg in swing_legs else "stance"
            just_entered_swing = state == "swing" and prev_leg_state[leg] != "swing"

            if just_entered_swing:
                swing_start_count += 1
                lift_off_pos[leg] = prev_targets[leg].copy()
                touch_down_pos[leg] = lift_off_pos[leg].copy()
                touch_down_pos[leg][0] += STRIDE_X

            if state == "swing":
                target = swing_target(lift_off_pos[leg], touch_down_pos[leg], progress)
                swing_samples[leg] += 1
            else:
                target = prev_targets[leg].copy()
                target[2] = nominal[leg][2]
                stance_samples[leg] += 1

            target_by_leg[leg] = target
            prev_leg_state[leg] = state

            min_target_z = min(min_target_z, float(target[2]))
            max_target_z = max(max_target_z, float(target[2]))

            delta = target - prev_targets[leg]
            max_step_delta_norm = max(max_step_delta_norm, float(np.linalg.norm(delta)))
            max_step_delta_z = max(max_step_delta_z, abs(float(delta[2])))

        for leg in LEG_ORDER:
            prev_targets[leg] = target_by_leg[leg].copy()

        row = {
            "step": step,
            "time": f"{step * DT:.9f}",
            "cycle_i": sched["cycle_i"],
            "phase": f"{sched['phase']:.12f}",
            "phase_step": sched["phase_step"],
            "mode": mode,
            "mode_step": sched["mode_step"],
            "phase_in_mode": f"{sched['phase_in_mode']:.12f}",
            "swing_progress": f"{progress:.12f}",
            "stance_legs": ",".join(stance_legs),
            "swing_legs": ",".join(swing_legs),
            "is_transition": str(is_transition),
        }

        for leg in LEG_ORDER:
            target = target_by_leg[leg]
            row[f"{leg}_target_x"] = f"{float(target[0]):.12f}"
            row[f"{leg}_target_y"] = f"{float(target[1]):.12f}"
            row[f"{leg}_target_z"] = f"{float(target[2]):.12f}"

        rows.append(row)

    z_pass = min_target_z >= MIN_TARGET_Z and max_target_z <= MAX_TARGET_Z
    smooth_pass = (
        max_step_delta_norm <= MAX_STEP_DELTA_NORM_WARN
        and max_step_delta_z <= MAX_STEP_DELTA_Z_WARN
    )
    balance_pass = all(swing_samples[leg] == stance_samples[leg] for leg in LEG_ORDER)
    transition_pass = transition_count == 5

    # step=0 初始已有 2 条 swing leg 进入 swing；
    # 后续每次 mode transition 又有 2 条 leg 进入 swing。
    expected_swing_start_count = 2 + 2 * transition_count
    swing_start_pass = swing_start_count == expected_swing_start_count

    pass_test = z_pass and smooth_pass and balance_pass and transition_pass and swing_start_pass

    summary = {
        "dt": DT,
        "total_steps": TOTAL_STEPS,
        "period_steps": PERIOD_STEPS,
        "half_period_steps": HALF_PERIOD_STEPS,
        "stride_x": STRIDE_X,
        "clearance_z": CLEARANCE_Z,
        "transition_count": transition_count,
        "swing_start_count": swing_start_count,
        "expected_swing_start_count": expected_swing_start_count,
        "min_target_z": f"{min_target_z:.12f}",
        "max_target_z": f"{max_target_z:.12f}",
        "max_step_delta_norm": f"{max_step_delta_norm:.12f}",
        "max_step_delta_z": f"{max_step_delta_z:.12f}",
        "FR_swing_samples": swing_samples["FR"],
        "FL_swing_samples": swing_samples["FL"],
        "RR_swing_samples": swing_samples["RR"],
        "RL_swing_samples": swing_samples["RL"],
        "FR_stance_samples": stance_samples["FR"],
        "FL_stance_samples": stance_samples["FL"],
        "RR_stance_samples": stance_samples["RR"],
        "RL_stance_samples": stance_samples["RL"],
        "z_pass": str(z_pass),
        "smooth_pass": str(smooth_pass),
        "balance_pass": str(balance_pass),
        "transition_pass": str(transition_pass),
        "swing_start_pass": str(swing_start_pass),
        "pass": str(pass_test),
    }

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print("Stage 7 online swing trajectory memory proto")
    for k, v in summary.items():
        print(f"{k}={v}")

    print(f"saved={OUTPUT_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
