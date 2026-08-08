"""実験 1: 知識想起 — 外部記憶 vs パラメータ記憶。

同規模のネットワークで、事実数 N を増やしながら完全一致想起率を比較する。

- MNEME(外部記憶): 汎用の符号化/復号を「一度だけ」学習し、
  事実は外部記憶に書き込むだけ(事実あたり勾配ステップ 0)。
- ベースライン(パラメータ記憶): 事実集合ごとに end-to-end で
  勾配学習して重みに焼き込む(通常の LLM の知識保持の縮図)。

使い方:
    python experiments/run_recall_benchmark.py
"""

import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mneme import MemoryRecallModel, ParametricRecallModel, make_facts
from mneme.recall import exact_match

SIZES = [64, 256, 1024, 4096]
CODEC_STEPS = 1500
BASELINE_STEPS = 2000
KEY_LEN, VAL_LEN = 8, 6


def count_params(model: torch.nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def main() -> None:
    torch.manual_seed(0)

    print("=== MNEME: 汎用コーデックを一度だけ学習(事実は一切見せない) ===")
    mneme = MemoryRecallModel(latent_dim=64, emb_dim=64, hidden=256)
    t0 = time.time()
    mneme.train_codec(steps=CODEC_STEPS, batch=128, str_len=VAL_LEN, seed=0, verbose=True)
    codec_time = time.time() - t0
    print(f"コーデック学習時間: {codec_time:.1f}s / パラメータ数: {count_params(mneme):,}\n")

    rows = []
    for n in SIZES:
        facts = make_facts(n, key_len=KEY_LEN, val_len=VAL_LEN, seed=100 + n)

        # --- MNEME: 書き込みのみ(勾配ステップ 0) ---
        mneme.memory.clear()
        t0 = time.time()
        mneme.write_facts(facts)
        write_time = time.time() - t0
        acc_mem = exact_match(mneme, facts)

        # --- ベースライン: 事実を重みへ勾配学習 ---
        torch.manual_seed(0)
        base = ParametricRecallModel(latent_dim=64, emb_dim=64, hidden=256)
        t0 = time.time()
        base.train_on_facts(facts, steps=BASELINE_STEPS, batch=128, seed=0)
        train_time = time.time() - t0
        acc_base = exact_match(base, facts)

        rows.append((n, acc_mem, write_time, acc_base, train_time))
        print(
            f"N={n:5d} | MNEME acc={acc_mem:6.1%} (書込 {write_time:5.2f}s, 学習 0 step)"
            f" | baseline acc={acc_base:6.1%} (学習 {train_time:5.1f}s, {BASELINE_STEPS} step)"
        )

    print("\n=== 結果まとめ(Markdown) ===")
    print("| 事実数 N | MNEME(外部記憶) | 追加コスト | ベースライン(パラメータ記憶) | 追加コスト |")
    print("|---:|---:|---:|---:|---:|")
    for n, am, wt, ab, tt in rows:
        print(
            f"| {n} | **{am:.1%}** | 書込のみ {wt:.2f}s・勾配 0 step "
            f"| {ab:.1%} | 再学習 {tt:.0f}s・勾配 {BASELINE_STEPS} step |"
        )
    print(f"\n両モデルのパラメータ数: MNEME {count_params(mneme):,} / baseline {count_params(ParametricRecallModel(64, 64, 256)):,}")

    print("\n=== 知識編集デモ: 再学習なしで事実を追加 ===")
    extra = make_facts(5, key_len=KEY_LEN, val_len=VAL_LEN, seed=999)
    mneme.write_facts(extra)
    preds = mneme.answer([k for k, _ in extra])
    for (k, v), p in zip(extra, preds):
        mark = "OK" if p == v else "NG"
        print(f"  {mark}: {k} -> {p} (正解 {v})")


if __name__ == "__main__":
    main()
