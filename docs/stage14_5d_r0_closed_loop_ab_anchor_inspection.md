# Stage 14.5D-R0 Closed-loop A/B Anchor Inspection

Scope: simulation-only source anchor inspection.

This step identifies likely source files for the later Stage 14.5D baseline vs MPC-assisted closed-loop A/B implementation.

It does not run MuJoCo closed-loop A/B, does not add the MPC-assisted switch, does not modify the frozen mixed baseline, and does not use ROS torque publishing.

## Evidence

- Summary JSON: `results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_inspection_summary.json`
- Candidate file list: `results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_candidates.txt`

## Result

- pass: True
- failed_checks: []

## Anchor categories

### baseline_runner

count: 105

- `PROJECT_STATUS.md`
- `README.md`
- `docs/CONTROL_ARCHITECTURE_OVERVIEW.md`
- `docs/DEMO_VIDEO_MANIFEST.md`
- `docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`
- `docs/ONE_PAGE_TECHNICAL_REPORT.md`
- `docs/REPORT_READY_CLAIMS_AND_LIMITATIONS.md`
- `docs/SIMULATION_ONLY_RESULTS_SUMMARY.md`
- `docs/STAGE07_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY.md`
- `docs/STAGE07_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_RECOMMENDED_TEST.md`
- `docs/STAGE07_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_SWEEP.md`
- `docs/STAGE08_ACTIVE_LEG_ORDER_REFACTOR_AND_REGRESSION.md`
- `docs/STAGE08_ADAPTER_BACKED_STAGE07_BASELINE_AB_TEST.md`
- `docs/STAGE08_ADAPTER_ZERO_CONTROL_REGRESSION_GUARD.md`
- `docs/STAGE08_BASELINE_FREEZE_MANIFEST.md`
- `docs/STAGE08_RUNTIME_INTERFACE_CONTRACT_CHECK.md`
- `docs/STAGE08_RUNTIME_MAPPING_AUDIT_TRIAGE.md`
- `docs/WBC_QP_EXPLAINED.md`
- `docs/stage13_0_simulation_only_locomotion_preflight_inventory.md`
- `docs/stage13_1a_existing_stage7_baseline_summary_verification.md`
- `docs/stage13_1b_rerun_1200step_simulation_only_mixed_baseline.md`
- `docs/stage13_2a_2400step_preflight_and_derived_runner.md`
- `docs/stage13_2a_r2_create_2400step_derived_runner.md`
- `docs/stage13_2b_r1_derive_contact_schedule_and_rerun_2400step.md`
- `docs/stage13_2b_run_2400step_simulation_only_robustness_regression.md`
- `docs/stage13_2c_final_2400step_robustness_evidence_freeze.md`
- `docs/stage13_3_report_ready_results_packaging.md`
- `docs/stage13_5a_mujoco_offscreen_rollout_demo_video.md`
- `docs/stage13_5a_r1_mujoco_offscreen_rollout_video_640fb.md`
- `docs/stage13_5a_r2_mujoco_offscreen_rollout_video_fixed_ffmpeg.md`
- `docs/stage13_5b_demo_video_evidence_freeze.md`
- `docs/stage14_4_base_velocity_tracking_mpc.md`
- `docs/stage14_4b_base_velocity_tracking_mpc_validation.md`
- `docs/stage14_4c_mpc_scope_explanation.md`
- `docs/stage14_4d_document_language_audit.md`
- `docs/stage14_5a_mpc_wbc_integration_preflight.md`
- `docs/stage14_5b_offline_mpc_force_to_torque_candidate_check.md`
- `docs/stage14_5c_mpc_force_reference_offline_qp_check.md`
- `results/logs_sample/stage08_6_backup_stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py.txt`
- `results/logs_sample/stage08_6_py_compile_stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py.stderr.txt`
- `results/logs_sample/stage08_ab_adapter_backed_stdout.txt`
- `results/logs_sample/stage08_ab_original_stdout.txt`
- `results/logs_sample/stage08_adapter_zero_control_regression_guard_stage07_stdout.txt`
- `results/logs_sample/stage08_freeze_integrity_recommended_entrypoint_stdout.txt`
- `results/logs_sample/stage08_recommended_runtime_safe_entrypoint_stdout.txt`
- `results/logs_sample/stage13_0_simulation_only_locomotion_preflight_inventory_summary.json`
- `results/logs_sample/stage13_1a_existing_stage7_baseline_summary_verification_summary.json`
- `results/logs_sample/stage13_1b_rerun_1200step_simulation_only_mixed_baseline_summary.json`
- `results/logs_sample/stage13_2a_2400step_preflight_and_derived_runner_summary.json`
- `results/logs_sample/stage13_2a_r1_runner_structure_inspection_summary.json`
- `results/logs_sample/stage13_2a_r2_create_2400step_derived_runner_summary.json`
- `results/logs_sample/stage13_2b_r1_derive_contact_schedule_and_rerun_2400step_summary.json`
- `results/logs_sample/stage13_2b_run_2400step_simulation_only_robustness_regression_summary.json`
- `results/logs_sample/stage13_2c_final_2400step_robustness_evidence_freeze_summary.json`
- `results/logs_sample/stage13_3_report_ready_results_packaging_summary.json`
- `results/logs_sample/stage13_5a_mujoco_offscreen_rollout_demo_video_summary.json`
- `results/logs_sample/stage13_5a_r1_mujoco_offscreen_rollout_video_640fb_summary.json`
- `results/logs_sample/stage13_5a_r2_mujoco_offscreen_rollout_video_fixed_ffmpeg_summary.json`
- `results/logs_sample/stage13_5b_demo_video_evidence_freeze_summary.json`
- `results/logs_sample/stage13_5c_final_package_with_demo_video_manifest.json`
- ... truncated in docs; see `results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_candidates.txt`

