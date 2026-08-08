"""MNEME プロトタイプのスモークテスト。"""

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mneme import (
    ByteDecoder,
    ByteEncoder,
    EntropyPatcher,
    EpisodicMemory,
    MemoryRecallModel,
    MnemeLM,
    make_facts,
)
from mneme.modules import pad_batch, to_bytes

CORPUS = (
    b"The quick brown fox jumps over the lazy dog. "
    b"Memory is the mother of all wisdom. "
    b"Specialized intelligence needs exact recall, not a bigger vocabulary. "
) * 40


def test_memory_exact_recall():
    torch.manual_seed(0)
    mem = EpisodicMemory(dim=32)
    keys = torch.randn(50, 32)
    values = torch.randn(50, 32)
    mem.write(keys, values)
    out, scores = mem.read(keys[:10], k=1)
    assert torch.allclose(out, values[:10], atol=1e-5)
    assert torch.all(scores > 0.99)


def test_memory_empty_read():
    mem = EpisodicMemory(dim=16)
    out, scores = mem.read(torch.randn(3, 16), k=4)
    assert out.shape == (3, 16)
    assert torch.all(out == 0)


def test_encoder_decoder_shapes():
    torch.manual_seed(0)
    enc = ByteEncoder(latent_dim=32, emb_dim=16, hidden=48)
    dec = ByteDecoder(latent_dim=32, emb_dim=16, hidden=48)
    x, lengths = pad_batch([to_bytes("hello"), to_bytes("hi")])
    latent = enc(x, lengths)
    assert latent.shape == (2, 32)
    logits = dec(latent, x)
    assert logits.shape == (2, x.shape[1] + 1, 259)
    seqs = dec.generate(latent, max_len=8)
    assert len(seqs) == 2


def test_patcher_segments_cover_and_respect_max():
    torch.manual_seed(0)
    p = EntropyPatcher(max_patch=8)
    p.fit(CORPUS, steps=60, verbose=False)
    p.calibrate(CORPUS, target_avg_patch=4.0)
    data = b"The quick brown fox jumps over the lazy dog."
    spans = p.segment(data)
    assert spans[0][0] == 0 and spans[-1][1] == len(data)
    for (a, b), (c, _) in zip(spans[:-1], spans[1:]):
        assert b == c  # 隙間なく被覆
        assert 1 <= b - a <= 8


def test_recall_pipeline_zero_shot_facts():
    torch.manual_seed(0)
    model = MemoryRecallModel(latent_dim=64, emb_dim=64, hidden=256)
    losses = model.train_codec(steps=500, batch=128, str_len=6, seed=1)
    assert losses[-1] < losses[0]
    facts = make_facts(16, key_len=6, val_len=6, seed=2)
    model.write_facts(facts)  # 勾配学習なしで知識を追加
    preds = model.answer([k for k, _ in facts[:8]])
    correct = sum(p == v for p, (_, v) in zip(preds, facts[:8]))
    assert correct >= 4  # 短時間学習でも過半数は完全想起できるはず


def test_lm_smoke_loss_decreases():
    torch.manual_seed(0)
    patcher = EntropyPatcher(max_patch=12)
    patcher.fit(CORPUS, steps=60)
    patcher.calibrate(CORPUS, target_avg_patch=5.0)
    lm = MnemeLM(dim=64, core_layers=1, core_heads=2, max_patch=12, patcher=patcher)
    opt = torch.optim.Adam(lm.parameters(), lr=1e-3)
    sample = CORPUS[:256]
    first = None
    for _ in range(25):
        loss = lm(sample)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if first is None:
            first = loss.item()
    assert loss.item() < first


def test_lm_memory_write_and_gated_read():
    torch.manual_seed(0)
    patcher = EntropyPatcher(max_patch=12)
    patcher.fit(CORPUS, steps=40)
    patcher.calibrate(CORPUS, target_avg_patch=5.0)
    lm = MnemeLM(dim=64, core_layers=1, core_heads=2, max_patch=12, patcher=patcher)
    lm.memorize(CORPUS[:200])
    assert len(lm.memory) > 0
    loss = lm(CORPUS[200:400], use_memory=True)
    assert torch.isfinite(loss)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok: {name}")
