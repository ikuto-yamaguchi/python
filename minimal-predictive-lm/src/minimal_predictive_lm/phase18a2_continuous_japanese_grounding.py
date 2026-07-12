from __future__ import annotations

from collections import Counter, defaultdict
from itertools import product
import json
from math import exp
from pathlib import Path
from typing import Iterable, Mapping

from ._phase18a2_continuous_japanese_core import (
    ACTION_BITS,
    ACTION_LEXEMES,
    ENTITY_LEXEMES,
    FLIPS_PER_GROUP,
    FRAME_SPECS,
    IDENTIFYING_PAIRS,
    MAX_LEXEME_CHARACTERS,
    MIN_BOUNDARY_VARIANTS,
    REPETITIONS,
    ContinuousJapaneseModel,
    ContinuousJapaneseObservation,
    TransitionRoles,
    extract_segmented_factor,
    fit_action_lexicon,
    induce_continuous_japanese,
    infer_transition_roles,
    normalize_continuous,
    robust_entity_span_search,
)


def render_sentence(
    action: str,
    frame: int,
    left: str,
    right: str,
    *,
    index: int,
    evaluation: bool = False,
) -> str:
    core = FRAME_SPECS[frame][0].format(
        left=left,
        right=right,
        action=action,
    )
    if evaluation:
        prefixes = ("念のため", "記録では", "あとで")
        suffixes = ("かもしれない", "と聞いた", "のだ")
    else:
        prefixes = ("", "今日は", "静かに", "その後", "たしか")
        suffixes = ("", "よ", "らしい", "そうだ", "とのこと")
    return (
        prefixes[index % len(prefixes)]
        + core
        + suffixes[(index // 3) % len(suffixes)]
        + "。"
    )


def participant_pair(group_index: int, repetition: int) -> tuple[int, int]:
    left = (group_index + repetition) % len(ENTITY_LEXEMES)
    right = (group_index + 2 * repetition + 1) % len(ENTITY_LEXEMES)
    if left == right:
        right = (right + 1) % len(ENTITY_LEXEMES)
    return left, right


def build_observation(
    *,
    action: str,
    frame: int,
    left_coordinate: int,
    right_coordinate: int,
    index: int,
    flip_label: bool = False,
    sentence: str | None = None,
    evaluation: bool = False,
) -> ContinuousJapaneseObservation:
    before = tuple(index * 100 + coordinate + 1 for coordinate in range(4))
    effective_forward = ACTION_BITS[action] ^ FRAME_SPECS[frame][1]
    if flip_label:
        effective_forward = not effective_forward
    source, destination = (
        (left_coordinate, right_coordinate)
        if effective_forward
        else (right_coordinate, left_coordinate)
    )
    after = list(before)
    after[destination] = before[source]
    rendered = sentence or render_sentence(
        action,
        frame,
        ENTITY_LEXEMES[left_coordinate],
        ENTITY_LEXEMES[right_coordinate],
        index=index,
        evaluation=evaluation,
    )
    return ContinuousJapaneseObservation.build(rendered, before, after)


def semantic_training_observations(
) -> tuple[ContinuousJapaneseObservation, ...]:
    rows: list[ContinuousJapaneseObservation] = []
    for group_index, (action, frame) in enumerate(IDENTIFYING_PAIRS):
        for repetition in range(REPETITIONS):
            left, right = participant_pair(group_index, repetition)
            rows.append(
                build_observation(
                    action=action,
                    frame=frame,
                    left_coordinate=left,
                    right_coordinate=right,
                    index=group_index * REPETITIONS + repetition,
                    flip_label=repetition < FLIPS_PER_GROUP,
                )
            )
    return tuple(rows)


def auxiliary_noise_observations(
) -> tuple[ContinuousJapaneseObservation, ...]:
    return (
        build_observation(
            action="渡す",
            frame=0,
            left_coordinate=0,
            right_coordinate=1,
            index=10_000,
            sentence="今日はアキが渡す。",
        ),
        build_observation(
            action="写す",
            frame=1,
            left_coordinate=2,
            right_coordinate=3,
            index=10_001,
            sentence="アキを見ながらチカからダイへ写す。",
        ),
    )


def training_observations(
) -> tuple[ContinuousJapaneseObservation, ...]:
    return (
        *semantic_training_observations(),
        *auxiliary_noise_observations(),
    )


def heldout_unseen_compositions(
) -> tuple[ContinuousJapaneseObservation, ...]:
    unseen = tuple(
        pair
        for pair in product(ACTION_LEXEMES, tuple(FRAME_SPECS))
        if pair not in IDENTIFYING_PAIRS
    )
    rows: list[ContinuousJapaneseObservation] = []
    for pair_index, (action, frame) in enumerate(unseen):
        left = pair_index % len(ENTITY_LEXEMES)
        right = (pair_index + 2) % len(ENTITY_LEXEMES)
        state_index = 20_000 + pair_index
        for surface_left, surface_right in ((left, right), (right, left)):
            rows.append(
                build_observation(
                    action=action,
                    frame=frame,
                    left_coordinate=surface_left,
                    right_coordinate=surface_right,
                    index=state_index,
                    sentence=render_sentence(
                        action,
                        frame,
                        ENTITY_LEXEMES[surface_left],
                        ENTITY_LEXEMES[surface_right],
                        index=30_000 + pair_index,
                        evaluation=True,
                    ),
                    evaluation=True,
                )
            )
    return tuple(rows)


def evaluate_model(
    model: ContinuousJapaneseModel,
    observations: Iterable[ContinuousJapaneseObservation],
) -> tuple[float, float]:
    rows = tuple(observations)
    answered = 0
    correct = 0
    for observation in rows:
        predicted = model.predict(observation.sentence, observation.before)
        if predicted is None:
            continue
        answered += 1
        correct += int(predicted == observation.after)
    return (
        correct / len(rows) if rows else 0.0,
        answered / len(rows) if rows else 0.0,
    )


def positionless_character_upper_bound(
    observations: Iterable[ContinuousJapaneseObservation],
) -> float:
    rows = tuple(observations)
    grouped: dict[
        tuple[tuple[str, ...], tuple[int, ...]],
        Counter[tuple[int, ...]],
    ] = defaultdict(Counter)
    for observation in rows:
        grouped[
            (tuple(sorted(observation.text)), observation.before)
        ][observation.after] += 1
    return (
        sum(max(counts.values()) for counts in grouped.values()) / len(rows)
        if rows
        else 0.0
    )


def exact_sentence_memorizer_coverage(
    training: Iterable[ContinuousJapaneseObservation],
    evaluation: Iterable[ContinuousJapaneseObservation],
) -> float:
    known = {observation.text for observation in training}
    rows = tuple(evaluation)
    return (
        sum(observation.text in known for observation in rows) / len(rows)
        if rows
        else 0.0
    )


def factor_baseline(
    training: Iterable[ContinuousJapaneseObservation],
    evaluation: Iterable[ContinuousJapaneseObservation],
    model: ContinuousJapaneseModel,
    *,
    use_action: bool,
    use_frame: bool,
) -> tuple[float, float]:
    grouped: dict[object, Counter[bool]] = defaultdict(Counter)

    def key(factor: object) -> object:
        return (
            factor.action if use_action else None,
            factor.frame if use_frame else None,
        )

    for observation in training:
        factor, _ = extract_segmented_factor(
            observation,
            entity_grounding=model.entity_lexicon,
            action_lexicon=model.action_lexicon,
        )
        grouped[key(factor)][factor.effective_forward] += 1

    rows = tuple(evaluation)
    answered = 0
    correct = 0
    for observation in rows:
        factor, _ = extract_segmented_factor(
            observation,
            entity_grounding=model.entity_lexicon,
            action_lexicon=model.action_lexicon,
        )
        counts = grouped.get(key(factor))
        if not counts:
            continue
        prediction = counts[True] >= counts[False]
        answered += 1
        correct += int(prediction == factor.effective_forward)
    return (
        correct / len(rows) if rows else 0.0,
        answered / len(rows) if rows else 0.0,
    )


def majority_recovery_union_bound(
    *,
    groups: int,
    repetitions: int,
    flip_probability: float,
) -> float:
    if groups < 1 or repetitions < 1:
        raise ValueError("groups and repetitions must be positive")
    if not 0.0 <= flip_probability < 0.5:
        raise ValueError("flip probability must be in [0, 0.5)")
    gap = 0.5 - flip_probability
    return min(1.0, groups * exp(-2.0 * repetitions * gap * gap))


def boundary_ablation_optima() -> int:
    return len(
        robust_entity_span_search(
            training_observations(),
            require_boundary_diversity=False,
        ).best_mappings
    )


def collision_control_optima() -> int:
    rows: list[ContinuousJapaneseObservation] = []
    for index, observation in enumerate(training_observations()):
        mimics_entity_occurrence = "アキ" in observation.text
        text = observation.text
        if mimics_entity_occurrence:
            insertion = "甲影乙" if index % 2 == 0 else "丙影丁"
            text = insertion + text
        rows.append(
            ContinuousJapaneseObservation.build(
                text,
                observation.before,
                observation.after,
            )
        )
    return len(robust_entity_span_search(rows).best_mappings)


def tied_majority_is_rejected() -> bool:
    rows = (
        build_observation(
            action="渡す",
            frame=0,
            left_coordinate=0,
            right_coordinate=1,
            index=60_000,
            flip_label=False,
        ),
        build_observation(
            action="渡す",
            frame=0,
            left_coordinate=0,
            right_coordinate=1,
            index=60_001,
            flip_label=True,
        ),
    )
    grounding = tuple(
        (lexeme, coordinate)
        for coordinate, lexeme in enumerate(ENTITY_LEXEMES)
    )
    fitted = fit_action_lexicon(rows, grounding, ("渡す",))
    return fitted is None


def disconnected_graph_is_rejected() -> bool:
    pairs = (
        ("渡す", 0),
        ("受ける", 0),
        ("写す", 2),
        ("移す", 2),
    )
    rows: list[ContinuousJapaneseObservation] = []
    for group_index, (action, frame) in enumerate(pairs):
        for repetition in range(5):
            left, right = participant_pair(group_index, repetition)
            rows.append(
                build_observation(
                    action=action,
                    frame=frame,
                    left_coordinate=left,
                    right_coordinate=right,
                    index=70_000 + group_index * 5 + repetition,
                )
            )
    grounding = tuple(
        (lexeme, coordinate)
        for coordinate, lexeme in enumerate(ENTITY_LEXEMES)
    )
    return fit_action_lexicon(rows, grounding, ACTION_LEXEMES) is None


def run() -> dict[str, object]:
    training = training_observations()
    semantic_training = semantic_training_observations()
    heldout = heldout_unseen_compositions()
    model, grounding_search, action_search, skipped = induce_continuous_japanese(
        training
    )
    accuracy, coverage = evaluate_model(model, heldout)
    action_only_accuracy, action_only_coverage = factor_baseline(
        semantic_training,
        heldout,
        model,
        use_action=True,
        use_frame=False,
    )
    frame_only_accuracy, frame_only_coverage = factor_baseline(
        semantic_training,
        heldout,
        model,
        use_action=False,
        use_frame=True,
    )
    joint_accuracy, joint_coverage = factor_baseline(
        semantic_training,
        heldout,
        model,
        use_action=True,
        use_frame=True,
    )
    flip_rate = FLIPS_PER_GROUP / REPETITIONS
    recovery_bound = majority_recovery_union_bound(
        groups=len(IDENTIFYING_PAIRS),
        repetitions=REPETITIONS,
        flip_probability=flip_rate,
    )
    unsegmented_optima = boundary_ablation_optima()
    collision_optima = collision_control_optima()

    theorem_checks = {
        "continuous_entity_segmentation_is_unique": len(
            grounding_search.best_mappings
        )
        == 1,
        "entity_segmentation_has_positive_margin": (
            grounding_search.margin is not None
            and grounding_search.margin > 0
        ),
        "admissible_branch_and_bound_ranks_two_distinct_optima": (
            grounding_search.theoretical_assignments
            >= grounding_search.complete_assignments_evaluated
            > 0
        ),
        "boundary_evidence_is_necessary": unsegmented_optima > 1,
        "entity_mimicking_substring_is_non_identifying": collision_optima > 1,
        "auxiliary_incomplete_rows_are_skipped": skipped == 2,
        "action_segmentation_has_one_best_model": action_search.best_models == 1,
        "connected_cycle_consistent_model_survives": (
            action_search.cycle_consistent_connected_models >= 1
        ),
        "bounded_direction_noise_is_recovered": (
            action_search.best_training_errors
            == len(IDENTIFYING_PAIRS) * FLIPS_PER_GROUP
        ),
        "finite_sample_bound_is_below_one_percent": recovery_bound < 0.01,
        "tied_majority_is_rejected": tied_majority_is_rejected(),
        "disconnected_factor_graph_is_rejected": disconnected_graph_is_rejected(),
        "heldout_unseen_compositions_are_perfect": (
            accuracy == 1.0 and coverage == 1.0
        ),
        "positionless_character_classifier_bound_is_half": (
            positionless_character_upper_bound(heldout) == 0.5
        ),
        "exact_sentence_memorizer_has_zero_coverage": (
            exact_sentence_memorizer_coverage(training, heldout) == 0.0
        ),
        "joint_pair_memorizer_has_zero_coverage": joint_coverage == 0.0,
        "action_only_ablation_is_insufficient": action_only_accuracy < 1.0,
        "frame_only_ablation_is_insufficient": frame_only_accuracy < 1.0,
        "raw_sentences_contain_no_whitespace": all(
            not any(character.isspace() for character in observation.sentence)
            for observation in (*training, *heldout)
        ),
    }

    return {
        "campaign": {
            "name": "phase18a2-continuous-japanese-segmentation-c1",
            "language": "controlled continuous Japanese character strings",
            "whitespace_token_boundaries_provided": False,
            "predicate_suffix_heuristic_used": False,
            "particle_script_or_length_heuristic_used": False,
            "maximum_candidate_lexeme_characters": MAX_LEXEME_CHARACTERS,
            "boundary_diversity_prior": MIN_BOUNDARY_VARIANTS,
            "anonymous_world_coordinates": True,
            "bounded_label_noise": True,
            "public_benchmark_examples_used": 0,
        },
        "segmentation": {
            "candidate_lexemes": grounding_search.candidate_lexemes,
            "theoretical_injective_assignments": (
                grounding_search.theoretical_assignments
            ),
            "complete_assignments_evaluated_after_exact_pruning": (
                grounding_search.complete_assignments_evaluated
            ),
            "branch_nodes": grounding_search.branch_nodes,
            "best_grounding_cost": grounding_search.best_cost,
            "second_best_grounding_cost": grounding_search.second_best_cost,
            "grounding_margin": grounding_search.margin,
            "best_grounding_models": len(grounding_search.best_mappings),
            "without_boundary_diversity_best_models": unsegmented_optima,
            "collision_control_best_models": collision_optima,
            "candidate_action_lexemes": (
                action_search.candidate_action_lexemes
            ),
            "exact_cover_action_lexicons": action_search.exact_cover_lexicons,
            "connected_consistent_action_models": (
                action_search.cycle_consistent_connected_models
            ),
            "best_action_models": action_search.best_models,
            "best_action_training_errors": action_search.best_training_errors,
        },
        "evaluation": {
            "training_observations": len(training),
            "semantic_training_observations": len(semantic_training),
            "skipped_incomplete_observations": skipped,
            "heldout_observations": len(heldout),
            "heldout_accuracy": accuracy,
            "heldout_coverage": coverage,
            "positionless_character_upper_bound": (
                positionless_character_upper_bound(heldout)
            ),
            "exact_memorizer_coverage": exact_sentence_memorizer_coverage(
                training,
                heldout,
            ),
            "action_only_accuracy": action_only_accuracy,
            "action_only_coverage": action_only_coverage,
            "frame_only_accuracy": frame_only_accuracy,
            "frame_only_coverage": frame_only_coverage,
            "joint_memorizer_accuracy": joint_accuracy,
            "joint_memorizer_coverage": joint_coverage,
        },
        "theory": {
            "identifying_action_frame_edges": len(IDENTIFYING_PAIRS),
            "repetitions_per_edge": REPETITIONS,
            "adversarial_flips_per_edge": FLIPS_PER_GROUP,
            "empirical_flip_rate": flip_rate,
            "iid_hoeffding_union_bound": recovery_bound,
            "bound_assumption": (
                "independent Bernoulli direction flips below one half; the "
                "generated experiment uses a deterministic bounded flip count"
            ),
            "segmentation_identifiability_condition": (
                "the correct recurring substring has a unique minimum causal "
                "incidence loss and at least two observed left and right boundary "
                "contexts; action/frame exact covers are then filtered by connected "
                "cycle-consistent XOR semantics and MDL tie-breaking"
            ),
        },
        "resource_accounting": {
            "serialized_acquired_model_bits": model.description_bits,
            "phase18a2_module_source_bytes": (
                Path(__file__).read_bytes().__len__()
                + Path(__file__)
                .with_name("_phase18a2_continuous_japanese_core.py")
                .read_bytes()
                .__len__()
            ),
            "python_runtime_and_standard_library_bytes_included": False,
        },
        "learned_model": {
            "entity_lexicon": [list(row) for row in model.entity_lexicon],
            "action_lexicon": list(model.action_lexicon),
            "frame_templates": [list(row) for row in model.frame_index],
            "factorization": model.factorization.render(),
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "whitespace_free_controlled_japanese_grounding_demonstrated": all(
                theorem_checks.values()
            ),
            "morphology_free_lexeme_search_demonstrated": all(
                theorem_checks.values()
            ),
            "general_japanese_tokenization_demonstrated": False,
            "natural_language_understanding_demonstrated": False,
            "japanese_high_school_intelligence_demonstrated": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "candidate lexemes are capped at six normalized characters",
            "boundary diversity is a fixed generic segmentation prior",
            "sentences still contain exactly one binary copy event",
            "entity names and action words do not exhibit synonymy, inflection, or polysemy",
            "case frames are stored as literal character templates after semantic spans are selected",
            "world interventions remain noiseless apart from bounded direction-label flips",
            "prefix and suffix discourse material lies outside the learned semantic core",
            "Python and its standard library remain excluded substrate",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    segmentation = payload["segmentation"]
    evaluation = payload["evaluation"]
    theory = payload["theory"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 18a-2 results: continuous Japanese segmentation and grounding",
        "",
        "Phase 18a-2 removes whitespace token boundaries, the predicate-ending",
        "heuristic, and the hiragana particle heuristic. It searches recurring",
        "character substrings and selects segmentation jointly with causal grounding",
        "and connected action/frame semantics.",
        "",
        "## Segmentation identification",
        "",
        f"- Candidate recurring lexemes: **{segmentation['candidate_lexemes']}**",
        f"- Theoretical injective grounding assignments: **{segmentation['theoretical_injective_assignments']}**",
        f"- Complete assignments evaluated after exact pruning: **{segmentation['complete_assignments_evaluated_after_exact_pruning']}**",
        f"- Grounding cost / second-best: **{segmentation['best_grounding_cost']} / {segmentation['second_best_grounding_cost']}**",
        f"- Grounding margin: **{segmentation['grounding_margin']}**",
        f"- Grounding optima: **{segmentation['best_grounding_models']}**",
        f"- Optima without boundary evidence: **{segmentation['without_boundary_diversity_best_models']}**",
        f"- Entity-mimicking substring control optima: **{segmentation['collision_control_best_models']}**",
        f"- Action candidates / exact covers / connected models: **{segmentation['candidate_action_lexemes']} / {segmentation['exact_cover_action_lexicons']} / {segmentation['connected_consistent_action_models']}**",
        "",
        "## Held-out transfer",
        "",
        f"- Training / semantic / skipped rows: **{evaluation['training_observations']} / {evaluation['semantic_training_observations']} / {evaluation['skipped_incomplete_observations']}**",
        f"- Held-out unseen action-frame rows: **{evaluation['heldout_observations']}**",
        f"- Accuracy / coverage: **{100 * evaluation['heldout_accuracy']:.1f}% / {100 * evaluation['heldout_coverage']:.1f}%**",
        f"- Positionless character upper bound: **{100 * evaluation['positionless_character_upper_bound']:.1f}%**",
        f"- Exact sentence memorizer coverage: **{100 * evaluation['exact_memorizer_coverage']:.1f}%**",
        f"- Action-only accuracy: **{100 * evaluation['action_only_accuracy']:.1f}%**",
        f"- Frame-only accuracy: **{100 * evaluation['frame_only_accuracy']:.1f}%**",
        f"- Seen action-frame pair memorizer coverage: **{100 * evaluation['joint_memorizer_coverage']:.1f}%**",
        "",
        "## Noise and resource accounting",
        "",
        f"- Direction flip rate: **{100 * theory['empirical_flip_rate']:.1f}%**",
        f"- IID Hoeffding union bound: **{100 * theory['iid_hoeffding_union_bound']:.3f}%**",
        f"- Serialized acquired model: **{resources['serialized_acquired_model_bits']} bits**",
        f"- Phase 18a-2 source: **{resources['phase18a2_module_source_bytes']} bytes**",
        "- Python runtime and standard library: excluded and declared",
        "",
        "## Claim boundary",
        "",
        "This is evidence for segmentation and semantic factorization in a small",
        "continuous-character Japanese micro-language. It is not unrestricted",
        "Japanese tokenization, reading comprehension, or high-school intelligence.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase18a2.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18a2.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
