#!/usr/bin/env python3
from pathlib import Path
import ast
import csv
import re
import sys
from collections import defaultdict, deque

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

AUDIT_LOG = ROOT / "results/logs_sample/stage08_runtime_mapping_duplication_audit_log.csv"
AUDIT_SUMMARY = ROOT / "results/logs_sample/stage08_runtime_mapping_duplication_audit_summary.csv"

ENTRYPOINTS = [
    "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py",
    "scripts/stage08_adapter_backed_stage07_recommended_test.py",
]

OUTPUT_LOG = ROOT / "results/logs_sample/stage08_runtime_mapping_audit_triage_log.csv"
OUTPUT_SUMMARY = ROOT / "results/logs_sample/stage08_runtime_mapping_audit_triage_summary.csv"
DOC_PATH = ROOT / "docs/STAGE08_RUNTIME_MAPPING_AUDIT_TRIAGE.md"


def parse_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def load_metric_summary(path: Path):
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
            for k, v in zip(header, row):
                metrics[k.strip()] = v.strip()
            return metrics

    return metrics


def load_audit_rows(path: Path):
    if not path.exists():
        return []

    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def module_to_script_path(module: str):
    if not module:
        return None

    candidates = []

    if module.startswith("scripts."):
        rel = module.replace(".", "/") + ".py"
        candidates.append(ROOT / rel)

    rel = module.replace(".", "/") + ".py"
    candidates.append(SCRIPTS_DIR / rel)

    rel_init = module.replace(".", "/") + "/__init__.py"
    candidates.append(SCRIPTS_DIR / rel_init)

    for path in candidates:
        if path.exists():
            return path.relative_to(ROOT).as_posix()

    return None


def literal_script_refs(text: str):
    refs = set()

    patterns = [
        r"scripts/[A-Za-z0-9_./-]+\.py",
        r"stage[0-9][0-9A-Za-z_./-]+\.py",
    ]

    for pat in patterns:
        for m in re.finditer(pat, text):
            raw = m.group(0)
            if raw.startswith("scripts/"):
                rel = raw
            else:
                rel = "scripts/" + raw

            path = ROOT / rel
            if path.exists():
                refs.add(path.relative_to(ROOT).as_posix())

    return refs


def extract_local_dependencies(script_rel: str):
    path = ROOT / script_rel
    deps = set()

    if not path.exists() or not path.suffix == ".py":
        return deps

    text = path.read_text(errors="replace")

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return deps | literal_script_refs(text)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                rel = module_to_script_path(alias.name)
                if rel:
                    deps.add(rel)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            rel = module_to_script_path(module)
            if rel:
                deps.add(rel)

            # from common import x
            if module:
                for alias in node.names:
                    rel = module_to_script_path(module + "." + alias.name)
                    if rel:
                        deps.add(rel)

    deps |= literal_script_refs(text)
    deps.discard(script_rel)
    return deps


def build_active_dependency_closure(entrypoints):
    active = set()
    q = deque()

    for rel in entrypoints:
        if (ROOT / rel).exists():
            active.add(rel)
            q.append(rel)

    graph = defaultdict(set)

    while q:
        current = q.popleft()
        deps = extract_local_dependencies(current)
        graph[current] = deps

        for dep in deps:
            if dep not in active:
                active.add(dep)
                q.append(dep)

    return active, graph


def classify_stage(file_rel: str):
    name = Path(file_rel).name

    m = re.match(r"stage(\d+)", name)
    if m:
        return f"Stage {int(m.group(1))}"

    if file_rel.startswith("scripts/common/"):
        return "common"

    return "unknown"