### mujoco_step_loop

count: 232

- `PROJECT_STATUS.md`
- `README.md`
- `assets/go1/README.md`
- `assets/go1/go1.xml`
- `assets/go1/scene.xml`
- `assets/stage00_minimal_leg.xml`
- `docs/CONTROL_ARCHITECTURE_OVERVIEW.md`
- `docs/CPP_CONTROL_ALGORITHMS.md`
- `docs/DEMO_VIDEO_MANIFEST.md`
- `docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`
- `docs/ONE_PAGE_TECHNICAL_REPORT.md`
- `docs/SIMULATION_ONLY_SCOPE.md`
- `docs/STAGE06_QP_FORCE_TO_ACTUATOR_TORQUE.md`
- `docs/STAGE06_QP_TORQUE_SUPPORT_TEST.md`
- `docs/STAGE06_SUMMARY_AND_STAGE07_INTERFACE.md`
- `docs/STAGE07_CONSOLIDATED_SUMMARY_AFTER_SWING.md`
- `docs/STAGE07_CONTACT_MODE_SEQUENCE_RAMP_TEST.md`
- `docs/STAGE07_CONTACT_MODE_TORQUE_RAMP_CHECK.md`
- `docs/STAGE07_CONTACT_SCHEDULE_WBC_QP.md`
- `docs/STAGE07_FINAL_SUMMARY.md`
- `docs/STAGE07_FINAL_UPDATE_AFTER_MODE_SEQUENCE.md`
- `docs/STAGE07_FULL_WBC_BASE_VERTICAL_ACCEL_TASK_QP.md`
- `docs/STAGE07_FULL_WBC_DYNAMICS_QP.md`
- `docs/STAGE07_FULL_WBC_FINAL_UPDATE.md`
- `docs/STAGE07_FULL_WBC_STANCE_CONSTRAINT_QP.md`
- `docs/STAGE07_FULL_WBC_SUMMARY.md`
- `docs/STAGE07_FULL_WBC_SWING_ACCEL_TASK_QP.md`
- `docs/STAGE07_FULL_WBC_TORQUE_RECONSTRUCTION_AND_RAMP_CHECK.md`
- `docs/STAGE07_FULL_WBC_TORQUE_SEQUENCE_SUPPORT_TEST.md`
- `docs/STAGE07_MINIMAL_WBC_TORQUE_QP.md`
- `docs/STAGE07_ONLINE_FULL_WBC_STEP_LOOP_PROTO.md`
- `docs/STAGE07_ONLINE_FULL_WBC_WITH_SCHEDULER_PROTO.md`
- `docs/STAGE07_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY.md`
- `docs/STAGE07_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_RECOMMENDED_TEST.md`
- `docs/STAGE07_ONLINE_SWING_TRAJECTORY_TRACKING_CHECK.md`
- `docs/STAGE07_SUMMARY_AND_NEXT_STEPS.md`
- `docs/STAGE07_SWING_FOOT_TRACKING_QP.md`
- `docs/STAGE07_SWING_JOINT_TARGET_SEQUENCE.md`
- `docs/STAGE07_SWING_JOINT_TARGET_TRACKING_RECOMMENDED_TEST.md`
- `docs/STAGE07_SWING_TRAJECTORY_QP.md`
- `docs/STAGE07_WBC_BASE_WRENCH_QP.md`
- `docs/STAGE07_WBC_BASE_WRENCH_SUPPORT_TEST.md`
- `docs/STAGE07_WBC_TORQUE_SUPPORT_TEST.md`
- `docs/STAGE08_0_7_RUNTIME_INTERFACE_HARDENING_SUMMARY.md`
- `docs/STAGE08_ACTIVE_LEG_ORDER_REFACTOR_AND_REGRESSION.md`
- `docs/STAGE08_RUNTIME_INTERFACE_ADAPTER_MODULE_CHECK.md`
- `docs/STAGE08_RUNTIME_INTERFACE_CONTRACT_CHECK.md`
- `docs/STAGE08_RUNTIME_MAPPING_AUDIT_TRIAGE.md`
- `docs/STAGE08_RUNTIME_MAPPING_DUPLICATION_AUDIT.md`
- `docs/STAGE09_0_6_INTERFACE_MIRROR_FREEZE_SUMMARY.md`
- `docs/STAGE09_CPP_MIRROR_CONTRACT_REPORT.md`
- `docs/STAGE09_PYTHON_BASELINE_ROS2_FIELD_MAPPING.md`
- `docs/STAGE09_ROS2_RUNTIME_MIRROR_SMOKE_TEST.md`
- `docs/STAGE10_CONTROLLER_IMPLEMENTATION_PLAN_AND_SAFETY_GATE.md`
- `docs/STAGE10_TORQUE_PUBLISHER_ENABLE_GATE_DESIGN.md`
- `docs/WBC_QP_EXPLAINED.md`
- `docs/interview/INTERVIEW_3MIN_SYSTEM_EXPLANATION.md`
- `docs/stage01_ros2_mujoco_bridge.md`
- `docs/stage02_pinocchio_kinematics_validation.md`
- `docs/stage03_standing_pd_baseline.md`
- ... truncated in docs; see `results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_candidates.txt`

