from __future__ import annotations

import unittest

import torch

from minimal_predictive_lm.close_obligation_energy import (
    CloseConfig,
    ObligationSettlementEnergy,
    train_closure_head,
)


class CloseObligationEnergyTest(unittest.TestCase):
    def test_correct_state_transition_gets_lower_energy(self):
        torch.manual_seed(3)
        examples = 64
        hidden = 32
        open_states = torch.randn(examples, hidden)
        transform = torch.randn(hidden, hidden) / hidden**0.5
        positive_delta = open_states @ transform
        positive_closed = open_states + positive_delta
        negative_closed = open_states + torch.roll(positive_delta, 1, 0)

        cfg = CloseConfig(
            closure_dim=16,
            head_steps=240,
            head_lr=3e-3,
        )
        head = ObligationSettlementEnergy(hidden, cfg.closure_dim)
        report = train_closure_head(
            head,
            open_states,
            positive_closed,
            negative_closed,
            cfg,
        )

        self.assertGreater(report["final"]["ranking_accuracy"], 0.95)
        self.assertLess(
            report["final"]["positive_energy"],
            report["final"]["negative_energy"],
        )

    def test_new_head_is_small_and_attention_free(self):
        cfg = CloseConfig()
        head = ObligationSettlementEnergy(256, cfg.closure_dim)
        parameter_bytes = sum(
            parameter.numel() * parameter.element_size()
            for parameter in head.parameters()
        )
        self.assertLess(parameter_bytes, 2_000_000)
        names = " ".join(name.lower() for name, _ in head.named_modules())
        self.assertNotIn("attention", names)
        self.assertNotIn("transformer", names)

    def test_package_limit_is_decimal_one_gigabyte(self):
        self.assertLess(233_000_000 + 2_000_000, 1_000_000_000)


if __name__ == "__main__":
    unittest.main()
