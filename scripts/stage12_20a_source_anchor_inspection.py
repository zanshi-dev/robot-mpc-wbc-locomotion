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

def find_lines(text: str, patterns):
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines, start=1):
        for p in patterns:
            if re.search(p, line):
                hits.append({
                    "line": i,
                    "pattern": p,
                    "text": line.rstrip()
                })
    return hits

def context(lines, center, radius=12):
    lo = max(1, center - radius)
    hi = min(len(lines), center + radius)
    return "\n".join(f"{i:04d}: {lines[i-1]}" for i in range(lo, hi + 1))

result = {
    "stage": "12.20A",
    "name": "source_anchor_inspection_before_bounded_continuous_streaming_patch",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "source": str(SRC),
    "source_exists": SRC.exists(),
    "pass": False,
    "fail_reasons": [],
    "anchors": {},
    "contexts": {},
}

if not SRC.exists():
    result["fail_reasons"].append("missing disabled_controller_node.cpp")
else:
    text = SRC.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    h = sha256_text(text)
    result["source_hash"] = h
    result["source_hash_matches_stage1219"] = (h == EXPECTED_STAGE1219_HASH)

    publish_hits = find_lines(text, [
        r"\.publish\s*\(",
        r"->publish\s*\(",
    ])

    timer_hits = find_lines(text, [
        r"create_wall_timer",
        r"timer_",
        r"one_shot",
        r"cancel\s*\(",
    ])

    param_hits = find_lines(text, [
        r"declare_parameter",
        r"get_parameter",
        r"enable_torque_publisher",
        r"confirm_torque_publisher_enable",
    ])

    helper_hits = find_lines(text, [
        r"zero",
        r"safe",
        r"Float64MultiArray",
        r"joint_torque_cmd",
        r"bounded",
        r"publish",
    ])

    continuous_hits = find_lines(text, [
        r"continuous",
        r"streaming",
        r"enable_continuous_torque_streaming",
        r"confirm_continuous_torque_streaming",
        r"continuous_torque_streaming_timer",
        r"Stage 12\.20",
        r"Stage12\.20",
    ])

    result["publish_call_count"] = len(publish_hits)
    result["anchors"]["publish_hits"] = publish_hits
    result["anchors"]["timer_hits"] = timer_hits
    result["anchors"]["param_hits"] = param_hits
    result["anchors"]["helper_hits"] = helper_hits
    result["anchors"]["continuous_hits"] = continuous_hits

    for group_name, hits in result["anchors"].items():
        result["contexts"][group_name] = []
        for hit in hits[:8]:
            result["contexts"][group_name].append({
                "center_line": hit["line"],
                "context": context(lines, hit["line"], radius=10)
            })

    result["has_existing_continuous_streaming_markers"] = len(continuous_hits) > 0
    result["source_has_exactly_one_publish_call"] = len(publish_hits) == 1
    result["source_has_no_continuous_streaming_markers"] = len(continuous_hits) == 0

    required = [
        result["source_hash_matches_stage1219"],
        result["source_has_exactly_one_publish_call"],
        result["source_has_no_continuous_streaming_markers"],
    ]

    if not result["source_hash_matches_stage1219"]:
        result["fail_reasons"].append("source hash does not match Stage 12.19 frozen hash")
    if not result["source_has_exactly_one_publish_call"]:
        result["fail_reasons"].append("publish call count is not exactly 1")
    if not result["source_has_no_continuous_streaming_markers"]:
        result["fail_reasons"].append("source already contains continuous streaming markers")

    result["pass"] = all(required)

summary_path = OUT_DIR / "stage12_20a_source_anchor_inspection_summary.json"
summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md = []
md.append("# Stage 12.20A Source Anchor Inspection\n")
md.append(f"- source: `{result['source']}`")
md.append(f"- pass: `{result['pass']}`")
md.append(f"- fail_reasons: `{result['fail_reasons']}`")
if result.get("source_hash"):
    md.append(f"- source_hash: `{result['source_hash']}`")
    md.append(f"- source_hash_matches_stage1219: `{result['source_hash_matches_stage1219']}`")
md.append(f"- publish_call_count: `{result.get('publish_call_count')}`")
md.append(f"- source_has_no_continuous_streaming_markers: `{result.get('source_has_no_continuous_streaming_markers')}`")
md.append("\n## Key contexts\n")
for group_name, contexts in result.get("contexts", {}).items():
    md.append(f"\n### {group_name}\n")
    for item in contexts[:4]:
        md.append(f"\ncenter_line={item['center_line']}\n")
        md.append("```text")
        md.append(item["context"])
        md.append("```")
doc_path = DOC_DIR / "stage12_20a_source_anchor_inspection.md"
doc_path.write_text("\n".join(md), encoding="utf-8")

print(json.dumps({
    "stage": result["stage"],
    "pass": result["pass"],
    "summary": str(summary_path),
    "doc": str(doc_path),
    "fail_reasons": result["fail_reasons"],
    "publish_call_count": result.get("publish_call_count"),
    "source_hash_matches_stage1219": result.get("source_hash_matches_stage1219"),
    "source_has_no_continuous_streaming_markers": result.get("source_has_no_continuous_streaming_markers"),
}, indent=2, ensure_ascii=False))