### torque_candidate_or_tau

count: 417

- `PROJECT_STATUS.md`
- `README.md`
- `docs/CONTROL_ARCHITECTURE_OVERVIEW.md`
- `docs/CPP_CONTROL_ALGORITHMS.md`
- `docs/DEMO_VIDEO_MANIFEST.md`
- `docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`
- `docs/ONE_PAGE_TECHNICAL_REPORT.md`
- `docs/REPORT_READY_CLAIMS_AND_LIMITATIONS.md`
- `docs/REPORT_READY_FIGURES.md`
- `docs/REPORT_READY_METRICS_TABLE.md`
- `docs/REPORT_READY_PACKAGE_MANIFEST.md`
- `docs/REPORT_READY_RESULTS.md`
- `docs/SIMULATION_ONLY_RESULTS_SUMMARY.md`
- `docs/SIMULATION_ONLY_SCOPE.md`
- `docs/STAGE06_QP_FORCE_TO_ACTUATOR_TORQUE.md`
- `docs/STAGE06_QP_TORQUE_SUPPORT_TEST.md`
- `docs/STAGE06_SUMMARY_AND_STAGE07_INTERFACE.md`
- `docs/STAGE07_CONSOLIDATED_SUMMARY_AFTER_SWING.md`
- `docs/STAGE07_CONTACT_MODE_SEQUENCE_RAMP_TEST.md`
- `docs/STAGE07_CONTACT_MODE_TORQUE_RAMP_CHECK.md`
- `docs/STAGE07_CONTACT_MODE_TRANSITION_CHECK.md`
- `docs/STAGE07_CONTACT_SCHEDULE_WBC_QP.md`
- `docs/STAGE07_CONTACT_SCHEDULE_WBC_SCALED_SUPPORT_TEST.md`
- `docs/STAGE07_FINAL_SUMMARY.md`
- `docs/STAGE07_FINAL_UPDATE_AFTER_MODE_SEQUENCE.md`
- `docs/STAGE07_FULL_WBC_BASE_VERTICAL_ACCEL_TASK_QP.md`
- `docs/STAGE07_FULL_WBC_DYNAMICS_QP.md`
- `docs/STAGE07_FULL_WBC_FINAL_UPDATE.md`
- `docs/STAGE07_FULL_WBC_STANCE_CONSTRAINT_QP.md`
- `docs/STAGE07_FULL_WBC_SUMMARY.md`
- `docs/STAGE07_FULL_WBC_SWING_ACCEL_TASK_QP.md`
- `docs/STAGE07_FULL_WBC_TORQUE_RECONSTRUCTION_AND_RAMP_CHECK.md`
- `docs/STAGE07_FULL_WBC_TORQUE_SEQUENCE_SUPPORT_TEST.md`
- `docs/STAGE07_GAIT_PHASE_SCHEDULER_PROTO.md`
- `docs/STAGE07_MINIMAL_WBC_TORQUE_QP.md`
- `docs/STAGE07_ONLINE_FULL_WBC_PLUS_SWING_JOINT_TRACKING_SWEEP.md`
- `docs/STAGE07_ONLINE_FULL_WBC_SCHEDULER_RECOMMENDED_RUN.md`
- `docs/STAGE07_ONLINE_FULL_WBC_SCHEDULER_STABILITY_SWEEP.md`
- `docs/STAGE07_ONLINE_FULL_WBC_STEP_LOOP_PROTO.md`
- `docs/STAGE07_ONLINE_FULL_WBC_WITH_SCHEDULER_PROTO.md`
- `docs/STAGE07_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY.md`
- `docs/STAGE07_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_RECOMMENDED_TEST.md`
- `docs/STAGE07_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_SWEEP.md`
- `docs/STAGE07_ONLINE_SWING_JOINT_TRACKING_RECOMMENDED_TEST.md`
- `docs/STAGE07_ONLINE_SWING_JOINT_TRACKING_STABILITY_SWEEP.md`
- `docs/STAGE07_ONLINE_SWING_TRAJECTORY_MEMORY_PROTO.md`
- `docs/STAGE07_ONLINE_SWING_TRAJECTORY_TRACKING_CHECK.md`
- `docs/STAGE07_SUMMARY_AND_NEXT_STEPS.md`
- `docs/STAGE07_SWING_JOINT_TARGET_SEQUENCE.md`
- `docs/STAGE07_SWING_JOINT_TARGET_TRACKING_RECOMMENDED_TEST.md`
- `docs/STAGE07_SWING_TRACKING_MODE_SEQUENCE_TEST.md`
- `docs/STAGE07_SWING_TRACKING_RECOMMENDED_BOTH_MODES.md`
- `docs/STAGE07_SWING_TRAJECTORY_QP.md`
- `docs/STAGE07_WBC_BASE_WRENCH_QP.md`
- `docs/STAGE07_WBC_BASE_WRENCH_SUPPORT_TEST.md`
- `docs/STAGE07_WBC_TORQUE_SUPPORT_TEST.md`
- `docs/STAGE07_WBC_VARIANT_COMPARISON.md`
- `docs/STAGE08_0_7_RUNTIME_INTERFACE_HARDENING_SUMMARY.md`
- `docs/STAGE08_ACTIVE_LEG_ORDER_REFACTOR_AND_REGRESSION.md`
- `docs/STAGE08_ADAPTER_BACKED_STAGE07_BASELINE_AB_TEST.md`
- ... truncated in docs; see `results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_candidates.txt`

