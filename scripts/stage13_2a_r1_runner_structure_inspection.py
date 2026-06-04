#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import json
import re
import hashlib
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

SUMMARY = OUT / "stage13_2a_r1_runner_structure_inspection_summary.json"
DOC = DOCS / "stage13_2a_r1_runner_structure_inspection.md"

FILES = {
    "stage13_2a_summary": OUT / "stage13_2a_2400step_preflight_and_derived_runner_summary.json",
    "stage13_1b_summary": OUT / "stage13_1b_rerun_1200step_simulation_only_mixed_baseline_summary.json",
    "recommended_runner": ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py",
    "wbc_runner": ROOT / "scripts/stage07_online_full_wbc_scheduler_recommended_run.py",
    "swing_target_csv": OUT / "stage07_online_swing_trajectory_tracking_check.csv",
}

def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def read_json(path):
    if not path.exists():
        return None
    return json.loads(read(path))

def sha(path):
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect_script(path):
    text = read(path)
    lines = text.splitlines()
    step_related = []
    numeric_1200_lines = []
    numeric_2400_lines = []
    csv_related = []
    subprocess_related = []
    import_related = []
    output_related = []

    for i, line in enumerate(lines, start=1):
        low = line.lower()
        item = {"line": i, "text": line.rstrip()}

        if re.search(r"\b(step|steps|total_steps|num_steps|n_steps|horizon|rollout|range|len)\b", low):
            step_related.append(item)
        if re.search(r"\b1200\b", line):
            numeric_1200_lines.append(item)
        if re.search(r"\b2400\b", line):
            numeric_2400_lines.append(item)
        if ".csv" in low or "read_csv" in low or "csv." in low or "savetxt" in low or "writer" in low:
            csv_related.append(item)
        if "subprocess" in low or "run(" in low or "popen" in low or "system(" in low:
            subprocess_related.append(item)
        if re.search(r"^\s*(import|from)\s+", line):
            import_related.append(item)
        if "saved_" in low or "summary" in low or "log" in low or "results/logs_sample" in low:
            output_related.append(item)

    return {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha(path),
        "line_count": len(lines),
        "literal_1200_count": len(numeric_1200_lines),
        "literal_2400_count": len(numeric_2400_lines),
        "step_related_count": len(step_related),
        "csv_related_count": len(csv_related),
        "subprocess_related_count": len(subprocess_related),
        "step_related_lines": step_related[:120],
        "literal_1200_lines": numeric_1200_lines[:80],
        "literal_2400_lines": numeric_2400_lines[:80],
        "csv_related_lines": csv_related[:80],
        "subprocess_related_lines": subprocess_related[:80],
        "output_related_lines": output_related[:80],
        "import_related_lines": import_related[:40],
    }

def inspect_csv(path):
    if not path.exists():
        return {"exists": False}
    text = read(path)
    lines = text.splitlines()
    header = lines[0] if lines else ""
    return {
        "exists": True,
        "path": str(path),
        "sha256": sha(path),
        "line_count": len(lines),
        "header": header,
        "first_data_line": lines[1] if len(lines) > 1 else "",
        "last_data_line": lines[-1] if lines else "",
    }

stage13_2a = read_json(FILES["stage13_2a_summary"])
stage13_1b = read_json(FILES["stage13_1b_summary"])

recommended = inspect_script(FILES["recommended_runner"])
wbc = inspect_script(FILES["wbc_runner"])
swing_csv = inspect_csv(FILES["swing_target_csv"])

diagnosis = []

if recommended["literal_1200_count"] == 0 and wbc["literal_1200_count"] > 0:
    diagnosis.append("1200-step horizon likely lives in WBC runner, not recommended wrapper")
elif recommended["literal_1200_count"] == 0 and wbc["literal_1200_count"] == 0:
    diagnosis.append("1200-step horizon likely derived indirectly from CSV length, loop range variable, or generated trajectory length")
else:
    diagnosis.append("recommended wrapper contains literal 1200 and can likely be patched directly")

if swing_csv.get("line_count", 0) >= 1200:
    diagnosis.append("swing target CSV is available and may control or verify rollout length")

fail_reasons = []
if stage13_1b is None or stage13_1b.get("pass") is not True:
    fail_reasons.append("Stage 13.1B prerequisite missing or failed")
if not FILES["recommended_runner"].exists():
    fail_reasons.append("recommended runner missing")
if not FILES["wbc_runner"].exists():
    fail_reasons.append("WBC runner missing")

summary = {
    "stage": "13.2A-R1",
    "name": "runner_structure_inspection_for_2400step_derivation",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "inspection_only": True,
    "source_changed": False,
    "simulation_only_project": True,
    "hardware_deployment_completed": False,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "control_law_changed": False,
    "stage13_2a_pass": None if stage13_2a is None else stage13_2a.get("pass"),
    "stage13_2a_fail_reasons": None if stage13_2a is None else stage13_2a.get("fail_reasons"),
    "stage13_1b_pass": None if stage13_1b is None else stage13_1b.get("pass"),
    "recommended_runner": recommended,
    "wbc_runner": wbc,
    "swing_target_csv": swing_csv,
    "diagnosis": diagnosis,
    "recommended_next_stage": "Stage 13.2A-R2 create 2400-step runner using inspected horizon source; no original runner modification",
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 13.2A-R1 Runner Structure Inspection",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- inspection_only: `{summary['inspection_only']}`",
    f"- source_changed: `{summary['source_changed']}`",
    f"- simulation_only_project: `{summary['simulation_only_project']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    "",
    "## Diagnosis",
]
md += [f"- {x}" for x in diagnosis]

md += [
    "",
    "## Recommended runner",
    f"- literal_1200_count: `{recommended['literal_1200_count']}`",
    f"- step_related_count: `{recommended['step_related_count']}`",
    f"- subprocess_related_count: `{recommended['subprocess_related_count']}`",
    "",
    "## WBC runner",
    f"- literal_1200_count: `{wbc['literal_1200_count']}`",
    f"- step_related_count: `{wbc['step_related_count']}`",
    f"- csv_related_count: `{wbc['csv_related_count']}`",
    "",
    "## Swing target CSV",
    f"- exists: `{swing_csv.get('exists')}`",
    f"- line_count: `{swing_csv.get('line_count')}`",
    "",
    f"Recommended next stage: `{summary['recommended_next_stage']}`",
]
DOC.write_text("\n".join(md), encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
