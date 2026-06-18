# Stage 16.4 README Rewrite

## Goal

Stage 16.4 rewrites the public README using the style rule:

```text
中文正文 + 标准英文术语 + 代码标识符保留英文
```

The README is aligned with Stage 15/16 evidence and explicitly avoids over-claiming.

## Boundary

The README does not claim:

- real robot deployment
- torque-enable readiness
- `torque_enable_ready=True`
- stable locomotion from Stage 15 smoke tests
- full MPC-WBC closed-loop locomotion completion
- hardware-ready ROS torque publisher

## Validation

Run:

```bash
bash scripts/stage16_4_validate_readme_rewrite.sh
```

Expected marker:

```text
stage16_4_result: pass
```
