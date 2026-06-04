# Stage 12.20D-R1 Reparse Existing Evidence

- pass: `False`
- fail_reasons: `['stream message count not in 1..30: 0', 'not all stream payloads have length 12: lengths=[]', 'not all stream payload values are finite', 'not all stream payload values are zero-safe']`
- original_stage1220d_pass: `False`
- original_stage1220d_fail_reasons: `['parameter set log does not show successful four-flag activation', 'stream message count not in 1..30: 0', 'not all stream payloads have length 12: lengths=[]', 'not all stream payload values are finite', 'not all stream payload values are zero-safe']`
- node_seen: `True`
- param_set_ok: `True`
- stream_message_count: `0`
- stream_message_count_in_1_to_30: `False`
- all_stream_payloads_length_12: `False`
- all_stream_payload_values_finite: `False`
- all_stream_payload_values_zero_safe: `False`
- final_flags_false: `True`
- after_stop_echo_timeout: `True`
- after_stop_echo_has_data: `False`
- continuous_torque_streaming_completed: `False`

Safety boundary: bounded zero/safe dry-run only; no hardware deployment; no control-law change.