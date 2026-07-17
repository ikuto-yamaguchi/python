from minimal_predictive_lm.sparc_text_world_gate import (
    BASE,
    NOVEL,
    event,
    training_documents,
    unlabelled_corpus,
)
from minimal_predictive_lm.text_world_learner import TextWorldLearner


def model():
    learner = TextWorldLearner(confidence_threshold=0.20, margin_threshold=0.006)
    learner.learn_documents(
        training_documents(tuple(BASE), 11),
        unlabelled_sentences=unlabelled_corpus((*BASE, *NOVEL)),
        reset=True,
    )
    return learner


def test_reads_updates_and_answers_without_state_table():
    learner = model()
    learner.chat("北倉庫には40個あった。")
    learner.chat("南倉庫には20個あった。")
    assert (
        learner.chat(
            event("add", BASE["add"][1], "北倉庫", "南倉庫", 7, heldout=True)
        )
        == "出来事を反映しました。"
    )
    assert learner.chat("北倉庫は現在何個ですか？") == "47個です。"


def test_multistep_provenance_and_arithmetic():
    learner = model()
    learner.chat("甲棚には50個あった。")
    learner.chat("乙棚には30個あった。")
    first = event(
        "transfer", BASE["transfer"][1], "甲棚", "乙棚", 8, heldout=True
    )
    assert learner.chat(first) == "出来事を反映しました。"
    assert learner.chat("甲棚と乙棚の合計はいくつですか？") == "80個です。"
    assert (
        learner.chat("乙棚が現在の値になった理由は何ですか？")
        == f"「{first.rstrip('。')}」という出来事を反映したためです。"
    )


def test_continual_program_growth_and_restore():
    learner = model()
    assert len(learner.programs) == 6
    learner.learn_documents(training_documents(tuple(NOVEL), 12), reset=False)
    assert len(learner.programs) == 8
    restored = TextWorldLearner.from_bytes(learner.to_bytes())
    restored.chat("光班には12個あった。")
    restored.chat("影班には5個あった。")
    assert (
        restored.chat(
            event("sum", NOVEL["sum"][1], "光班", "影班", 0, heldout=True)
        )
        == "出来事を反映しました。"
    )
    assert restored.chat("光班は何個ですか？") == "17個です。"
