# MECI-001 scope and limits

The executable prototype is a byte-level causal predictor. It merges contexts with identical empirical next-byte distributions and exposes the same state system through a JSONL dialogue interface. It is a real non-neural language machine, but it is not yet comparable in language quality with a large language model.

The working state is a quotient-state index plus the scratch space used by the selected executable program. Once histories merge, this state does not grow merely because the raw transcript grows. This benefit is conditional: the number of operational classes can become very large when the requested capability truly needs many distinctions.

Established related work includes minimum-description-length learning, algorithmic induction, AIXI, time-bounded Kolmogorov complexity, Myhill-Nerode minimization, epsilon machines, predictive-state representations, bisimulation, entropy coding, and active automata learning.

The unverified novelty candidate is the complete combination of a budget-indexed executable-query quotient, finite-class memory-bound attainment, entropy-near-optimal state dispatch, executable counterexamples as refinement certificates, and one non-neural state system used for prediction, answers, planning, and action. If prior work already contains this complete construction and guarantee, the novelty claim must be withdrawn.

The next mandatory experiment uses a public text corpus and reports bits per byte or perplexity, peak memory, training operations, and generation throughput. It must compare against context-tree or PPM methods, n-gram, a small Transformer, and an efficient recurrent or state-space model at matched quality. The same machine must also receive copying, arithmetic, instruction-following, and dialogue tests. If quotient growth or program search removes the resource advantage, MECI must be rejected or fundamentally changed.
