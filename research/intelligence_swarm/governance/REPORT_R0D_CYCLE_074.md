# R0-D Cycle 074 — normalized cell identity core integration

`evaluation_contract.py` now canonicalizes domain and condition labels before
dataset topology, shuffle donor checks, score grouping, instance fingerprints,
confidence intervals and paired tests. Unicode width/case, whitespace and
condition token order/delimiter aliases cannot create separate evidence cells.

Distinct raw labels that collapse to the same canonical label are rejected
fail-closed. Any failure remains classified as `initial_reproduction_failure`.
