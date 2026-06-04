#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

SUMMARY = OUT / "stage12_21_r2c_capture_failure_inspection_summary.json"
DOC = DOCS / "stage12_21_r2c_capture_failure_inspection.md"

FILES = {
    "r2b_summary": OUT / "stage12_21_r2b_robust_subscriber_warmup_rerun_summary.json",
    "capture_script": ROOT / "scripts/stage12_21_r2b_capture.py",
    "main_script": ROOT / "scripts/stage12_21_r2b_robust_subscriber_warmup_rerun.py",
    "capture_log": OUT / "stage12_21_r2b_capture.log",
    "after_stop_capture_log": OUT / "stage12_21_r2b_after_stop_capture.log",
    "capture_json": OUT / "stage12_21_r2b_capture.json",
    "after_stop_capture_json": OUT / "stage12_21_r2b_after_stop_capture.json",
    "param_set_log": OUT / "stage12_21_r2b_param_set.log",
    "param_final_log": OUT / "stage12_21_r2b_param_final.log",
    "node_log": OUT / "stage12_21_r2b_node.log",
}

def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def sha(path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

r2b = read_json(FILES["r2b_summary"]) or {}
capture_log_text = read(FILES["capture_log"])
after_log_text = read(FILES["after_stop_capture_log"])
capture_script_text = read(FILES["capture_script"])
main_script_text = read(FILES["main_script"])

diagnosis = []

if not FILES["capture_script"].exists():
    diagnosis.append("capture helper script missing")
if FILES["capture_script"].exists() and "import rclpy" not in capture_script_text:
    diagnosis.append("capture helper does not contain rclpy import")
if "can't open file" in capture_log_text or "No such file or directory" in capture_log_text:
    diagnosis.append("capture helper path/file not found at runtime")
if "ModuleNotFoundError" in capture_log_text:
    diagnosis.append("capture helper failed due to missing Python module")
if "Traceback" in capture_log_text:
    diagnosis.append("capture helper raised Python exception")
if r2b.get("capture_returncode") == 2 and not FILES["capture_json"].exists():
    diagnosis.append("capture process exited before writing capture_json")
if not capture_log_text.strip():
    diagnosis.append("capture_log empty; subprocess likely failed before Python emitted diagnostics or log handle was not flushed")

param_set_text = read(FILES["param_set_log"])
param_final_text = read(FILES["param_final_log"])

result = {
    "stage": "12.21-R2C",
    "name": "capture_helper_failure_inspection",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": True,
    "inspection_only": True,
    "source_changed": False,
    "r2b_pass": r2b.get("pass"),
    "r2b_fail_reasons": r2b.get("fail_reasons"),
    "capture_returncode": r2b.get("capture_returncode"),
    "after_stop_capture_returncode": r2b.get("after_stop_capture_returncode"),
    "files": {
        k: {
            "path": str(v),
            "exists": v.exists(),
            "size": v.stat().st_size if v.exists() else None,
            "sha256": sha(v),
        }
        for k, v in FILES.items()
    },
    "capture_log_excerpt": capture_log_text[-4000:],
    "after_stop_capture_log_excerpt": after_log_text[-4000:],
    "diagnosis": diagnosis,
    "param_set_ok_from_r2b": r2b.get("param_set_ok"),
    "final_flags_false_from_r2b": r2b.get("final_flags_false"),
    "recommended_next_stage": "Stage 12.21-R2D repair capture launch path / helper execution, then rerun subscriber-warmup regression; no source change",
    "safety": {
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "hardware_deployment_completed": False,
        "control_law_changed": False,
    },
}

SUMMARY.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 12.21-R2C Capture Helper Failure Inspection",
    "",
    f"- pass: `{result['pass']}`",
    f"- inspection_only: `{result['inspection_only']}`",
    f"- source_changed: `{result['source_changed']}`",
    f"- r2b_pass: `{result['r2b_pass']}`",
    f"- r2b_fail_reasons: `{result['r2b_fail_reasons']}`",
    f"- capture_returncode: `{result['capture_returncode']}`",
    f"- after_stop_capture_returncode: `{result['after_stop_capture_returncode']}`",
    f"- param_set_ok_from_r2b: `{result['param_set_ok_from_r2b']}`",
    f"- final_flags_false_from_r2b: `{result['final_flags_false_from_r2b']}`",
    f"- diagnosis: `{result['diagnosis']}`",
    "",
    "## Capture log excerpt",
    "",
    "```text",
    result["capture_log_excerpt"],
    "```",
    "",
    "## After-stop capture log excerpt",
    "",
    "```text",
    result["after_stop_capture_log_excerpt"],
    "```",
    "",
    f"Recommended next stage: `{result['recommended_next_stage']}`",
    "",
    "Safety boundary: inspection only; no source change; no hardware deployment.",
]
DOC.write_text("\n".join(md), encoding="utf-8")

print(json.dumps(result, indent=2, ensure_ascii=False))
