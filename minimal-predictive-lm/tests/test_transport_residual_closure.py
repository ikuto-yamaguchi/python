import tempfile
import unittest

from minimal_predictive_lm.transport_residual_closure import (
    Episode,
    TransportResidualClosure,
    make_data,
    run_experiment,
)


class TransportResidualClosureTests(unittest.TestCase):
    def test_does_not_store_complete_answers(self):
        model = TransportResidualClosure()
        episodes = make_data(72, 1)
        model.fit(episodes)
        serialized = str(model.operators)
        for episode in episodes:
            self.assertNotIn(episode.future, serialized)

    def test_reads_are_bounded(self):
        model = TransportResidualClosure(max_reads=4)
        model.fit(make_data(1152, 7))
        before = model.reads
        model.generate(("未知の状況",), "どうする")
        self.assertLessEqual(model.reads - before, 4)

    def test_single_model_runs_all_integrated_probes(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_experiment(directory)
        self.assertEqual(len(report["results"]), 12)
        self.assertTrue(report["under_1gb"])
        self.assertFalse(report["architecture"]["stored_complete_answers"])
        self.assertFalse(report["architecture"]["problem_specific_branching"])
        self.assertFalse(report["highschool_level_passed"])
        self.assertFalse(report["native_japanese_communication_passed"])

    def test_transport_requires_repeated_effect(self):
        model = TransportResidualClosure()
        model.fit([Episode(("一度だけ",), "変更", "結果")])
        self.assertEqual(model.operators, [])


if __name__ == "__main__":
    unittest.main()
