# Stage 18.3: Velocity Comparison Analysis

## 1. Goal

Stage 18.3 converts the Stage 18.2 velocity rollout evidence into a clear comparison analysis.

This stage exists to prevent over-claiming. It separates two claims:

- stability boundary: both baseline and candidate pass;
- velocity tracking: baseline is better in the current Stage 18.2 evidence.

## 2. Result

Stage 18.3 result: pass

Failure count: 0

## 3. Comparison

| metric | baseline | candidate | candidate_minus_baseline | interpretation |
| --- | --- | --- | --- | --- |
| mean_vx | 0.131362 | 0.066640 | -0.064722 | candidate slower than baseline |
| mean_abs_velocity_error | 0.078494 | 0.147469 | 0.068975 | candidate worse velocity tracking |
| forward_displacement | 0.630505 | 0.319838 | -0.310667 | candidate lower displacement |

## 4. Conclusion

The Stage 18.2 candidate injection case remains stable but does not improve velocity tracking. At target_vx=0.2 m/s, the baseline has higher mean_vx, lower mean_abs_velocity_error, and larger forward displacement.

## 5. Supported Statement

The project can state:

    Stage 18 adds simulation-only velocity evidence. In the current target_vx=0.2 m/s test, both baseline and low-scale MPC/WBC candidate injection pass stability and safety checks, but the baseline has better forward velocity tracking.

## 6. Unsupported Statement

The project cannot state:

    The low-scale MPC/WBC candidate improves velocity tracking over the baseline.

## 7. Claim Boundary

This is simulation-only evidence based on finite-difference velocity from qpos[0]. It is not hardware execution, not a full MPC-WBC velocity controller, and not proof that MPC/WBC comprehensively outperforms the baseline.
