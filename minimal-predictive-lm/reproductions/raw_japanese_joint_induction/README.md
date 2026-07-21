# Raw Japanese Joint Induction 001

This reproduction track asks a narrower upstream question than the main intelligence track:

> Can candidate variables, operations, and goals be induced from raw Japanese dialogue without hand-written slots, task labels, a pretrained LLM, or a problem-specific parser?

It starts from `research/rift-recurrent-feedback-001` / PR #116 and exchanges findings with the main research line through `docs/research/coordination/SHARED_RESEARCH_LEDGER.md`.

## Research basis

The hypothesis combines ideas from several existing lines rather than claiming a complete new intelligence architecture:

- unsupervised grammar induction and latent constituency;
- joint syntax–semantics bootstrapping;
- latent structured alignments and abstract programs;
- minimum-message-length / minimum-description-length program induction;
- controlled shortcut tests for role learning.

Primary references include:

- Portelance, Reddy and O'Donnell, *Reframing linguistic bootstrapping as joint inference using visually-grounded grammar induction models* (2025).
- Zhao et al., *Grammar induction from visual, speech and text* (Artificial Intelligence, 2025).
- Park and Kim, *Probability Distribution Collapse: A Critical Bottleneck to Compact Unsupervised Neural Grammar Induction* (EMNLP 2025).
- Wang, Titov and Lapata, *Learning Semantic Parsers from Denotations with Latent Structured Alignments and Abstract Programs* (2019).
- Sharma et al., *Learning Logical Rules using Minimum Message Length* (2025).
- Wang et al., *The Illusion of Role Separation: Hidden Shortcuts in LLM Role Learning* (ICML 2025).

## Hypothesis: Joint Predictive Anti-Unification

Two utterances are anti-unified into a candidate frame when they share literal structure but contain differing spans. A differing span becomes a variable candidate only when:

1. the frame recurs with multiple distinct fillers;
2. it provides compression;
3. its occurrences have a coherent two-turn future.

From accepted frames, the same generic mechanism induces:

- **variables**: differing spans inside reusable frames;
- **operations**: adjacent frame transitions, including filler carry mappings;
- **goals**: frames that predict a stable near-future outcome such as dialogue termination.

No semantic slot names are supplied. The system never receives labels such as `person`, `location`, `request`, `goal`, or a task/domain ID.

## Real corpus

CI checks out [`nu-dialogue/real-persona-chat`](https://github.com/nu-dialogue/real-persona-chat), a CC BY-SA 4.0 corpus of natural Japanese chat, and runs 16 / 64 / 256-dialogue scales with seeds 1 / 7 / 19. The corpus is not copied into this repository.

## Baselines and counterexamples

- lexical nearest-neighbour continuation;
- grammar-only anti-unification without future constraints;
- joint predictive anti-unification;
- filler replacement with unseen nonce strings;
- shuffled turn order;
- held-out dialogues;
- strict free-Japanese integrated gate.

Metrics include candidate counts, coverage, next-frame accuracy, response bigram Jaccard, rename stability, operation reuse, goal-outcome accuracy, serialized bytes, peak RSS, training time, inference time, and candidate reads.

## Claim boundary

Even a successful frame induction result is not free Japanese intelligence. The model has no open-ended semantic executor or generator. Therefore the strict integrated gate remains failed unless coherent unseen responses, instructions, reading, reasoning, planning, counterfactuals, writing, long dialogue, and continual learning are all demonstrated by the same model.

`highschool_level_passed=false`

`native_japanese_communication_passed=false`

`weak_smartphone_verified=false`

`completion=false`
