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

EXPECTED_STAGE1219_HASH = "1970e55723158545b775a707b99f4e5801f80d96f93cf1f3301f5e27aa15d3e6"

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def count_publish_calls(text: str) -> int:
    return len(re.findall(r"(?:->|\.)publish\s*\(", text))

def find_matching_brace(text: str, open_pos: int) -> int:
    depth = 0
    in_str = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    esc = False
    for i in range(open_pos, len(text)):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if c == "\n":
                in_line_comment = False
            continue
        if in_block_comment:
            if c == "*" and n == "/":
                in_block_comment = False
                continue
            continue
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if in_char:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == "'":
                in_char = False
            continue

        if c == "/" and n == "/":
            in_line_comment = True
            continue
        if c == "/" and n == "*":
            in_block_comment = True
            continue
        if c == '"':
            in_str = True
            continue
        if c == "'":
            in_char = True
            continue

        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1

def previous_header(text: str, brace_pos: int) -> str:
    j = brace_pos - 1
    while j >= 0 and text[j].isspace():
        j -= 1
    k = j
    while k >= 0 and text[k] not in "{};":
        k -= 1
    return text[k + 1:j + 1].strip()

def extract_method_name_from_header(header: str):
    compact = " ".join(header.split())
    if any(x in compact for x in [" if ", " for ", " while ", " switch ", " catch ", "[]", "create_wall_timer"]):
        return None
    m = re.search(r"(?:\w+::)?(\w+)\s*\(([^()]*)\)\s*(?:const)?\s*$", compact)
    if not m:
        return None
    name = m.group(1)
    args = m.group(2).strip()
    if args not in ("", "void"):
        return None
    return name

def detect_class_name(text: str):
    m = re.search(r"class\s+(\w+)\s*:\s*public\s+rclcpp::Node", text)
    return m.group(1) if m else None

def detect_publish_helper(text: str, class_name: str):
    pub_match = re.search(r"(?:->|\.)publish\s*\(", text)
    if not pub_match:
        return None, "no publish call found"
    pub_pos = pub_match.start()

    candidates = []
    for m in re.finditer(r"\{", text):
        open_pos = m.start()
        if open_pos > pub_pos:
            break
        close_pos = find_matching_brace(text, open_pos)
        if close_pos < pub_pos:
            continue
        header = previous_header(text, open_pos)
        name = extract_method_name_from_header(header)
        if not name:
            continue
        if name == class_name:
            continue
        candidates.append((close_pos - open_pos, name, header))

    if not candidates:
        return None, "could not identify zero/safe publish helper enclosing the only publish call"

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1], None

def find_constructor_block(text: str, class_name: str):
    pat = re.compile(r"(?:explicit\s+)?" + re.escape(class_name) + r"\s*\(")
    m = pat.search(text)
    if not m:
        return None, None, "constructor not found"
    brace = text.find("{", m.end())
    if brace < 0:
        return None, None, "constructor opening brace not found"
    close = find_matching_brace(text, brace)
    if close < 0:
        return None, None, "constructor closing brace not found"
    return brace, close, None

result = {
    "stage": "12.20B",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "source": str(SRC),
    "pass": False,
    "fail_reasons": [],
    "patch_applied": False,
}

if not SRC.exists():
    result["fail_reasons"].append("missing source file")
