from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .scalable_recurrent_core import (
    CI_PROFILE,
    LOCAL_4060_PROFILE,
    SCALE_PROFILE,
    MultiScaleRecurrentCore,
)


CAPABILITY_ID = "CAP-GEN-002-SHARED-LATENT-SMOKE"


def mixed_raw_corpus() -> tuple[str, ...]:
    return (
        "日本の高校生は数学、国語、理科、社会、英語、情報を学ぶ。",
        "物体の平均速度は移動距離を経過時間で割って求める。",
        "二次方程式では判別式を使って実数解の個数を判断できる。",
        "細胞のDNAには遺伝情報が保存されている。",
        "酸と塩基が反応すると中和が起こる。",
        "鎌倉幕府は日本史上の武家政権である。",
        "文章を読むときは主張と根拠を区別する。",
        "プログラムの不具合は入力、状態遷移、出力を追跡して調べる。",
        "実験結果を解釈するときは仮説と観測事実を分ける。",
        "誤った解答を直すには途中の推論を検算する。",
        "未知の記号は定義を読み、既知の概念との関係を作る。",
        "会話では直前の質問だけでなく、それまでの文脈を保つ。",
    )


def run_smoke() -> dict[str, object]:
    model = MultiScaleRecurrentCore(CI_PROFILE, seed=7)
    corpus = mixed_raw_corpus() * 2
    training = model.fit_texts(
        corpus,
        epochs=8,
        learning_rate=0.04,
    )
    model.remember("平均速度はどう求める？", "移動距離を経過時間で割る。")
    model.remember("DNAには何が保存される？", "遺伝情報。")
    model.remember("不具合をどう調べる？", "入力、状態遷移、出力を追跡する。")
    resource = model.resource_report()
    mechanism_passed = (
        training.nll_after < training.nll_before * 0.80
        and model.answer("平均速度はどう求める？")
        == "移動距離を経過時間で割る。"
    )
    return {
        "capability_id": CAPABILITY_ID,
        "purpose": (
            "replace the two-kilobyte symbolic critical path with a scalable, "
            "trainable, task-name-free non-Transformer recurrent foundation"
        ),
        "training": asdict(training),
        "resource": resource,
        "profiles": {
            "ci_smoke_bytes": CI_PROFILE.persistent_bytes(),
            "local_4060_bytes": LOCAL_4060_PROFILE.persistent_bytes(),
            "scale_bytes": SCALE_PROFILE.persistent_bytes(),
            "local_4060_training_peak_bytes": (
                LOCAL_4060_PROFILE.training_peak_bytes()
            ),
            "scale_training_peak_bytes": SCALE_PROFILE.training_peak_bytes(),
        },
        "checks": {
            "mixed_raw_japanese_loss_reduced": (
                training.nll_after < training.nll_before * 0.80
            ),
            "shared_memory_works_without_task_name": (
                model.answer("平均速度はどう求める？")
                == "移動距離を経過時間で割る。"
            ),
            "local_profile_exceeds_128_mib": (
                LOCAL_4060_PROFILE.persistent_bytes()
                >= 128 * 1024 * 1024
            ),
            "local_training_plan_fits_8_gib": (
                LOCAL_4060_PROFILE.training_peak_bytes() <= 8 * 1024**3
            ),
            "transformer_not_used": not bool(resource["transformer_used"]),
        },
        "mechanism_passed": mechanism_passed,
        "cap_gen_002_passed": False,
        "highschool_level_passed": False,
        "claim_boundary": (
            "This is an executable scalable architecture smoke test, not evidence "
            "of high-school intelligence. Promotion requires improvement on the "
            "axis-blind integrated public gate and prospectively frozen transfer axes."
        ),
    }


def render_markdown(result: dict[str, object]) -> str:
    training = result["training"]
    profiles = result["profiles"]
    lines = [
        "# CAP-GEN-002 shared latent recurrent smoke",
        "",
        f"Mechanism passed: **{result['mechanism_passed']}**",
        f"CAP-GEN-002 passed: **{result['cap_gen_002_passed']}**",
        f"High-school level passed: **{result['highschool_level_passed']}**",
        "",
        f"- NLL before: **{training['nll_before']:.6f}**",
        f"- NLL after: **{training['nll_after']:.6f}**",
        f"- Training updates: **{training['updates']}**",
        f"- CI smoke plan: **{profiles['ci_smoke_bytes']:,} bytes**",
        f"- RTX 4060 candidate plan: **{profiles['local_4060_bytes']:,} bytes**",
        f"- Next scale plan: **{profiles['scale_bytes']:,} bytes**",
        "",
        "## Claim boundary",
        "",
        str(result["claim_boundary"]),
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_smoke()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "cap_gen_002_shared_latent_smoke.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(result)
    (output_dir / "cap_gen_002_shared_latent_smoke.md").write_text(
        markdown, encoding="utf-8"
    )
    print(markdown, end="")
    if not result["mechanism_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
