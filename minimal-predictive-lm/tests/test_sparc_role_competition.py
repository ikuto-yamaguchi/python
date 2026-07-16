from minimal_predictive_lm.sparc_discourse import SPARCHS9Model
from minimal_predictive_lm.sparc_role_induction_v3 import SPARCHS10ModelV3


def test_learned_layer_does_not_hijack_base_discourse() -> None:
    base = SPARCHS9Model()
    base.ingest_discourse(
        "探究学習を段階的に増やすべきである。"
        "なぜなら生徒の発表回数が増えたからである。"
        "したがって小規模な導入から始める。",
        source_id="探究資料",
        title="探究学習論",
    )
    model = SPARCHS10ModelV3(base)
    weak = (
        "循環計画は改善を進めると考える。"
        "なぜなら廃棄量が減ったからである。"
        "例えば試行区で再利用率が上がった。"
        "しかし費用負担が残る。"
        "確かに混乱は避けにくい。"
        "したがって段階導入が重要である。"
    )
    model.fit_role_documents([weak] * 20)
    cue_free = (
        "循環計画は資源利用を見直す方針が望ましい。"
        "導入後の観測で廃棄量が減少した。"
        "試行区では再利用率が上昇した。"
        "初期設備費の負担が残る。"
        "短期的な混乱も避けられない。"
        "全体として段階導入が妥当だ。"
    )
    model.ingest_learned_discourse(
        cue_free, source_id="循環資料", title="無接続語循環論"
    )
    old_reply = model.reply("探究学習論を要約してください。")
    new_reply = model.reply("無接続語循環論を要約してください。")
    assert "探究学習" in old_reply.text
    assert "循環計画" not in old_reply.text
    assert "段階導入が妥当" in new_reply.text
