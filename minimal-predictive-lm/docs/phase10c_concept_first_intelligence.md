# Phase 10c: concept-first intelligence and language as a codec

## 1. Motivation

A language model trained only through token prediction must infer several different
objects at once:

1. the syntax and statistics of a surface language,
2. the entities and relations referred to by that language,
3. causal regularities of the external world,
4. goals, values, and social conventions,
5. procedures for planning, checking, and acting,
6. a mapping from all of the above back into text.

This joint learning problem can be effective because text contains an enormous
amount of compressed human experience. It can also be wasteful when the same
world regularity is represented repeatedly in different languages, phrasings,
domains, prompts, and token contexts.

Phase 10c tests a different factorization:

```text
perception / interaction / reward
              ↓
decision-sufficient causal state
              ↓
latent concepts and executable schemas
              ↓
prediction / planning / verification
              ↕
language codec, tool codec, visual codec
```

The central intelligence state is not a sentence and is not tied to any one
language. Language is one observation and action channel over the shared state.

## 2. What is a concept?

A concept is not defined by a human-readable name. It is an equivalence class of
histories, observations, or actions that have the same relevant consequences for
future prediction and decision.

For histories `h1` and `h2`, a decision-relative causal equivalence is

```text
h1 ~ h2
```

when, for every relevant intervention `a`,

```text
P(future | h1, do(a)) = P(future | h2, do(a))
```

and the optimal continuation is unchanged. If two surface actions modify the
same relation with the same argument roles and induce the same future behavior,
they can share one concept even if their names, languages, or tool formats differ.

In the Phase 10c finite world, an executable concept schema is

```text
(relation, subject_argument, value_argument)
```

For example, several opaque actions can all induce

```text
(location, argument 0, argument 1)
```

without the learner receiving the label `MOVE`.

## 3. Intelligence before language

The concept machine is learned from tuples of

```text
state_before, opaque_action, arguments, state_after, reward
```

The learner compares state differences and argument roles. Stable effect
signatures are merged; unstable actions are rejected rather than forced into a
false concept.

Once a schema exists, planning can occur without language:

1. compare current and target state,
2. identify the relation that differs,
3. select the concept schema capable of changing it,
4. bind the subject and value arguments,
5. execute and verify the resulting state.

Language is unnecessary for this internal transition. This is the sense in which
intelligence can exist independently of its verbal description.

## 4. Language as a bidirectional codec

After concepts are induced, a language adapter learns mappings of the form

```text
surface expression ↔ concept identifier
```

and output templates of the form

```text
concept identifier + arguments → surface expression
```

A new language does not require relearning location, ownership, status, or
messaging dynamics. It requires only a new grounding and rendering layer over the
existing concepts.

This separation avoids storing the full transition schema in every phrase-specific
program. The experiment compares:

### Language-first repeated programs

```text
surface phrase
+ relation schema
+ argument roles
+ output template
```

for each phrase.

### Concept-first factorization

```text
world concept schemas once
+ sparse surface-to-concept rules
+ language-specific output templates
```

The comparison includes both the world model and the language codec. It does not
claim that a few concept bits replace the complete implementation or runtime.

## 5. Why text alone cannot completely ground meaning

Suppose there are `K` latent concepts and only text co-occurrence is observed.
Permuting the concept names leaves the text likelihood unchanged. There are

```text
K!
```

semantically permuted groundings with the same text-only evidence. Breaking this
symmetry requires at least

```text
log2(K!)
```

bits of external grounding evidence in the ideal noiseless case.

For four concepts, there are 24 equivalent permutations and the lower bound is
approximately 4.585 bits. In realistic noisy environments, more evidence is
required.

The symmetry can be broken by:

- perception,
- interaction and observed effects,
- reward or preference,
- trusted demonstrations,
- tool execution,
- cross-modal correspondence,
- already-grounded concepts.

Text can learn rich relational structure, analogies, and procedures. What text
alone cannot determine is which arbitrary internal symbol is attached to which
external referent without some anchor.

## 6. Is language merely an output format?

No. It is better modeled as both an input sensor and an output actuator.

Language can transmit information that would be prohibitively expensive or
impossible for one agent to rediscover locally:

- historical events,
- scientific experiments,
- mathematical definitions,
- legal and social conventions,
- counterfactual reports,
- private mental states,
- plans for unbuilt systems.

Therefore, discarding language would force the machine to repeat much of human
civilization's experimentation. The efficient design is not `no language`; it is

```text
shared grounded concepts
+ language used when its expected information value exceeds its cost
```

A retrieved statement should be converted into a proposition with provenance,
confidence, scope, and possible contradiction, rather than copied permanently as
raw token context.

## 7. Where Transformer language learning may be wasteful

The following are hypotheses to test, not assumptions that all Transformers are
inefficient:

1. **Surface duplication** — similar concepts may be represented repeatedly across
   languages and paraphrases.
2. **Entangled storage** — grammar, facts, procedures, and uncertainty are mixed in
   dense parameters, making targeted update and deletion expensive.
3. **Repeated reconstruction** — the same semantic state may be reconstructed from
   a long token history on each invocation.
4. **Dense execution** — many parameters are evaluated even when a small compiled
   program would suffice for a familiar task.
5. **Weak provenance** — a fluent answer can be produced without an explicit path
   to the supporting observation.
6. **Update interference** — changing one fact or skill can affect unrelated
   behavior.

Transformers also provide major advantages that a concept-first machine must
reproduce before any superiority claim:

- powerful candidate generation,
- robust interpolation between expressions,
- broad world knowledge,
- natural language generation,
- amortized learning from huge corpora,
- implicit representation discovery.

A concept-first system that lacks these abilities is smaller because it is less
capable, not because it solved the same problem more efficiently.

## 8. Why waste cannot be reduced to exactly zero

Zero waste is not generally achievable.

### Identification cost

Different worlds can generate the same observations so far. Additional evidence
is necessary to distinguish them.

### Exploration cost

An unknown action may have to be tried before its consequences are known. No
algorithm can infer arbitrary hidden effects without information.

### Search cost

Finding the shortest useful program can itself be more expensive than executing a
larger known program. General minimum-program discovery is not computable in the
strongest unrestricted form.

### Communication cost

At least enough bits must be transmitted to distinguish the relevant alternatives.

### Irreducible uncertainty

A stochastic environment has entropy that cannot be compressed away without
losing predictive calibration.

The realistic objective is therefore not zero operations or zero bits. It is the
minimum lifetime resource conditional on a required quality and risk level:

```text
J = task loss
  + program and knowledge bits
  + active state bits
  + bits read and written
  + primitive operations
  + observations and tool effects
  + induction and compiler cost
  + verification, migration, and rollback
  + shifted-distribution regret
```

## 9. Phase 10c experiment

The controlled experiment contains four hidden relation schemas and twelve opaque
surface actions. No language is supplied during concept induction.

The experiment then adds Japanese, English, and tool expressions as codecs, and a
fourth synthetic language through a small calibration set.

Measured questions:

1. Are opaque actions grouped by their causal effects?
2. Can the machine plan for unseen subjects and values without language?
3. Does a concept-first representation use fewer bits than phrase-specific
   repeated programs under the explicit serialization used here?
4. Can a new language be attached without changing the world model?
5. How many text-only semantic permutations remain without grounding?

## 10. Limits of the result

The experiment is deliberately small:

- the relation vocabulary is finite,
- each interaction changes one fact,
- action arguments are already segmented,
- held-out expressions share lexical roots with calibration examples,
- perception is symbolic and noiseless,
- there is no open-domain knowledge or natural conversation benchmark.

Accordingly, this phase does not increase the Stage-C readiness score. It tests an
architectural factorization, not parity with an open language model.

## 11. Next research steps

1. learn relation candidates rather than supplying the relation vocabulary,
2. infer entities and argument boundaries from perception and raw language,
3. handle simultaneous, delayed, stochastic, and partially observed effects,
4. learn concepts from image, audio, code, and tool traces in one workspace,
5. attach external textual knowledge with provenance and contradiction handling,
6. compile repeatedly used reasoning paths while retaining reversible evidence,
7. compare the same tasks against small open models with matched inputs, tools,
   latency, memory, and energy.

The intended architecture is neither a pure symbolic system nor a pure language
model. It is an open-ended causal concept machine whose language and neural
components are retained only where they improve the lifetime quality-resource
frontier.
