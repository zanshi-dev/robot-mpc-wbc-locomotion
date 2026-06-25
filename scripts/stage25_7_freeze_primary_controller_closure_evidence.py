#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    summary_json = logs / "stage25_7_primary_controller_closure_evidence_freeze_summary.json"
    validation_csv = logs / "stage25_7_primary_controller_closure_evidence_freeze_validation.csv"
    manifest_json = logs / "stage25_7_primary_controller_closure_evidence_manifest.json"
    hashes_csv = logs / "stage25_7_primary_controller_closure_evidence_hashes.csv"
    doc = docs / "STAGE25_7_PRIMARY_CONTROLLER_CLOSURE_EVIDENCE_FREEZE.md"

    s25_0 = load_json(logs / "stage25_0_mpc_wbc_primary_controller_roadmap_summary.json")
    s25_1 = load_json(logs / "stage25_1_control_source_audit_summary.json")
    s25_2 = load_json(logs / "stage25_2_primary_mpc_wbc_mode_implementation_summary.json")
    s25_3 = load_json(logs / "stage25_3_primary_mpc_wbc_smoke_summary.json")
    s25_4 = load_json(logs / "stage25_4_primary_mpc_wbc_failure_diagnosis_summary.json")
    s25_5 = load_json(logs / "stage25_5_stabilized_primary_mpc_wbc_mode_summary.json")
    s25_6 = load_json(logs / "stage25_6_stabilized_primary_mpc_wbc_smoke_summary.json")

    direct_summary_csv = root / s25_3.get("runner_summary_csv", "")
    stabilized_summary_csv = root / s25_6.get("runner_summary_csv", "")

    direct_rows = read_csv_rows(direct_summary_csv)
    stabilized_rows = read_csv_rows(stabilized_summary_csv)

    direct = direct_rows[0] if direct_rows else {}
    stabilized = stabilized_rows[0] if stabilized_rows else {}

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    check("stage25_0_exists", bool(s25_0), "roadmap summary")
    check("stage25_2_pass", s25_2.get("result") == "pass", f"result={s25_2.get('result')}")
    check("stage25_3_pass", s25_3.get("result") == "pass", f"result={s25_3.get('result')}")
    check("stage25_4_pass", s25_4.get("result") == "pass", f"result={s25_4.get('result')}")
    check("stage25_5_pass", s25_5.get("result") == "pass", f"result={s25_5.get('result')}")
    check("stage25_6_pass", s25_6.get("result") == "pass", f"result={s25_6.get('result')}")

    check("direct_primary_executed", str(direct.get("primary_mpc_wbc_executed", "")).lower() == "true", str(direct.get("primary_mpc_wbc_executed")))
    check("direct_primary_smoke_failed", str(direct.get("pass", "")).lower() == "false", str(direct.get("pass")))
    check("direct_failure_class_recorded", s25_4.get("failure_class") == "posture_limit_violation_with_torque_saturation_no_qp_failure", str(s25_4.get("failure_class")))

    check("stabilized_primary_executed", str(stabilized.get("stabilized_primary_mpc_wbc_executed", "")).lower() == "true", str(stabilized.get("stabilized_primary_mpc_wbc_executed")))
    check("stabilized_primary_smoke_passed", str(stabilized.get("pass", "")).lower() == "true", str(stabilized.get("pass")))
    check("stabilized_qp_fail_zero", str(stabilized.get("qp_fail_steps", "")) in ("0", "0.0"), str(stabilized.get("qp_fail_steps")))
    check("stabilized_saturation_zero", str(stabilized.get("saturation_steps", "")) in ("0", "0.0"), str(stabilized.get("saturation_steps")))
    check("stabilized_simulation_only", str(stabilized.get("simulation_only_project", "")).lower() == "true", str(stabilized.get("simulation_only_project")))
    check("no_hardware_torque", str(stabilized.get("real_robot_torque_commanded", "")).lower() == "false", str(stabilized.get("real_robot_torque_commanded")))

    artifact_candidates = [
        "docs/STAGE25_MPC_WBC_PRIMARY_CONTROLLER_ROADMAP.md",
        "docs/STAGE25_2_PRIMARY_MPC_WBC_MODE_IMPLEMENTATION.md",
        "docs/STAGE25_3_PRIMARY_MPC_WBC_SMOKE_ROLLOUT.md",
        "docs/STAGE25_4_PRIMARY_MPC_WBC_FAILURE_DIAGNOSIS.md",
        "docs/STAGE25_5_STABILIZED_PRIMARY_MPC_WBC_MODE.md",
        "docs/STAGE25_6_STABILIZED_PRIMARY_MPC_WBC_SMOKE_ROLLOUT.md",
        "scripts/stage25_2_primary_mpc_wbc_runner.py",
        "scripts/stage25_5_stabilized_primary_mpc_wbc_runner.py",
        "results/logs_sample/stage25_2_primary_mpc_wbc_mode_implementation_summary.json",
        "results/logs_sample/stage25_3_primary_mpc_wbc_smoke_summary.json",
        "results/logs_sample/stage25_4_primary_mpc_wbc_failure_diagnosis_summary.json",
        "results/logs_sample/stage25_5_stabilized_primary_mpc_wbc_mode_summary.json",
        "results/logs_sample/stage25_6_stabilized_primary_mpc_wbc_smoke_summary.json",
        s25_3.get("runner_summary_csv", ""),
        s25_3.get("runner_log_csv", ""),
        s25_6.get("runner_summary_csv", ""),
        s25_6.get("runner_log_csv", ""),
    ]

    manifest_items = []
    hash_rows = []

    for rel in artifact_candidates:
        if not rel:
            continue
        p = root / rel
        exists = p.is_file()
        check(f"artifact_exists::{rel}", exists, rel)
        item = {
            "path": rel,
            "exists": exists,
            "size_bytes": p.stat().st_size if exists else 0,
            "sha256": sha256_file(p) if exists else "",
        }
        manifest_items.append(item)
        hash_rows.append(item)

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    comparison = {
        "direct_primary_mpc_wbc": {
            "executed": direct.get("primary_mpc_wbc_executed"),
            "pass": direct.get("pass"),
            "max_abs_roll": direct.get("max_abs_roll"),
            "max_abs_pitch": direct.get("max_abs_pitch"),
            "qp_fail_steps": direct.get("qp_fail_steps"),
            "saturation_steps": direct.get("saturation_steps"),
            "max_tau_total_abs": direct.get("max_tau_total_abs"),
            "failure_class": s25_4.get("failure_class"),
        },
        "stabilized_primary_mpc_wbc": {
            "executed": stabilized.get("stabilized_primary_mpc_wbc_executed"),
            "pass": stabilized.get("pass"),
            "stabilized_primary_scale": stabilized.get("stabilized_primary_scale"),
            "stabilized_primary_ramp_steps": stabilized.get("stabilized_primary_ramp_steps"),
            "max_abs_roll": stabilized.get("max_abs_roll"),
            "max_abs_pitch": stabilized.get("max_abs_pitch"),
            "qp_fail_steps": stabilized.get("qp_fail_steps"),
            "saturation_steps": stabilized.get("saturation_steps"),
            "max_tau_total_abs": stabilized.get("max_tau_total_abs"),
        },
    }

    summary = {
        "stage": "25.7",
        "name": "primary controller closure evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "final_claim": "simulation-only stabilized MPC-WBC primary controller closure smoke evidence",
        "direct_primary_mpc_wbc_status": "executed_but_smoke_failed",
        "stabilized_primary_mpc_wbc_status": "executed_and_smoke_passed",
        "comparison": comparison,
        "claim_boundary": [
            "simulation-only",
            "stabilized primary variant, not direct full primary torque",
            "smoke rollout evidence only",
            "no real robot torque execution",
            "no hardware torque enablement",
            "no complex terrain robustness",
            "no external-force robustness",
            "not production-grade MPC-WBC maturity",
        ],
        "supported_statements": [
            "primary_mpc_wbc mode was implemented and executed in simulation",
            "direct primary_mpc_wbc failed smoke stability due to posture violation and torque saturation",
            "stabilized_primary_mpc_wbc was implemented with ramp, scale, posture residual, and WBC residual",
            "stabilized_primary_mpc_wbc passed the nominal 2400-step simulation-only smoke rollout",
            "qp_fail_steps=0 and saturation_steps=0 for the stabilized smoke rollout",
        ],
        "unsupported_statements": [
            "direct primary_mpc_wbc is stable",
            "full MPC/WBC torque can replace baseline without residual stabilization",
            "real robot closed loop is complete",
            "hardware torque enablement is complete",
            "robustness to terrain or external disturbances has been proven",
        ],
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(hashes_csv.relative_to(root)),
            str(manifest_json.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "checks": checks,
    }

    write_csv(validation_csv, checks, ["check", "status", "detail"])
    write_csv(hashes_csv, hash_rows, ["path", "exists", "size_bytes", "sha256"])
    manifest_json.write_text(json.dumps({"items": manifest_items}, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 25.7：MPC-WBC primary controller closure evidence freeze

## 1. 目标

Stage 25.7 冻结 Stage 25.0–25.6 的 simulation-only MPC-WBC primary controller closure 证据。

本阶段不新增控制器，不新增 rollout，只汇总证据、冻结边界和生成 manifest / hash。

## 2. 冻结结果

Stage 25.7 result: {result}

Failure count: {failure_count}

Final claim:

    simulation-only stabilized MPC-WBC primary controller closure smoke evidence

## 3. Direct primary 与 stabilized primary 对比

| 项目 | direct primary_mpc_wbc | stabilized_primary_mpc_wbc |
|---|---:|---:|
| executed | {direct.get("primary_mpc_wbc_executed")} | {stabilized.get("stabilized_primary_mpc_wbc_executed")} |
| pass | {direct.get("pass")} | {stabilized.get("pass")} |
| max_abs_roll | {direct.get("max_abs_roll")} | {stabilized.get("max_abs_roll")} |
| max_abs_pitch | {direct.get("max_abs_pitch")} | {stabilized.get("max_abs_pitch")} |
| qp_fail_steps | {direct.get("qp_fail_steps")} | {stabilized.get("qp_fail_steps")} |
| saturation_steps | {direct.get("saturation_steps")} | {stabilized.get("saturation_steps")} |
| max_tau_total_abs | {direct.get("max_tau_total_abs")} | {stabilized.get("max_tau_total_abs")} |

## 4. 固定结论

Stage 25 支持以下表述：

    项目已实现并验证 simulation-only stabilized MPC-WBC primary controller closure。
    direct primary_mpc_wbc 已实际进入 MuJoCo torque loop，但未通过稳定性边界。
    stabilized_primary_mpc_wbc 通过了 nominal 2400-step smoke rollout。
    stabilized 版本使用 ramp / scale / posture residual / WBC residual，并保留 swing PD 和 torque safety filter。
    stabilized rollout 中 qp_fail_steps=0，saturation_steps=0。

## 5. 不能说的内容

Stage 25 不支持以下表述：

  * direct primary_mpc_wbc 已稳定；
  * full MPC/WBC torque 已经可以无残差稳定替代 baseline；
  * 已完成真实机器人闭环；
  * 已完成 hardware torque enablement；
  * 已验证复杂地形或外力扰动鲁棒性；
  * 已达到工程级成熟 MPC-WBC 控制器。

## 6. 面试表述建议

可以说：

    我先把 MPC/WBC candidate torque 接入为 primary stance torque，构成 primary_mpc_wbc 模式。
    直接主控版本确实进入了 MuJoCo torque loop，但 smoke rollout 暴露出姿态超限和力矩饱和问题。
    之后我做了失败诊断，确认不是 QP failure，而是 torque composition 需要稳定化。
    所以我实现了 stabilized_primary_mpc_wbc，在 primary candidate torque 外加入 ramp、scale、stance posture residual 和 online WBC residual。
    该稳定化版本在 nominal 2400-step simulation-only smoke rollout 中通过稳定性边界，且没有 QP failure 和 torque saturation。
    这个结果只证明仿真固定场景下的稳定化主控闭环，不代表真实机器人或复杂地形鲁棒性。

## 7. 证据文件

Manifest:

    {manifest_json.relative_to(root)}

Hashes:

    {hashes_csv.relative_to(root)}

Summary:

    {summary_json.relative_to(root)}
""", encoding="utf-8")

    print(f"stage25_7_result: {result}")
    print(f"failure_count: {failure_count}")
    print("final_claim: simulation-only stabilized MPC-WBC primary controller closure smoke evidence")
    print("direct_primary_mpc_wbc_status: executed_but_smoke_failed")
    print("stabilized_primary_mpc_wbc_status: executed_and_smoke_passed")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"hashes: {hashes_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
