import unittest

import torch

from minimal_predictive_lm.japanese_dialogue_model import (
    ByteCodec,
    Config,
    DialogueCycleModel,
    Pair,
    batch_loss,
    make_batch,
)


class JapaneseDialogueModelTest(unittest.TestCase):
    def test_utf8_roundtrip(self):
        text = "日本語で会話できます。"
        decoded, valid = ByteCodec.decode(ByteCodec.encode(text, 100))
        self.assertTrue(valid)
        self.assertEqual(text, decoded)

    def test_forward_reverse_and_generation(self):
        cfg = Config(embedding_dim=16, hidden_dim=24, max_prompt_bytes=48, max_response_bytes=48, batch_size=2)
        model = DialogueCycleModel(cfg)
        pairs = [Pair("こんにちは", "こんにちは。"), Pair("短く答えて", "はい。")]
        forward = batch_loss(model, make_batch(pairs, cfg, False), torch.device("cpu"))
        reverse = batch_loss(model, make_batch(pairs, cfg, True), torch.device("cpu"))
        self.assertTrue(torch.isfinite(forward + reverse))
        (forward + reverse).backward()
        output, valid, tokens = model.generate("こんにちは", max_bytes=12)
        self.assertIsInstance(output, str)
        self.assertIsInstance(valid, bool)
        self.assertLessEqual(len(tokens), 12)


if __name__ == "__main__":
    unittest.main()
