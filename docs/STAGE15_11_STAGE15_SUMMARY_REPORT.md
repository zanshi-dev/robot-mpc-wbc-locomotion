# Stage 15.11 Stage 15 Summary Report

## 1. Goal

Stage 15.11 generates a report-level summary for Stage 15.1 through Stage 15.10.

It collects local validation artifacts and produces:

```text
docs/STAGE15_UPGRADE_SUMMARY.md
results/logs_sample/stage15_11_stage15_summary_report.json
results/logs_sample/stage15_11_stage15_summary_report.csv
results/logs_sample/stage15_11_stage15_summary_report_validation_summary.json
results/logs_sample/stage15_11_stage15_summary_report_validation.csv
results/logs_sample/stage15_11_stage15_summary_report.log
```

## 2. Purpose

This stage does not add another controller feature. It consolidates evidence.

The report separates:

- what has been validated
- what can be claimed
- what cannot be claimed
- which parts are still dry-run or smoke-test only
- how to explain Stage 15 in interviews

## 3. Run

```bash
bash scripts/stage15_11_validate_stage15_summary_report.sh
```

Expected marker:

```text
stage15_11_result: pass
```

## 4. Boundary

The summary explicitly avoids claiming:

- stable locomotion from Stage 15
- full MPC-WBC closed-loop control
- hardware deployment
- ROS torque publisher readiness for hardware
- `torque_enable_ready=True`

## 5. Next Step

After this report passes, update README and the one-page technical report so the public-facing description matches Stage 15 evidence.
