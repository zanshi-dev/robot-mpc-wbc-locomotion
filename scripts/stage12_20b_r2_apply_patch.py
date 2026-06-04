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

    i = open_pos
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if c == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if c == "*" and n == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue

        if in_char:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == "'":
                in_char = False
            i += 1
            continue

        if c == "/" and n == "/":
            in_line_comment = True
            i += 2
            continue
        if c == "/" and n == "*":
            in_block_comment = True
            i += 2
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "'":
            in_char = True
            i += 1
            continue

        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i

        i += 1

    return -1

def previous_header(text: str, brace_pos: int) -> str:
    j = brace_pos - 1
    while j >= 0 and text[j].isspace():
        j -= 1

    k = j
    while k >= 0 and text[k] not in "{};":
        k -= 1

    return text[k + 1:j + 1].strip()

def normalize_header(header: str) -> str:
    return " ".join(header.split())

def method_name_from_header(header: str):
    compact = normalize_header(header)
    if not compact:
        return None

    reject_tokens = [
        " if ", " for ", " while ", " switch ", " catch ",
        "[]", "[this", "[&", "[="
    ]
    padded = f" {compact} "
    if any(tok in padded for tok in reject_tokens):
        return None

    m = re.search(r"(?:[\w:<>~]+\s+)*(\w+)\s*\(([^()]*)\)\s*(?:const)?\s*$", compact)
    if not m:
        return None

    return m.group(1)

def detect_class_spans(text: str):
    spans = []
    for m in re.finditer(r"\b(class|struct)\s+(\w+)", text):
        name = m.group(2)
        brace = text.find("{", m.end())
        if brace < 0:
            continue

        semicolon = text.find(";", m.end())
        if semicolon >= 0 and semicolon < brace:
            continue

        close = find_matching_brace(text, brace)
        if close < 0:
            continue

        header = text[m.start():brace]
        body = text[brace + 1:close]
        score = 0
        if "rclcpp::Node" in header:
            score += 100
        if re.search(rf"\b{name}\s*\(", body):
            score += 40
        if "declare_parameter" in body:
            score += 20
        if "create_wall_timer" in body:
            score += 20
        if re.search(r"(?:->|\.)publish\s*\(", body):
            score += 20
        if "joint_torque_cmd" in body:
            score += 10

        spans.append({
            "name": name,
            "start": m.start(),
            "brace": brace,
            "close": close,
            "header": header,
            "score": score,
        })

    spans.sort(key=lambda x: (-x["score"], x["start"]))
    return spans

def detect_publish_helper(text: str, class_span):
    pub_match = re.search(r"(?:->|\.)publish\s*\(", text)
    if not pub_match:
        return None, "no publish call found"

    pub_pos = pub_match.start()
    if not (class_span["brace"] < pub_pos < class_span["close"]):
        return None, "publish call is not inside detected class"

    candidates = []
    for m in re.finditer(r"\{", text[class_span["brace"]:class_span["close"]]):
        open_pos = class_span["brace"] + m.start()
        if open_pos > pub_pos:
            break

        close_pos = find_matching_brace(text, open_pos)
        if close_pos < pub_pos:
            continue

        header = previous_header(text, open_pos)
        name = method_name_from_header(header)
        if not name:
            continue
        if name == class_span["name"]:
            continue

        candidates.append({
            "name": name,
            "header": normalize_header(header),
            "open": open_pos,
            "close": close_pos,
            "size": close_pos - open_pos,
        })

    candidates.sort(key=lambda x: x["size"])
    if not candidates:
        return None, "could not detect callable helper enclosing publish call"

    return candidates[0]["name"], None

def detect_constructor(text: str, class_span):
    name = class_span["name"]
    candidates = []

    for m in re.finditer(r"\{", text[class_span["brace"]:class_span["close"]]):
        open_pos = class_span["brace"] + m.start()
        close_pos = find_matching_brace(text, open_pos)
        if close_pos < 0 or close_pos > class_span["close"]:
            continue

        header = previous_header(text, open_pos)
        compact = normalize_header(header)

        if re.search(rf"(?:explicit\s+)?{re.escape(name)}\s*\([^)]*\)\s*(?::.*)?$", compact):
            candidates.append({
                "open": open_pos,
                "close": close_pos,
                "header": compact,
                "size": close_pos - open_pos,
            })

    candidates.sort(key=lambda x: x["size"])
    if not candidates:
        return None, "constructor block not found"

    return candidates[0], None

def find_private_insert_pos(text: str, class_span):
    body_start = class_span["brace"] + 1
    body_end = class_span["close"]
    body = text[body_start:body_end]

    private_hits = list(re.finditer(r"^\s*private\s*:\s*$", body, re.MULTILINE))
    if private_hits:
        return body_start + private_hits[0].end() + 1, False

    return body_end, True

