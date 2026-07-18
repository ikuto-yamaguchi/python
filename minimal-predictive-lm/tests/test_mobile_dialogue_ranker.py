from minimal_predictive_lm.mobile_dialogue_ranker import (
    DialoguePair,
    QuantizedDialogueRanker,
)


TRAIN = (
    DialoguePair("平均速度はどう求めますか", "移動距離を経過時間で割ります。"),
    DialoguePair("平均の速さの計算方法は", "移動距離を経過時間で割ります。"),
    DialoguePair("速さは距離と時間からどう計算する", "移動距離を経過時間で割ります。"),
    DialoguePair("DNAには何が入っていますか", "遺伝情報が保存されています。"),
    DialoguePair("DNAが保存するものは何", "遺伝情報が保存されています。"),
    DialoguePair("酸と塩基が反応するとどうなる", "中和が起こります。"),
    DialoguePair("酸性とアルカリ性を混ぜると", "中和が起こります。"),
    DialoguePair("鎌倉幕府は何ですか", "日本史上の武家政権です。"),
    DialoguePair("鎌倉幕府の性質を説明して", "日本史上の武家政権です。"),
    DialoguePair("バグを調べる基本は", "入力、状態遷移、出力を追跡します。"),
    DialoguePair("不具合調査では何を追う", "入力、状態遷移、出力を追跡します。"),
    DialoguePair("文章の主張を確かめるには", "主張と根拠を区別します。"),
    DialoguePair("読解で意見と理由をどう扱う", "主張と根拠を区別します。"),
)


HELD_OUT = (
    ("距離と時間が分かると平均速度はどう出すの", "移動距離を経過時間で割ります。"),
    ("DNAの中には何が記録されているの", "遺伝情報が保存されています。"),
    ("酸とアルカリを合わせたら何が起きる", "中和が起こります。"),
    ("鎌倉幕府ってどんな政権", "日本史上の武家政権です。"),
    ("プログラムの問題を調査するとき何を確認する", "入力、状態遷移、出力を追跡します。"),
    ("説明文では結論と理由をどう読む", "主張と根拠を区別します。"),
)


def build_model():
    model, report = QuantizedDialogueRanker.fit(
        TRAIN,
        pair_dimensions=8192,
        retrieval_dimensions=2048,
        epochs=8,
        top_weights=4096,
        centroid_top_features=96,
        max_candidates=8,
        seed=3,
    )
    return model, report


def test_answers_unseen_cross_domain_paraphrases():
    model, report = build_model()
    assert report.pairs == len(TRAIN)
    assert report.responses == 6
    assert all(prompt not in {row.prompt for row in TRAIN} for prompt, _ in HELD_OUT)
    correct = 0
    for prompt, expected in HELD_OUT:
        prediction = model.predict(prompt, minimum_confidence=0.02)
        correct += int(prediction.response == expected)
        assert prediction.candidates_scored <= 8
    assert correct >= 5


def test_serialization_preserves_predictions():
    model, _report = build_model()
    restored = QuantizedDialogueRanker.from_bytes(model.to_bytes())
    for prompt, _expected in HELD_OUT:
        assert restored.predict(prompt, minimum_confidence=0.02).response == model.predict(
            prompt, minimum_confidence=0.02
        ).response


def test_unknown_prompt_can_abstain():
    model, _report = build_model()
    prediction = model.predict(
        "量子色力学の繰り込み群について証明してください",
        minimum_confidence=10.0,
    )
    assert prediction.response is None


def test_mobile_resource_and_claim_boundaries():
    model, _report = build_model()
    report = model.resource_report()
    assert report["serialized_bytes"] < 512_000
    assert report["estimated_active_weight_bytes"] < 4_000_000
    assert report["task_name_input_used"] is False
    assert report["domain_router_used"] is False
    assert report["highschool_level_passed"] is False
