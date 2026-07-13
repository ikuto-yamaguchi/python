# Phase 18a-5: Conjugation classes and allomorphy

## Research question

Phase 18a-4 induced a stem × voice × polarity representation, but every family
used the same regular ichidan-like morphology. Phase 18a-5 asks whether the
learner can discover recurring conjugation classes, assign sparsely observed
families to those classes, and use the class both to understand and generate
held-out inflections.

## Controlled class inventory

The campaign contains three unlabeled paradigms:

- one ichidan-like class;
- one godan-s-like class;
- one godan-r-like class.

Each class has two complete support families and one target family. Support
families expose active/passive/causative × positive/negative. Target families
expose only active positive and active negative before evaluation.

The suffix tables used by the generator are not supplied to the learner. They
must recur across two independent support families before being accepted as a
class rather than a lexical exception.

## Induction

For each recurring-prefix lexical family, transition interventions identify:

- positive versus negative through changed versus unchanged state;
- causative through three-participant arity;
- active positive as the unique minimum-description positive binary form;
- passive positive as the remaining binary form, which must reverse the active
  surface direction;
- active negative as the unique minimum-description negative binary form;
- passive negative as the remaining binary negative form.

Complete support paradigms are grouped by identical six-slot suffix tables.
A target family is assigned to a class only when its active-positive and
active-negative suffix pair matches exactly one recurring class. Its base event
direction is recovered from the active-positive interventions.

## Frozen evaluation

The three target families are tested on four unseen forms each:

- passive positive;
- passive negative;
- causative positive;
- causative negative.

Each form is evaluated with a participant-role reversal pair, giving 24 raw
continuous-Japanese rows. The same 12 forms must also be generated exactly.

## Baselines and adversarial controls

- A whole-surface memorizer has zero target coverage.
- A class-agnostic generator chooses one global suffix per operator and cannot
  generate every class correctly.
- A global suffix analyzer can understand the intended operator but falsely
  accepts grammatically wrong allomorphs from another class.
- The class-conditioned model must reject every wrong-class allomorph.
- Removing target active-negative anchors must make class assignment fail,
  because ichidan and godan-r active positives both end in `る`.
- Removing the second support family from every class must make recurring class
  evidence fail.
- Unknown lexical anchors cause abstention.
- The positive role-swap character-bag upper bound remains 50%.

## Resource accounting

The report counts a compact serialization of:

- nine `(stem, class, base-bit)` entries;
- three ordered six-suffix paradigm tables.

It compares this with literal storage of the 42 observed forms and all 54 forms
supported by the learned capability. Python and the standard library remain an
excluded and declared substrate.

## Claim boundary

Passing this campaign demonstrates three recurring conjugation classes,
class-conditioned grammaticality, and bidirectional held-out inflection in a
controlled Japanese microgrammar. It does not establish unrestricted Japanese
conjugation, irregular verbs, phonological alternation, tense/aspect,
politeness, reading comprehension, or Japanese high-school-level intelligence.

The next language gate should leave isolated predicate morphology and move to
multiple events, negation scope, conjunction, and context-dependent ellipsis.