result = {
    "stage": "12.20B-R2",
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
    result["pre_publish_call_count"] = count_publish_calls(text)

    if pre_hash != EXPECTED_STAGE1219_HASH:
        result["fail_reasons"].append("source hash does not match Stage 12.19 frozen hash")
    if result["pre_publish_call_count"] != 1:
        result["fail_reasons"].append("pre patch publish_call_count is not 1")
    if re.search(r"continuous_torque_streaming|enable_continuous_torque_streaming|Stage 12\.20", text):
        result["fail_reasons"].append("source already contains continuous streaming markers")

    class_spans = detect_class_spans(text)
    result["class_candidates"] = [
        {"name": c["name"], "score": c["score"], "start": c["start"], "close": c["close"]}
        for c in class_spans[:5]
    ]

    if not class_spans:
        result["fail_reasons"].append("no class/struct span detected")
    else:
        class_span = class_spans[0]
        result["detected_class_name"] = class_span["name"]
        result["detected_class_score"] = class_span["score"]

        helper_name, helper_err = detect_publish_helper(text, class_span)
        result["detected_publish_helper"] = helper_name
        if helper_err:
            result["fail_reasons"].append(helper_err)

        ctor, ctor_err = detect_constructor(text, class_span)
        if ctor_err:
            result["fail_reasons"].append(ctor_err)
        else:
            result["constructor_header"] = ctor["header"]

    if not result["fail_reasons"]:
        class_span = class_spans[0]
        private_insert_pos, needs_private_label = find_private_insert_pos(text, class_span)

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
            "\nprivate:\n"
            if needs_private_label else ""
        ) + (
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
        inserts.append((private_insert_pos, member_code))
        inserts.append((ctor["close"], ctor_code))

        patched = text
        for pos, code in sorted(inserts, key=lambda x: x[0], reverse=True):
            patched = patched[:pos] + code + patched[pos:]

        result["post_hash_candidate"] = sha256_text(patched)
        result["post_publish_call_count_candidate"] = count_publish_calls(patched)
        result["post_has_continuous_params_candidate"] = all(s in patched for s in [
            "enable_continuous_torque_streaming",
            "confirm_continuous_torque_streaming",
            "continuous_torque_streaming_max_ticks",
            "continuous_torque_streaming_max_duration_sec",
        ])
        result["post_has_four_flag_gate_candidate"] = "four_flag_gate" in patched
        result["post_has_continuous_timer_candidate"] = "continuous_torque_streaming_timer_" in patched
        result["post_calls_existing_publish_helper_candidate"] = f"this->{helper_name}();" in patched

        static_ok = all([
            result["post_publish_call_count_candidate"] == 1,
            result["post_has_continuous_params_candidate"],
            result["post_has_four_flag_gate_candidate"],
            result["post_has_continuous_timer_candidate"],
            result["post_calls_existing_publish_helper_candidate"],
        ])

        if not static_ok:
            result["fail_reasons"].append("candidate post-patch static checks failed; source not modified")
        else:
            backup = SRC.with_suffix(".cpp.stage1219_pre_stage1220b_r2.bak")
            shutil.copy2(SRC, backup)
            SRC.write_text(patched, encoding="utf-8")
            result["backup"] = str(backup)
            result["patch_applied"] = True
            result["post_hash"] = result["post_hash_candidate"]
            result["post_publish_call_count"] = result["post_publish_call_count_candidate"]
            result["post_has_continuous_params"] = result["post_has_continuous_params_candidate"]
            result["post_has_four_flag_gate"] = result["post_has_four_flag_gate_candidate"]
            result["post_has_continuous_timer"] = result["post_has_continuous_timer_candidate"]
            result["post_calls_existing_publish_helper"] = result["post_calls_existing_publish_helper_candidate"]
            result["pass"] = True

summary_path = OUT_DIR / "stage12_20b_r2_source_patch_summary.json"
summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

doc = [
    "# Stage 12.20B-R2 Source Patch Summary",
    "",
    f"- pass: `{result['pass']}`",
    f"- patch_applied: `{result['patch_applied']}`",
    f"- fail_reasons: `{result['fail_reasons']}`",
    f"- source: `{result['source']}`",
    f"- pre_hash: `{result.get('pre_hash')}`",
    f"- post_hash: `{result.get('post_hash')}`",
    f"- detected_class_name: `{result.get('detected_class_name')}`",
    f"- detected_publish_helper: `{result.get('detected_publish_helper')}`",
    f"- constructor_header: `{result.get('constructor_header')}`",
    f"- pre_publish_call_count: `{result.get('pre_publish_call_count')}`",
    f"- post_publish_call_count: `{result.get('post_publish_call_count')}`",
    f"- post_has_continuous_params: `{result.get('post_has_continuous_params')}`",
    f"- post_has_four_flag_gate: `{result.get('post_has_four_flag_gate')}`",
    f"- post_has_continuous_timer: `{result.get('post_has_continuous_timer')}`",
    "",
    "Safety boundary: bounded zero/safe dry-run only; no hardware deployment; no control-law change.",
]
doc_path = DOC_DIR / "stage12_20b_r2_source_patch_summary.md"
doc_path.write_text("\n".join(doc), encoding="utf-8")

print(json.dumps({
    "stage": result["stage"],
    "pass": result["pass"],
    "patch_applied": result["patch_applied"],
    "summary": str(summary_path),
    "doc": str(doc_path),
    "fail_reasons": result["fail_reasons"],
    "detected_class_name": result.get("detected_class_name"),
    "detected_publish_helper": result.get("detected_publish_helper"),
    "post_publish_call_count": result.get("post_publish_call_count"),
    "post_has_continuous_params": result.get("post_has_continuous_params"),
    "post_has_four_flag_gate": result.get("post_has_four_flag_gate"),
    "post_has_continuous_timer": result.get("post_has_continuous_timer"),
}, indent=2, ensure_ascii=False))