def main():
    OUTPUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    audit_summary = load_metric_summary(AUDIT_SUMMARY)
    audit_pass = parse_bool(audit_summary.get("pass", "False"))

    audit_rows = load_audit_rows(AUDIT_LOG)

    active_files, graph = build_active_dependency_closure(ENTRYPOINTS)

    triage_rows = []
    active_counts = defaultdict(int)
    legacy_counts = defaultdict(int)
    severity_counts = defaultdict(int)
    active_severity_counts = defaultdict(int)

    for row in audit_rows:
        file_rel = row.get("file", "")
        severity = row.get("severity", "")

        is_active = file_rel in active_files
        bucket = "active_dependency_path" if is_active else "legacy_or_nonactive_script"

        out = dict(row)
        out["bucket"] = bucket
        out["stage_family"] = classify_stage(file_rel)
        triage_rows.append(out)

        severity_counts[severity] += 1
        if is_active:
            active_counts[file_rel] += 1
            active_severity_counts[severity] += 1
        else:
            legacy_counts[file_rel] += 1

    active_findings = sum(active_counts.values())
    legacy_findings = sum(legacy_counts.values())
    active_high = active_severity_counts["high"]
    active_medium = active_severity_counts["medium"]
    active_low = active_severity_counts["low"]

    active_files_with_findings = len(active_counts)
    legacy_files_with_findings = len(legacy_counts)

    all_pass = audit_pass and AUDIT_LOG.exists() and AUDIT_SUMMARY.exists()

    with OUTPUT_LOG.open("w", newline="") as f:
        fieldnames = [
            "bucket",
            "stage_family",
            "file",
            "line",
            "pattern",
            "severity",
            "match",
            "meaning",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in triage_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    summary_rows = [
        ("stage", "Stage 8.5"),
        ("test_name", "runtime_mapping_audit_triage"),
        ("audit_log", str(AUDIT_LOG.relative_to(ROOT))),
        ("audit_summary", str(AUDIT_SUMMARY.relative_to(ROOT))),
        ("audit_pass", audit_pass),
        ("entrypoints", ";".join(ENTRYPOINTS)),
        ("active_dependency_file_count", len(active_files)),
        ("active_files_with_findings", active_files_with_findings),
        ("legacy_files_with_findings", legacy_files_with_findings),
        ("total_findings", len(audit_rows)),
        ("active_dependency_findings", active_findings),
        ("legacy_or_nonactive_findings", legacy_findings),
        ("active_high_severity_findings", active_high),
        ("active_medium_severity_findings", active_medium),
        ("active_low_severity_findings", active_low),
        ("total_high_severity_findings", severity_counts["high"]),
        ("total_medium_severity_findings", severity_counts["medium"]),
        ("total_low_severity_findings", severity_counts["low"]),
        ("pass", all_pass),
        ("log_csv", str(OUTPUT_LOG.relative_to(ROOT))),
        ("summary_csv", str(OUTPUT_SUMMARY.relative_to(ROOT))),
    ]

    with OUTPUT_SUMMARY.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(summary_rows)

    active_top = "\n".join(
        f"- `{file}`: {count} findings"
        for file, count in sorted(active_counts.items(), key=lambda kv: kv[1], reverse=True)[:20]
    )
    if not active_top:
        active_top = "- No active dependency findings."

    legacy_top = "\n".join(
        f"- `{file}`: {count} findings"
        for file, count in sorted(legacy_counts.items(), key=lambda kv: kv[1], reverse=True)[:20]
    )
    if not legacy_top:
        legacy_top = "- No legacy findings."

    active_list = "\n".join(f"- `{x}`" for x in sorted(active_files))
    if not active_list:
        active_list = "- No active files resolved."

    DOC_PATH.write_text(f"""# Stage 8.5 Runtime Mapping Audit Triage

## Target

Classify Stage 8.4 runtime mapping findings into:

1. active dependency path findings
2. legacy or non-active script findings

This prevents historical validation scripts from being treated as current controller-chain risk.

## Boundary

This stage is audit-only.

No controller logic, gains, gait scheduler, WBC/QP logic, swing tracking, or ROS2/C++ code is modified.

## Entrypoints

{chr(10).join(f"- `{x}`" for x in ENTRYPOINTS)}

## Active dependency closure

{active_list}

## Result

- pass: `{all_pass}`
- audit_pass: `{audit_pass}`
- total_findings: `{len(audit_rows)}`
- active_dependency_findings: `{active_findings}`
- legacy_or_nonactive_findings: `{legacy_findings}`
- active_high_severity_findings: `{active_high}`
- active_medium_severity_findings: `{active_medium}`
- active_low_severity_findings: `{active_low}`

## Active files with findings

{active_top}

## Legacy or non-active files with most findings

{legacy_top}

## Interpretation

If `active_high_severity_findings > 0`, Stage 8.6 should refactor only the active-path file with the highest high-severity count and then run A/B regression.

If `active_high_severity_findings = 0`, Stage 8.6 should not refactor legacy Stage 0/2 validation scripts. Instead, it should promote the adapter-backed entrypoint as the recommended Stage 8 runtime-safe baseline.
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 8.5 Runtime Mapping Audit Triage

Stage 8.5 classified Stage 8.4 runtime mapping findings into active dependency path findings and legacy/non-active script findings.

- Script: `scripts/stage08_runtime_mapping_audit_triage.py`
- Log: `results/logs_sample/stage08_runtime_mapping_audit_triage_log.csv`
- Summary: `results/logs_sample/stage08_runtime_mapping_audit_triage_summary.csv`
- Docs: `docs/STAGE08_RUNTIME_MAPPING_AUDIT_TRIAGE.md`
- pass: `{all_pass}`
- audit_pass: `{audit_pass}`
- active_dependency_file_count: `{len(active_files)}`
- total_findings: `{len(audit_rows)}`
- active_dependency_findings: `{active_findings}`
- legacy_or_nonactive_findings: `{legacy_findings}`
- active_high_severity_findings: `{active_high}`
- active_medium_severity_findings: `{active_medium}`
- active_low_severity_findings: `{active_low}`

Findings in legacy validation scripts are not treated as current controller-chain failures. Stage 8 remains focused on runtime interface hardening and does not complete pure WBC locomotion, ROS2/C++ migration, EKF, or full MPC.
""".strip()

    old_status = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 8.5 Runtime Mapping Audit Triage"
    if marker not in old_status:
        status_path.write_text(old_status.rstrip() + "\n\n" + block + "\n")

    print("[Stage 8.5] runtime mapping audit triage")
    print(f"pass={all_pass}")
    print(f"active_dependency_file_count={len(active_files)}")
    print(f"total_findings={len(audit_rows)}")
    print(f"active_dependency_findings={active_findings}")
    print(f"legacy_or_nonactive_findings={legacy_findings}")
    print(f"active_high_severity_findings={active_high}")
    print(f"active_medium_severity_findings={active_medium}")
    print(f"active_low_severity_findings={active_low}")
    print(f"log_csv={OUTPUT_LOG.relative_to(ROOT)}")
    print(f"summary_csv={OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed prerequisites:")
        print(f"- audit_log_exists={AUDIT_LOG.exists()}")
        print(f"- audit_summary_exists={AUDIT_SUMMARY.exists()}")
        print(f"- audit_pass={audit_pass}")
        sys.exit(2)


if __name__ == "__main__":
    main()
