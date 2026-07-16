from minimal_predictive_lm.sparc_curriculum import heldout_cases, seed_sessions
from minimal_predictive_lm.sparc_language import SPARCLanguageModel


def test_heldout_paraphrase_and_context() -> None:
    model = SPARCLanguageModel("ci").fit_sessions(seed_sessions())
    correct = 0
    for prompt, expected in heldout_cases():
        model.reset()
        correct += int(model.reply(prompt).text == expected)
    assert correct / len(heldout_cases()) >= 0.90

    model.reset()
    assert model.reply("ランニングが趣味です").text == "ランニングが好きなんですね。"
    assert model.reply("それについてもっと教えて").text.startswith("ランニングでは")

    model.reset()
    assert model.reply("AI研究をしています").text == "AI研究に取り組んでいるんですね。"
    assert model.reply("それについてもっと教えて").text.startswith("AI研究では")


def test_online_learning_and_roundtrip() -> None:
    model = SPARCLanguageModel("ci").fit_sessions(seed_sessions())
    model.learn("青い箱の合言葉は？", "みずいろです。")
    restored = SPARCLanguageModel.from_bytes(model.to_bytes())
    assert restored.reply("青い箱の合言葉は？").text == "みずいろです。"
    assert restored.report()["growing_kv_cache_used"] is False


def test_capacity_does_not_preallocate_dense_memory() -> None:
    model = SPARCLanguageModel("desktop-large").fit(
        [("項目Aは？", "答えAです。"), ("項目Bは？", "答えBです。")]
    )
    report = model.report()
    assert report["configured_response_capacity"] == 262144
    assert report["response_assemblies"] == 2
    assert report["capacity_preallocated"] is False
