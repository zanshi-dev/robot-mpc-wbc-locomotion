#!/usr/bin/env python3
from pathlib import Path
import csv
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

ADAPTER_MODULE = ROOT / "scripts/common/go1_runtime_interface.py"
STAGE83_SUMMARY = ROOT / "results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv"

LOG_DIR = ROOT / "results/logs_sample"
AUDIT_LOG = LOG_DIR / "stage08_runtime_mapping_duplication_audit_log.csv"
AUDIT_SUMMARY = LOG_DIR / "stage08_runtime_mapping_duplication_audit_summary.csv"
DOC_PATH = ROOT / "docs/STAGE08_RUNTIME_MAPPING_DUPLICATION_AUDIT.md"


PATTERNS = [
    {
        "name": "mujoco_leg_order_literal",
        "regex": r"\[\s*['\"]FR['\"]\s*,\s*['\"]FL['\"]\s*,\s*['\"]RR['\"]\s*,\s*['\"]RL['\"]\s*\]",
        "severity": "high",
        "meaning": "Hard-coded MuJoCo leg order.",
    },
    {
        "name": "pinocchio_leg_order_literal",
        "regex": r"\[\s*['\"]FL['\"]\s*,\s*['\"]FR['\"]\s*,\s*['\"]RL['\"]\s*,\s*['\"]RR['\"]\s*\]",
        "severity": "high",
        "meaning": "Hard-coded Pinocchio leg order.",
    },
    {
        "name": "mujoco_free_joint_quat_slice",
        "regex": r"q_?mj\s*\[\s*4\s*:\s*7\s*\]|qpos\s*\[\s*4\s*:\s*7\s*\]|data\.qpos\s*\[\s*4\s*:\s*7\s*\]",
        "severity": "high",
        "meaning": "Likely MuJoCo quaternion vector slice qx,qy,qz.",
    },
    {
        "name": "mujoco_free_joint_qw_index",
        "regex": r"q_?mj\s*\[\s*3\s*\]|qpos\s*\[\s*3\s*\]|data\.qpos\s*\[\s*3\s*\]",
        "severity": "high",
        "meaning": "Likely MuJoCo quaternion scalar qw index.",
    },
    {
        "name": "pinocchio_free_flyer_quat_slice",
        "regex": r"q_?pin\s*\[\s*3\s*:\s*6\s*\]",
        "severity": "high",
        "meaning": "Likely Pinocchio quaternion vector slice qx,qy,qz.",
    },
    {
        "name": "pinocchio_free_flyer_qw_index",
        "regex": r"q_?pin\s*\[\s*6\s*\]",
        "severity": "high",
        "meaning": "Likely Pinocchio quaternion scalar qw index.",
    },
    {
        "name": "manual_qpos_actuated_offset",
        "regex": r"\b7\s*\+\s*i\b|\b7\s*\+\s*idx\b|\bqpos_idx\b",
        "severity": "medium",
        "meaning": "Possible manual qpos actuated index offset.",
    },
    {
        "name": "manual_qvel_actuated_offset",
        "regex": r"\b6\s*\+\s*i\b|\b6\s*\+\s*idx\b|\bqvel_idx\b",
        "severity": "medium",
        "meaning": "Possible manual qvel actuated index offset.",
    },
    {
        "name": "manual_tau_reorder",
        "regex": r"tau_?mj|tau_?pin|torque_?mj|torque_?pin|actuator_order|joint_order",
        "severity": "medium",
        "meaning": "Possible manual torque or joint order mapping site.",
    },
    {
        "name": "direct_frame_or_foot_name_contract",
        "regex": r"FR_foot|FL_foot|RR_foot|RL_foot|mj_name2id|getFrameId",
        "severity": "low",
        "meaning": "Possible direct foot name/frame contract use.",
    },
]


def parse_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def load_summary(path: Path):
    metrics = {}
    if not path.exists():
        return metrics

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