else:
    text = SRC.read_text(encoding="utf-8", errors="replace")
    pre_hash = sha256_text(text)
    result["pre_hash"] = pre_hash
    result["pre_publish_call_count"] = count_publish_calls(text)

    if pre_hash != EXPECTED_STAGE1219_HASH:
        result["fail_reasons"].append("source hash does not match Stage 12.19 frozen hash")
    if count_publish_calls(text) != 1:
        result["fail_reasons"].append("pre patch publish_call_count is not 1")
    if re.search(r"continuous_torque_streaming|enable_continuous_torque_streaming|Stage 12\.20", text):
        result["fail_reasons"].append("source already contains continuous streaming markers")

    class_name = detect_class_name(text)
    result["class_name"] = class_name
    if not class_name:
        result["fail_reasons"].append("could not detect rclcpp::Node class name")

    helper_name = None
    if class_name:
        helper_name, err = detect_publish_helper(text, class_name)
        result["detected_publish_helper"] = helper_name
        if err:
            result["fail_reasons"].append(err)

    ctor_open = ctor_close = None
    if class_name:
        ctor_open, ctor_close, err = find_constructor_block(text, class_name)
        if err:
            result["fail_reasons"].append(err)

    private_match = re.search(r"\n\s*private\s*:\s*\n", text)
    if not private_match:
        result["fail_reasons"].append("private section not found")

    if not result["fail_reasons"]:
        backup = SRC.with_suffix(".cpp.stage1219_pre_stage1220b.bak")
        shutil.copy2(SRC, backup)
        result["backup"] = str(backup)

        include_insert = ""
        if "#include <chrono>" not in text:
            include_insert += "#include <chrono>\n"
        if "#include <memory>" not in text:
            include_insert += "#include <memory>\n"

        include_pos = 0
        includes = list(re.finditer(r"^#include\s+[<\"].*[>\"]\s*$", text, re.MULTILINE))
        if include_insert and includes:
            include_pos = includes[-1].end() + 1

        member_code = (
            "  // Stage 12.20: bounded continuous zero/safe streaming dry-run timer.\n"
            "  rclcpp::TimerBase::SharedPtr continuous_torque_streaming_timer_;\n\n"
        )

        ctor_code = f"""

    // Stage 12.20: bounded continuous zero/safe streaming dry-run parameters.
    this->declare_parameter<bool>("enable_continuous_torque_streaming", false);
    this->declare_parameter<bool>("confirm_continuous_torque_streaming", false);
    this->declare_parameter<int>("continuous_torque_streaming_max_ticks", 30);
    this->declare_parameter<double>("continuous_torque_streaming_max_duration_sec", 3.0);

    auto stage1220_continuous_tick_count = std::make_shared<int>(0);
    auto stage1220_continuous_started = std::make_shared<bool>(false);
    auto stage1220_continuous_start_time = std::make_shared<rclcpp::Time>(this->now());

    continuous_torque_streaming_timer_ = this->create_wall_timer(
      std::chrono::milliseconds(100),
      [this,
       stage1220_continuous_tick_count,
       stage1220_continuous_started,
       stage1220_continuous_start_time]() {{
        const bool enable_torque_publisher =
          this->get_parameter("enable_torque_publisher").as_bool();
        const bool confirm_torque_publisher_enable =
          this->get_parameter("confirm_torque_publisher_enable").as_bool();
        const bool enable_continuous_torque_streaming =
          this->get_parameter("enable_continuous_torque_streaming").as_bool();
        const bool confirm_continuous_torque_streaming =
          this->get_parameter("confirm_continuous_torque_streaming").as_bool();

        const bool four_flag_gate =
          enable_torque_publisher &&
          confirm_torque_publisher_enable &&
          enable_continuous_torque_streaming &&
          confirm_continuous_torque_streaming;

        if (!four_flag_gate) {{
          *stage1220_continuous_tick_count = 0;
          *stage1220_continuous_started = false;
          return;
        }}

        if (!*stage1220_continuous_started) {{
          *stage1220_continuous_started = true;
          *stage1220_continuous_tick_count = 0;
          *stage1220_continuous_start_time = this->now();
        }}

        int max_ticks =
          static_cast<int>(this->get_parameter("continuous_torque_streaming_max_ticks").as_int());
        if (max_ticks < 1) {{
          max_ticks = 1;
        }}
        if (max_ticks > 30) {{
          max_ticks = 30;
        }}

        double max_duration_sec =
          this->get_parameter("continuous_torque_streaming_max_duration_sec").as_double();
        if (max_duration_sec < 0.1) {{
          max_duration_sec = 0.1;
        }}
        if (max_duration_sec > 3.0) {{
          max_duration_sec = 3.0;
        }}

        if (*stage1220_continuous_tick_count >= max_ticks) {{
          continuous_torque_streaming_timer_->cancel();
          return;
        }}

        const double elapsed_sec = (this->now() - *stage1220_continuous_start_time).seconds();
        if (elapsed_sec > max_duration_sec) {{
          continuous_torque_streaming_timer_->cancel();
          return;
        }}

        this->{helper_name}();
        ++(*stage1220_continuous_tick_count);

        if (*stage1220_continuous_tick_count >= max_ticks) {{
          continuous_torque_streaming_timer_->cancel();
          return;
        }}
      }});
"""

        inserts = []
        if include_insert:
            inserts.append((include_pos, include_insert))
        inserts.append((private_match.end(), member_code))
        inserts.append((ctor_close, ctor_code))

        patched = text
        for pos, code in sorted(inserts, key=lambda x: x[0], reverse=True):
            patched = patched[:pos] + code + patched[pos:]

        SRC.write_text(patched, encoding="utf-8")

        post_hash = sha256_text(patched)
        result["post_hash"] = post_hash
        result["post_publish_call_count"] = count_publish_calls(patched)
        result["post_has_continuous_params"] = all(s in patched for s in [
            "enable_continuous_torque_streaming",
            "confirm_continuous_torque_streaming",
            "continuous_torque_streaming_max_ticks",
            "continuous_torque_streaming_max_duration_sec",
        ])
        result["post_has_four_flag_gate"] = "four_flag_gate" in patched
        result["post_has_continuous_timer"] = "continuous_torque_streaming_timer_" in patched
        result["post_calls_existing_publish_helper"] = f"this->{helper_name}();" in patched
        result["patch_applied"] = True

        required = [
            result["post_publish_call_count"] == 1,
            result["post_has_continuous_params"],
            result["post_has_four_flag_gate"],
            result["post_has_continuous_timer"],
            result["post_calls_existing_publish_helper"],
        ]
        if not all(required):
            result["fail_reasons"].append("post patch static checks failed")

        result["pass"] = len(result["fail_reasons"]) == 0

