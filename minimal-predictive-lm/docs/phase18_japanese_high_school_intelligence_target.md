# Phase 18 target: Exceeding a strong Japanese high-school student

## Operational target

The phrase "strong Japanese high-school student" is made testable rather than used
as a vague aspiration. The engineering target is performance comparable to or above
a top-decile general academic student across the current Japanese high-school
curriculum, while preserving transfer, calibration, and resource accounting.

This is an intermediate target on the route toward broad open-model parity. Passing
one entrance examination or one subject is insufficient.

## Capability domains

The frozen evaluation matrix must cover at least:

1. Japanese language
   - modern expository and literary reading;
   - argument structure, implication, reference, and ambiguity;
   - classical Japanese and kanbun at curriculum level;
   - concise written explanation and evidence-based composition.
2. Mathematics
   - Mathematics I, A, II, B, III, and C;
   - algebra, functions, geometry, probability, statistics, sequences, vectors,
     limits, differentiation, and integration;
   - proof, counterexample, modeling, and multi-step calculation.
3. English
   - reading, listening-transcript understanding, grammar in context, translation,
     summarization, and short composition.
4. Science
   - physics, chemistry, biology, and earth science;
   - experiment interpretation, dimensional reasoning, graph reading, and causal
     explanation.
5. Geography, history, civics, and economics
   - source comparison, chronology, maps and statistics, institutional reasoning,
     and evidence-constrained claims.
6. Information
   - algorithms, data representation, networks, databases, security, statistics,
     simulation, and small-program reasoning.
7. Cross-domain work
   - long-document synthesis;
   - planning and error correction;
   - unfamiliar notation and newly taught rules;
   - explanation of uncertainty and calibrated abstention.

## Primary pass gate

A campaign may claim the target only if all of the following hold on a prospectively
frozen suite:

- at least 80% aggregate score;
- at least 70% in every capability domain;
- at least 75% on newly authored or procedurally generated items unavailable during
  development;
- at least 70% on written-response items graded by a rubric blind to model identity;
- no domain gains produced by sacrificing previously passed domains by more than two
  percentage points;
- error detection and correction on at least 80% of deliberately flawed solutions;
- calibration error and abstention quality reported, not hidden by forced answers;
- matched tool conditions and separate tool-free and tool-assisted scores.

The numeric thresholds are project gates, not claims about a measured national
percentile until a human comparison study is run.

## Anti-shortcut design

The suite must prevent test-specific classification from masquerading as general
intelligence.

- Lexical and formatting cues are balanced across answers.
- Entity names, numbers, units, diagrams, and surface templates shift between train
  and evaluation.
- Each major concept appears in unseen combinations with concepts from another
  domain.
- Some questions share surface form but require different operations.
- Some questions use different surface forms for the same latent operation.
- Public examination questions are supplemented by fresh isomorphic and adversarial
  variants.
- Exact-match memorization, retrieval-only, bag-of-words, finite-state, and compact
  neural baselines are reported.
- Hidden test authors do not inspect model failures before freezing the final set.
- Task and subject names are hidden from the model where they are not intrinsically
  part of the question.

## Required evaluation layers

### Layer A: curriculum competence

Subject-specific questions establish that the system has the required declarative
and procedural knowledge.

### Layer B: systematic transfer

New vocabulary, changed notation, paraphrases, unseen compositions, and reordered
premises test whether acquired structures are reusable.

### Layer C: interactive learning

The system receives a short lesson defining a genuinely new notation, law, or
micro-world and must solve held-out problems without parameter retraining.

### Layer D: explanation and verification

Answers must include checkable intermediate claims where appropriate. Independent
verifiers score equations, citations to supplied sources, causal links, and final
answers separately.

### Layer E: practical work

The system must inspect a small code repository, diagnose a failing test, propose a
minimal patch, and explain the regression risk. It must also analyze tables and
multi-page Japanese documents.

## Resource accounting

For every score, report:

```text
persistent learned bits
+ fixed front-end/runtime bits
+ knowledge-store bits
+ retrieval index bits
+ peak working memory
+ induction operations
+ inference operations
+ latency and energy proxy
```

External tools and indexes are not free. Tool-free and tool-assisted systems are
separate tracks.

## Critical-path entry conditions

The former Phase 18a–18d component sequence is retained as evidence, but it is no
longer sufficient evidence of movement toward this target. Before an HSS campaign
may begin, the project must pass:

1. `CAP-GEN-001`: one frozen axis-blind worker measured on the integrated 15-axis
   public reality suite;
2. `CAP-GEN-002`: at least 50% aggregate, at least 20% on every public axis, and
   transfer to prospectively frozen axes without task-specific handlers;
3. `CAP-GEN-003`: at least 60% aggregate and 40% per domain on one checkpoint jointly
   covering natural Japanese, mathematics, science, code, and newly taught rules.

These are entry conditions, not substitutes for the full HSS gate.

## Development sequence

### CAP-GEN-001: integrated reality baseline

Freeze the current complete worker and expose the actual cross-domain score. Do not
improve individual axes before the baseline is recorded.

### CAP-GEN-002: shared representation and learning objective

Train one shared latent sequence/event model and generic execution library. Reject
linear growth in task handlers, parsers, and routing descriptions.

### CAP-GEN-003: natural curriculum integration

Jointly train and test Japanese reading, mathematical language, science experiments,
code, and unfamiliar taught rules in one model state.

### HSS-001: integrated frozen examination

Run the full multi-domain suite only after the general-learning entry conditions are
met. Reserve a final unseen examination and shifted practical task set for forecast
validation.

## Forecast rule

A calendar estimate is forbidden until two consecutive major architecture iterations
raise both CAP-GEN aggregate accuracy and the minimum-axis floor. Prior to that,
calendar claims are speculation. Three major iterations with less than fifteen total
aggregate percentage points of improvement force abandonment of the current core
architecture.

## Claim boundary

Until every primary pass gate is satisfied, the project may report progress on
individual mechanisms but must not claim Japanese high-school-level intelligence.
Passing public multiple-choice questions alone is explicitly insufficient.
