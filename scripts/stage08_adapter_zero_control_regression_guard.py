#!/usr/bin/env python3
from pathlib import Path
import csv
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common.go1_runtime_interface import (  # noqa: E402
    CONTRACT,
    make_nominal_mujoco_qpos,
    roundtrip_errors,
)

STAGE07_SCRIPT = ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py"
STAGE07_SUMMARY = ROOT / "results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv"

LOG_DIR = ROOT / "results/logs_sample"
LOG_PATH = LOG_DIR / "stage08_adapter_zero_control_regression_guard_log.csv"
SUMMARY_PATH = LOG_DIR / "stage08_adapter_zero_control_regression_guard_summary.csv"
SUBPROCESS_STDOUT_PATH = LOG_DIR / "stage08_adapter_zero_control_regression_guard_stage07_stdout.txt"
SUBPROCESS_STDERR_PATH = LOG_DIR / "stage08_adapter_zero_control_regression_guard_stage07_stderr.txt"
DOC_PATH = ROOT / "docs/STAGE08_ADAPTER_ZERO_CONTROL_REGRESSION_GUARD.md"


def parse_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def parse_float(metrics, key, default=np.nan):
    try:
        return float(metrics.get(key, default))
    except Exception:
        return default


def load_summary(path: Path):
    """
    Supports both summary CSV schemas:

    1. Vertical:
       metric,value
       pass,True

    2. Wide:
       total_steps,...,pass,pass_margin
       1200,...,True,True
    """
    metrics = {}

    with path.open(newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return metrics

    header = [cell.strip() for cell in rows[0]]

    # Vertical metric,value schema.
    if len(header) >= 2 and header[0] == "metric" and header[1] == "value":
        for row in rows[1:]:
            if len(row) >= 2:
                metrics[row[0].strip()] = row[1].strip()
        return metrics

    # Wide header + first non-empty value row schema.
    for row in rows[1:]:
        if any(cell.strip() for cell in row):
            for key, value in zip(header, row):
                metrics[key.strip()] = value.strip()
            return metrics

    return metrics


def add_check(rows, name, value, expected, passed, detail=""):
    rows.append({
        "check": name,
        "value": str(value),
        "expected": str(expected),
        "pass": bool(passed),
        "detail": detail,
    })


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    q_mj = make_nominal_mujoco_qpos(
        base_xyz=(0.12, -0.03, 0.286),
        quat_wxyz=(1.0, 0.01, -0.02, 0.015),
        one_leg_q=(0.0, 0.9, -1.8),
    )
    q_mj[7:] += np.linspace(-0.03, 0.03, CONTRACT.mj_nu)
    v_mj = np.linspace(-0.17, 0.19, CONTRACT.mj_nv)
    tau_mj = np.linspace(-5.0, 5.0, CONTRACT.mj_nu)

    adapter_errors = roundtrip_errors(q_mj, v_mj, tau_mj)

    add_check(
        rows,
        "adapter_qpos_roundtrip",
        adapter_errors["qpos_roundtrip_max_abs"],
        "<=1e-12",
        adapter_errors["qpos_roundtrip_max_abs"] <= 1e-12,
    )
    add_check(
        rows,
        "adapter_qvel_roundtrip",
        adapter_errors["qvel_roundtrip_max_abs"],
        "<=1e-12",
        adapter_errors["qvel_roundtrip_max_abs"] <= 1e-12,
    )
    add_check(
        rows,
        "adapter_torque_roundtrip",
        adapter_errors["torque_roundtrip_max_abs"],
        "<=1e-12",
        adapter_errors["torque_roundtrip_max_abs"] <= 1e-12,
    )

    add_check(rows, "stage07_script_exists", STAGE07_SCRIPT.exists(), True, STAGE07_SCRIPT.exists(), str(STAGE07_SCRIPT))

    if not STAGE07_SCRIPT.exists():
        raise FileNotFoundError(f"Missing Stage 7 recommended script: {STAGE07_SCRIPT}")

    proc = subprocess.run(
        [sys.executable, str(STAGE07_SCRIPT)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    SUBPROCESS_STDOUT_PATH.write_text(proc.stdout)
    SUBPROCESS_STDERR_PATH.write_text(proc.stderr)

    add_check(rows, "stage07_subprocess_returncode", proc.returncode, 0, proc.returncode == 0)
    add_check(rows, "stage07_summary_exists", STAGE07_SUMMARY.exists(), True, STAGE07_SUMMARY.exists(), str(STAGE07_SUMMARY))

    metrics = {}
    if STAGE07_SUMMARY.exists():
        metrics = load_summary(STAGE07_SUMMARY)

    stage07_pass = parse_bool(metrics.get("pass", "False"))
    stage07_pass_margin = parse_bool(metrics.get("pass_margin", "False"))

    qp_fail_steps = parse_float(metrics, "qp_fail_steps")
    saturation_steps = parse_float(metrics, "saturation_steps")
    max_tau_total_abs = parse_float(metrics, "max_tau_total_abs")
    min_z = parse_float(metrics, "min_z")
    max_abs_roll = parse_float(metrics, "max_abs_roll")
    max_abs_pitch = parse_float(metrics, "max_abs_pitch")
    max_joint_error = parse_float(metrics, "max_joint_error")

    add_check(rows, "stage07_pass", stage07_pass, True, stage07_pass)
    add_check(rows, "stage07_pass_margin", stage07_pass_margin, True, stage07_pass_margin)
    add_check(rows, "stage07_qp_fail_steps", qp_fail_steps, 0, qp_fail_steps == 0)
    add_check(rows, "stage07_saturation_steps", saturation_steps, 0, saturation_steps == 0)
    add_check(rows, "stage07_max_tau_total_abs_within_limit", max_tau_total_abs, f"<={CONTRACT.torque_limit}", max_tau_total_abs <= CONTRACT.torque_limit)
    add_check(rows, "stage07_min_z_margin", min_z, ">=0.22", min_z >= 0.22)
    add_check(rows, "stage07_roll_bound_guard", max_abs_roll, "<=0.08", max_abs_roll <= 0.08)
    add_check(rows, "stage07_pitch_bound_guard", max_abs_pitch, "<=0.08", max_abs_pitch <= 0.08)
    add_check(rows, "stage07_joint_error_guard", max_joint_error, "<=0.12", max_joint_error <= 0.12)

    all_pass = all(row["pass"] for row in rows)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = [
        ("stage", "Stage 8.2"),
        ("test_name", "adapter_zero_control_regression_guard"),
        ("adapter_module", "scripts/common/go1_runtime_interface.py"),
        ("stage07_script", str(STAGE07_SCRIPT.relative_to(ROOT))),
        ("stage07_summary", str(STAGE07_SUMMARY.relative_to(ROOT))),
        ("adapter_qpos_roundtrip_max_abs", adapter_errors["qpos_roundtrip_max_abs"]),
        ("adapter_qvel_roundtrip_max_abs", adapter_errors["qvel_roundtrip_max_abs"]),
        ("adapter_torque_roundtrip_max_abs", adapter_errors["torque_roundtrip_max_abs"]),
        ("stage07_pass", stage07_pass),
        ("stage07_pass_margin", stage07_pass_margin),
        ("stage07_qp_fail_steps", qp_fail_steps),
        ("stage07_saturation_steps", saturation_steps),
        ("stage07_min_z", min_z),
        ("stage07_max_abs_roll", max_abs_roll),
        ("stage07_max_abs_pitch", max_abs_pitch),
        ("stage07_max_joint_error", max_joint_error),
        ("stage07_max_tau_total_abs", max_tau_total_abs),
        ("num_checks", len(rows)),
        ("num_failed_checks", sum(1 for row in rows if not row["pass"])),
        ("pass", all_pass),
        ("log_csv", str(LOG_PATH.relative_to(ROOT))),
        ("summary_csv", str(SUMMARY_PATH.relative_to(ROOT))),
        ("stage07_stdout", str(SUBPROCESS_STDOUT_PATH.relative_to(ROOT))),
        ("stage07_stderr", str(SUBPROCESS_STDERR_PATH.relative_to(ROOT))),
    ]

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(summary_rows)

    DOC_PATH.write_text(f"""# Stage 8.2 Adapter Zero-Control Regression Guard

## Target

Before modifying the Stage 7 mixed baseline controller, this check verifies that:

1. The Stage 8.1 runtime adapter still satisfies qpos/qvel/torque round-trip contracts.
2. The existing Stage 7 recommended mixed baseline still passes without changing control logic.

## Control boundary

No controller parameter is changed in this stage.

Stage 7 baseline remains:

- stance PD
- scaled stance WBC feedforward
- swing target PD

This is still a mixed online control baseline, not pure full WBC locomotion.

## Outputs

- Log CSV: `results/logs_sample/stage08_adapter_zero_control_regression_guard_log.csv`
- Summary CSV: `results/logs_sample/stage08_adapter_zero_control_regression_guard_summary.csv`
- Stage 7 stdout: `results/logs_sample/stage08_adapter_zero_control_regression_guard_stage07_stdout.txt`
- Stage 7 stderr: `results/logs_sample/stage08_adapter_zero_control_regression_guard_stage07_stderr.txt`

## Result

- pass: `{all_pass}`
- adapter_qpos_roundtrip_max_abs: `{adapter_errors["qpos_roundtrip_max_abs"]}`
- adapter_qvel_roundtrip_max_abs: `{adapter_errors["qvel_roundtrip_max_abs"]}`
- adapter_torque_roundtrip_max_abs: `{adapter_errors["torque_roundtrip_max_abs"]}`
- stage07_pass: `{stage07_pass}`
- stage07_pass_margin: `{stage07_pass_margin}`
- stage07_qp_fail_steps: `{qp_fail_steps}`
- stage07_saturation_steps: `{saturation_steps}`

## Interpretation

Passing this stage means the reusable adapter is available and the previous Stage 7 recommended baseline remains intact before any refactor.

The next step can safely refactor duplicated state/torque mapping code to use `scripts/common/go1_runtime_interface.py`.
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 8.2 Adapter Zero-Control Regression Guard

Stage 8.2 verified the Stage 8.1 runtime adapter and reran the Stage 7 recommended mixed baseline without changing controller logic.

- Script: `scripts/stage08_adapter_zero_control_regression_guard.py`
- Log: `results/logs_sample/stage08_adapter_zero_control_regression_guard_log.csv`
- Summary: `results/logs_sample/stage08_adapter_zero_control_regression_guard_summary.csv`
- Docs: `docs/STAGE08_ADAPTER_ZERO_CONTROL_REGRESSION_GUARD.md`
- pass: `{all_pass}`
- adapter_qpos_roundtrip_max_abs: `{adapter_errors["qpos_roundtrip_max_abs"]}`
- adapter_qvel_roundtrip_max_abs: `{adapter_errors["qvel_roundtrip_max_abs"]}`
- adapter_torque_roundtrip_max_abs: `{adapter_errors["torque_roundtrip_max_abs"]}`
- stage07_pass: `{stage07_pass}`
- stage07_pass_margin: `{stage07_pass_margin}`
- stage07_qp_fail_steps: `{qp_fail_steps}`
- stage07_saturation_steps: `{saturation_steps}`

This stage is a zero-control-change regression guard. It does not complete ROS2/C++ migration, EKF, base velocity tracking, full MPC, or pure full WBC locomotion.
""".strip()

    old_status = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 8.2 Adapter Zero-Control Regression Guard"
    if marker not in old_status:
        status_path.write_text(old_status.rstrip() + "\n\n" + block + "\n")

    print("[Stage 8.2] adapter zero-control regression guard")
    print(f"pass={all_pass}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed checks:")
        for row in rows:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        print(f"\nStage 7 stdout: {SUBPROCESS_STDOUT_PATH.relative_to(ROOT)}")
        print(f"Stage 7 stderr: {SUBPROCESS_STDERR_PATH.relative_to(ROOT)}")
        sys.exit(2)


if __name__ == "__main__":
    main()
