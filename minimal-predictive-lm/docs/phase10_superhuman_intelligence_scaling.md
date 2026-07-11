# Phase 10 theory: can the minimum-resource machine become superhuman?

## 1. The target must be defined without rhetoric

"More intelligent than humanity" is not a scalar property unless a task
distribution, information interface, time horizon, risk tolerance, and resource
budget are specified.

For a machine family `A`, task distribution `D`, and lifetime budget `B`, define
the attainable frontier

```text
F_A(B,D) = sup expected utility over systems whose lifetime cost is within B.
```

The cost vector is not only parameter count:

```text
static bits
+ dynamic bits
+ reads and writes
+ primitive operations
+ external effects
+ data acquisition
+ induction / training
+ verification
+ migration
+ rollback
```

A system is superhuman on `D` only when it exceeds a well-defined human
reference on quality, reliability, breadth, or speed under a stated comparison.
The project should report a Pareto frontier rather than hide trade-offs inside
one arbitrary weighted sum.

## 2. Why the current direction could exceed humans

A fixed finite machine cannot contain unlimited knowledge or solve every task.
An open-ended family can nevertheless exceed human performance on increasingly
broad task distributions by combining several advantages.

1. **Exact cumulative memory.** Knowledge can be retained with provenance and
   indexed without biological forgetting.
2. **Fast compiled skill.** Expensive discovery can be performed once and
   compiled into a small decision program.
3. **Parallel hypothesis testing.** Independent candidate models and tests can
   be evaluated concurrently when the value of computation is positive.
4. **Active experiment design.** The machine can choose observations that most
   reduce decision regret instead of passively consuming data.
5. **Cross-domain reuse.** A causal operation learned in code, conversation, or
   tool use can share one representation rather than being relearned.
6. **Representation invention.** When the current state language collapses
   situations requiring different actions, the machine can introduce a new
   predicate, role, edge, macro, or latent variable.
7. **Verified self-modification.** The learner, compiler, index, and planner can
   be replaced when the replacement passes held-out, shifted, adversarial, and
   rollback tests and repays its lifetime cost.

These advantages make superhuman performance possible in principle on many
defined domains. They do not imply omniscience, universal optimality, or free
knowledge.

## 3. Representation insufficiency is the central failure detector

Let `phi(h)` map history `h` to the active internal state. If two histories map
to the same state but have different optimal actions, no policy using only that
state can be optimal on both histories.

```text
same active state
+ different required action or future prediction
= representation collision
```

The machine must then consider actions such as:

- split a state;
- add a relation or argument role;
- create a hierarchical event node;
- introduce a latent cause;
- preserve an additional observation;
- change the temporal abstraction;
- create a reusable option;
- or query for information.

Phase 9b is a small instance of this principle. A single operation label could
not represent an `EMIT` speech act whose content was a `VERIFY(test=PASS)`
proposition. The event graph removes the collision.

## 4. Representation invention must itself be resource-rational

A richer language is not automatically better. Accept a proposed
representation change only when:

```text
expected reduction in decision loss
+ expected runtime saving
+ expected future induction saving
>
invention + storage + migration + verification cost
```

For a reusable compiled option with per-use saving `delta`, promote it when:

```text
number of future uses * delta
>
discovery + program + verification + migration cost
```

Phase 9b's synthetic benchmark gives a break-even of five reuses for the event
graph under its explicit loss scale. That number is not universal; the gate is.

## 5. Learning is only one route to intelligence acquisition

The architecture should combine:

- statistical updating from repeated outcomes;
- one-shot symbolic instruction;
- deduction from existing rules;
- active experimentation;
- analogy and program transformation;
- external retrieval;
- search over candidate programs;
- and representation invention.

All are state transitions in the same substrate. "Learning" should not be a
special dense weight-update ritual. It is any verified change that improves the
lifetime frontier.

## 6. Candidate generation matters as much as selection

A perfect selector over a weak candidate set remains weak. The action space
must include meta-actions:

```text
generate a candidate
invent a new action
change representation
decompose a goal
compile a repeated sequence
request evidence
construct a test
```

Progressive widening should allocate more candidate-generation compute only
when the expected value of a new candidate exceeds its cost. This is essential
for creativity, theorem discovery, scientific hypotheses, and novel code.

## 7. Self-improvement without uncontrolled bloat

A proposed successor should not replace the current system merely because it
performs better on the examples that created it. A change is accepted only when
a conservative improvement bound remains positive after subtracting:

- extra lifetime resources;
- distribution-shift risk;
- irreversible-risk cost;
- verification and migration cost.

Required evidence includes:

- held-out tasks;
- distribution shifts;
- adversarial counterexamples;
- ablation of the new component;
- lifetime resource accounting;
- reproducibility;
- rollback state;
- comparison with the best retained predecessor.

Several Pareto-optimal predecessors should remain available when uncertainty
is material. This avoids one-way local commitment.

## 8. What cannot be optimized away

The following lower bounds remain even for a superhuman machine.

- New independent facts require information to enter through observation,
  instruction, or retrieval.
- Some causal processes require sequential steps.
- Exact optimal planning is intractable or uncomputable in sufficiently general
  worlds.
- An objective cannot be inferred uniquely from no evidence.
- Value conflicts and long horizons cannot always be compressed into one
  objectively correct scalar.
- Verification of powerful self-modifications may be as hard as the task itself.
- Adversarial or non-stationary environments can invalidate old abstractions.

The honest target is low regret and expanding competence under explicit
budgets, not a claim of universal perfection.

## 9. Architecture implied by the theory

```text
raw observations / language / code / tools
        ↓
sparse hierarchical event graph
        ↓
decision-sufficient belief state + provenance
        ↓
causal prediction and counterfactual simulation
        ↓
candidate generation + representation invention
        ↓
VOC / VOI bounded search
        ↓
action, question, tool call, or response
        ↓
outcome and error trace
        ↓
update / compile / split / merge / delete / rollback
```

There should be one effect boundary and one canonical state substrate. Neural
components may be used where they win the measured Pareto comparison,
especially for raw perception and candidate generation, but they are not exempt
from storage, communication, training, and inference costs.

## 10. Research milestones toward a credible superhuman claim

1. **Hierarchical grounding:** multiple events, conditions, negation, quotation,
   and reference in one utterance.
2. **Learned structural grammar:** remove the hand-specified connector inventory.
3. **Real repository work:** locate files, patch, test, rollback, and report on
   held-out repositories.
4. **Causal model induction:** distinguish correlation from intervention and
   predict counterfactual effects.
5. **Open representation invention:** create new predicates and latent variables
   from persistent decision collisions.
6. **Self-improving compiler:** compile repeated successful reasoning while
   preserving proof, tests, and rollback.
7. **Broad human comparison:** evaluate against skilled humans and strong LLMs
   with the same tools, information, deadlines, and explicit lifetime cost.
8. **Adversarial and long-horizon evaluation:** prevent benchmark specialization
   from masquerading as general intelligence.

A superhuman result should be claimed only after these evaluations show broad,
repeatable Pareto improvement. Until then, each phase is evidence about one
necessary mechanism, not evidence that general superhuman intelligence has
already been achieved.
