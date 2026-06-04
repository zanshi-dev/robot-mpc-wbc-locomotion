# Stage 13.2A-R1 Runner Structure Inspection

- pass: `True`
- fail_reasons: `[]`
- inspection_only: `True`
- source_changed: `False`
- simulation_only_project: `True`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

## Diagnosis
- 1200-step horizon likely lives in WBC runner, not recommended wrapper
- swing target CSV is available and may control or verify rollout length

## Recommended runner
- literal_1200_count: `0`
- step_related_count: `8`
- subprocess_related_count: `0`

## WBC runner
- literal_1200_count: `1`
- step_related_count: `12`
- csv_related_count: `10`

## Swing target CSV
- exists: `True`
- line_count: `1201`

Recommended next stage: `Stage 13.2A-R2 create 2400-step runner using inspected horizon source; no original runner modification`