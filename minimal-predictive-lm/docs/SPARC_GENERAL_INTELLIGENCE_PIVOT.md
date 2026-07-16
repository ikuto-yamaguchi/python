# SPARC general-intelligence pivot

## Why the current path was insufficient

The original goal is a resource-efficient model with broadly useful Japanese high-school-level intelligence. The research drifted into capability accretion: causal judgement, reference resolution, belief state, discourse roles, and response composition were added as bounded specialist mechanisms. Those mechanisms are useful evidence about sparse computation, but they do not by themselves imply a route to general intelligence.

The missing argument was never established:

> Why should adding more bounded specialist circuits produce a learner that autonomously discovers representations, transfers them across domains, acquires broad knowledge, and plans under novelty?

No experiment demonstrated that implication. Continuing to add specialists without testing it was therefore not a justified path to the stated objective.

## Root research error

The project optimized downstream competence before validating the upstream learner.

Existing stages are strongest when one or more of the following have already been supplied:

- event and entity boundaries;
- task-relevant variables;
- relation types;
- semantic slots;
- synthetic curricula expressing the desired latent structure;
- routing order among specialist modules.

A generally intelligent learner must infer or revise those structures from raw experience. It must also reuse them when the surface form, domain, objective, and required subtask order change. That capability has not yet been demonstrated.

## Revised central hypothesis

General intelligence will not be pursued as a collection of task solvers. The central object of study is now a **shared predictive latent-program learner** with four coupled operations:

1. **Segment** raw streams into candidate entities, events, relations, quantities, goals, and discourse acts.
2. **Compress** repeated predictive structure into reusable latent programs.
3. **Compose** latent programs to predict, explain, answer, and act in unseen combinations.
4. **Revise** the latent inventory when prediction errors cannot be explained by existing programs.

Language, mathematics, causal reasoning, dialogue, and planning must be learned as different observations and executions of this shared latent-program system rather than as independently routed benchmark modules.

## Architectural requirements

### Shared latent workspace

One sparse workspace must represent observations, beliefs, hypotheses, goals, uncertainty, and intermediate results. Specialist representations may exist only as learned subgraphs or programs inside this workspace, not as a hand-ordered fallback chain.

### Structure induction objective

Training must reward all of the following simultaneously:

- predictive accuracy;
- minimum description length;
- reuse across examples and domains;
- calibrated uncertainty;
- bounded active compute;
- preservation of previously useful programs;
- successful composition on held-out structures.

### Program proposal and consolidation

When prediction fails, the learner must propose edits such as:

- introduce a variable or relation;
- split an overloaded concept;
- merge equivalent concepts;
- add a conditional or temporal dependency;
- introduce a reusable subprogram;
- retire a program whose predictive value has disappeared.

Candidates are tested against replayed prior experience and untouched transfer data before consolidation.

### Learned controller

Problem decomposition, memory retrieval, calculation, external-tool use, explanation, and verification must be selected by a learned controller from execution traces. The controller may abstain or ask for missing evidence. Fixed task-name routing is forbidden.

### Continual knowledge acquisition

The model must ingest ordinary Japanese educational text and dialogue, retain provenance, reconcile contradictions, and answer through retrieved internal evidence. Public benchmark answers must never become training targets after inspection.

## Immediate falsifiable experiments

### Experiment A: unseen paraphrase-family transfer

Train on several Japanese realizations of latent operations while withholding an entire paraphrase family. Recover the correct latent program and arguments from the frozen family.

Pass condition:

- at least 70% exact latent-plan recovery;
- at least 80% selective accuracy;
- no task-name routing or frozen-target use;
- bounded active reads independent of corpus size.

Failure implication: surface-schema induction is insufficient; do not add phrase handlers. Replace the representation learner.

### Experiment B: cross-domain latent reuse

Train a latent relation using one domain, then test the same hidden operation in a different domain with different vocabulary and surface order.

Pass condition:

- improvement over lexical retrieval and nearest-template baselines;
- no new domain-specific fields;
- retained performance on the source domain.

Failure implication: the representation is not abstract enough to support general intelligence.

### Experiment C: autonomous variable proposal

Provide raw sequences whose best compression requires discovering an unlabelled state variable or relation. Compare a fixed-inventory learner with a learner allowed to propose variables.

Pass condition:

- lower held-out predictive description length;
- recovered intervention-relevant variable;
- transfer to a changed observation encoding.

Failure implication: the project has not solved the central missing mechanism.

### Experiment D: continual curriculum acquisition

Sequentially ingest Japanese material from mathematics, science, history, and everyday reasoning without explicit task labels.

Pass condition:

- multi-passage questions answered from acquired evidence;
- provenance returned;
- less than 5% regression on previous domains;
- contradictions revised rather than appended blindly.

### Experiment E: controller generalization

Train on tasks requiring known primitive operations in some orders; test new tasks requiring a previously unseen order and stopping condition.

Pass condition:

- successful decomposition and execution on at least 70% of frozen tasks;
- no memorized full action trace match;
- operation and memory budgets reported.

## Stop rules

The following no longer count as progress toward the main claim by themselves:

- improving one public benchmark axis;
- adding another hand-written semantic field;
- adding a new specialist fallback;
- generating fluent text from human-supplied semantic slots;
- succeeding only when train and test share the same surface schema;
- increasing code volume without a frozen transfer improvement.

A stage counts as main-line progress only when it improves autonomous representation, transfer, continual acquisition, or learned control on untouched data.

## Integration policy

HS18 and HS19 remain bounded supporting experiments and must be closed as pass or fail. Their useful mechanisms may later become learned programs inside the shared workspace. They are not the architecture of the final intelligence model.

No HS20 capability module should be added until the first latent-program experiment is implemented and evaluated. The next main research branch must target Experiment A and Experiment C rather than another benchmark specialist.

## Claim boundary

There is currently no validated path from the existing specialist stack to Japanese high-school-level intelligence. The revised hypothesis above is a research direction, not a guarantee. It becomes a credible path only if the falsifiable experiments demonstrate cross-surface, cross-domain, and continual transfer under bounded resources.
