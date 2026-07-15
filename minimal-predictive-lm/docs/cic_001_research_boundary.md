# CIC-001 research boundary

CIC is a non-neural counterfactual intervention compiler. It does not infer semantics by choosing any expression that happens to match one numerical answer. Training traces are converted into executable arithmetic mechanisms and intervention signatures. Japanese quantity mentions are aligned to mechanism roles by local relational evidence. At inference, a sparse mechanism graph is assembled and executed.

The public protocol uses only the first 200 aligned GSM8K/MGSM items for learning. MGSM items 201-250 remain untouched holdout data. English GSM8K solution traces are supervision for the first 200 items only; no rationale or answer from the final 50 may be read during training, model selection, or rule creation.

This is a new project hypothesis, not an established novelty claim. Related work includes expression-tree word-problem solvers, unit dependency graphs, semantic parsing, CEGIS/STUN, causal representation learning, and anti-unification. CIC must differ operationally by using intervention signatures as the learned interface between language relations and executable mechanisms, and by compiling a sparse graph without enumerating all complete programs at inference.

The first gate requires improvement over the rejected FEMI result on the same fixed 200/50 split, while recording model bytes, peak memory, training work, activated mechanisms, and inference work. Passing this gate is not high-school-level intelligence.
