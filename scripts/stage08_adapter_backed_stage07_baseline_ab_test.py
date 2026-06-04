#!/usr/bin/env python3
from pathlib import Path
import csv
import runpy
import shutil
import subprocess
import sys
import textwrap
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common.go1_runtime_interface import (  # noqa: E402
    CONTRACT,
    make_nominal_mujoco_qpos,
    roundtrip_errors,
)

STAGE07_ORIGINAL_SCRIPT = ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py"
STAGE08_ADAPTER_BACKED_SCRIPT = ROOT / "scripts/stage08_adapter_backed_stage07_recommended_test.py"

STAGE07_SUMMARY = ROOT / "results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv"
STAGE07_LOG = ROOT / "results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv"

LOG_DIR = ROOT / "results/logs_sample"

ORIGINAL_SUMMARY_COPY = LOG_DIR / "stage08_ab_original_stage07_summary.csv"
ORIGINAL_LOG_COPY = LOG_DIR / "stage08_ab_original_stage07_log.csv"
ADAPTER_SUMMARY_COPY = LOG_DIR / "stage08_ab_adapter_backed_stage07_summary.csv"
ADAPTER_LOG_COPY = LOG_DIR / "stage08_ab_adapter_backed_stage07_log.csv"

ORIGINAL_STDOUT = LOG_DIR / "stage08_ab_original_stdout.txt"
ORIGINAL_STDERR = LOG_DIR / "stage08_ab_original_stderr.txt"
ADAPTER_STDOUT = LOG_DIR / "stage08_ab_adapter_backed_stdout.txt"
ADAPTER_STDERR = LOG_DIR / "stage08_ab_adapter_backed_stderr.txt"

AB_LOG_PATH = LOG_DIR / "stage08_adapter_backed_stage07_baseline_ab_test_log.csv"
AB_SUMMARY_PATH = LOG_DIR / "stage08_adapter_backed_stage07_baseline_ab_test_summary.csv"
DOC_PATH = ROOT / "docs/STAGE08_ADAPTER_BACKED_STAGE07_BASELINE_AB_TEST.md"


KEY_BOOL_METRICS = [
    "pass",
    "pass_margin",
]

KEY_NUMERIC_METRICS = [
    "total_steps",
    "transition_count",
    "trot_FR_RL_steps",
    "trot_FL_RR_steps",
    "initial_z",
    "final_z",
    "min_z",
    "max_z",
    "delta_z",
    "final_roll",
    "final_pitch",
    "max_abs_roll",
    "max_abs_pitch",
    "z_margin_to_0p22",
    "max_joint_error",
    "max_swing_joint_error",
    "max_stance_joint_error",
    "max_tau_stance_pd_abs",
    "max_tau_stance_wbc_abs",
    "max_tau_swing_pd_abs",
    "max_tau_total_abs",
    "qp_fail_steps",
    "saturation_steps",
]


def parse_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def parse_float(x):
    try:
        return float(str(x).strip())
    except Exception:
        return np.nan


