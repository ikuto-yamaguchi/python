# Phase 18a-4: Voice and polarity morphology

## Research question

Phase 18a-3 replaced literal Japanese case-frame storage with reusable action,
case-marker, and order atoms. Its action lexicon still treated each inflected
predicate surface as an indivisible item.

Phase 18a-4 asks whether continuous Japanese predicate strings can be factored
into:

```text
lexical stem × voice morph × polarity ending
```

and whether that factorization predicts forms that are absent globally during
training.

## Inherited boundary

This campaign inherits the entity lexicon and local case-marker inventory from
Phase 18a-3. It does not claim to re-induce segmentation, case grammar, voice,
and polarity jointly from scratch.

The morphology learner receives raw predicate residuals and anonymous
before/after world states. It is not given stem boundaries, voice labels,
polarity labels, or a list of inflection suffixes.

## Controlled morphology

Six regular ichidan-like predicate families are used. The surface algebra is:

```text
surface = stem + voice_morph + polarity_ending

voice_morph ∈ {"", "られ", "させ"}
polarity_ending ∈ {"る", "ない"}
```

These strings are used only by the data generator. The learner searches all
finite prefix/ending splits of the observed predicate suffixes.

The semantic operators are:

- active positive: execute the base binary event;
- passive positive: execute the same event while reversing the two surface
  participant positions;
- causative positive: leave the causer unchanged and execute the base event
  between the actor and target;
- any negative form: suppress the event and preserve the state.

## Frozen training and evaluation split

Every family exposes:

- active positive;
- active negative;
- either passive positive or causative positive.

Therefore training contains 18 family/operator cells and 198 observations.
Each cell has 11 repetitions and one bounded corrupted transition signature.

The frozen held-out evaluation contains two different kinds of transfer:

1. **family × positive voice recombination** — each family is evaluated on the
   positive non-active voice that it never saw;
2. **global operator composition** — passive-negative and causative-negative
   forms are absent for every family during training.

Each cell is evaluated with a participant-role reversal pair. The positive
pairs have the same character multiset and initial state but require different
world transitions.

## Identifiability conditions

The declared finite learner accepts a factorization only when:

1. recurring-prefix family clusters form one unique minimum-description exact
   cover of the observed predicates;
2. observed suffixes admit exactly three voice prefixes and two polarity
   endings;
3. one ending is supported only by no-change interventions and the other only
   by changed-state interventions;
4. one voice prefix is observed with both polarities in every family;
5. one positive voice has arity three, identifying the causative operator;
6. the remaining positive binary voice reverses the active direction within
   families where both are observed;
7. all family base-direction bits are consistent with the induced operators.

The behavior is unique over the complete 6 × 3 × 2 predicate grid. Merely
having a low-description string split is insufficient if it changes held-out
behavior.

## Falsification controls

The campaign fails unless all of the following hold:

- deleting all negative anchor forms makes polarity non-identifiable;
- deleting all passive evidence makes the three-voice factorization
  non-identifiable;
- a tied transition signature for one surface is rejected;
- unknown morphology causes abstention;
- a causative predicate with only two participants causes abstention;
- changing active to passive preserves the same underlying positive event;
- changing positive to negative suppresses the event;
- a whole-surface memorizer has zero held-out coverage;
- a whole-suffix model can solve family recombination but has zero coverage on
  the globally unseen negative compositions;
- the positive role-swap character-bag upper bound remains 50%;
- the factorized model reaches 100% accuracy and coverage on every frozen row.

## Resource accounting

The report separates:

- serialized factorized model payload;
- literal storage of the 18 observed surface forms;
- literal storage of all 36 supported family × voice × polarity forms;
- Phase 18a-4 source bytes;
- excluded Python runtime and standard-library substrate.

A lookup table of only observed forms can be close in size to the factorized
model but has zero transfer. The relevant capability comparison is against
literal enumeration of the complete supported surface grid.

## Claim boundary

Passing this campaign demonstrates compositional voice and polarity morphology
inside one controlled regular ichidan-like microgrammar. It does not establish
multiple Japanese conjugation classes, unrestricted Japanese morphology,
reading comprehension, or Japanese high-school-level intelligence.

The next gate should introduce multiple inflection classes and allomorphy,
including godan predicates, and freeze class-held-out forms so that a single
suffix table cannot solve the task.
