from __future__ import annotations

import unittest

from minimal_predictive_lm.concept_first_intelligence import (
    Interaction,
    WorldState,
    codec_accuracy,
    induce_concepts,
    induce_language_codec,
    permutation_equivalent_groundings,
)
from minimal_predictive_lm.phase10c_experiment import (
    HELDOUT_SPECIFICATION,
    NEW_LANGUAGE_CALIBRATION,
    NEW_LANGUAGE_HELDOUT,
    TRAINING_SPECIFICATION,
    _concept_ids,
    _language_examples,
    _planning_accuracy,
    output_templates,
    run,
    world_interactions,
)


class ConceptFirstIntelligenceTests(unittest.TestCase):
    def test_induces_four_concepts_without_language(self) -> None:
        machine = induce_concepts(world_interactions())
        self.assertEqual(len(machine.schemas), 4)
        self.assertEqual(len(set(machine.action_to_concept.values())), 4)

    def test_rejects_action_with_unstable_effect(self) -> None:
        before = WorldState()
        first = WorldState.from_dict({("location", "box"): "room"})
        second = WorldState.from_dict({("owner", "box"): "alice"})
        interactions = [
            Interaction("opaque", ("box", "room"), before, first),
            Interaction("opaque", ("box", "alice"), before, second),
        ]
        with self.assertRaises(ValueError):
            induce_concepts(interactions)

    def test_language_codec_is_separate_from_concepts(self) -> None:
        machine = induce_concepts(world_interactions())
        concept_ids = _concept_ids(machine)
        training = _language_examples(TRAINING_SPECIFICATION, concept_ids)
        heldout = _language_examples(HELDOUT_SPECIFICATION, concept_ids)
        templates = {
            key: value
            for key, value in output_templates(concept_ids).items()
            if key[0] in {"ja", "en", "tool"}
        }
        codec = induce_language_codec(
            training,
            templates,
            minimum_support=2,
        )
        self.assertEqual(codec_accuracy(codec, heldout), 1.0)

    def test_adds_new_language_without_relearning_world_model(self) -> None:
        machine = induce_concepts(world_interactions())
        original_machine_bits = machine.description_bits
        concept_ids = _concept_ids(machine)
        training = _language_examples(TRAINING_SPECIFICATION, concept_ids)
        calibration = _language_examples(
            NEW_LANGUAGE_CALIBRATION,
            concept_ids,
        )
        heldout = _language_examples(NEW_LANGUAGE_HELDOUT, concept_ids)
        codec = induce_language_codec(
            training + calibration,
            output_templates(concept_ids),
            minimum_support=2,
        )
        self.assertEqual(codec_accuracy(codec, heldout), 1.0)
        self.assertEqual(machine.description_bits, original_machine_bits)

    def test_language_free_planning_transfers_to_unseen_arguments(self) -> None:
        machine = induce_concepts(world_interactions())
        accuracy, trials = _planning_accuracy(machine)
        self.assertEqual(trials, 1024)
        self.assertEqual(accuracy, 1.0)

    def test_text_only_grounding_has_permutation_symmetry(self) -> None:
        self.assertEqual(permutation_equivalent_groundings(4), 24)

    def test_reproducible_phase10c_results(self) -> None:
        payload = run()
        self.assertEqual(
            payload["world_concept_induction"][
                "pairwise_partition_recovery"
            ],
            1.0,
        )
        self.assertEqual(
            payload["language_as_codec"]["heldout_accuracy"],
            1.0,
        )
        self.assertEqual(payload["new_language"]["heldout_accuracy"], 1.0)
        self.assertEqual(
            payload["language_free_planning"]["accuracy"],
            1.0,
        )
        self.assertEqual(payload["stage_c"]["changed_by_this_phase"], 0)
        self.assertGreater(
            payload["language_first_comparison"][
                "language_first_total_bits"
            ],
            payload["language_first_comparison"][
                "concept_first_total_bits"
            ],
        )


if __name__ == "__main__":
    unittest.main()