def load_summary(path: Path):
    metrics = {}
    with path.open(newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return metrics

    header = [cell.strip() for cell in rows[0]]

    if len(header) >= 2 and header[0] == "metric" and header[1] == "value":
        for row in rows[1:]:
            if len(row) >= 2:
                metrics[row[0].strip()] = row[1].strip()
        return metrics

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


def adapter_preflight_errors():
    q_mj = make_nominal_mujoco_qpos(
        base_xyz=(0.12, -0.03, 0.286),
        quat_wxyz=(1.0, 0.01, -0.02, 0.015),
        one_leg_q=(0.0, 0.9, -1.8),
    )
    q_mj[7:] += np.linspace(-0.03, 0.03, CONTRACT.mj_nu)
    v_mj = np.linspace(-0.17, 0.19, CONTRACT.mj_nv)
    tau_mj = np.linspace(-5.0, 5.0, CONTRACT.mj_nu)
    return roundtrip_errors(q_mj, v_mj, tau_mj)


def write_adapter_backed_entrypoint():
    code = f'''#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common.go1_runtime_interface import (
    CONTRACT,
    make_nominal_mujoco_qpos,
    roundtrip_errors,
)

STAGE07_ORIGINAL_SCRIPT = ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py"


def adapter_preflight():
    q_mj = make_nominal_mujoco_qpos(
        base_xyz=(0.12, -0.03, 0.286),
        quat_wxyz=(1.0, 0.01, -0.02, 0.015),
        one_leg_q=(0.0, 0.9, -1.8),
    )
    q_mj[7:] += np.linspace(-0.03, 0.03, CONTRACT.mj_nu)
    v_mj = np.linspace(-0.17, 0.19, CONTRACT.mj_nv)
    tau_mj = np.linspace(-5.0, 5.0, CONTRACT.mj_nu)

    errors = roundtrip_errors(q_mj, v_mj, tau_mj)

    if errors["qpos_roundtrip_max_abs"] > 1e-12:
        raise RuntimeError(f"qpos adapter round-trip failed: {{errors}}")
    if errors["qvel_roundtrip_max_abs"] > 1e-12:
        raise RuntimeError(f"qvel adapter round-trip failed: {{errors}}")
    if errors["torque_roundtrip_max_abs"] > 1e-12:
        raise RuntimeError(f"torque adapter round-trip failed: {{errors}}")

    print("[adapter-preflight] pass=True")
    print(f"[adapter-preflight] qpos_roundtrip_max_abs={{errors['qpos_roundtrip_max_abs']}}")
    print(f"[adapter-preflight] qvel_roundtrip_max_abs={{errors['qvel_roundtrip_max_abs']}}")
    print(f"[adapter-preflight] torque_roundtrip_max_abs={{errors['torque_roundtrip_max_abs']}}")


def main():
    if not STAGE07_ORIGINAL_SCRIPT.exists():
        raise FileNotFoundError(STAGE07_ORIGINAL_SCRIPT)

    adapter_preflight()
    runpy.run_path(str(STAGE07_ORIGINAL_SCRIPT), run_name="__main__")


if __name__ == "__main__":
    main()
'''
    STAGE08_ADAPTER_BACKED_SCRIPT.write_text(code)
    STAGE08_ADAPTER_BACKED_SCRIPT.chmod(0o755)


def run_script(script: Path, stdout_path: Path, stderr_path: Path):
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    stdout_path.write_text(proc.stdout)
    stderr_path.write_text(proc.stderr)
    return proc.returncode


def copy_if_exists(src: Path, dst: Path):
    if src.exists():
        shutil.copy2(src, dst)
        return True
    return False


def compare_metrics(rows, original, adapter):
    tolerance = 1e-9

    for key in KEY_BOOL_METRICS:
        o = parse_bool(original.get(key, "False"))
        a = parse_bool(adapter.get(key, "False"))
        add_check(rows, f"ab_bool_equal_{key}", {"original": o, "adapter": a}, "equal", o == a)

    for key in KEY_NUMERIC_METRICS:
        o = parse_float(original.get(key, "nan"))
        a = parse_float(adapter.get(key, "nan"))

        both_finite = np.isfinite(o) and np.isfinite(a)
        diff = abs(o - a) if both_finite else np.nan
        passed = both_finite and diff <= tolerance

        add_check(
            rows,
            f"ab_numeric_equal_{key}",
            {"original": o, "adapter": a, "abs_diff": diff},
            f"abs_diff<={tolerance}",
            passed,
        )


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    add_check(rows, "stage07_original_script_exists", STAGE07_ORIGINAL_SCRIPT.exists(), True, STAGE07_ORIGINAL_SCRIPT.exists())
    if not STAGE07_ORIGINAL_SCRIPT.exists():
        raise FileNotFoundError(STAGE07_ORIGINAL_SCRIPT)

    errors = adapter_preflight_errors()
    add_check(rows, "adapter_qpos_roundtrip", errors["qpos_roundtrip_max_abs"], "<=1e-12", errors["qpos_roundtrip_max_abs"] <= 1e-12)
    add_check(rows, "adapter_qvel_roundtrip", errors["qvel_roundtrip_max_abs"], "<=1e-12", errors["qvel_roundtrip_max_abs"] <= 1e-12)
    add_check(rows, "adapter_torque_roundtrip", errors["torque_roundtrip_max_abs"], "<=1e-12", errors["torque_roundtrip_max_abs"] <= 1e-12)

    write_adapter_backed_entrypoint()
    add_check(rows, "adapter_backed_script_created", STAGE08_ADAPTER_BACKED_SCRIPT.exists(), True, STAGE08_ADAPTER_BACKED_SCRIPT.exists())

    original_rc = run_script(STAGE07_ORIGINAL_SCRIPT, ORIGINAL_STDOUT, ORIGINAL_STDERR)
    add_check(rows, "original_stage07_returncode", original_rc, 0, original_rc == 0)

    original_summary_exists = copy_if_exists(STAGE07_SUMMARY, ORIGINAL_SUMMARY_COPY)
    original_log_exists = copy_if_exists(STAGE07_LOG, ORIGINAL_LOG_COPY)
    add_check(rows, "original_summary_copied", original_summary_exists, True, original_summary_exists)
    add_check(rows, "original_log_copied", original_log_exists, True, original_log_exists)

    adapter_rc = run_script(STAGE08_ADAPTER_BACKED_SCRIPT, ADAPTER_STDOUT, ADAPTER_STDERR)
    add_check(rows, "adapter_backed_stage07_returncode", adapter_rc, 0, adapter_rc == 0)

    adapter_summary_exists = copy_if_exists(STAGE07_SUMMARY, ADAPTER_SUMMARY_COPY)
    adapter_log_exists = copy_if_exists(STAGE07_LOG, ADAPTER_LOG_COPY)
    add_check(rows, "adapter_summary_copied", adapter_summary_exists, True, adapter_summary_exists)
    add_check(rows, "adapter_log_copied", adapter_log_exists, True, adapter_log_exists)

    original_metrics = load_summary(ORIGINAL_SUMMARY_COPY) if ORIGINAL_SUMMARY_COPY.exists() else {}
    adapter_metrics = load_summary(ADAPTER_SUMMARY_COPY) if ADAPTER_SUMMARY_COPY.exists() else {}

    add_check(rows, "original_stage07_pass", parse_bool(original_metrics.get("pass", "False")), True, parse_bool(original_metrics.get("pass", "False")))
    add_check(rows, "adapter_stage07_pass", parse_bool(adapter_metrics.get("pass", "False")), True, parse_bool(adapter_metrics.get("pass", "False")))
    add_check(rows, "original_stage07_pass_margin", parse_bool(original_metrics.get("pass_margin", "False")), True, parse_bool(original_metrics.get("pass_margin", "False")))
    add_check(rows, "adapter_stage07_pass_margin", parse_bool(adapter_metrics.get("pass_margin", "False")), True, parse_bool(adapter_metrics.get("pass_margin", "False")))

    compare_metrics(rows, original_metrics, adapter_metrics)

    all_pass = all(row["pass"] for row in rows)

    with AB_LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = [
        ("stage", "Stage 8.3"),
        ("test_name", "adapter_backed_stage07_baseline_ab_test"),
        ("original_script", str(STAGE07_ORIGINAL_SCRIPT.relative_to(ROOT))),
        ("adapter_backed_script", str(STAGE08_ADAPTER_BACKED_SCRIPT.relative_to(ROOT))),
        ("adapter_qpos_roundtrip_max_abs", errors["qpos_roundtrip_max_abs"]),
        ("adapter_qvel_roundtrip_max_abs", errors["qvel_roundtrip_max_abs"]),
        ("adapter_torque_roundtrip_max_abs", errors["torque_roundtrip_max_abs"]),
        ("original_returncode", original_rc),
        ("adapter_returncode", adapter_rc),
        ("original_pass", parse_bool(original_metrics.get("pass", "False"))),
        ("adapter_pass", parse_bool(adapter_metrics.get("pass", "False"))),
        ("original_pass_margin", parse_bool(original_metrics.get("pass_margin", "False"))),
        ("adapter_pass_margin", parse_bool(adapter_metrics.get("pass_margin", "False"))),
        ("original_max_tau_total_abs", original_metrics.get("max_tau_total_abs", "")),
        ("adapter_max_tau_total_abs", adapter_metrics.get("max_tau_total_abs", "")),
        ("original_min_z", original_metrics.get("min_z", "")),
        ("adapter_min_z", adapter_metrics.get("min_z", "")),
        ("original_max_abs_roll", original_metrics.get("max_abs_roll", "")),
        ("adapter_max_abs_roll", adapter_metrics.get("max_abs_roll", "")),
        ("original_max_abs_pitch", original_metrics.get("max_abs_pitch", "")),
        ("adapter_max_abs_pitch", adapter_metrics.get("max_abs_pitch", "")),
        ("original_qp_fail_steps", original_metrics.get("qp_fail_steps", "")),
        ("adapter_qp_fail_steps", adapter_metrics.get("qp_fail_steps", "")),
        ("original_saturation_steps", original_metrics.get("saturation_steps", "")),
        ("adapter_saturation_steps", adapter_metrics.get("saturation_steps", "")),
        ("num_checks", len(rows)),
        ("num_failed_checks", sum(1 for row in rows if not row["pass"])),
        ("pass", all_pass),
        ("log_csv", str(AB_LOG_PATH.relative_to(ROOT))),
        ("summary_csv", str(AB_SUMMARY_PATH.relative_to(ROOT))),
        ("original_summary_copy", str(ORIGINAL_SUMMARY_COPY.relative_to(ROOT))),
        ("adapter_summary_copy", str(ADAPTER_SUMMARY_COPY.relative_to(ROOT))),
        ("original_stdout", str(ORIGINAL_STDOUT.relative_to(ROOT))),
        ("original_stderr", str(ORIGINAL_STDERR.relative_to(ROOT))),
        ("adapter_stdout", str(ADAPTER_STDOUT.relative_to(ROOT))),
        ("adapter_stderr", str(ADAPTER_STDERR.relative_to(ROOT))),
    ]

    with AB_SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(summary_rows)

    DOC_PATH.write_text(f"""# Stage 8.3 Adapter-backed Stage 7 Baseline A/B Test

## Target

Create an adapter-backed Stage 7 baseline entrypoint and compare it against the original Stage 7 recommended mixed baseline.

## Scripts

- Original: `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- Adapter-backed entrypoint: `scripts/stage08_adapter_backed_stage07_recommended_test.py`
- A/B test: `scripts/stage08_adapter_backed_stage07_baseline_ab_test.py`

## Boundary

This stage does not change control parameters or controller structure.

The adapter-backed entrypoint performs a runtime adapter preflight before executing the original Stage 7 recommended baseline.

This is still the Stage 7 mixed online control baseline:

- stance PD
- scaled stance WBC feedforward
- swing target PD

It is not pure full WBC locomotion.

## Outputs

- A/B log: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_log.csv`
- A/B summary: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv`
- Original summary copy: `results/logs_sample/stage08_ab_original_stage07_summary.csv`
- Adapter-backed summary copy: `results/logs_sample/stage08_ab_adapter_backed_stage07_summary.csv`

## Result

- pass: `{all_pass}`
- adapter_qpos_roundtrip_max_abs: `{errors["qpos_roundtrip_max_abs"]}`
- adapter_qvel_roundtrip_max_abs: `{errors["qvel_roundtrip_max_abs"]}`
- adapter_torque_roundtrip_max_abs: `{errors["torque_roundtrip_max_abs"]}`
- original_pass: `{parse_bool(original_metrics.get("pass", "False"))}`
- adapter_pass: `{parse_bool(adapter_metrics.get("pass", "False"))}`
- original_pass_margin: `{parse_bool(original_metrics.get("pass_margin", "False"))}`
- adapter_pass_margin: `{parse_bool(adapter_metrics.get("pass_margin", "False"))}`

## Interpretation

Passing this stage means the adapter-backed entrypoint does not change the Stage 7 recommended baseline result.

The next stage may refactor duplicated runtime mapping calls to use `scripts/common/go1_runtime_interface.py` directly, if such duplicated calls exist in controller scripts.
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 8.3 Adapter-backed Stage 7 Baseline A/B Test

Stage 8.3 created an adapter-backed Stage 7 entrypoint and compared it with the original Stage 7 recommended mixed baseline.

- Original script: `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- Adapter-backed script: `scripts/stage08_adapter_backed_stage07_recommended_test.py`
- A/B script: `scripts/stage08_adapter_backed_stage07_baseline_ab_test.py`
- Log: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_log.csv`
- Summary: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv`
- Docs: `docs/STAGE08_ADAPTER_BACKED_STAGE07_BASELINE_AB_TEST.md`
- pass: `{all_pass}`
- adapter_qpos_roundtrip_max_abs: `{errors["qpos_roundtrip_max_abs"]}`
- adapter_qvel_roundtrip_max_abs: `{errors["qvel_roundtrip_max_abs"]}`
- adapter_torque_roundtrip_max_abs: `{errors["torque_roundtrip_max_abs"]}`
- original_pass: `{parse_bool(original_metrics.get("pass", "False"))}`
- adapter_pass: `{parse_bool(adapter_metrics.get("pass", "False"))}`
- original_pass_margin: `{parse_bool(original_metrics.get("pass_margin", "False"))}`
- adapter_pass_margin: `{parse_bool(adapter_metrics.get("pass_margin", "False"))}`

This is an adapter-backed entrypoint regression, not a controller redesign. It does not complete pure WBC locomotion, ROS2/C++ migration, EKF, or full MPC.
""".strip()

    old_status = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 8.3 Adapter-backed Stage 7 Baseline A/B Test"
    if marker not in old_status:
        status_path.write_text(old_status.rstrip() + "\n\n" + block + "\n")

    print("[Stage 8.3] adapter-backed Stage 7 baseline A/B test")
    print(f"pass={all_pass}")
    print(f"log_csv={AB_LOG_PATH.relative_to(ROOT)}")
    print(f"summary_csv={AB_SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed checks:")
        for row in rows:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        print(f"\nOriginal stderr: {ORIGINAL_STDERR.relative_to(ROOT)}")
        print(f"Adapter stderr: {ADAPTER_STDERR.relative_to(ROOT)}")
        sys.exit(2)


if __name__ == "__main__":
    main()
