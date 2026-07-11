from __future__ import annotations

import unittest
from fractions import Fraction

from minimal_predictive_lm.phase8f_experiment import run
from minimal_predictive_lm.probabilistic_effects import (
    BinarySensor,
    EffectBelief,
    TemporalFactLedger,
    choose_probe,
    posterior_probability,
)


class ProbabilisticEffectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run()

    def test_missing_observations_do_not_invent_failures_or_lags(self) -> None:
        belief = EffectBelief(max_lag=4)
        belief.observe(None)
        self.assertEqual(belief.successes, 0)
        self.assertEqual(belief.failures, 0)
        self.assertEqual(belief.lag_counts, [0, 0, 0, 0])

        belief.observe(True, None)
        self.assertEqual(belief.successes, 1)
        self.assertEqual(belief.lag_counts, [0, 0, 0, 0])

    def test_exact_bayes_update_and_one_probe_choice(self) -> None:
        sensor = BinarySensor(
            true_positive=Fraction(9, 10),
            false_positive=Fraction(2, 25),
            missing_probability=Fraction(1, 4),
            cost=Fraction(4, 1),
        )
        posterior = posterior_probability(Fraction(1, 2), sensor, True)
        self.assertEqual(posterior, Fraction(45, 49))

        uncertain = choose_probe(Fraction(1, 2), sensor, Fraction(64, 1))
        confident = choose_probe(Fraction(1, 10), sensor, Fraction(64, 1))
        self.assertTrue(uncertain.should_probe)
        self.assertFalse(confident.should_probe)

    def test_voi_matches_full_two_action_enumeration(self) -> None:
        exactness = self.result["voi_exactness"]
        self.assertEqual(exactness["priors_checked"], 21)
        self.assertTrue(exactness["matches_full_two-action_enumeration"])
        self.assertEqual(exactness["probe_outcomes_enumerated"], 3)

    def test_voi_uses_less_resource_at_same_accuracy_as_always_probe(self) -> None:
        policies = self.result["policies"]
        self.assertEqual(policies["voi"]["accuracy"], policies["always"]["accuracy"])
        self.assertLess(policies["voi"]["probes"], policies["always"]["probes"])
        self.assertLess(
            policies["voi"]["total_objective"],
            policies["always"]["total_objective"],
        )
        self.assertLess(
            policies["voi"]["total_objective"],
            policies["none"]["total_objective"],
        )

    def test_sufficient_statistics_beat_episode_replay(self) -> None:
        training = self.result["training"]
        self.assertEqual(training["sufficient_stat_bits"], 126)
        self.assertGreater(training["history_to_sufficient_stat_ratio"], 80)
        prediction = self.result["prediction"]
        self.assertLess(prediction["learned_brier"], prediction["uniform_brier"])

    def test_retraction_restores_previous_claim(self) -> None:
        ledger = TemporalFactLedger()
        older = ledger.add("設計書", "棚A", 1)
        newer = ledger.add("設計書", "保管庫", 2)
        self.assertEqual(older, 0)
        self.assertEqual(ledger.resolve("設計書"), "保管庫")
        ledger.retract(newer)
        self.assertEqual(ledger.resolve("設計書"), "棚A")

        result = self.result["contradiction_and_retraction"]
        self.assertTrue(result["retraction_restores_previous_claim"])
        self.assertLess(result["finalized_snapshot_bits"], result["provenance_ledger_bits"])
        self.assertGreater(result["finalized_compaction_ratio"], 20)


if __name__ == "__main__":
    unittest.main()
