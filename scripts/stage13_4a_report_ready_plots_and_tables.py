#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import csv
import json
import math
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
FIGS = DOCS / "figures"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)

STAGE13_3 = OUT / "stage13_3_report_ready_results_packaging_summary.json"
METRICS_CSV = OUT / "stage13_3_report_ready_metrics_table.csv"

SUMMARY = OUT / "stage13_4a_report_ready_plots_and_tables_summary.json"
DOC = DOCS / "stage13_4a_report_ready_plots_and_tables.md"
PLOT_INDEX = DOCS / "REPORT_READY_FIGURES.md"
TABLE_MD = DOCS / "REPORT_READY_METRICS_TABLE.md"

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def parse_float(x):
    try:
        if x is None or str(x).strip() == "":
            return None
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def read_metrics(path):
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f))

fail_reasons = []

stage13_3 = read_json(STAGE13_3)
if stage13_3 is None:
    fail_reasons.append("missing Stage 13.3 summary")
elif stage13_3.get("pass") is not True:
    fail_reasons.append("Stage 13.3 did not pass")

if not METRICS_CSV.exists():
    fail_reasons.append("missing report-ready metrics CSV")

rows = []
if METRICS_CSV.exists():
    rows = read_metrics(METRICS_CSV)
    if len(rows) < 2:
        fail_reasons.append("metrics CSV has fewer than 2 rows")

figures = {}

if not fail_reasons:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        labels = [r["experiment"] for r in rows]

        def save_bar(metric, title, ylabel, filename, include_blank=False):
            vals = [parse_float(r.get(metric)) for r in rows]
            filtered = [(lab, val) for lab, val in zip(labels, vals) if val is not None or include_blank]
            labs = [x[0] for x in filtered]
            nums = [0.0 if x[1] is None else x[1] for x in filtered]

            fig = plt.figure(figsize=(8, 4.5))
            ax = fig.add_subplot(111)
            ax.bar(labs, nums)
            ax.set_title(title)
            ax.set_ylabel(ylabel)
            ax.tick_params(axis="x", rotation=25)
            ax.grid(axis="y", alpha=0.3)
            fig.tight_layout()
            path = FIGS / filename
            fig.savefig(path, dpi=160)
            plt.close(fig)
            figures[metric] = str(path)

        save_bar("min_z", "Minimum base height", "m", "stage13_4a_min_z.png")
        save_bar("max_abs_roll", "Maximum absolute roll", "rad", "stage13_4a_max_abs_roll.png")
        save_bar("max_abs_pitch", "Maximum absolute pitch", "rad", "stage13_4a_max_abs_pitch.png")
        save_bar("max_joint_error", "Maximum joint tracking error", "rad", "stage13_4a_max_joint_error.png")
        save_bar("max_tau_total_abs", "Maximum absolute total torque", "Nm", "stage13_4a_max_tau_total_abs.png")
        save_bar("total_steps", "Experiment horizon", "steps", "stage13_4a_total_steps.png")

    except Exception as e:
        fail_reasons.append(f"plot generation failed: {repr(e)}")

expected_figures = [
    "min_z",
    "max_abs_roll",
    "max_abs_pitch",
    "max_joint_error",
    "max_tau_total_abs",
    "total_steps",
]

for k in expected_figures:
    p = Path(figures.get(k, ""))
    if not p.exists():
        fail_reasons.append(f"missing generated figure: {k}")

# Markdown metrics table.
if rows:
    headers = [
        "experiment",
        "total_steps",
        "transition_count",
        "min_z",
        "final_z",
        "max_abs_roll",
        "max_abs_pitch",
        "max_joint_error",
        "max_tau_total_abs",
        "qp_fail_steps",
        "saturation_steps",
        "pass",
    ]

    lines = [
        "# Report-Ready Metrics Table",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]

    for r in rows:
        lines.append("| " + " | ".join(str(r.get(h, "")) for h in headers) + " |")

    TABLE_MD.write_text("\n".join(lines), encoding="utf-8")
else:
    fail_reasons.append("no rows available for markdown table")

plot_index_lines = [
    "# Report-Ready Figures",
    "",
    "These figures are generated from `results/logs_sample/stage13_3_report_ready_metrics_table.csv`.",
    "",
    "Scope reminder: simulation-only; no hardware deployment, actuator enablement, or real robot torque execution is claimed.",
    "",
]

for metric, path in figures.items():
    rel = Path(path).relative_to(DOCS)
    plot_index_lines.append(f"- {metric}: `docs/{rel}`")

PLOT_INDEX.write_text("\n".join(plot_index_lines), encoding="utf-8")

summary = {
    "stage": "13.4A",
    "name": "report_ready_plots_and_table_export",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "simulation_only_project": True,
    "hardware_deployment_scope": "out_of_scope_by_user_constraint",
    "hardware_deployment_completed": False,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "control_law_changed": False,
    "baseline_type": "mixed_online_control_baseline",
    "input_metrics_csv": str(METRICS_CSV),
    "figures": figures,
    "table_markdown": str(TABLE_MD),
    "plot_index": str(PLOT_INDEX),
    "next_stage": "Stage 14 simulation-only improvement planning or stop at report-ready package",
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

doc_lines = [
    "# Stage 13.4A Report-Ready Plots and Table Export",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- simulation_only_project: `{summary['simulation_only_project']}`",
    f"- hardware_deployment_scope: `{summary['hardware_deployment_scope']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    f"- baseline_type: `{summary['baseline_type']}`",
    "",
    "## Generated figures",
]

for metric, path in figures.items():
    doc_lines.append(f"- {metric}: `{path}`")

doc_lines += [
    "",
    f"- table_markdown: `{TABLE_MD}`",
    f"- plot_index: `{PLOT_INDEX}`",
    "",
    f"Next stage: `{summary['next_stage']}`",
]

DOC.write_text("\n".join(doc_lines), encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
