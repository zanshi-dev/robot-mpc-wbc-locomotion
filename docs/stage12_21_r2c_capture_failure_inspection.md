# Stage 12.21-R2C Capture Helper Failure Inspection

- pass: `True`
- inspection_only: `True`
- source_changed: `False`
- r2b_pass: `False`
- r2b_fail_reasons: `['subscriber_ready_before_activation', 'capture_ok', 'stream_message_count_in_1_to_30', 'all_stream_payloads_length_12', 'all_stream_payload_values_finite', 'all_stream_payload_values_zero_safe']`
- capture_returncode: `2`
- after_stop_capture_returncode: `2`
- param_set_ok_from_r2b: `True`
- final_flags_false_from_r2b: `True`
- diagnosis: `['capture helper script missing', 'capture helper path/file not found at runtime', 'capture process exited before writing capture_json']`

## Capture log excerpt

```text
/usr/bin/python3: can't open file '/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage12_21_r2b_capture.py': [Errno 2] No such file or directory

```

## After-stop capture log excerpt

```text
/usr/bin/python3: can't open file '/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage12_21_r2b_capture.py': [Errno 2] No such file or directory

```

Recommended next stage: `Stage 12.21-R2D repair capture launch path / helper execution, then rerun subscriber-warmup regression; no source change`

Safety boundary: inspection only; no source change; no hardware deployment.