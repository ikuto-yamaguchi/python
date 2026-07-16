from minimal_predictive_lm.sparc_dialogue_composer import (
    DialogueDemonstration,
    DialoguePlan,
    SparseDialogueComposer,
)


def _composer() -> SparseDialogueComposer:
    rows = (
        DialogueDemonstration(
            DialoguePlan(
                "explain",
                subject="水の沸点",
                answer="水は100度で沸騰します",
                evidence="標準気圧で蒸気圧が釣り合うため",
                caveat="気圧が変わると沸点も変わります",
                source="理科資料A",
            ),
            "水の沸点については、水は100度で沸騰します。"
            "理由は標準気圧で蒸気圧が釣り合うためです。"
            "ただし、気圧が変わると沸点も変わります。"
            "出典は理科資料Aです。",
        ),
        DialogueDemonstration(
            DialoguePlan(
                "explain",
                subject="光合成",
                answer="植物は光エネルギーを化学エネルギーへ変換します",
                evidence="葉緑体で有機物を合成するため",
                caveat="二酸化炭素濃度などにも制約されます",
                source="生物資料B",
            ),
            "光合成については、植物は光エネルギーを化学エネルギーへ変換します。"
            "理由は葉緑体で有機物を合成するためです。"
            "ただし、二酸化炭素濃度などにも制約されます。"
            "出典は生物資料Bです。",
        ),
        DialogueDemonstration(
            DialoguePlan(
                "correction",
                subject="惑星Xの公転周期",
                old_value="320日",
                new_value="340日",
                evidence="改訂観測記録で再計算されたため",
            ),
            "惑星Xの公転周期は、320日ではなく340日です。"
            "根拠は改訂観測記録で再計算されたためです。",
        ),
        DialogueDemonstration(
            DialoguePlan(
                "correction",
                subject="資料Yの発行年",
                old_value="2019年",
                new_value="2021年",
                evidence="新版の奥付を確認したため",
            ),
            "資料Yの発行年は、2019年ではなく2021年です。"
            "根拠は新版の奥付を確認したためです。",
        ),
    )
    model = SparseDialogueComposer()
    assert model.fit(rows) >= 2
    return model


def test_unseen_slot_combination_is_composed_instead_of_selected_wholesale():
    model = _composer()
    plan = DialoguePlan(
        "explain",
        subject="慣性の法則",
        answer="外力がなければ物体の運動状態は保たれます",
        evidence="運動方程式で合力がゼロなら加速度もゼロになるため",
        caveat="摩擦がある環境では外力を無視できません",
        source="物理資料C",
    )
    result = model.compose(plan)
    assert result.mechanism == "learned-slot-template"
    assert "慣性の法則" in result.text
    assert "運動方程式" in result.text
    assert "物理資料C" in result.text
    assert result.text not in {
        "水の沸点については、水は100度で沸騰します。理由は標準気圧で蒸気圧が釣り合うためです。",
        "光合成については、植物は光エネルギーを化学エネルギーへ変換します。",
    }


def test_correction_template_recombines_unseen_subject_and_values():
    model = _composer()
    result = model.compose(
        DialoguePlan(
            "correction",
            subject="恒星Zの距離",
            old_value="42光年",
            new_value="39光年",
            evidence="年周視差の再解析で更新されたため",
        )
    )
    assert result.mechanism == "learned-slot-template"
    assert result.text == (
        "恒星Zの距離は、42光年ではなく39光年です。"
        "根拠は年周視差の再解析で更新されたためです。"
    )


def test_followup_uses_only_bounded_latest_focus_after_thirty_turns():
    model = _composer()
    for index in range(30):
        model.compose(
            DialoguePlan(
                "explain",
                subject=f"主題{index}",
                answer=f"説明{index}",
                evidence=f"根拠{index}",
                caveat=f"留保{index}",
                source=f"資料{index}",
            )
        )
    followup = model.compose(
        DialoguePlan(
            "explain",
            answer="追加説明です",
            evidence="直前の主題を固定長焦点から取得したため",
            caveat="古い履歴全体は走査していません",
            source="焦点記憶",
        ),
        user_text="それについてもう少し詳しく教えて",
    )
    assert "主題29" in followup.text
    assert "主題0" not in followup.text
    assert len(model.focus) <= 32


def test_save_restore_preserves_templates_and_focus():
    model = _composer()
    model.compose(
        DialoguePlan(
            "explain",
            subject="保存対象",
            answer="保存前の説明",
            evidence="復元試験のため",
            caveat="これは回帰試験です",
            source="試験資料",
        )
    )
    restored = SparseDialogueComposer.from_bytes(model.to_bytes())
    result = restored.compose(
        DialoguePlan(
            "explain",
            answer="復元後の追加説明",
            evidence="保存された焦点を使えたため",
            caveat="全履歴は保持していません",
            source="復元資料",
        ),
        user_text="それについて詳しく",
    )
    assert "保存対象" in result.text
    assert restored.report()["complete_response_selection_used"] is False
    assert restored.report()["full_history_scan_used"] is False
