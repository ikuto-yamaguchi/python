# R0-D Cycle 055 — direct core optional-metric coverage

`evaluation_contract.score()` now rejects partial `gold_inverse`, selective per-method `pred_inverse` omission, and prediction-only inverse output. Inverse cell means, confidence intervals, minimum-cell gaps, and paired tests are emitted only after complete same-instance coverage across all six registered methods.

Scope is R0 reproducibility/statistics/leakage auditing only. No memory, replay, fast weights, sleep, forgetting, or new mechanism was added. Any violation is `initial_reproduction_failure`; no real R0 reproduction is accepted by this change alone.
