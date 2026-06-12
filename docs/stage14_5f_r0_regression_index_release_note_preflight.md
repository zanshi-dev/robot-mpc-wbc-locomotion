# Stage 14.5F-R0 Regression Index and Release Note Preflight

Scope: simulation-only release evidence index preflight.

This step indexes Stage 14.5A-E summaries, docs, key CSV outputs, and runner sources. It does not run MuJoCo and does not modify any runner.

## Result

- pass: True
- failed_checks: []
- summary_count: 17
- doc_count: 17
- key_csv_count: 10
- indexed_artifact_count: 47

## Frozen release metrics

- stage14_5d_complete: True
- stage14_5e_complete: True
- validated_candidate_scale_max_simulation_only: 0.1

## Stage pass map

- 14.5A: True
- 14.5B: True
- 14.5C: True
- 14.5D-R0: True
- 14.5D-R1: True
- 14.5D-R2: True
- 14.5D-R3: True
- 14.5D-R4: True
- 14.5D-R5: True
- 14.5D-R6: True
- 14.5D-R7: True
- 14.5D-R8: True
- 14.5D-R9: True
- 14.5E-R0: True
- 14.5E-R1: True
- 14.5E-R2: True
- 14.5E-R3: True

## Boundary

- release_index_preflight_only: True
- mujoco_rollout_executed_in_f0: False
- mujoco_sim_data_ctrl_used_in_f0: False
- runner_modified_in_f0: False
- real_robot_torque_commanded: False
- ros_publisher_used: False
- torque_enable_ready: False

This is an index/preflight artifact only. It is not hardware-readiness evidence.

## Evidence

- release evidence index: `results/logs_sample/stage14_5f_r0_release_evidence_index.csv`
- release evidence manifest: `results/logs_sample/stage14_5f_r0_release_evidence_manifest.json`
- summary: `results/logs_sample/stage14_5f_r0_regression_index_release_note_preflight_summary.json`
