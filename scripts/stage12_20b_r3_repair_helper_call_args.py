#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import re
import shutil
from datetime import datetime

ROOT = Path.cwd()
SRC = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
OUT_DIR = ROOT / "results/logs_sample"
DOC_DIR = ROOT / "docs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_R2_POST_HASH = "0873b101328d54813a0e8b765060abf72207f2ca84f92afe10670a3ae7d3308d"

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def count_publish_calls(text: str) -> int:
    return len(re.findall(r"(?:->|\.)publish\s*\(", text))

def count_zero_arg_helper_calls(text: str) -> int:
    return len(re.findall(
        r"this->publishBoundedZeroSafeTorqueOnceIfAllowed\s*\(\s*\)\s*;",
        text
    ))

def count_repaired_helper_calls(text: str) -> int:
    return len(re.findall(
        r"this->publishBoundedZeroSafeTorqueOnceIfAllowed\s*\(\s*"
        r"enable_torque_publisher\s*,\s*"
        r"confirm_torque_publisher_enable\s*,\s*"
        r"true\s*\)\s*;",
        text
    ))

result = {
    "stage": "12.20B-R3",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "source": str(SRC),
    "pass": False,
    "patch_applied": False,
    "fail_reasons": [],
}

if not SRC.exists():
    result["fail_reasons"].append("missing disabled_controller_node.cpp")
else:
    text = SRC.read_text(encoding="utf-8", errors="replace")
    pre_hash = sha256_text(text)

    result["pre_hash"] = pre_hash
    result["pre_hash_matches_r2_post_hash"] = pre_hash == EXPECTED_R2_POST_HASH
    result["pre_publish_call_count"] = count_publish_calls(text)
    result["pre_zero_arg_helper_call_count"] = count_zero_arg_helper_calls(text)
    result["pre_repaired_helper_call_count"] = count_repaired_helper_calls(text)

    if pre_hash != EXPECTED_R2_POST_HASH:
        result["fail_reasons"].append("source hash does not match Stage 12.20B-R2 post hash")
    if result["pre_publish_call_count"] != 1:
        result["fail_reasons"].append("pre repair publish_call_count is not 1")
    if result["pre_zero_arg_helper_call_count"] != 1:
        result["fail_reasons"].append("expected exactly one zero-arg helper call to repair")

    required_markers = [
        "enable_continuous_torque_streaming",
        "confirm_continuous_torque_streaming",
        "continuous_torque_streaming_max_ticks",
        "continuous_torque_streaming_max_duration_sec",
        "four_flag_gate",
        "continuous_torque_streaming_timer_",
        "std::chrono::milliseconds(100)",
    ]
    missing_markers = [m for m in required_markers if m not in text]
    result["missing_required_markers"] = missing_markers
    if missing_markers:
        result["fail_reasons"].append("missing Stage 12.20 continuous streaming markers")

    if not result["fail_reasons"]:
        backup = SRC.with_suffix(".cpp.stage1220b_r2_pre_r3.bak")
        shutil.copy2(SRC, backup)

        patched = re.sub(
            r"this->publishBoundedZeroSafeTorqueOnceIfAllowed\s*\(\s*\)\s*;",
            "this->publishBoundedZeroSafeTorqueOnceIfAllowed("
            "enable_torque_publisher, "
            "confirm_torque_publisher_enable, "
            "true);",
            text,
            count=1,
        )

        result["backup"] = str(backup)
        result["post_hash"] = sha256_text(patched)
        result["post_publish_call_count"] = count_publish_calls(patched)
        result["post_zero_arg_helper_call_count"] = count_zero_arg_helper_calls(patched)
        result["post_repaired_helper_call_count"] = count_repaired_helper_calls(patched)

        result["post_has_continuous_params"] = all(s in patched for s in [
            "enable_continuous_torque_streaming",
            "confirm_continuous_torque_streaming",
            "continuous_torque_streaming_max_ticks",
            "continuous_torque_streaming_max_duration_sec",
        ])
        result["post_has_four_flag_gate"] = "four_flag_gate" in patched
        result["post_has_continuous_timer"] = "continuous_torque_streaming_timer_" in patched
        result["post_rate_limited_to_10hz"] = "std::chrono::milliseconds(100)" in patched
        result["post_calls_existing_publish_helper_with_args"] = result["post_repaired_helper_call_count"] >= 1

        static_ok = all([
            result["post_publish_call_count"] == 1,
            result["post_zero_arg_helper_call_count"] == 0,
            result["post_repaired_helper_call_count"] >= 1,
            result["post_has_continuous_params"],
            result["post_has_four_flag_gate"],
            result["post_has_continuous_timer"],
            result["post_rate_limited_to_10hz"],
        ])

        if static_ok:
            SRC.write_text(patched, encoding="utf-8")
            result["patch_applied"] = True
            result["pass"] = True
        else:
            result["fail_reasons"].append("post repair static checks failed; source not written")

summary_path = OUT_DIR / "stage12_20b_r3_repair_summary.json"
summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

doc = [
    "# Stage 12.20B-R3 Build Repair Summary",
    "",
    f"- pass: `{result['pass']}`",
    f"- patch_applied: `{result['patch_applied']}`",
    f"- fail_reasons: `{result['fail_reasons']}`",
    f"- pre_hash: `{result.get('pre_hash')}`",
    f"- pre_hash_matches_r2_post_hash: `{result.get('pre_hash_matches_r2_post_hash')}`",
    f"- post_hash: `{result.get('post_hash')}`",
    f"- pre_publish_call_count: `{result.get('pre_publish_call_count')}`",
    f"- post_publish_call_count: `{result.get('post_publish_call_count')}`",
    f"- pre_zero_arg_helper_call_count: `{result.get('pre_zero_arg_helper_call_count')}`",
    f"- post_zero_arg_helper_call_count: `{result.get('post_zero_arg_helper_call_count')}`",
    f"- post_repaired_helper_call_count: `{result.get('post_repaired_helper_call_count')}`",
    f"- post_has_continuous_params: `{result.get('post_has_continuous_params')}`",
    f"- post_has_four_flag_gate: `{result.get('post_has_four_flag_gate')}`",
    f"- post_has_continuous_timer: `{result.get('post_has_continuous_timer')}`",
    f"- post_rate_limited_to_10hz: `{result.get('post_rate_limited_to_10hz')}`",
    "",
    "Repair: replace zero-argument helper invocation with guarded helper invocation using existing torque publisher flags and a true dry-run publish allowance inside the already-checked four-flag gate.",
    "",
    "Safety boundary: bounded zero/safe dry-run only; no hardware deployment; no control-law change.",
]
doc_path = DOC_DIR / "stage12_20b_r3_repair_summary.md"
doc_path.write_text("\n".join(doc), encoding="utf-8")

print(json.dumps({
    "stage": result["stage"],
    "pass": result["pass"],
    "patch_applied": result["patch_applied"],
    "summary": str(summary_path),
    "doc": str(doc_path),
    "fail_reasons": result["fail_reasons"],
    "pre_hash_matches_r2_post_hash": result.get("pre_hash_matches_r2_post_hash"),
    "post_publish_call_count": result.get("post_publish_call_count"),
    "post_zero_arg_helper_call_count": result.get("post_zero_arg_helper_call_count"),
    "post_repaired_helper_call_count": result.get("post_repaired_helper_call_count"),
    "post_has_four_flag_gate": result.get("post_has_four_flag_gate"),
    "post_has_continuous_timer": result.get("post_has_continuous_timer"),
    "post_rate_limited_to_10hz": result.get("post_rate_limited_to_10hz"),
}, indent=2, ensure_ascii=False))
