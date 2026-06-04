#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime

ROOT = Path.cwd()
SRC = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
OUT_DIR = ROOT / "results/logs_sample"
DOC_DIR = ROOT / "docs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_STAGE1219_HASH = "1970e55723158545b775a707b99f4e5801f80d96f93cf1f3301f5e27aa15d3e6"

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def count_publish_calls(text: str) -> int:
    return len(re.findall(r"(?:->|\.)publish\s*\(", text))

def line_context(lines, center, radius=16):
    lo = max(1, center - radius)
    hi = min(len(lines), center + radius)
    return "\n".join(f"{i:04d}: {lines[i-1]}" for i in range(lo, hi + 1))

def grep_lines(lines, patterns):
    hits = []
    for i, line in enumerate(lines, start=1):
        for name, pat in patterns:
            if re.search(pat, line):
                hits.append({
                    "line": i,
                    "kind": name,
                    "text": line.rstrip(),
                    "context": line_context(lines, i)
                })
    return hits

result = {
    "stage": "12.20B-R1",
    "name": "source_structure_inspection_after_class_detector_failure",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "source": str(SRC),
    "source_exists": SRC.exists(),
    "pass": False,
    "fail_reasons": [],
}

if not SRC.exists():
    result["fail_reasons"].append("missing disabled_controller_node.cpp")
else:
    text = SRC.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    result["source_hash"] = sha256_text(text)
    result["source_hash_matches_stage1219"] = result["source_hash"] == EXPECTED_STAGE1219_HASH
    result["publish_call_count"] = count_publish_calls(text)

    patterns = [
        ("class_or_struct", r"^\s*(class|struct)\s+\w+"),
        ("rclcpp_node", r"rclcpp::Node"),
        ("constructor_hint", r"Node\s*\(|:\s*Node\s*\(|rclcpp::Node\s*\("),
        ("private", r"^\s*private\s*:"),
        ("public", r"^\s*public\s*:"),
        ("publisher_member", r"Publisher<|PublisherBase|publisher_|torque.*publisher|joint_torque_cmd"),
        ("timer", r"create_wall_timer|TimerBase|timer_|cancel\s*\("),
        ("parameter", r"declare_parameter|get_parameter|enable_torque_publisher|confirm_torque_publisher_enable"),
        ("publish_call", r"(?:->|\.)publish\s*\("),
        ("zero_safe", r"zero|safe|bounded|Float64MultiArray"),
    ]

    hits = grep_lines(lines, patterns)
    result["hits"] = hits

    class_related = [h for h in hits if h["kind"] in ("class_or_struct", "rclcpp_node", "constructor_hint", "private", "public")]
    publish_related = [h for h in hits if h["kind"] in ("publisher_member", "publish_call", "zero_safe")]
    timer_param_related = [h for h in hits if h["kind"] in ("timer", "parameter")]

    result["class_related_count"] = len(class_related)
    result["publish_related_count"] = len(publish_related)
    result["timer_param_related_count"] = len(timer_param_related)

    if not result["source_hash_matches_stage1219"]:
        result["fail_reasons"].append("source hash changed from Stage 12.19")
    if result["publish_call_count"] != 1:
        result["fail_reasons"].append("publish_call_count is not 1")

    result["pass"] = (
        result["source_hash_matches_stage1219"]
        and result["publish_call_count"] == 1
        and len(class_related) > 0
        and len(publish_related) > 0
    )

summary_path = OUT_DIR / "stage12_20b_r1_source_structure_inspection_summary.json"
summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md = []
md.append("# Stage 12.20B-R1 Source Structure Inspection\n")
md.append(f"- pass: `{result['pass']}`")
md.append(f"- fail_reasons: `{result['fail_reasons']}`")
md.append(f"- source_hash: `{result.get('source_hash')}`")
md.append(f"- source_hash_matches_stage1219: `{result.get('source_hash_matches_stage1219')}`")
md.append(f"- publish_call_count: `{result.get('publish_call_count')}`")
md.append("\n## Context hits\n")

for h in result.get("hits", []):
    md.append(f"\n### {h['kind']} line {h['line']}\n")
    md.append("```text")
    md.append(h["context"])
    md.append("```")

doc_path = DOC_DIR / "stage12_20b_r1_source_structure_inspection.md"
doc_path.write_text("\n".join(md), encoding="utf-8")

print(json.dumps({
    "stage": result["stage"],
    "pass": result["pass"],
    "summary": str(summary_path),
    "doc": str(doc_path),
    "fail_reasons": result["fail_reasons"],
    "source_hash_matches_stage1219": result.get("source_hash_matches_stage1219"),
    "publish_call_count": result.get("publish_call_count"),
    "class_related_count": result.get("class_related_count"),
    "publish_related_count": result.get("publish_related_count"),
    "timer_param_related_count": result.get("timer_param_related_count"),
}, indent=2, ensure_ascii=False))
