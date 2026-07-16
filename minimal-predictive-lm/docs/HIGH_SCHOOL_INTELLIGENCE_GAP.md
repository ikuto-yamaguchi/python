# Japanese high-school intelligence gap

The current SPARC line has demonstrated several bounded sparse mechanisms, but it must not be described as Japanese high-school-level intelligence. The largest remaining gap is not response rendering. It is autonomous representation and learning.

## Confirmed strengths

- bounded sparse retrieval and variable binding;
- explicit world and belief state updates;
- discourse-role and relation induction inside restricted formats;
- causal adjudication inside learned or compiled fragments;
- compositional Japanese response rendering from semantic plans;
- copy-and-reorder schema induction from raw paired turns without semantic slot labels.

## Primary blockers

### 1. Language schema transfer

The raw-pair transducer can discover variables and reuse a learned input/output surface for unseen values. It currently abstains when the same meaning is expressed through a wholly unseen Japanese surface. A high-school-level system must infer that paraphrases, reordered clauses, ellipsis, metaphors, and domain-specific wording can instantiate the same latent operation.

Required gate: train without one paraphrase family and achieve at least 70% exact semantic-plan recovery on the frozen family, with no benchmark-name routing and no target use.

### 2. Autonomous variable discovery

Most successful stages operate after events, entities, relations, duties, normality, quantities, or dialogue slots have already been made explicit by a compiler or a synthetic curriculum. A general learner must propose useful variables from prediction errors and merge equivalent variables across tasks.

Required gate: recover a shared latent relation inventory from raw Japanese documents and conversations, then transfer it to a new domain without new hand-written fields.

### 3. Broad knowledge acquisition and consolidation

The current models contain small generated curricula and bounded task memories, not a broad high-school curriculum. They need continual acquisition from ordinary text, correction without catastrophic interference, provenance, contradiction handling, and selective forgetting.

Required gate: ingest unseen Japanese educational material, answer questions that require combining multiple passages, preserve prior domains, and cite the acquired evidence.

### 4. Unified planning and control

Current capabilities are composed as specialist circuits and ordered fallbacks. A high-school-level agent must choose subgoals, request missing evidence, run tools or calculations, compare alternative plans, and revise a failed plan through one shared controller.

Required gate: solve long tasks whose subtask order is not present in training, under a fixed operation and memory budget.

### 5. Open-ended dialogue grounding

Surface composition is not enough. The model must infer the user's intent, beliefs, uncertainty, emotional context, and desired level of detail; maintain these over long conversations; and correct itself after new evidence.

Required gate: frozen multi-session Japanese dialogues with hidden state changes, corrections, ambiguous references, and explanations scored for factual state, consistency, and calibrated uncertainty.

### 6. Evaluation integrity

A public slice becomes development data after its failures are inspected. Aggregate benchmark accuracy cannot by itself establish general intelligence. Every architecture revision needs a genuinely untouched transfer set, plus adversarial and open-ended evaluation.

## Immediate research order

1. Close HS18 causal V4 with a final untouched tail or reject it.
2. Close HS19 explicit-plan and raw-pair generation gates.
3. Extend HS19 with a frozen unseen-paraphrase transfer gate. Do not add phrase-specific fixes after opening it; if it fails, change the representation learner and freeze a new family.
4. Replace ordered specialist fallback with a learned sparse controller trained from execution traces.
5. Add document-to-latent-schema continual learning before expanding benchmark coverage.

## Claim rule

Do not claim Japanese high-school-level intelligence until all of the following are simultaneously demonstrated on frozen data:

- unrestricted Japanese paraphrase transfer;
- curriculum-scale knowledge acquisition;
- cross-domain reasoning and planning;
- long-dialogue state and correction;
- open-ended generation grounded in internal evidence;
- non-regression under continual learning;
- bounded resource measurements on the target local machine.
