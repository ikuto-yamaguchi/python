"""実験 2: エントロピー動的パッチング(トークナイザーの置き換え)のデモ。

極小のバイトレベル LM を学習し、次バイト予測エントロピーが跳ねる位置で
パッチを区切る。予測が容易な区間(単語の続き、定型句)は長いパッチに
圧縮され、情報密度の高い位置(単語の頭、未知の並び)で細かく切れる
ことを確認する。

使い方:
    python experiments/run_patcher_demo.py
"""

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mneme import EntropyPatcher

CORPUS = (
    "The quick brown fox jumps over the lazy dog. "
    "Memory is the mother of all wisdom. "
    "Specialized intelligence needs exact recall, not a bigger vocabulary. "
    "A small reasoning core with a large exact memory can solve complex tasks. "
    "Knowledge should live in an editable store, not in frozen weights. "
).encode("utf-8") * 30

SAMPLES = [
    "Memory is the mother of all wisdom.",
    "The quick brown fox jumps over the lazy dog.",
    "Specialized intelligence needs exact recall.",
    "zqxv jkwp unseen bytes 12345",  # 分布外: 細かく切れるはず
]


def main() -> None:
    torch.manual_seed(0)
    patcher = EntropyPatcher(emb_dim=32, hidden=96, max_patch=16)
    print("=== 極小バイト LM を学習(エントロピー推定器) ===")
    losses = patcher.fit(CORPUS, steps=400, batch=32, seqlen=128, verbose=True)
    print(f"loss: {losses[0]:.3f} -> {losses[-1]:.3f}")

    th = patcher.calibrate(CORPUS, target_avg_patch=6.0)
    print(f"閾値(平均パッチ長 6 バイト狙い): {th:.3f} bits\n")

    print("=== パッチ境界の可視化('|' が境界) ===")
    total_bytes = 0
    total_patches = 0
    for s in SAMPLES:
        data = s.encode("utf-8")
        spans = patcher.segment(data)
        total_bytes += len(data)
        total_patches += len(spans)
        print(f"  [{len(data):3d} bytes -> {len(spans):2d} patches] {patcher.show(s)}")

    print(
        f"\nサンプル平均パッチ長: {total_bytes / total_patches:.2f} bytes/patch"
        "(分布外サンプル込み)"
    )

    # ドメイン内テキスト(学習コーパスと同分布の 1 周期)での圧縮率
    domain = CORPUS[: len(CORPUS) // 30]
    spans = patcher.segment(domain)
    ratio = len(domain) / len(spans)
    print(
        f"ドメイン内テキストの平均パッチ長: {ratio:.2f} bytes/patch "
        f"→ 潜在系列はバイト列の 1/{ratio:.1f}、"
        f"コアの O(L^2) 注意計算は約 1/{ratio * ratio:.0f}"
    )
    n_params = sum(p.numel() for p in patcher.lm.parameters())
    print(f"エントロピー推定器のパラメータ数: {n_params:,}(語彙表 0 エントリ)")


if __name__ == "__main__":
    main()
