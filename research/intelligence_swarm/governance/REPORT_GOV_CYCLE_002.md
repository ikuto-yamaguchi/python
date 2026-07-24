# Governance Cycle 002 — Symmetry-Breaking Witness Grounding

## Decision

**CONTINUE S1 / FREEZE HF-005 / PROMOTE AF-003**

Semantic Identity Gate G1は未達のため、段階遷移は行わない。PR349/350により、behavioral equivalence単独でindividual identityを定義する仮説族を凍結し、trajectory continuity・不可逆痕跡・個体履歴などのsymmetry-breaking witnessをraw Japaneseへ接地するAF-003を最優先本線へ昇格する。

## Inputs reviewed

- coordination branch: `STATE.md`, `BACKLOG.md`, `EVIDENCE.jsonl`, `governance/`
- governance reset: PR348
- C causal identifiability: PR349
- D memory eligibility: PR350
- stale pre-governance A/B proposals: PR346, PR347
- frozen evidence base: PR316–345

## External capability evidence only

### PR349 — causal identifiability limit

| protocol | remaining world automorphisms |
|---|---:|
| passive transition | 12.00 |
| random repeated transitions | 1.67 |
| object swap interventions | 48.00 |
| object + value interventions | 48.00 |
| exhaustive symmetric interventions | 144.00 |

Interpretation: intervention coverage does not guarantee individual identity. Symmetric intervention can preserve or enlarge the automorphism class. Behavioral equivalence identifies causal roles, not individuals.

### PR350 — witness eligibility pilot

| evidence | acquisition | after 96 interference episodes |
|---|---:|---:|
| behavior only | 0.0000 | 0.0000 |
| trajectory continuity | 0.9663 | 0.8333 |
| irreversible scar | 1.0000 | 1.0000 |
| joint witness | 1.0000 | 1.0000 |
| shuffled joint identity | 0.0236 | n/a |

Interpretation: Correct–shuffle gap is large and external, but limited to a synthetic observation-side re-identification pilot. Raw Japanese was not used as a retrieval key; therefore this does not pass G1.

## Hypothesis-family decisions

### Frozen

- HF-001 Surface Span First
- HF-002 Compression Creates Meaning
- HF-003 Memory Before Re-identifiable Semantics
- HF-004 Constraint/Graph Repair Creates Meaning
- **HF-005 Behavioral Equivalence Alone Defines Individual Identity**

### Continued with reduced scope

- AF-001 is retained only for causal-role equivalence, not individual identity.
- AF-002 active identifiability remains supporting work, but symmetric query repetition is insufficient.

### Promoted

- **AF-003 Symmetry-Breaking Witness Grounding**

## Maximum upstream bottleneck

The remaining bottleneck is not whether an individual is observable in principle. The pilot shows that it can be, when trajectory or irreversible traces exist. The bottleneck is whether raw Japanese utterances can become bound to that witness-bearing unit without handwritten slots, fixed ontology, string retrieval, RAG or an external LLM, and whether the same unit can be regenerated across held-out paraphrase, rename and domains for both prospective prediction and inverse query.

## Reassignment

- A: form witness-bearing units from Japanese–trajectory/scar synchrony; held-out paraphrase and rename are mandatory.
- B: do not resume surface grammar. Generate operation/goal counterexamples conditioned on correct vs incorrect witness identity.
- C: test necessity and sufficiency of trajectory, scars and history under automorphisms, cross-domain transfer and counterfactual worlds.
- D: keep memory optimization frozen. Maintain eligibility and acquisition/retention separation until raw-Japanese grounding passes.
- E: define a common G1a benchmark and prevent synthetic identifiability from being reported as semantic identity.

## Required next common benchmark

At least 3 seeds with identical samples across:

- correct synchrony
- time-shuffled trajectory
- shuffled irreversible scar
- identity shuffle
- behavior-only
- surface-only
- random

Held-out conditions:

- paraphrase
- rename
- unknown word order
- subject omission
- multi-paragraph
- free Japanese
- cross-domain twins

Required tasks:

- prospective target selection
- inverse identity query
- support movement after target swap
- twin-object discrimination
- selective witness lesion

## Resource and safety interpretation

PR349 used 0 learned bytes, 0.1717 seconds total and 109,476 KiB peak RSS. PR350 estimated 1,920 bytes for 48 records, approximately 40 bytes per episode, 0.901 seconds total, 60.16 microseconds estimated matching latency and 161,120 KiB peak RSS. These pilots fit the sub-1GB constraint, but weak-smartphone hardware remains unverified. Final identities were evaluation-only and answer leakage was not reported.

## Status

- Stage: S1 Semantic Identity Birth — **continued**
- G1a identifiability prerequisite: **limited synthetic support**
- G1 Semantic Identity Gate: **not passed**
- Memory/consolidation mainline: **frozen**
- High-school-level intelligence: **not achieved**
- Native Japanese communication: **not achieved**
- Weak smartphone verification: **not achieved**
- Completion: **false**
