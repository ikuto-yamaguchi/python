# RESET-E021 — R0 Research Reconstruction Integration

Date: 2026-07-25

## Scope

This integration keeps all work on `research/intelligence-swarm-reconstruction-001`. No new toy mechanism, architecture family, memory/replay/fast-weights/sleep/forgetting path, researcher-authored SILG intervention ontology, stacked branch or successor PR is created.

Existing stacked drafts remain negative-results archives only.

## Integrated evidence

### R0.1 public SILG/RTFM baseline

The latest completed and accepted evidence remains the official SILG `multi` recurrent at 32,768 requested frames for seeds `1,7,19`.

- parameters: `4,916,915`
- state-dict audit: `19,694,385 bytes`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind / State-only / Language-shuffle: `0.0167` each

Correct remains below Random. The result is insufficient policy competence, not evidence that language is unnecessary.

The 131,072-frame reproduction has no verified completed artifact at the current canonical head. Earlier attempts were stopped by a fixed harness timeout or repeatedly restarted by workflow triggers. Timeout scaling, concurrency and trigger scope have been corrected. No incomplete value is recognized.

### R0.2 Environment-first faithful transfer

Cycle 010 adds a typed SILG policy-trajectory exporter compatible with the fail-closed Gaddy & Klein-style full-method path.

The exporter preserves typed state fields, schema, categorical cardinalities, episode/seed/split/fingerprint provenance, dataset SHA-256 and schema SHA-256. Text, reward, done and post-treatment outcomes are excluded from environment state. Unknown fields or cardinalities are rejected rather than inferred from evaluation data.

The faithful structured-message baseline and typed exporter are implemented but not qualified or executed on competent three-seed trajectories. Current classification:

`typed_discrete_message_and_typed_export_paths_implemented_execution_blocked`

### Evaluation contract

D017 adds exact canonical-seed coverage at every `domain × split × condition` cell. Each evaluation cell must contain exactly seeds `1,7,19`; missing, extra and noncanonical seeds fail closed. A lightweight evaluation-only workflow was added so contract tests do not restart expensive SILG training.

D016/D017 workflow completion is not verified at the current head, so the confirmed passing-test count remains D015's 18. Real outcome-shuffle predictions, target-label-shuffle predictions or a formal inapplicability record, immutable serialized test data, complete six-method artifact joins and a competent baseline remain absent.

Classification remains:

`initial_reproduction_failure`

### Prior-art and RQ-001 boundary

C014 integrates general-environment causal representation learning and subset-intervention causal-abstraction boundaries.

Unknown targets, incomplete environment labels, nonlinear latent dynamics or nonparametric observation mixing do not by themselves make language necessary. Under sufficient environment changes, non-language CRL can already identify broad latent causal structure. When interventions are insufficient, the remaining object must be stated as a residual causal abstraction.

If

`L ⟂ M | X,E`

or equivalently

`I(M;L | X,E)=0`,

language cannot refine the causal equivalence class left by non-language observations. Language-shuffle degradation, environment classification, semantic naming and finite-sample prediction gains are not population-level identifiability guarantees.

RQ-001 is narrowed to one unadopted candidate: after exhausting general-environment statistics, language must provide an independent separating relation that strictly refines a formally specified residual causal abstraction on unseen utterance forms and intervention compositions.

No implementation is authorized before public baseline reproduction and preregistration.

## Current decision

- learned external public capability baseline: `0`
- formal R0.2 reproduction: `0`
- R0.3 empirical track: rejected
- broad RQ-001: rejected
- residual-abstraction refinement: narrowed, not adopted
- novelty: not established
- intelligence principle: none
- capability progress: not recognized
- high-school-level intelligence: not achieved

## Single P0

Launch and finish exactly one clean 131,072-frame official recurrent run from the stable workflow head, verify all three checkpoints and immutable artifacts, then run matched controls and policy-competence/anti-collapse checks.

Until that passes, R0.2 tuning, new architecture and RQ-001 implementation remain forbidden.

## Stage transition

No next stage is proposed. Transition remains blocked until R0.1–R0.3 disposition, immutable three-seed controls, qualified typed R0.2 online comparison, complete novelty matrix and exactly one preregistered successor claim are all present.
