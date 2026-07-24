# Causal Grounding Cycle 010

## Hypothesis

**Episode-Local Syntax Orbit Restores Causal Candidate Support**

PR #388 mixed prefix, suffix, interleave and reverse utterance order inside one dataset, while each candidate hypothesis required one global form for every utterance. Therefore the true causal mapping was absent from the candidate version space in two of three seeds. This cycle tested whether syntax order must remain an episode-local nuisance orbit while target mapping, operation mapping and arity are constrained by external intervention outcomes.

## Design

- Base: global-form candidate family inherited from PR #388.
- Local Active: form is marginalized per episode; active witness maximizes prediction partition entropy.
- Local Random: same supported candidate family, random witnesses.
- Argument shuffle: destroys target argument links after calibration.
- Outcome shuffle: destroys witness/outcome correspondence.
- 4 opaque targets, 4 opaque operations, mixed order utterances.
- 5 calibration witnesses, 3 seeds.
- Final evaluation uses only before + command.

No final-test outcome, completed trajectory, dictionary, shared ID, RAG or external LLM is used for selection or prediction.

## External measurements

| Method | True support | Prospective | Inverse | Repair | Mixed order | Counterfactual |
|---|---:|---:|---:|---:|---:|---:|
| Global form | 0.3333 | 0.2188 | 0.2292 | 0.2188 | 0.2424 | 0.2188 |
| Local Active | **1.0000** | **0.9583** | **1.0000** | **0.9531** | **0.9427** | **0.9740** |
| Local Random | **1.0000** | **0.9583** | **1.0000** | **0.9531** | **0.9427** | **0.9740** |
| Argument shuffle | 0.3333 | 0.5052 | 1.0000 | 0.5208 | 0.4831 | 0.5156 |
| Outcome shuffle | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Decision

**The candidate-support diagnosis is supported, but capability progress is not recognized. G1 and G2 remain unmet.**

Allowing episode-local syntax orbit restores the true causal hypothesis in all three seeds and produces large Correct-vs-global/outcome-shuffle gaps. Argument-link shuffle selectively destroys prospective and counterfactual target use while leaving operation inverse recognition high, confirming that the recovered mapping is not only a global output-frequency artifact.

However, Local Active and Local Random are exactly tied. The result therefore does not demonstrate superior intervention selection. It shows that PR #388's destructive over-pruning was caused primarily by a misspecified global syntax type, not by insufficient entropy optimization.

This is still an oracle upper-bound experiment. Opaque object and operation character classes, the target/operation factorization, the operation family and the arity multiset are supplied. Natural free Japanese, subject omission, multi-paragraph discourse and genuinely unknown relation arity are not solved.

## Returns to other tracks

- **A:** Keep wording/order as an episode-local nuisance orbit until external outcomes justify a shared semantic boundary. Do not force one global segmentation/order template.
- **B:** Candidate support must be audited before active pruning. A selector must not compare structures in a family that excludes the true mixed-order parser.
- **D:** No formal memory-eligible unit. The result is an oracle-supported causal mapping, not raw-language semantic acquisition.
- **E:** AF-010 may continue, but `one_global_surface_structure_per_semantic_unit` should be rejected as a lower-level premise.

## Next bottleneck

The next causal question is whether two disjoint witness sets independently reconverge on the same mapping when syntax order is local **and** the learner must choose between zero/unary/binary argument structures without oracle character-class membership.

## Resources

- Candidate hypotheses: 6,912 local / 27,648 global.
- Surviving model: 78 bytes mean for Local Active.
- Peak RSS: 164,324 KiB including Python runtime.
- Three-seed local run: about 9.20 seconds.
- 1 GB constraint: passed.
- Weak smartphone device: not verified.

## Status

- Semantic Identity Gate G1: not passed.
- Operation/Goal Gate G2: not passed.
- High-school-level intelligence: not achieved.
- Native Japanese communication: not achieved.
- Completion: false.
