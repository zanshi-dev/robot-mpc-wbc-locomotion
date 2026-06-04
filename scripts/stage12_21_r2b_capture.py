#!/usr/bin/env /usr/bin/python3
import json
import math
import signal
import sys
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

out_path = Path(sys.argv[1])
ready_path = Path(sys.argv[2])
duration_sec = float(sys.argv[3])
node_suffix = sys.argv[4]

messages = []
stop_requested = False
start_time = None

def handle_signal(signum, frame):
    global stop_requested
    stop_requested = True

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

class CaptureNode(Node):
    def __init__(self):
        super().__init__(f"stage12_21_r2b_joint_torque_capture_{node_suffix}")
        self.sub = self.create_subscription(
            Float64MultiArray,
            "/go1/joint_torque_cmd",
            self.cb,
            10,
        )

    def cb(self, msg):
        data = [float(x) for x in msg.data]
        messages.append({
            "t_rel_sec": time.time() - start_time,
            "length": len(data),
            "data": data,
            "all_finite": all(math.isfinite(x) for x in data),
            "max_abs": max([abs(x) for x in data], default=0.0),
        })

try:
    rclpy.init()
    node = CaptureNode()
    start_time = time.time()
    ready_path.write_text("ready\n", encoding="utf-8")

    while rclpy.ok() and not stop_requested and (time.time() - start_time) < duration_sec:
        rclpy.spin_once(node, timeout_sec=0.1)

    out_path.write_text(json.dumps({
        "ok": True,
        "capture_duration_sec": time.time() - start_time,
        "message_count": len(messages),
        "messages": messages,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    node.destroy_node()
    rclpy.shutdown()
except Exception as e:
    out_path.write_text(json.dumps({
        "ok": False,
        "error": repr(e),
        "message_count": len(messages),
        "messages": messages,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    raise