summary_path = OUT_DIR / "stage12_20b_source_patch_summary.json"
summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

doc = [
    "# Stage 12.20B Source Patch Summary",
    "",
    f"- pass: `{result['pass']}`",
    f"- patch_applied: `{result['patch_applied']}`",
    f"- fail_reasons: `{result['fail_reasons']}`",
    f"- source: `{result['source']}`",
    f"- pre_hash: `{result.get('pre_hash')}`",
    f"- post_hash: `{result.get('post_hash')}`",
    f"- pre_publish_call_count: `{result.get('pre_publish_call_count')}`",
    f"- post_publish_call_count: `{result.get('post_publish_call_count')}`",
    f"- detected_publish_helper: `{result.get('detected_publish_helper')}`",
    f"- post_has_continuous_params: `{result.get('post_has_continuous_params')}`",
    f"- post_has_four_flag_gate: `{result.get('post_has_four_flag_gate')}`",
    f"- post_has_continuous_timer: `{result.get('post_has_continuous_timer')}`",
    "",
    "Safety boundary: bounded zero/safe dry-run only; no hardware deployment; no control-law change.",
]
doc_path = DOC_DIR / "stage12_20b_source_patch_summary.md"
doc_path.write_text("\n".join(doc), encoding="utf-8")

print(json.dumps({
    "stage": result["stage"],
    "pass": result["pass"],
    "patch_applied": result["patch_applied"],
    "summary": str(summary_path),
    "doc": str(doc_path),
    "fail_reasons": result["fail_reasons"],
    "detected_publish_helper": result.get("detected_publish_helper"),
    "post_publish_call_count": result.get("post_publish_call_count"),
    "post_has_continuous_params": result.get("post_has_continuous_params"),
    "post_has_four_flag_gate": result.get("post_has_four_flag_gate"),
    "post_has_continuous_timer": result.get("post_has_continuous_timer"),
}, indent=2, ensure_ascii=False))
