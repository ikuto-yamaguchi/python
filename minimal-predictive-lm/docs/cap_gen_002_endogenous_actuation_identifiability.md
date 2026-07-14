# CAP-GEN-002-EAI-001: endogenous actuation identifiability

## Why the research changes direction here

RII-001--003, EPQ-001, and SPG-001 established useful constraints:

- raw boundaries, delayed links, and small executable transformations can be discovered in
  controlled streams;
- exact repeated contexts can be replaced by factorized context classes;
- wholly unseen surfaces cannot be assigned to predictive roles without an observable
  separating relation;
- shared executable probe components must be charged once;
- one-probe-at-a-time greedy selection can be arbitrarily bad.

Continuing to add more probe-selection refinements would risk a local loop around finite
automata.  The general-intelligence goal requires a more basic capability: an agent must
learn which parts of experience merely describe the world and which parts are experiments
or actions that change it.

A passive corpus does not provide that distinction for free.  This document therefore
starts with an impossibility result and then states the weakest finite assumptions under
which action-like surfaces become identifiable.

## Prior-art audit

The following are established areas and are not the contribution:

1. **Action-model learning.**  Given observed action occurrences and partial state
   observations, deterministic action preconditions and effects can be learned exactly in
   restricted logical classes.  Amir and Chang explicitly assume action traces rather than
   discovering which raw spans are actions:
   https://arxiv.org/abs/1401.3437
2. **Joint state/action discovery in videos.**  Object states and manipulation actions have
   been jointly clustered under task-specific video and temporal-order assumptions:
   https://arxiv.org/abs/1702.02738
3. **Independently controllable features/factors.**  Interactive agents can use deliberate
   actions to discover factors they can control:
   https://arxiv.org/abs/1703.07718
   https://arxiv.org/abs/1708.01289
4. **Causal representation learning from interventions.**  Multiple interventional
   environments can identify latent causal variables under declared assumptions, even
   when intervention targets are unknown:
   https://arxiv.org/abs/2209.11924
   https://arxiv.org/abs/2306.00542
   https://arxiv.org/abs/2306.02235
   https://arxiv.org/abs/2406.05937
5. **Predictive-state and active-automata learning.**  Once actions/tests are defined,
   predictive states and compact automata can be identified from their responses.

Therefore none of the following is novel by itself:

- learning action effects;
- exploiting policy or environment shifts;
- grouping surfaces by equal transition effects;
- using invariant mechanisms;
- learning a state/action representation jointly;
- compressing many surface actions into fewer behavioral action classes.

The open candidate is narrower:

> From one raw mixed interaction stream, jointly discover candidate span boundaries,
> policy regimes, action-vs-observation roles, behavioral action classes, the predictive
> quotient, and a shared executable action grammar, while charging parser bits, program
> bits, induction operations, action executions, inference operations, peak memory, and
> identifying support separately.

The novelty of that full construction is unverified.  EAI-001 does not claim it.

## Formal setting

Assume a finite predictive quotient `S` has provisionally been obtained.  Raw surface
spans are drawn from a finite set `U`.  Data are collected under policy regimes `e in E`.
For the finite gate we observe exact tables:

```text
selection_count(e, s, u)
passive_successor(s)
surface_successor(s, u)
```

The semantic role of each surface is hidden.  A surface is action-like only under the
following finite assumptions:

1. its normalized selection frequency changes across policy regimes;
2. its successor effect is invariant across those regimes;
3. it changes at least one successor relative to passive dynamics;
4. every state/surface combination needed for the effect signature has support.

An observation-like surface in this gate has regime-invariant frequency and no direct
successor effect after conditioning on predictive state.

These assumptions are deliberately strong.  Their purpose is to mark the boundary between
what is identified by evidence and what would be guessed.

## Theorem 1: passive actuation decomposition is non-identifiable

Given only one passive raw trace with no observable action marker, policy regime,
intervention record, or counterfactual response, the division of spans into actions and
autonomous emissions is not identifiable.

### Construction

Consider the same raw trace:

```text
s0, u, s1, v, s0, u, s1
```

World A treats positions containing `u` and `v` as agent-selected actions and the `s*`
spans as observations.  World B treats every span as an emission of one autonomous
generator.  The raw trace and every passive substring statistic are identical, while the
actuation assignments disagree.

### Consequence

