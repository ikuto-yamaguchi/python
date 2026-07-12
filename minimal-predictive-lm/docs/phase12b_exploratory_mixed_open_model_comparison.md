# Phase 12b: exploratory mixed open-model comparison

## Question

Phase 10i showed that a compiled concept program can outperform
SmolLM2-135M-Instruct on one public direct-arithmetic benchmark. Phase 12b asks
a narrower follow-up question: does the result survive when several distinct
micro-capabilities are interleaved and one shared MPM learner is used?

## Protocol

Both systems receive:

- the same 70 benchmark prompts
- the same forty prompt-output demonstrations
- the same output-character limit
- no tools
- deterministic decoding
- the same scorer
- a fresh subprocess resource measurement

The axes are direct arithmetic, state-result calculation, conditional choice,
affine string transformation, string composition, provenance selection, and
event-source extraction.

MPM induces one 11-rule typed program/primitive model. SmolLM2 receives the
forty demonstrations as chat history for every query.

## Why the result is exploratory

The comparison intentionally fails the strict claim gate for two independent
reasons.

First, only the arithmetic axis is a pinned public benchmark. The other six
axes are deterministic synthetic held-out tasks. A model designed while seeing
the implementation could indirectly benefit from those task families even when
exact benchmark prompts are withheld.

Second, MPM receives a structured before/after state trace for four calibration
interactions, while SmolLM2 receives the same prompts and scalar outputs but not
the internal state delta. The delta is redundant for the scalar answer in this
micro-suite, but the evidence structures are still not identical.

Consequently, neither strict quality parity nor runtime Pareto is authorized.
The measurements are useful diagnostics, not a general superiority result.

## Result interpretation

MPM solves all 70 tasks after compiling the demonstrations into 892 bytes.
SmolLM2 solves 25 tasks. The open model matches MPM on event-source extraction
and provenance selection, is partial on conditions, composition, and direct
arithmetic, and fails the synthetic affine transform and state-result slices.

This indicates that explicit induction and compilation are effective when a
small executable hypothesis explains a task family. It does not show that the
same mechanism handles unrestricted language, latent world knowledge, long
reasoning chains, code repositories, or natural generation.

## Resource interpretation

The reference SmolLM2 runner rereads a long shared demonstration prefix for
every benchmark item. It does not reuse prefix KV state. Therefore the observed
40.28× wall-time ratio is not a lower bound for optimized transformer serving.

Conversely, MPM's fresh worker re-runs induction, and the 108,238 candidate
evaluations are not hidden. A deployed compiled model could omit induction, but
a lifetime comparison must include it and compare it with the amortized cost of
LLM pretraining and adaptation.

## Next evidence gate

The next comparison should be a fully public multi-domain raw-input suite with
pinned source revisions and licenses. It should be evaluated before adding
benchmark-specific repairs. Expected failures should be preserved and used to
drive representation invention.

A useful next suite should include at least:

- direct arithmetic
- multi-step quantitative reasoning
- symbolic or boolean reasoning
- state or temporal tracking
- string/sequence transformation
- retrieval or grounded knowledge

Only after the whole manifest is public and evidence visibility is matched may
the public multi-domain quality gate be considered.
