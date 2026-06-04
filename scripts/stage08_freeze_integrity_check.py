#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"
DOC_PATH = ROOT / "docs/STAGE08_FREEZE_INTEGRITY_CHECK.md"

RECOMMENDED_ENTRYPOINT = ROOT / "scripts/stage08_adapter_backed_stage07_recommended_test.py"

FREEZE_FILES = [
    "scripts/stage08_adapter_backed_stage07_recommended_test.py",
    "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py",
    "scripts/stage07_online_full_wbc_scheduler_recommended_run.py",
    "scripts/common/go1_runtime_interface.py",
    "docs/STAGE08_0_7_RUNTIME_INTERFACE_HARDENING_SUMMARY.md",
    "docs/STAGE08_RECOMMENDED_RUNTIME_SAFE_ENTRYPOINT.md",
    "docs/STAGE08_BASELINE_FREEZE_MANIFEST.md",
    "results/logs_sample/stage08_baseline_freeze_manifest.csv",
    "results/logs_sample/stage08_0_7_runtime_interface_hardening_summary.csv",
    "results/logs_sample/stage08_recommended_runtime_safe_entrypoint_promotion_summary.csv",
    "results/logs_sample/stage08_active_leg_order_refactor_and_regression_summary.csv",
    "results/logs_sample/stage08_runtime_mapping_audit_triage_summary.csv",
    "results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv",
]

HASH_LOG = LOG_DIR / "stage08_freeze_integrity_hashes.csv"
SUMMARY_PATH = LOG_DIR / "stage08_freeze_integrity_check_summary.csv"
RUN_STDOUT = LOG_DIR / "stage08_freeze_integrity_recommended_entrypoint_stdout.txt"
RUN_STDERR = LOG_DIR / "stage08_freeze_integrity_recommended_entrypoint_stderr.txt"


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    hash_rows = []
    missing_files = []

    for rel in FREEZE_FILES:
        path = ROOT / rel
        if path.exists():
            hash_rows.append({
                "file": rel,
                "exists": True,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
        else:
            missing_files.append(rel)
            hash_rows.append({
                "file": rel,
                "exists": False,
                "sha256": "",
                "size_bytes": "",
            })

    with HASH_LOG.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "exists", "sha256", "size_bytes"])
        writer.writeheader()
        writer.writerows(hash_rows)

    proc = subprocess.run(
        [sys.executable, str(RECOMMENDED_ENTRYPOINT)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    RUN_STDOUT.write_text(proc.stdout)
    RUN_STDERR.write_text(proc.stderr)

    adapter_preflight_pass = "[adapter-preflight] pass=True" in proc.stdout
    entrypoint_pass = proc.returncode == 0
    all_files_exist = len(missing_files) == 0
    all_pass = all_files_exist and entrypoint_pass and adapter_preflight_pass

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 8.10"])
        writer.writerow(["test_name", "freeze_integrity_check"])
        writer.writerow(["recommended_entrypoint", "scripts/stage08_adapter_backed_stage07_recommended_test.py"])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["all_files_exist", all_files_exist])
        writer.writerow(["recommended_entrypoint_returncode", proc.returncode])
        writer.writerow(["adapter_preflight_stdout_pass", adapter_preflight_pass])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["hash_log", str(HASH_LOG.relative_to(ROOT))])
        writer.writerow(["stdout", str(RUN_STDOUT.relative_to(ROOT))])
        writer.writerow(["stderr", str(RUN_STDERR.relative_to(ROOT))])
        writer.writerow(["pass", all_pass])

    DOC_PATH.write_text(f"""# Stage 8.10 Freeze Integrity Check

## 目标

对 Stage 8 Python runtime-safe frozen baseline 做最终完整性检查。

## 推荐入口

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

## 检查内容

1. 核心冻结文件是否存在；
2. 生成每个冻结文件的 SHA256；
3. 再运行一次推荐入口；
4. 检查 adapter preflight 是否通过；
5. 明确当前仍是 mixed online control baseline。

## 输出

- Hash log: results/logs_sample/stage08_freeze_integrity_hashes.csv
- Summary: results/logs_sample/stage08_freeze_integrity_check_summary.csv
- Stdout: results/logs_sample/stage08_freeze_integrity_recommended_entrypoint_stdout.txt
- Stderr: results/logs_sample/stage08_freeze_integrity_recommended_entrypoint_stderr.txt

## 结果

- pass: {all_pass}
- all_files_exist: {all_files_exist}
- recommended_entrypoint_returncode: {proc.returncode}
- adapter_preflight_stdout_pass: {adapter_preflight_pass}

## 边界

本阶段不改变控制律，不完成 pure WBC locomotion，不完成 ROS2/C++ real-time controller，不完成 EKF，不完成 full 3D centroidal MPC。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 8.10 Freeze Integrity Check

Stage 8.10 完成 Python runtime-safe frozen baseline 的完整性检查。

- Script: `scripts/stage08_freeze_integrity_check.py`
- Hash log: `results/logs_sample/stage08_freeze_integrity_hashes.csv`
- Summary: `results/logs_sample/stage08_freeze_integrity_check_summary.csv`
- Docs: `docs/STAGE08_FREEZE_INTEGRITY_CHECK.md`
- pass: `{all_pass}`
- all_files_exist: `{all_files_exist}`
- recommended_entrypoint_returncode: `{proc.returncode}`
- adapter_preflight_stdout_pass: `{adapter_preflight_pass}`

当前 baseline 仍是 mixed online control baseline，不是 pure full WBC locomotion。后续 ROS2/C++ 或控制器改造必须以该 frozen baseline 为回归基准。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 8.10 Freeze Integrity Check"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 8.10] freeze integrity check")
    print(f"pass={all_pass}")
    print(f"all_files_exist={all_files_exist}")
    print(f"missing_file_count={len(missing_files)}")
    print(f"recommended_entrypoint_returncode={proc.returncode}")
    print(f"adapter_preflight_stdout_pass={adapter_preflight_pass}")
    print(f"hash_log={HASH_LOG.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        if missing_files:
            print("Missing files:")
            for rel in missing_files:
                print(f"- {rel}")
        sys.exit(2)


if __name__ == "__main__":
    main()
