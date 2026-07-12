from __future__ import annotations

import unittest

from minimal_predictive_lm.generic_quantifier import (
    MembershipObservation,
    induce_generic_quantifier,
)
from minimal_predictive_lm.phase13d_experiment import (
    build_public_quantifier,
    quantity_calibration,
    universal_concept_calibration,
)


class Phase13dGenericQuantifierTests(unittest.TestCase):
    def test_variable_length_universal_count(self) -> None:
        model = build_public_quantifier()
        self.assertEqual(
            model.answer(
                "I have two servers, a router, and three disks. How many objects do I have?"
            ),
            6,
        )
        self.assertEqual(
            model.answer(
                "I have a badge, four cables, an alert, and two queues. How many objects do I have?"
            ),
            8,
        )

    def test_unknown_category_returns_interval_and_abstains(self) -> None:
        model = build_public_quantifier()
        prompt = (
            "I have two quorps, a zibble, and three narns. "
            "How many glippets do I have?"
        )
        interval = model.identifiability_interval(prompt)
        self.assertIsNotNone(interval)
        assert interval is not None
        self.assertEqual((interval.minimum, interval.maximum), (0, 6))
        self.assertFalse(interval.identifiable)
        self.assertIsNone(model.answer(prompt))

    def test_membership_grounding_makes_category_identifiable(self) -> None:
        model = induce_generic_quantifier(
            quantity_calibration(),
            universal_concept_calibration(),
            memberships=(
                MembershipObservation("servers", "infrastructure"),
                MembershipObservation("router", "infrastructure"),
                MembershipObservation("disks", "infrastructure"),
            ),
        )
        self.assertEqual(
            model.answer(
                "I have two servers, a router, and three disks. How many infrastructure do I have?"
            ),
            6,
        )

    def test_known_nonmembers_are_excluded(self) -> None:
        model = induce_generic_quantifier(
            quantity_calibration(),
            universal_concept_calibration(),
            memberships=(
                MembershipObservation("servers", "infrastructure"),
                MembershipObservation("router", "network"),
                MembershipObservation("disks", "storage"),
            ),
        )
        self.assertEqual(
            model.answer(
                "I have two servers, a router, and three disks. How many infrastructure do I have?"
            ),
            2,
        )

    def test_program_has_no_domain_handlers_or_public_item_dictionary(self) -> None:
        model = build_public_quantifier()
        self.assertEqual(model.domain_specific_handlers, 0)
        self.assertEqual(len(model.memberships), 0)
        self.assertGreater(model.description_bits, 0)


if __name__ == "__main__":
    unittest.main()
