# Phase 6b: Minimal Choice Machine

## Core insight

Intelligence can be modeled as a sequence of small choices from a current state. A useful machine should not attempt to enumerate an entire future tree. It should spend computation only when additional lookahead is expected to change the selected action enough to justify its cost.

The target is therefore not merely a predictor, parser, reasoner, or planner. It is a **resource-rational choice machine** whose common operation is:

```text
observe current state
-> construct the smallest sufficient belief/state
-> generate a small set of non-dominated actions
-> estimate consequences across relevant horizons
-> optionally buy more information or computation
-> commit to one minimal action
-> observe the result and repeat
```

Coding edits, prose decisions, tool calls, memory writes, proof steps, and creative transformations are all actions in the same formalism.

## Why a globally best action is not directly defined

An action is best only relative to:

- an objective or utility function
- a time horizon or termination distribution
- uncertainty about the current state and transition law
- risk tolerance and hard constraints
- resource prices for memory, reads, writes, search, and external effects

A locally attractive action can destroy long-term option value. A long-horizon action can also be wasteful when the world will be re-observed soon. The machine therefore must not use one fixed horizon for every choice.

## Multi-horizon value

For belief state `b`, candidate action `a`, and horizon `h`, define:

```text
Q_h(b, a) = expected task utility through horizon h
             + expected option value at h
             - expected irreversible damage
             - execution resource cost
```

Instead of selecting one arbitrary horizon, use a task-dependent distribution over horizons:

```text
Q(b, a) = sum_h w(h | b, goal) * Q_h(b, a)
```

The horizon weights may represent termination probability, deadline structure, user intent, or the probability that a future observation will invalidate the current plan.

For safety and correctness, hard constraints are checked before scalar utility. The choice order is:

1. remove invalid or unsafe actions
2. remove actions dominated at all relevant horizons
3. compare remaining actions by expected utility and option value
4. charge memory, computation, information acquisition, and side effects

## The metachoice: think more or act now

The central minimum-compute rule is the value of computation.

Let the current best estimated action value be:

```text
V_now = max_a Q_current(b, a)
```

For an additional computation or observation `c`, estimate:

```text
VOC(c) = E[max_a Q_after_c(b, a)] - V_now - cost(c)
```

Execute `c` only when `VOC(c) > 0`.

This turns reasoning depth, branch expansion, test execution, file reading, retrieval, simulation, and clarification into ordinary candidate actions. The machine stops thinking exactly when another unit of thought is not expected to pay for itself.

This is the intended replacement for fixed layer depth, fixed context reading, and fixed chain-of-thought length.

## Minimum-state principle

Two histories are equivalent for the current decision when they induce the same values for every currently admissible action across the relevant horizon distribution:

```text
history_1 ~ history_2
iff
for every action a and relevant horizon h,
Q_h(history_1, a) = Q_h(history_2, a)
```

The runtime should preserve only the equivalence class needed to choose. Information that cannot change any admissible choice should be forgotten or archived outside active state.

This is stronger than next-token predictive equivalence: the state is compressed for **decision sufficiency**, not merely sequence likelihood.

## Option value and least commitment

Under uncertainty, the best immediate action is often one that preserves future choices. Therefore the state and utility must represent:

- reversibility
- recoverability
- information gained by acting
- number and quality of future options
- lock-in and rollback cost

Examples:

- Coding: prefer a small reversible patch plus tests over a broad rewrite when evidence is weak.
- Writing: retain unresolved alternatives until the thesis and audience constraints distinguish them.
- Agency: inspect a cheap dependency before performing an irreversible external action.

This prevents a greedy machine from optimizing only the next token, next test, or next tool call.

## Hierarchical choices without separate modules

Long actions are reusable programs made of the same primitive rewrites. They are called `options` only as compressed macros, not as a second planner architecture.

```text
primitive action: add/delete/match/emit/effect
compiled option: a reusable sequence with entry condition, exit condition, and cost model
```

An option becomes native only if lifetime savings exceed its program bits, dispatch cost, verification burden, and representation cost.

The hierarchy can expand without a fixed maximum depth:

```text
byte/symbol choice
-> phrase or AST edit
-> proof or patch step
-> task subgoal
-> project strategy
```

All levels use the same state, value-of-computation rule, and cost ledger.

## Search discipline

The machine must avoid exhaustive future trees through:

- exact state equivalence and merging
- dominance pruning across all relevant horizons
- branch-and-bound using admissible utility bounds
- memoized subproblems and compiled options
- event-driven replanning after surprising observations
- progressive widening: add actions only when current candidates are insufficient
- adaptive horizon extension only when action ranking is unstable

A choice can be committed early when one action remains optimal under all plausible models and horizons. More computation is reserved for close, uncertain, high-impact, or irreversible decisions.

## Application to language generation

Do not treat every next byte or token as an equally important life choice.

```text
user goal and constraints
-> decision-sufficient semantic state
-> choose claims, structure, code edits, or tool effects
-> verify consequences
-> compile the chosen semantic program into surface text
```

Surface realization can remain cheap. Expensive choice is spent on decisions that affect meaning, correctness, future consistency, or action consequences.

## Scaling target

A fixed finite machine cannot be literally infinitely intelligent. The target is an open-ended family whose capability increases with available knowledge, memory, observations, and search budget without a fixed architectural ceiling.

For every resource budget `B`, report:

```text
quality(B)
static bits(B)
dynamic bits(B)
bits read and written(B)
primitive operations(B)
external effects(B)
search/training amortization(B)
regret relative to the best known policy(B)
```

The desired scaling property is that additional resources are spent only on decisions whose expected regret can still be reduced. Easy decisions converge to compiled constant-cost paths; difficult and novel decisions receive more computation.

## Non-negotiable limitations

- There is no best action without a specified objective and horizon model.
- Exact long-term optimality is generally unavailable under unknown dynamics and combinatorial futures.
- New independent information must be read or stored somewhere.
- Some sequential dependencies require sequential work.
- A small core cannot contain unlimited world knowledge for free.

The research claim must therefore be about measured regret and distance to lower bounds, not perfect omniscience.

## Phase 6b experiment

Construct a unified coding-agent episode with decisions whose preferred action changes by horizon:

1. quick local patch that passes immediate tests but creates future inconsistency
2. reversible diagnostic action that costs one extra step but identifies the true cause
3. broad rewrite with high immediate cost and uncertain long-term benefit

Compare:

- greedy one-step choice
- fixed-depth lookahead
- exhaustive search oracle on the small environment
- adaptive-horizon Minimal Choice Machine using value of computation

Measure:

- task success and long-horizon regret
- action and tool-call count
- observations read
- state bits and peak frontier
- planning operations
- irreversible mistakes
- how often additional lookahead changed the chosen action

Success requires matching the oracle on the micro-world while spending near-greedy resources on easy cases and deeper resources only on ambiguous high-impact cases.
