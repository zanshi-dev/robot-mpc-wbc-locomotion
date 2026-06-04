#!/usr/bin/env python3
from pathlib import Path
import csv
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"
DOC_PATH = ROOT / "docs/STAGE08_ACTIVE_LEG_ORDER_REFACTOR_AND_REGRESSION.md"

TARGET_FILES = [
    ROOT / "scripts/stage07_online_full_wbc_scheduler_recommended_run.py",
    ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py",
]

AB_SCRIPT = ROOT / "scripts/stage08_adapter_backed_stage07_baseline_ab_test.py"
AUDIT_SCRIPT = ROOT / "scripts/stage08_runtime_mapping_duplication_audit.py"
TRIAGE_SCRIPT = ROOT / "scripts/stage08_runtime_mapping_audit_triage.py"

AB_SUMMARY = LOG_DIR / "stage08_adapter_backed_stage07_baseline_ab_test_summary.csv"
TRIAGE_SUMMARY = LOG_DIR / "stage08_runtime_mapping_audit_triage_summary.csv"

LOG_PATH = LOG_DIR / "stage08_active_leg_order_refactor_and_regression_log.csv"
SUMMARY_PATH = LOG_DIR / "stage08_active_leg_order_refactor_and_regression_summary.csv"


def load_summary(path: Path):
    metrics = {}
    if not path.exists():
        return metrics

    with path.open(newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return metrics

    header = [x.strip() for x in rows[0]]

    if len(header) >= 2 and header[0] == "metric" and header[1] == "value":
        for row in rows[1:]:
            if len(row) >= 2:
                metrics[row[0].strip()] = row[1].strip()
        return metrics

    for row in rows[1:]:
        if any(x.strip() for x in row):
            for k, v in zip(header, row):
                metrics[k.strip()] = v.strip()
            return metrics

    return metrics


def as_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def add_row(rows, check, value, expected, passed, detail=""):
    rows.append({
        "check": check,
        "value": str(value),
        "expected": str(expected),
        "pass": bool(passed),
        "detail": detail,
    })


def run_py(script: Path):
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    stem = script.stem
    (LOG_DIR / f"stage08_6_{stem}_stdout.txt").write_text(proc.stdout)
    (LOG_DIR / f"stage08_6_{stem}_stderr.txt").write_text(proc.stderr)

    return proc.returncode


def ensure_adapter_import(text: str):
    import_line = "from common.go1_runtime_interface import MJ_LEG_ORDER"

    if import_line in text:
        return text, False

    lines = text.splitlines()

    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1

    # Keep future imports first if present.
    while insert_at < len(lines) and lines[insert_at].startswith("from __future__ import"):
        insert_at += 1

    lines.insert(insert_at, import_line)
    return "\n".join(lines) + "\n", True


def patch_file(path: Path):
    original = path.read_text()

    backup = LOG_DIR / f"stage08_6_backup_{path.name}.txt"
    if not backup.exists():
        backup.write_text(original)

    text, import_added = ensure_adapter_import(original)

    pattern = re.compile(
        r'^LEG_ORDER\s*=\s*\[\s*[\'"]FR[\'"]\s*,\s*[\'"]FL[\'"]\s*,\s*[\'"]RR[\'"]\s*,\s*[\'"]RL[\'"]\s*\]\s*$',
        flags=re.MULTILINE,
    )

    text2, count = pattern.subn("LEG_ORDER = list(MJ_LEG_ORDER)", text)

    if count == 0 and "LEG_ORDER = list(MJ_LEG_ORDER)" not in text:
        raise RuntimeError(f"No hard-coded LEG_ORDER assignment found in {path}")

    changed = text2 != original
    if changed:
        path.write_text(text2)

    return {
        "path": path,
        "backup": backup,
        "changed": changed,
        "import_added": import_added,
        "replacement_count": count,
    }


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for path in TARGET_FILES:
        add_row(rows, f"target_exists_{path.name}", path.exists(), True, path.exists(), str(path))
        if not path.exists():
            raise FileNotFoundError(path)

    patch_results = []
    for path in TARGET_FILES:
        result = patch_file(path)
        patch_results.append(result)

        add_row(
            rows,
            f"patched_{path.name}",
            {
                "changed": result["changed"],
                "replacement_count": result["replacement_count"],
                "import_added": result["import_added"],
            },
            "LEG_ORDER = list(MJ_LEG_ORDER)",
            "LEG_ORDER = list(MJ_LEG_ORDER)" in path.read_text(),
            str(result["backup"].relative_to(ROOT)),
        )

    for path in TARGET_FILES:
        rc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        (LOG_DIR / f"stage08_6_py_compile_{path.name}.stderr.txt").write_text(rc.stderr)
        add_row(rows, f"py_compile_{path.name}", rc.returncode, 0, rc.returncode == 0)

    ab_rc = run_py(AB_SCRIPT)
    add_row(rows, "rerun_stage83_ab_returncode", ab_rc, 0, ab_rc == 0)

    ab_metrics = load_summary(AB_SUMMARY)
    ab_pass = as_bool(ab_metrics.get("pass", "False"))
    original_pass = as_bool(ab_metrics.get("original_pass", "False"))
    adapter_pass = as_bool(ab_metrics.get("adapter_pass", "False"))
    original_pass_margin = as_bool(ab_metrics.get("original_pass_margin", "False"))
    adapter_pass_margin = as_bool(ab_metrics.get("adapter_pass_margin", "False"))

    add_row(rows, "rerun_stage83_ab_pass", ab_pass, True, ab_pass)
    add_row(rows, "rerun_original_pass", original_pass, True, original_pass)
    add_row(rows, "rerun_adapter_pass", adapter_pass, True, adapter_pass)
    add_row(rows, "rerun_original_pass_margin", original_pass_margin, True, original_pass_margin)
    add_row(rows, "rerun_adapter_pass_margin", adapter_pass_margin, True, adapter_pass_margin)

    audit_rc = run_py(AUDIT_SCRIPT)
    add_row(rows, "rerun_stage84_audit_returncode", audit_rc, 0, audit_rc == 0)

    triage_rc = run_py(TRIAGE_SCRIPT)
    add_row(rows, "rerun_stage85_triage_returncode", triage_rc, 0, triage_rc == 0)

    triage_metrics = load_summary(TRIAGE_SUMMARY)
    triage_pass = as_bool(triage_metrics.get("pass", "False"))
    active_high = int(float(triage_metrics.get("active_high_severity_findings", "999")))
    active_medium = int(float(triage_metrics.get("active_medium_severity_findings", "999")))
    active_low = int(float(triage_metrics.get("active_low_severity_findings", "999")))
    active_total = int(float(triage_metrics.get("active_dependency_findings", "999")))

    add_row(rows, "rerun_stage85_triage_pass", triage_pass, True, triage_pass)
    add_row(rows, "active_high_severity_findings_after_refactor", active_high, 0, active_high == 0)

    all_pass = all(row["pass"] for row in rows)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = [
        ("stage", "Stage 8.6"),
        ("test_name", "active_leg_order_refactor_and_regression"),
        ("patched_files", ";".join(str(x["path"].relative_to(ROOT)) for x in patch_results)),
        ("rerun_stage83_ab_pass", ab_pass),
        ("rerun_original_pass", original_pass),
        ("rerun_adapter_pass", adapter_pass),
        ("rerun_original_pass_margin", original_pass_margin),
        ("rerun_adapter_pass_margin", adapter_pass_margin),
        ("rerun_stage85_triage_pass", triage_pass),
        ("active_dependency_findings_after_refactor", active_total),
        ("active_high_severity_findings_after_refactor", active_high),
        ("active_medium_severity_findings_after_refactor", active_medium),
        ("active_low_severity_findings_after_refactor", active_low),
        ("num_checks", len(rows)),
        ("num_failed_checks", sum(1 for row in rows if not row["pass"])),
        ("pass", all_pass),
        ("log_csv", str(LOG_PATH.relative_to(ROOT))),
        ("summary_csv", str(SUMMARY_PATH.relative_to(ROOT))),
    ]

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(summary_rows)

    DOC_PATH.write_text(f"""# Stage 8.6 Active-path Hard-coded MuJoCo Leg Order Refactor and Regression

## Target

Replace active-path hard-coded MuJoCo leg order assignments with the shared runtime adapter constant:

- `MJ_LEG_ORDER`
- source module: `scripts/common/go1_runtime_interface.py`

## Patched files

- `scripts/stage07_online_full_wbc_scheduler_recommended_run.py`
- `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`

## Boundary

This stage only replaces duplicated active-path leg-order constants.

It does not change:

- control gains
- gait scheduler
- WBC/QP formulation
- swing target tracking
- torque limits
- ROS2/C++ code
- EKF
- MPC

The controller remains the Stage 7 mixed online control baseline.

## Regression

After patching, Stage 8.3 A/B regression was rerun.

## Result

- pass: `{all_pass}`
- rerun_stage83_ab_pass: `{ab_pass}`
- rerun_original_pass: `{original_pass}`
- rerun_adapter_pass: `{adapter_pass}`
- rerun_original_pass_margin: `{original_pass_margin}`
- rerun_adapter_pass_margin: `{adapter_pass_margin}`
- active_high_severity_findings_after_refactor: `{active_high}`
- active_medium_severity_findings_after_refactor: `{active_medium}`
- active_low_severity_findings_after_refactor: `{active_low}`

## Interpretation

If `active_high_severity_findings_after_refactor = 0`, the highest-risk active-path runtime mapping duplication has been removed.

Remaining active medium findings may be false positives from adapter preflight sample torque variables and should not be treated as controller failures without inspection.
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 8.6 Active-path Hard-coded MuJoCo Leg Order Refactor and Regression

Stage 8.6 replaced active-path hard-coded MuJoCo leg order assignments with the shared adapter constant `MJ_LEG_ORDER`.

- Script: `scripts/stage08_active_leg_order_refactor_and_regression.py`
- Patched files:
  - `scripts/stage07_online_full_wbc_scheduler_recommended_run.py`
  - `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- Log: `results/logs_sample/stage08_active_leg_order_refactor_and_regression_log.csv`
- Summary: `results/logs_sample/stage08_active_leg_order_refactor_and_regression_summary.csv`
- Docs: `docs/STAGE08_ACTIVE_LEG_ORDER_REFACTOR_AND_REGRESSION.md`
- pass: `{all_pass}`
- rerun_stage83_ab_pass: `{ab_pass}`
- active_high_severity_findings_after_refactor: `{active_high}`
- active_medium_severity_findings_after_refactor: `{active_medium}`
- active_low_severity_findings_after_refactor: `{active_low}`

This is an active-path runtime interface refactor with A/B regression. It does not complete pure WBC locomotion, ROS2/C++ migration, EKF, or full MPC.
""".strip()

    old_status = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 8.6 Active-path Hard-coded MuJoCo Leg Order Refactor and Regression"
    if marker not in old_status:
        status_path.write_text(old_status.rstrip() + "\n\n" + block + "\n")

    print("[Stage 8.6] active-path hard-coded MuJoCo leg order refactor and regression")
    print(f"pass={all_pass}")
    print(f"rerun_stage83_ab_pass={ab_pass}")
    print(f"active_high_severity_findings_after_refactor={active_high}")
    print(f"active_medium_severity_findings_after_refactor={active_medium}")
    print(f"active_low_severity_findings_after_refactor={active_low}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed checks:")
        for row in rows:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
