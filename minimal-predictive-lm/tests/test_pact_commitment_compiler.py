from __future__ import annotations

import unittest

import torch

from minimal_predictive_lm.pact_commitment_compiler import Config, PACTCompiler, Pair


class PACTCompilerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pairs = []
        examples = [
            Pair("東京の人口について説明してください。", "東京の人口について、統計資料を確認しながら説明します。"),
            Pair("大阪の人口について説明してください。", "大阪の人口について、統計資料を確認しながら説明します。"),
            Pair("17ではなく23に訂正してください。", "承知しました。17ではなく23に訂正します。"),
            Pair("青ではなく赤に訂正してください。", "承知しました。青ではなく赤に訂正します。"),
            Pair("猫の特徴を二つ挙げてください。", "猫の特徴は、柔軟な体と鋭い聴覚です。"),
            Pair("犬の特徴を二つ挙げてください。", "犬の特徴は、優れた嗅覚と高い社会性です。"),
        ]
        for _ in range(16):
            pairs.extend(examples)
        cfg = Config(
            hash_buckets=2048,
            embedding_dim=32,
            commitment_atoms=8,
            top_atoms=2,
            max_templates=200,
            epochs=2,
            batch_size=32,
            retrieval_candidates=32,
        )
        cls.model = PACTCompiler(cfg)
        cls.training = cls.model.train(pairs, device=torch.device("cpu"))

    def test_unknown_entity_is_rebound(self):
        output, trace = self.model.respond("京都の人口について説明してください。")
        self.assertIn("京都", output)
        self.assertFalse(trace["abstained"])

    def test_unknown_numbers_are_rebound(self):
        output, _ = self.model.respond("19ではなく31に訂正してください。")
        self.assertIn("19", output)
        self.assertIn("31", output)

    def test_unknown_animal_is_rebound(self):
        output, _ = self.model.respond("鳥の特徴を二つ挙げてください。")
        self.assertIn("鳥", output)

    def test_model_is_small_and_non_autoregressive(self):
        self.assertLess(self.training["total_bytes"], 2_000_000)
        self.assertFalse(hasattr(self.model.encoder, "attention"))


if __name__ == "__main__":
    unittest.main()
