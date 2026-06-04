#!/usr/bin/env python3
import csv
from pathlib import Path

import numpy as np
import osqp
import scipy.sparse as sp


INPUT_CSV = "results/logs_sample/stage06_qp_force_to_actuator_torque.csv"
OUTPUT_CSV = "results/logs_sample/stage07_minimal_wbc_torque_qp.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]

TORQUE_LIMIT = 23.7
W_TRACK = 1.0
W_REG = 1e-4


def read_tau_ref():
    with open(INPUT_CSV, "r", newline="") as f:
        row = next(csv.DictReader(f))

    tau = []
    names = []

    for leg in LEG_ORDER:
        for joint in JOINTS:
            col = f"{leg}_tau_{joint}"
            tau.append(float(row[col]))
            names.append(col)

    return np.array(tau, dtype=float), names


def solve_qp(tau_ref):
    n = 12

    # min 0.5 * tau^T P tau + q^T tau
    # equivalent to:
    # min W_TRACK * ||tau - tau_ref||^2 + W_REG * ||tau||^2
    P = 2.0 * (W_TRACK + W_REG) * sp.eye(n, format="csc")
    q = -2.0 * W_TRACK * tau_ref

    A = sp.eye(n, format="csc")
    l = -TORQUE_LIMIT * np.ones(n)
    u = TORQUE_LIMIT * np.ones(n)

    solver = osqp.OSQP()
    solver.setup(P=P, q=q, A=A, l=l, u=u, verbose=False, polish=True)
    result = solver.solve()

    if result.x is None:
        raise RuntimeError(f"OSQP failed, status={result.info.status}")

    return result


def main():
    tau_ref, names = read_tau_ref()
    result = solve_qp(tau_ref)
    tau_wbc = np.array(result.x, dtype=float)

    diff = tau_wbc - tau_ref

    tau_ref_max_abs = float(np.max(np.abs(tau_ref)))
    tau_wbc_max_abs = float(np.max(np.abs(tau_wbc)))
    diff_norm = float(np.linalg.norm(diff))
    diff_max_abs = float(np.max(np.abs(diff)))

    limit_pass = tau_wbc_max_abs <= TORQUE_LIMIT + 1e-9
    status_pass = result.info.status.lower() in ["solved", "solved inaccurate"]
    pass_test = bool(status_pass and limit_pass)

    row = {
        "osqp_status": result.info.status,
        "osqp_status_val": result.info.status_val,
        "objective": f"{result.info.obj_val:.12f}",
        "w_track": W_TRACK,
        "w_reg": W_REG,
        "torque_limit": TORQUE_LIMIT,
        "tau_ref_max_abs": f"{tau_ref_max_abs:.12f}",
        "tau_wbc_max_abs": f"{tau_wbc_max_abs:.12f}",
        "diff_norm": f"{diff_norm:.12f}",
        "diff_max_abs": f"{diff_max_abs:.12f}",
        "limit_pass": str(limit_pass),
        "pass": str(pass_test),
    }

    for name, v in zip(names, tau_ref):
        row[f"ref_{name}"] = f"{v:.12f}"

    for name, v in zip(names, tau_wbc):
        row[f"wbc_{name}"] = f"{v:.12f}"

    for name, v in zip(names, diff):
        row[f"diff_{name}"] = f"{v:.12f}"

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    print("Stage 7 minimal WBC torque QP")
    print(f"osqp_status={result.info.status}")
    print(f"objective={result.info.obj_val:.12f}")
    print(f"tau_ref_max_abs={tau_ref_max_abs:.12f}")
    print(f"tau_wbc_max_abs={tau_wbc_max_abs:.12f}")
    print(f"diff_norm={diff_norm:.12f}")
    print(f"diff_max_abs={diff_max_abs:.12f}")
    print(f"torque_limit={TORQUE_LIMIT:.12f}")
    print(f"limit_pass={limit_pass}")
    print(f"pass={pass_test}")
    print(f"saved={OUTPUT_CSV}")

    for i, name in enumerate(names):
        print(
            f"{name}: "
            f"tau_ref={tau_ref[i]: .9f}, "
            f"tau_wbc={tau_wbc[i]: .9f}, "
            f"diff={diff[i]: .9f}"
        )

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
