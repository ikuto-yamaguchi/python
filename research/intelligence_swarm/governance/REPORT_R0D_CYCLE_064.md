# R0-D Cycle 064 — normalized holdout identity in the core contract

`evaluation_contract.py` now canonicalizes entity and dynamics split identities before hashing.

Fail-closed normalization covers recursive mappings/sequences, Unicode NFKC, case folding,
whitespace/control/format removal, and numeric-vs-string scalar aliases. Therefore width,
case, invisible characters, or JSON scalar representation cannot make a train identity appear held out.

Focused regressions cover full-width/case aliases, invisible-space aliases, numeric/string aliases,
structured dynamics aliases, a rejected explicit holdout reuse, and a genuinely distinct holdout.

No memory, replay, fast weights, sleep, or forgetting mechanism was added. No public baseline or
real R0 bundle is accepted by this change. Unmet reproduction evidence remains classified as
`initial_reproduction_failure`.
