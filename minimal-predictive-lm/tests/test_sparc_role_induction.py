from minimal_predictive_lm.sparc_role_induction_v2 import (
    SPARCHS10ModelV2,
    SparseRoleInducerV2,
)


EXPECTED = (
    "claim",
    "evidence",
    "example",
    "counter",
    "concession",
    "conclusion",
)


def _weak(code: str) -> str:
    return (
        f"計画{code}は改善を進めると考える。"
        f"なぜなら計画{code}の観測値が向上したからである。"
        f"例えば試行区{code}では達成率が上がった。"
        f"しかし準備負担が残る。"
        f"確かに短期混乱は避けにくい。"
        f"したがって計画{code}は段階導入が重要である。"
    )


def _cue_free(code: str) -> str:
    return (
        f"循環案{code}は資源利用を見直す方針が望ましい。"
        f"導入後の観測で循環案{code}の廃棄量が減少した。"
        f"試行区{code}では再利用率が上昇した。"
        f"初期設備費の負担が残る。"
        f"短期的な混乱も避けられない。"
        f"全体として循環案{code}は段階導入が妥当だ。"
    )


def test_role_induction_transfers_without_bootstrap_cues() -> None:
    inducer = SparseRoleInducerV2()
    inducer.fit(_weak(str(index)) for index in range(80))
    text = _cue_free("X")
    assert all(
        cue not in text
        for cue in ("なぜなら", "例えば", "しかし", "確かに", "したがって")
    )
    assert inducer.predict(text) == EXPECTED
    assert inducer.last_role_candidates == 7
    assert inducer.last_transition_reads == 245


def test_induced_graph_answers_summary_evidence_and_counter() -> None:
    model = SPARCHS10ModelV2()
    model.fit_role_documents(_weak(str(index)) for index in range(80))
    model.ingest_learned_discourse(
        _cue_free("X"), source_id="資料X", title="無接続語論X"
    )
    summary = model.reply("無接続語論Xの主張を要約してください。")
    evidence = model.reply("無接続語論Xの根拠は何ですか？")
    counter = model.reply("無接続語論Xの反対意見は何ですか？")
    assert "段階導入が妥当" in summary.text
    assert "廃棄量が減少" in evidence.text
    assert "初期設備費" in counter.text
    assert model.learned_discourse.last_candidates == 1
    assert model.learned_discourse.last_anchor_reads == 0


def test_role_inducer_and_graph_survive_round_trip() -> None:
    model = SPARCHS10ModelV2()
    model.fit_role_documents(_weak(str(index)) for index in range(40))
    model.ingest_learned_discourse(
        _cue_free("Y"), source_id="資料Y", title="無接続語論Y"
    )
    restored = SPARCHS10ModelV2.from_bytes(model.to_bytes())
    assert restored.learned_discourse.inducer.documents_seen == 40
    reply = restored.reply("無接続語論Yの筆者の主張を要約してください。")
    assert "段階導入が妥当" in reply.text
