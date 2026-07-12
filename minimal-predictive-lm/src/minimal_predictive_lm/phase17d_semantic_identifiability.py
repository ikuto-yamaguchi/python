from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import product
import json
from math import ceil, log2
from pathlib import Path
from typing import Iterable, Mapping, Sequence


State = tuple[tuple[str, int], ...]

VERBS = ("dax", "zup", "miv", "rup")
TRUE_FORWARD = {
    "dax": True,
    "zup": False,
    "miv": True,
    "rup": False,
}


def normalize_state(state: Mapping[str, int] | Iterable[tuple[str, int]]) -> State:
    rows = dict(state)
    if not rows:
        raise ValueError("state must contain at least one entity")
    if any(value not in (0, 1) for value in rows.values()):
        raise ValueError("micro-world state values must be binary")
    return tuple(sorted(rows.items()))


@dataclass(frozen=True)
class SemanticObservation:
    sentence: str
    before: State
    after: State

    @classmethod
    def build(
        cls,
        sentence: str,
        before: Mapping[str, int],
        after: Mapping[str, int],
    ) -> "SemanticObservation":
        return cls(sentence, normalize_state(before), normalize_state(after))


@dataclass(frozen=True)
class SemanticFrame:
    verb: str
    source: str
    destination: str


@dataclass(frozen=True)
class SemanticHypothesis:
    """A tiny latent grammar with an explicit argument-coordinate gauge.

    ``swap_arguments`` changes the internal names of the two participant slots.
    Flipping every verb direction at the same time gives an observationally
    equivalent hypothesis. Identifiability is therefore evaluated over semantic
    behavior classes rather than raw parameter tuples.
    """

    swap_arguments: bool
    forward_by_verb: tuple[tuple[str, bool], ...]

    def direction_map(self) -> dict[str, bool]:
        return dict(self.forward_by_verb)

    def frame(self, sentence: str) -> SemanticFrame:
        tokens = sentence.casefold().split()
        if len(tokens) != 3:
            raise ValueError("controlled micro-language requires exactly three tokens")
        left_surface, verb, right_surface = tokens
        directions = self.direction_map()
        if verb not in directions:
            raise ValueError(f"unknown verb: {verb}")

        first, second = (
            (right_surface, left_surface)
            if self.swap_arguments
            else (left_surface, right_surface)
        )
        if directions[verb]:
            source, destination = first, second
        else:
            source, destination = second, first
        return SemanticFrame(verb, source, destination)

    def execute_frame(self, frame: SemanticFrame, before: State) -> State:
        state = dict(before)
        if frame.source not in state or frame.destination not in state:
            raise ValueError("sentence participants must exist in the world state")
        state[frame.destination] = state[frame.source]
        return normalize_state(state)

    def predict(self, sentence: str, before: State) -> State:
        return self.execute_frame(self.frame(sentence), before)

    def render(self) -> object:
        return {
            "swap_arguments": self.swap_arguments,
            "forward_by_verb": [list(row) for row in self.forward_by_verb],
        }

    @property
    def description_bits(self) -> int:
        return len(
            json.dumps(
                self.render(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8


def all_hypotheses(verbs: Sequence[str] = VERBS) -> tuple[SemanticHypothesis, ...]:
    return tuple(
        SemanticHypothesis(
            swap_arguments=swap,
            forward_by_verb=tuple(zip(verbs, directions)),
        )
        for swap in (False, True)
        for directions in product((False, True), repeat=len(verbs))
    )


def is_consistent(
    hypothesis: SemanticHypothesis,
    observations: Iterable[SemanticObservation],
) -> bool:
    for observation in observations:
        try:
            predicted = hypothesis.predict(observation.sentence, observation.before)
        except ValueError:
            return False
        if predicted != observation.after:
            return False
    return True


def version_space(
    observations: Iterable[SemanticObservation],
    hypotheses: Sequence[SemanticHypothesis] | None = None,
) -> tuple[SemanticHypothesis, ...]:
    candidates = all_hypotheses() if hypotheses is None else tuple(hypotheses)
    rows = tuple(observations)
    return tuple(candidate for candidate in candidates if is_consistent(candidate, rows))


def _probe_cases(verbs: Sequence[str]) -> tuple[tuple[str, State], ...]:
    states = (
        normalize_state({"left": 1, "right": 0}),
        normalize_state({"left": 0, "right": 1}),
    )
    rows: list[tuple[str, State]] = []
    for verb in verbs:
        for sentence in (f"left {verb} right", f"right {verb} left"):
            rows.extend((sentence, state) for state in states)
    return tuple(rows)


def behavior_signature(
    hypothesis: SemanticHypothesis,
    verbs: Sequence[str] = VERBS,
) -> tuple[State, ...]:
    return tuple(
        hypothesis.predict(sentence, before)
        for sentence, before in _probe_cases(verbs)
    )


def behavior_classes(
    hypotheses: Iterable[SemanticHypothesis],
    verbs: Sequence[str] = VERBS,
) -> dict[tuple[State, ...], tuple[SemanticHypothesis, ...]]:
    groups: dict[tuple[State, ...], list[SemanticHypothesis]] = defaultdict(list)
    for hypothesis in hypotheses:
        groups[behavior_signature(hypothesis, verbs)].append(hypothesis)
    return {signature: tuple(rows) for signature, rows in groups.items()}


def true_hypothesis() -> SemanticHypothesis:
    return SemanticHypothesis(False, tuple(TRUE_FORWARD.items()))


def _observe(sentence: str, before: Mapping[str, int]) -> SemanticObservation:
    normalized = normalize_state(before)
    after = true_hypothesis().predict(sentence, normalized)
    return SemanticObservation(sentence, normalized, after)


def non_identifying_observations() -> tuple[SemanticObservation, ...]:
    """Symmetric worlds make both copy directions observationally identical."""

    rows: list[SemanticObservation] = []
    for index, verb in enumerate(VERBS):
        value = index % 2
        rows.append(_observe(f"alice {verb} bob", {"alice": value, "bob": value}))
    return tuple(rows)


def identifying_interventions() -> tuple[SemanticObservation, ...]:
    """One asymmetric intervention per independent verb-direction bit."""

    rows: list[SemanticObservation] = []
    for index, verb in enumerate(VERBS):
        before = (
            {"alice": 1, "bob": 0}
            if index % 2 == 0
            else {"alice": 0, "bob": 1}
        )
        rows.append(_observe(f"alice {verb} bob", before))
    return tuple(rows)


def heldout_role_reversal_pairs() -> tuple[SemanticObservation, ...]:
    rows: list[SemanticObservation] = []
    entity_pairs = (
        ("eve", "frank"),
        ("grace", "heidi"),
        ("ivan", "judy"),
        ("karl", "lena"),
    )
    for verb, (left, right) in zip(VERBS, entity_pairs):
        before = {left: 1, right: 0}
        rows.append(_observe(f"{left} {verb} {right}", before))
        rows.append(_observe(f"{right} {verb} {left}", before))
    return tuple(rows)


def surface_representation(observation: SemanticObservation) -> object:
    """Positionless unigram representation plus the complete world state."""

    return (
        tuple(sorted(observation.sentence.casefold().split())),
        observation.before,
    )


def representation_accuracy_upper_bound(
    observations: Iterable[SemanticObservation],
) -> float:
    """Exact Bayes/deterministic upper bound for a fixed representation.

    All predictors that only receive ``surface_representation`` must issue one
    label for every equivalence class. The best possible class label is therefore
    the majority target within that class.
    """

    groups: dict[object, Counter[State]] = defaultdict(Counter)
    rows = tuple(observations)
    for observation in rows:
        groups[surface_representation(observation)][observation.after] += 1
    correct = sum(max(counts.values()) for counts in groups.values())
    return correct / len(rows) if rows else 0.0


def exact_memorizer_coverage(
    training: Iterable[SemanticObservation],
    evaluation: Iterable[SemanticObservation],
) -> float:
    known = {row.sentence for row in training}
    test = tuple(evaluation)
    covered = sum(row.sentence in known for row in test)
    return covered / len(test) if test else 0.0


def semantic_accuracy(
    hypothesis: SemanticHypothesis,
    observations: Iterable[SemanticObservation],
) -> float:
    rows = tuple(observations)
    correct = sum(
        hypothesis.predict(row.sentence, row.before) == row.after for row in rows
    )
    return correct / len(rows) if rows else 0.0


def role_intervention_consistency(
    hypothesis: SemanticHypothesis,
    paired_observations: Sequence[SemanticObservation],
) -> float:
    if len(paired_observations) % 2:
        raise ValueError("role-intervention suite must contain adjacent reversal pairs")
    correct = 0
    total = 0
    for index in range(0, len(paired_observations), 2):
        forward = paired_observations[index]
        reversed_surface = paired_observations[index + 1]
        frame = hypothesis.frame(forward.sentence)
        swapped = SemanticFrame(frame.verb, frame.destination, frame.source)
        intervened = hypothesis.execute_frame(swapped, forward.before)
        predicted_reversal = hypothesis.predict(
            reversed_surface.sentence,
            reversed_surface.before,
        )
        correct += int(intervened == predicted_reversal)
        total += 1
    return correct / total if total else 0.0


def choose_canonical_hypothesis(
    hypotheses: Sequence[SemanticHypothesis],
) -> SemanticHypothesis:
    if not hypotheses:
        raise ValueError("empty version space")
    return min(
        hypotheses,
        key=lambda row: (
            row.description_bits,
            json.dumps(row.render(), sort_keys=True),
        ),
    )


def run() -> dict[str, object]:
    prior = all_hypotheses()
    negative = non_identifying_observations()
    positive = identifying_interventions()
    heldout = heldout_role_reversal_pairs()

    negative_space = version_space(negative, prior)
    positive_space = version_space(positive, prior)
    prior_classes = behavior_classes(prior)
    negative_classes = behavior_classes(negative_space)
    positive_classes = behavior_classes(positive_space)
    learned = choose_canonical_hypothesis(positive_space)

    minimum_information_bits = ceil(log2(len(prior_classes)))
    module_source_bytes = Path(__file__).read_bytes().__len__()

    theorems = {
        "surface_bound_exact": representation_accuracy_upper_bound(heldout) == 0.5,
        "symmetric_observations_non_identifying": len(negative_classes) > 1,
        "interventions_identify_behavior_modulo_gauge": len(positive_classes) == 1,
        "gauge_equivalent_parameterizations_remain": len(positive_space) == 2,
        "one_informative_observation_per_verb_matches_information_lower_bound": (
            len(positive) == minimum_information_bits == len(VERBS)
        ),
        "heldout_compositional_accuracy_is_perfect": semantic_accuracy(learned, heldout)
        == 1.0,
        "latent_role_swap_matches_surface_role_reversal": role_intervention_consistency(
            learned, heldout
        )
        == 1.0,
        "exact_sentence_memorizer_has_zero_heldout_coverage": exact_memorizer_coverage(
            positive, heldout
        )
        == 0.0,
    }

    return {
        "campaign": {
            "name": "phase17d-interventional-semantic-identifiability-c1",
            "language": "three-token controlled micro-language",
            "verbs": list(VERBS),
            "raw_sentences_used": True,
            "handwritten_natural_language_parser_used": False,
            "fixed_three-token_grammar_bias": True,
            "world_supervision": "binary state transitions",
            "public_benchmark_examples_used": 0,
        },
        "theory": {
            "syntactic_hypotheses": len(prior),
            "semantic_behavior_classes": len(prior_classes),
            "information_lower_bound_bits": minimum_information_bits,
            "minimum_informative_interventions": len(VERBS),
            "reason": (
                "each verb contributes one independent direction bit; any unseen "
                "verb retains two behaviorally distinct meanings"
            ),
        },
        "negative_result": {
            "observations": len(negative),
            "surviving_syntactic_hypotheses": len(negative_space),
            "surviving_behavior_classes": len(negative_classes),
            "identifiable": len(negative_classes) == 1,
        },
        "positive_result": {
            "interventions": len(positive),
            "surviving_syntactic_hypotheses": len(positive_space),
            "surviving_behavior_classes": len(positive_classes),
            "identifiable_modulo_coordinate_gauge": len(positive_classes) == 1,
            "heldout_examples": len(heldout),
            "semantic_accuracy": semantic_accuracy(learned, heldout),
            "surface_unigram_upper_bound": representation_accuracy_upper_bound(heldout),
            "exact_memorizer_coverage": exact_memorizer_coverage(positive, heldout),
            "latent_role_intervention_consistency": role_intervention_consistency(
                learned, heldout
            ),
        },
        "resource_accounting": {
            "information_acquired_lower_bound_bits": minimum_information_bits,
            "serialized_acquired_hypothesis_bits": learned.description_bits,
            "phase17d_module_source_bytes": module_source_bytes,
            "python_runtime_and_standard_library_bytes_included": False,
        },
        "theorem_checks": theorems,
        "all_theorem_checks_pass": all(theorems.values()),
        "claim_boundary": {
            "controlled_semantic_grounding_demonstrated": all(theorems.values()),
            "positionless_surface_classifier_refuted": all(theorems.values()),
            "arbitrary_classifier_refuted": False,
            "natural_language_understanding_demonstrated": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the grammar length and verb position are fixed human-designed inductive bias",
            "entity symbols are grounded by appearing as keys in the observed world state",
            "only binary copy dynamics and four lexical meanings are learned",
            "the result proves identifiability for this finite hypothesis class, not for unrestricted language",
            "Python and its standard library are declared substrate rather than counted system bytes",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    theory = payload["theory"]
    negative = payload["negative_result"]
    positive = payload["positive_result"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 17d results: interventional semantic identifiability",
        "",
        "This campaign asks a narrower question than language-model benchmarking:",
        "can latent lexical direction and ordered semantic roles be recovered from",
        "raw symbol sequences plus observed world transitions?",
        "",
        "## Exhaustive identifiability result",
        "",
        f"- syntactic hypothesis count: **{theory['syntactic_hypotheses']}**",
        f"- distinct semantic behavior classes: **{theory['semantic_behavior_classes']}**",
        f"- information lower bound: **{theory['information_lower_bound_bits']} bits**",
        f"- required informative interventions: **{theory['minimum_informative_interventions']}**",
        "",
        "Symmetric states contain no directional information:",
        f"{negative['surviving_behavior_classes']} behavior classes survive and meaning",
        "is not identifiable. With one asymmetric intervention per verb, the version",
        f"space collapses to {positive['surviving_behavior_classes']} semantic behavior",
        "class. Two raw parameterizations remain, but they differ only by a global",
        "renaming of the two latent argument coordinates.",
        "",
        "## Classifier separation",
        "",
        "| evaluator | held-out result |",
        "|---|---:|",
        f"| any deterministic classifier using positionless unigrams + full before-state | at most {100 * positive['surface_unigram_upper_bound']:.1f}% |",
        f"| exact sentence memorizer | {100 * positive['exact_memorizer_coverage']:.1f}% coverage |",
        f"| induced semantic interpreter | {100 * positive['semantic_accuracy']:.1f}% accuracy |",
        f"| latent source/destination swap intervention | {100 * positive['latent_role_intervention_consistency']:.1f}% consistency |",
        "",
        "The 50% surface bound is exact: every representation-equivalence class",
        "contains two role-reversed sentences with the same token multiset and world",
        "state but different target transitions.",
        "",
        "## Resource accounting",
        "",
        f"- acquired-information lower bound: {resources['information_acquired_lower_bound_bits']} bits",
        f"- serialized acquired hypothesis: {resources['serialized_acquired_hypothesis_bits']} bits",
        f"- Phase 17d source module: {resources['phase17d_module_source_bytes']} bytes",
        "- Python runtime and standard library are declared substrate and are not counted.",
        "",
        "## Claim boundary",
        "",
        "This is a constructive proof that causal interventions can make lexical",
        "semantics identifiable in a finite controlled micro-language. It rejects the",
        "declared positionless surface classifier and exact memorization baselines.",
        "It does not prove unrestricted natural-language understanding, and a sufficiently",
        "general classifier can implement the same semantic algorithm.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    if not payload["all_theorem_checks_pass"]:
        failed = [
            name for name, passed in payload["theorem_checks"].items() if not passed
        ]
        raise RuntimeError(f"Phase 17d theorem checks failed: {failed}")
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase17d.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase17d.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
