#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common.go1_runtime_interface import (
    CONTRACT,
    make_nominal_mujoco_qpos,
    roundtrip_errors,
)

STAGE07_ORIGINAL_SCRIPT = ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py"


def adapter_preflight():
    q_mj = make_nominal_mujoco_qpos(
        base_xyz=(0.12, -0.03, 0.286),
        quat_wxyz=(1.0, 0.01, -0.02, 0.015),
        one_leg_q=(0.0, 0.9, -1.8),
    )
    q_mj[7:] += np.linspace(-0.03, 0.03, CONTRACT.mj_nu)
    v_mj = np.linspace(-0.17, 0.19, CONTRACT.mj_nv)
    tau_mj = np.linspace(-5.0, 5.0, CONTRACT.mj_nu)

    errors = roundtrip_errors(q_mj, v_mj, tau_mj)

    if errors["qpos_roundtrip_max_abs"] > 1e-12:
        raise RuntimeError(f"qpos adapter round-trip failed: {errors}")
    if errors["qvel_roundtrip_max_abs"] > 1e-12:
        raise RuntimeError(f"qvel adapter round-trip failed: {errors}")
    if errors["torque_roundtrip_max_abs"] > 1e-12:
        raise RuntimeError(f"torque adapter round-trip failed: {errors}")

    print("[adapter-preflight] pass=True")
    print(f"[adapter-preflight] qpos_roundtrip_max_abs={errors['qpos_roundtrip_max_abs']}")
    print(f"[adapter-preflight] qvel_roundtrip_max_abs={errors['qvel_roundtrip_max_abs']}")
    print(f"[adapter-preflight] torque_roundtrip_max_abs={errors['torque_roundtrip_max_abs']}")


def main():
    if not STAGE07_ORIGINAL_SCRIPT.exists():
        raise FileNotFoundError(STAGE07_ORIGINAL_SCRIPT)

    adapter_preflight()
    runpy.run_path(str(STAGE07_ORIGINAL_SCRIPT), run_name="__main__")


if __name__ == "__main__":
    main()