A learner trained only on passive text cannot prove that a question, command, code call,
or tool invocation is an intervention merely from co-occurrence.  It may learn useful
correlations, but the action/observation decomposition remains one of several compatible
causal explanations.

This is a no-free-lunch boundary, not a novel causal-discovery theorem.

## Theorem 2: one unchanged policy does not identify effectful surfaces as actions

Suppose a surface changes the observed successor, but its occurrence policy is identical
in every available dataset.  The same observations are compatible with:

- an agent action selected by a fixed hidden policy;
- an exogenous event emitted by the environment;
- a correlated observation of an unobserved cause that produces the transition.

Therefore an effect signature alone does not identify agency.  EAI-001 abstains rather
than labeling such a surface as an action.

## Theorem 3: finite identification under policy shift and invariant effects

Under the four assumptions above, action-like surfaces are identifiable in the exact
finite table:

- normalized selection frequency varies across regimes;
- the complete successor signature remains invariant;
- at least one successor differs from passive dynamics.

Observation-like surfaces satisfy the complementary finite condition used by the gate:
regime-invariant selection and no direct effect.

The classification is only as strong as the assumptions.  Regime-varying sensors,
policy-invariant actions, confounding, and incomplete support remain `abstain`.

## Theorem 4: behavioral action quotient

Two identified action surfaces are behaviorally equivalent when they have the same
successor for every predictive state:

```text
u ~= v  iff  successor(s, u) = successor(s, v) for every s in S.
```

The equivalence classes are identifiable up to names when the complete effect table is
observed.  This is ordinary behavioral quotienting, not a new result.

## Resource comparison

Let:

- `n` be the number of predictive states;
- `m` be the number of action surface spellings;
- `g` be the number of behavioral action classes;
- `K_parser` be the executable code for mapping raw spans to classes.

A flat transition table costs approximately:

```text
K_flat = n * m * ceil(log2 n).
```

The quotient representation costs:

```text
K_quotient = n * g * ceil(log2 n)
           + m * ceil(log2 g)
           + K_parser.
```

This is a standard sharing advantage.  It matters only if parser, acquisition, and runtime
costs are included.  Hiding a giant neural parser outside `K_parser` would invalidate the
comparison.

The frozen fixture uses `n=8`, `m=64`, `g=4`, and `K_parser=64`:

```text
flat table:       1536 bits
action quotient:   288 bits
ratio:              5.33x
```

No asymptotic separation from unrestricted neural or program models is claimed.

## Stagnation audit

This result is progress only because it changes the research trajectory.  It is not a
reason to generate more policy-shift toy worlds.

The following continuations are prohibited:

- adding more named action types;
- adding another synthetic effect function;
- optimizing the six-surface classifier;
- claiming that environment variation itself is new;
- treating passive text prediction as sufficient evidence of agency;
- building benchmark-specific command/question detectors.

## New theory target

The next positive theory must address **endogenous intervention discovery**:

```text
raw bytes
  -> candidate span/event parser
  -> latent policy-regime segmentation
  -> action/observation role hypotheses
  -> invariant effect programs
  -> predictive quotient refinement
  -> shared executable action grammar
```

The components must be selected jointly under:

```text
R = (
    executable bits,
    induction operations,
    physical/simulated action executions,
    inference operations,
    peak working memory,
    identifying support,
    prediction loss
).
```

A plausible new principle is **causal executable compression**:

> Prefer a decomposition only when separating policy-dependent selection from
> policy-invariant effects reduces held-out predictive code after paying for the raw
> parser, regime detector, action grammar, state updater, and every intervention used to
> identify the mechanism.

This principle overlaps MDL causal inference, invariant causal mechanisms, unknown-
intervention CRL, action-model learning, and program-library learning.  It becomes a
research contribution only if we prove a resource or identifiability result not already
implied by those fields.

## Required next theorem

Before another learner is implemented, establish one of the following:

1. a nontrivial sufficient condition under which raw event boundaries, policy regimes,
   action roles, and effect classes are jointly identifiable up to a declared equivalence;
2. a resource separation showing that the joint executable decomposition uses
   asymptotically fewer bits/operations/interventions than a precisely defined staged
   baseline;
3. a negative theorem proving that the proposed assumptions are still insufficient,
   thereby forcing another pivot.

A positive finite result must include a counterexample when each essential assumption is
removed.  No public-axis solver may be added during this theory stage.
