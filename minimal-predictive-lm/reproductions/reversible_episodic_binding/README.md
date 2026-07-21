# Reversible Episodic Binding

## Hypothesis

Store episode-specific surface atoms only in a reversible local binding channel and learn only equality-preserving relation-position schemas. This should permit transfer across total renaming without storing names or values in long-term knowledge.

## Guardrails

- no Transformer or neural network
- no task/ability classifier
- no RAG or external model
- no answer candidate search
- no completed-answer memory
- no exception-word patching
- one schema learner and one readout path across memory, location, causal and plan episodes

## Experiment

- 96 / 384 / 1536 training episodes
- seeds 1 / 7 / 19
- lexical suffix baseline versus reversible binding
- unseen names and values by total vocabulary rename
- location and causal transfer
- `反転` decoy requiring value transformation
- an answer value never observed in the episode
- planning and strict nine-case free-Japanese gate
- model bytes, peak RSS, train and inference time, candidates, reads and schema count

## Local result at 1536 episodes, three-seed mean

| Method | In-domain memory | Total rename | Location rename | Causal rename | Plan | Transform decoy | Unseen value | Free gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical suffix | 0.2222 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1481 |
| reversible binding | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Resources for reversible binding:

- serialized schema model: 407 bytes
- process peak RSS: about 288,796 KiB including Python and NumPy
- training: about 0.093 seconds
- inference: about 0.0119 ms/query
- mean candidates: 0.857
- mean schema/transaction reads: 14.34
- learned schemas: 7

## Interpretation

Supported only in a narrow sense:

- relation-position schemas can be reused across completely unseen names and values;
- episode-specific surfaces can be recovered without placing those surfaces in long-term knowledge;
- abstraction and instance identity need not be collapsed into the same representation.

Falsified as a general intelligence principle:

- it cannot generate an answer value that was not previously observed in the episode;
- it cannot perform a learned or novel transformation such as `反転`;
- it does not induce plans;
- the strict free-Japanese integrated gate remains zero;
- success is reversible reference, not semantic language generation.

`highschool_level_passed=false`

`native_japanese_communication_passed=false`

`weak_smartphone_verified=false`

`completion=false`

## Next bottleneck

The missing mechanism is not another role cluster or copy heuristic. A shared system must compose transformations over bound variables, create previously unobserved values or descriptions, and realize the result in Japanese while preserving the reversible link to episode entities. This must be learned from ordinary sequences rather than supplied as operation-specific code.