### ab_or_switch_anchor

count: 498

- `PROJECT_STATUS.md`
- `README.md`
- `assets/go1/CHANGELOG.md`
- `assets/go1/README.md`
- `assets/go1/go1.xml`
- `assets/go1/scene.xml`
- `assets/stage00_minimal_leg.xml`
- `docs/CONTROL_ARCHITECTURE_OVERVIEW.md`
- `docs/CPP_CONTROL_ALGORITHMS.md`
- `docs/DEMO_VIDEO_MANIFEST.md`
- `docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`
- `docs/ONE_PAGE_TECHNICAL_REPORT.md`
- `docs/REPORT_READY_CLAIMS_AND_LIMITATIONS.md`
- `docs/REPORT_READY_FIGURES.md`
- `docs/REPORT_READY_METRICS_TABLE.md`
- `docs/REPORT_READY_PACKAGE_MANIFEST.md`
- `docs/REPORT_READY_RESULTS.md`
- `docs/SIMULATION_ONLY_RESULTS_SUMMARY.md`
- `docs/SIMULATION_ONLY_SCOPE.md`
- `docs/STAGE06_QP_FORCE_TO_ACTUATOR_TORQUE.md`
- `docs/STAGE06_QP_TORQUE_SUPPORT_TEST.md`
- `docs/STAGE06_SUMMARY_AND_STAGE07_INTERFACE.md`
- `docs/STAGE07_CONSOLIDATED_SUMMARY_AFTER_SWING.md`
- `docs/STAGE07_CONTACT_MODE_SEQUENCE_RAMP_TEST.md`
- `docs/STAGE07_CONTACT_MODE_TORQUE_RAMP_CHECK.md`
- `docs/STAGE07_CONTACT_MODE_TRANSITION_CHECK.md`
- `docs/STAGE07_CONTACT_SCHEDULE_WBC_QP.md`
- `docs/STAGE07_CONTACT_SCHEDULE_WBC_SCALED_SUPPORT_TEST.md`
- `docs/STAGE07_FINAL_SUMMARY.md`
- `docs/STAGE07_FINAL_UPDATE_AFTER_MODE_SEQUENCE.md`
- `docs/STAGE07_FULL_WBC_BASE_VERTICAL_ACCEL_TASK_QP.md`
- `docs/STAGE07_FULL_WBC_DYNAMICS_QP.md`
- `docs/STAGE07_FULL_WBC_FINAL_UPDATE.md`
- `docs/STAGE07_FULL_WBC_STANCE_CONSTRAINT_QP.md`
- `docs/STAGE07_FULL_WBC_SUMMARY.md`
- `docs/STAGE07_FULL_WBC_SWING_ACCEL_TASK_QP.md`
- `docs/STAGE07_FULL_WBC_TORQUE_RECONSTRUCTION_AND_RAMP_CHECK.md`
- `docs/STAGE07_FULL_WBC_TORQUE_SEQUENCE_SUPPORT_TEST.md`
- `docs/STAGE07_GAIT_PHASE_SCHEDULER_PROTO.md`
- `docs/STAGE07_MINIMAL_WBC_TORQUE_QP.md`
- `docs/STAGE07_ONLINE_FULL_WBC_PLUS_SWING_JOINT_TRACKING_SWEEP.md`
- `docs/STAGE07_ONLINE_FULL_WBC_SCHEDULER_RECOMMENDED_RUN.md`
- `docs/STAGE07_ONLINE_FULL_WBC_SCHEDULER_STABILITY_SWEEP.md`
- `docs/STAGE07_ONLINE_FULL_WBC_STEP_LOOP_PROTO.md`
- `docs/STAGE07_ONLINE_FULL_WBC_WITH_SCHEDULER_PROTO.md`
- `docs/STAGE07_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY.md`
- `docs/STAGE07_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_RECOMMENDED_TEST.md`
- `docs/STAGE07_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_SWEEP.md`
- `docs/STAGE07_ONLINE_SWING_JOINT_TRACKING_RECOMMENDED_TEST.md`
- `docs/STAGE07_ONLINE_SWING_JOINT_TRACKING_STABILITY_SWEEP.md`
- `docs/STAGE07_ONLINE_SWING_TRAJECTORY_MEMORY_PROTO.md`
- `docs/STAGE07_ONLINE_SWING_TRAJECTORY_TRACKING_CHECK.md`
- `docs/STAGE07_SUMMARY_AND_NEXT_STEPS.md`
- `docs/STAGE07_SWING_FOOT_TRACKING_QP.md`
- `docs/STAGE07_SWING_JOINT_TARGET_SEQUENCE.md`
- `docs/STAGE07_SWING_JOINT_TARGET_TRACKING_RECOMMENDED_TEST.md`
- `docs/STAGE07_SWING_TRACKING_MODE_SEQUENCE_TEST.md`
- `docs/STAGE07_SWING_TRACKING_RECOMMENDED_BOTH_MODES.md`
- `docs/STAGE07_SWING_TRAJECTORY_QP.md`
- `docs/STAGE07_WBC_BASE_WRENCH_QP.md`
- ... truncated in docs; see `results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_candidates.txt`

### stage14_5_outputs

count: 7

- `docs/stage14_5b_offline_mpc_force_to_torque_candidate_check.md`
- `docs/stage14_5c_mpc_force_reference_offline_qp_check.md`
- `results/logs_sample/stage14_5b_force_rollout_source_inventory.json`
- `results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidate_summary.json`
- `results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_summary.json`
- `scripts/stage14_5b_offline_mpc_force_to_torque_candidate_check.py`
- `scripts/stage14_5c_mpc_force_reference_offline_qp_check.py`

## Boundary

This is not MPC-assisted closed-loop locomotion evidence. It is only the source-anchor inspection needed before introducing an explicit simulation-only A/B switch.
