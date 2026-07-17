import unittest

from minimal_predictive_lm.sparc_highschool_general import SparseGeneralLearner, World


class SparseHighSchoolGeneralTests(unittest.TestCase):
    def test_shared_fact_program_transfers_across_domains(self):
        learner = SparseGeneralLearner()
        for text, fact in [
            ("水は物質である", ("水", "R-kind", "物質")),
            ("鉄は金属である", ("鉄", "R-kind", "金属")),
        ]:
            learner.teach(text, World.from_parts(), World.from_parts([fact]))
        result = learner.apply("酸素は気体である", World.from_parts())
        self.assertTrue(result.accepted)
        self.assertIn(("酸素", "R-kind", "気体"), result.world.facts)
        self.assertEqual(1, len(learner.programs))

    def test_numeric_program_and_planning_share_executor(self):
        learner = SparseGeneralLearner()
        for subject, old, new, text in [
            ("箱A", 2, 5, "箱Aに3個加える"),
            ("箱B", 4, 7, "箱Bに3個加える"),
            ("箱A", 3, 6, "箱Aを2倍にする"),
            ("箱B", 5, 10, "箱Bを2倍にする"),
        ]:
            learner.teach(
                text,
                World.from_parts(numbers={(subject, "count"): old}),
                World.from_parts(numbers={(subject, "count"): new}),
            )
        start = World.from_parts(numbers={("箱C", "count"): 1})
        goal = World.from_parts(numbers={("箱C", "count"): 8})
        plan = learner.plan(start, goal, ["箱Cに3個加える", "箱Cを2倍にする"], max_depth=3)
        self.assertTrue(plan.found)
        self.assertEqual(("箱Cに3個加える", "箱Cを2倍にする"), plan.actions)

    def test_unknown_surface_abstains_without_mutation(self):
        learner = SparseGeneralLearner()
        learner.teach(
            "箱Aに3個加える",
            World.from_parts(numbers={("箱A", "count"): 2}),
            World.from_parts(numbers={("箱A", "count"): 5}),
        )
        before = World.from_parts([("保持", "R", "知識")])
        result = learner.apply("未知の理論を説明する", before)
        self.assertFalse(result.accepted)
        self.assertEqual(before, result.world)

    def test_serialization_preserves_program_bank(self):
        learner = SparseGeneralLearner()
        learner.teach(
            "水は物質である",
            World.from_parts(),
            World.from_parts([("水", "R-kind", "物質")]),
        )
        restored = SparseGeneralLearner.from_bytes(learner.to_bytes())
        result = restored.apply("酸素は気体である", World.from_parts())
        self.assertTrue(result.accepted)
        self.assertIn(("酸素", "R-kind", "気体"), result.world.facts)


if __name__ == "__main__":
    unittest.main()
