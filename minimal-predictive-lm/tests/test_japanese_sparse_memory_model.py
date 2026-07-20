import unittest

import torch

from minimal_predictive_lm.japanese_sparse_memory_model import (
    CharVocab,
    Config,
    Pair,
    SparseDialogueMemory,
    batch_loss,
    make_batch,
)


class JapaneseSparseMemoryTest(unittest.TestCase):
    def test_character_generation_and_sparse_memory(self):
        vocab = CharVocab.build(["こんにちは", "短く答えて", "はい。"], 128)
        cfg = Config(
            embedding_dim=16,
            hidden_dim=24,
            slots=4,
            topk=2,
            max_prompt_chars=32,
            max_response_chars=32,
            batch_size=2,
            epochs=1,
        )
        model = SparseDialogueMemory(cfg, len(vocab))
        pairs = [Pair("こんにちは", "こんにちは。"), Pair("短く答えて", "はい。")]
        loss = batch_loss(model, make_batch(pairs, vocab, cfg), torch.device("cpu"))
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        output, tokens = model.generate("こんにちは", vocab, max_chars=12)
        self.assertIsInstance(output, str)
        self.assertLessEqual(len(tokens), 12)


if __name__ == "__main__":
    unittest.main()
