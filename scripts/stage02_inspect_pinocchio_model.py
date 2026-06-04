import argparse
from pathlib import Path

import pinocchio as pin


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--urdf", default="assets/go1/urdf/go1.urdf")
    args = parser.parse_args()

    urdf_path = Path(args.urdf)
    if not urdf_path.exists():
        raise FileNotFoundError(urdf_path)

    model = pin.buildModelFromUrdf(str(urdf_path), pin.JointModelFreeFlyer())

    print("=== Pinocchio model summary ===")
    print(f"name = {model.name}")
    print(f"nq = {model.nq}")
    print(f"nv = {model.nv}")
    print(f"njoints = {model.njoints}")
    print(f"nframes = {len(model.frames)}")

    print("\n=== joints ===")
    for jid, name in enumerate(model.names):
        print(f"[{jid}] {name:24s} nq={model.nqs[jid]} nv={model.nvs[jid]} idx_q={model.idx_qs[jid]} idx_v={model.idx_vs[jid]}")

    print("\n=== frames containing foot/calf/hip/thigh/trunk ===")
    keywords = ["foot", "calf", "hip", "thigh", "trunk", "FR", "FL", "RR", "RL"]
    for fid, frame in enumerate(model.frames):
        if any(k.lower() in frame.name.lower() for k in keywords):
            parent_joint = model.names[frame.parentJoint]
            print(f"[{fid}] {frame.name:32s} type={frame.type} parent_joint={parent_joint}")

    print("\n=== expected joint existence check ===")
    expected_joints = [
        "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
        "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
        "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
        "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
    ]

    for name in expected_joints:
        exists = model.existJointName(name)
        print(f"{name}: {exists}")

    print("\n=== possible foot frame candidates ===")
    for leg in ["FR", "FL", "RR", "RL"]:
        candidates = []
        for fid, frame in enumerate(model.frames):
            lname = frame.name.lower()
            if leg.lower() in lname and ("foot" in lname or "calf" in lname or "toe" in lname):
                candidates.append((fid, frame.name))
        print(f"{leg}: {candidates}")


if __name__ == "__main__":
    main()