def should_scan(path: Path):
    rel = path.relative_to(ROOT).as_posix()

    excluded = {
        "scripts/common/go1_runtime_interface.py",
        "scripts/stage08_runtime_mapping_duplication_audit.py",
    }

    if rel in excluded:
        return False

    if "__pycache__" in rel:
        return False

    if rel.endswith(".py"):
        return True

    return False


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    stage83_metrics = load_summary(STAGE83_SUMMARY)
    stage83_pass = parse_bool(stage83_metrics.get("pass", "False"))

    findings = []

    for path in sorted((ROOT / "scripts").rglob("*.py")):
        if not should_scan(path):
            continue

        rel = path.relative_to(ROOT).as_posix()

        try:
            lines = path.read_text(errors="replace").splitlines()
        except Exception as e:
            findings.append({
                "file": rel,
                "line": "",
                "pattern": "read_error",
                "severity": "high",
                "match": "",
                "meaning": f"Failed to read file: {e}",
            })
            continue

        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            for pat in PATTERNS:
                if re.search(pat["regex"], stripped):
                    findings.append({
                        "file": rel,
                        "line": line_no,
                        "pattern": pat["name"],
                        "severity": pat["severity"],
                        "match": stripped[:240],
                        "meaning": pat["meaning"],
                    })

    high_count = sum(1 for x in findings if x["severity"] == "high")
    medium_count = sum(1 for x in findings if x["severity"] == "medium")
    low_count = sum(1 for x in findings if x["severity"] == "low")
    files_with_findings = len(set(x["file"] for x in findings))

    # Audit pass means: adapter exists, prior A/B regression passed, and audit completed.
    # Findings are not treated as failure; they are the refactor backlog.
    audit_completed = True
    all_pass = ADAPTER_MODULE.exists() and STAGE83_SUMMARY.exists() and stage83_pass and audit_completed

    with AUDIT_LOG.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file", "line", "pattern", "severity", "match", "meaning"],
        )
        writer.writeheader()
        writer.writerows(findings)

    summary_rows = [
        ("stage", "Stage 8.4"),
        ("test_name", "runtime_mapping_duplication_audit"),
        ("adapter_module", str(ADAPTER_MODULE.relative_to(ROOT))),
        ("adapter_module_exists", ADAPTER_MODULE.exists()),
        ("stage83_summary", str(STAGE83_SUMMARY.relative_to(ROOT))),
        ("stage83_pass", stage83_pass),
        ("files_with_findings", files_with_findings),
        ("total_findings", len(findings)),
        ("high_severity_findings", high_count),
        ("medium_severity_findings", medium_count),
        ("low_severity_findings", low_count),
        ("pass", all_pass),
        ("log_csv", str(AUDIT_LOG.relative_to(ROOT))),
        ("summary_csv", str(AUDIT_SUMMARY.relative_to(ROOT))),
    ]

    with AUDIT_SUMMARY.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(summary_rows)

    top_files = {}
    for item in findings:
        top_files[item["file"]] = top_files.get(item["file"], 0) + 1

    top_file_lines = "\n".join(
        f"- `{file}`: {count} findings"
        for file, count in sorted(top_files.items(), key=lambda kv: kv[1], reverse=True)[:20]
    )
    if not top_file_lines:
        top_file_lines = "- No duplicated runtime mapping candidates found."

    DOC_PATH.write_text(f"""# Stage 8.4 Runtime Mapping Duplication Audit

## Target

Scan Python scripts for duplicated MuJoCo/Pinocchio runtime mapping logic before refactoring controller scripts.

## Boundary

This stage is audit-only.

It does not modify controller logic, control gains, gait scheduler, WBC/QP, swing target tracking, or ROS2/C++ code.

## Inputs

- Adapter module: `scripts/common/go1_runtime_interface.py`
- Previous A/B regression: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv`

## Outputs

- Audit log: `results/logs_sample/stage08_runtime_mapping_duplication_audit_log.csv`
- Audit summary: `results/logs_sample/stage08_runtime_mapping_duplication_audit_summary.csv`

## Result

- pass: `{all_pass}`
- stage83_pass: `{stage83_pass}`
- files_with_findings: `{files_with_findings}`
- total_findings: `{len(findings)}`
- high_severity_findings: `{high_count}`
- medium_severity_findings: `{medium_count}`
- low_severity_findings: `{low_count}`

## Files with most findings

{top_file_lines}

## Interpretation

Findings are not failures.

They are candidate locations for Stage 8.5 refactoring into `scripts/common/go1_runtime_interface.py`.

A Stage 8.5 refactor should be done one script at a time and followed by an A/B regression test.
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 8.4 Runtime Mapping Duplication Audit

Stage 8.4 scanned Python scripts for duplicated MuJoCo/Pinocchio runtime mapping logic before refactoring.

- Script: `scripts/stage08_runtime_mapping_duplication_audit.py`
- Log: `results/logs_sample/stage08_runtime_mapping_duplication_audit_log.csv`
- Summary: `results/logs_sample/stage08_runtime_mapping_duplication_audit_summary.csv`
- Docs: `docs/STAGE08_RUNTIME_MAPPING_DUPLICATION_AUDIT.md`
- pass: `{all_pass}`
- stage83_pass: `{stage83_pass}`
- files_with_findings: `{files_with_findings}`
- total_findings: `{len(findings)}`
- high_severity_findings: `{high_count}`
- medium_severity_findings: `{medium_count}`
- low_severity_findings: `{low_count}`

Findings are refactor candidates, not controller failures. Stage 8 remains focused on runtime interface hardening and does not complete pure WBC locomotion, ROS2/C++ migration, EKF, or full MPC.
""".strip()

    old_status = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 8.4 Runtime Mapping Duplication Audit"
    if marker not in old_status:
        status_path.write_text(old_status.rstrip() + "\n\n" + block + "\n")

    print("[Stage 8.4] runtime mapping duplication audit")
    print(f"pass={all_pass}")
    print(f"files_with_findings={files_with_findings}")
    print(f"total_findings={len(findings)}")
    print(f"high_severity_findings={high_count}")
    print(f"medium_severity_findings={medium_count}")
    print(f"low_severity_findings={low_count}")
    print(f"log_csv={AUDIT_LOG.relative_to(ROOT)}")
    print(f"summary_csv={AUDIT_SUMMARY.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed prerequisites:")
        print(f"- adapter_module_exists={ADAPTER_MODULE.exists()}")
        print(f"- stage83_summary_exists={STAGE83_SUMMARY.exists()}")
        print(f"- stage83_pass={stage83_pass}")
        sys.exit(2)


if __name__ == "__main__":
    main()
