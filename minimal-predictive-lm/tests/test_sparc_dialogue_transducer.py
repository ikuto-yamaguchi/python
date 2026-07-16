import random
import string

from minimal_predictive_lm.sparc_dialogue_transducer import (
    DialoguePair,
    SparseDialogueTransducer,
)


def _token(rng: random.Random, prefix: str) -> str:
    return prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(8))


def _pairs(count: int, *, seed: int, shifted: bool = False) -> tuple[DialoguePair, ...]:
    rng = random.Random(seed)
    rows: list[DialoguePair] = []
    for index in range(count):
        family = index % 4
        if family == 0:
            subject = _token(rng, "主題")
            answer = _token(rng, "回答")
            evidence = _token(rng, "根拠")
            caveat = _token(rng, "留保")
            source = _token(rng, "資料")
            user = (
                f"説明対象:{subject}; 資料:{source}; 注意:{caveat}; 理由:{evidence}; 結論:{answer}"
                if shifted
                else f"{subject}を説明。答え={answer}、根拠={evidence}、留保={caveat}、資料={source}。"
            )
            assistant = (
                f"{subject}については、{answer}。理由は{evidence}です。"
                f"ただし、{caveat}。出典は{source}です。"
            )
        elif family == 1:
            subject = _token(rng, "訂正主題")
            old_value = _token(rng, "旧値")
            new_value = _token(rng, "新値")
            evidence = _token(rng, "訂正根拠")
            user = (
                f"修正対象:{subject}; 根拠:{evidence}; 正:{new_value}; 誤:{old_value}"
                if shifted
                else f"{subject}を訂正。旧={old_value}、新={new_value}、根拠={evidence}。"
            )
            assistant = (
                f"{subject}は、{old_value}ではなく{new_value}です。"
                f"根拠は{evidence}です。"
            )
        elif family == 2:
            subject = _token(rng, "回答主題")
            answer = _token(rng, "結論")
            evidence = _token(rng, "証拠")
            source = _token(rng, "出典")
            user = (
                f"問い:{subject}; 出典:{source}; 証拠:{evidence}; 回答:{answer}"
                if shifted
                else f"{subject}に回答。結論={answer}、証拠={evidence}、出典={source}。"
            )
            assistant = (
                f"{subject}への答えは{answer}です。"
                f"根拠は{evidence}で、出典は{source}です。"
            )
        else:
            subject = _token(rng, "比較主題")
            answer = _token(rng, "比較結論")
            evidence = _token(rng, "比較根拠")
            caveat = _token(rng, "比較留保")
            user = (
                f"比較案件:{subject}; 注意:{caveat}; 証拠:{evidence}; 判断:{answer}"
                if shifted
                else f"{subject}を比較。結論={answer}、根拠={evidence}、留保={caveat}。"
            )
            assistant = (
                f"{subject}を比べると、{answer}。"
                f"根拠は{evidence}です。ただし、{caveat}。"
            )
        rows.append(DialoguePair(user, assistant))
    return tuple(rows)


def test_induces_copy_schemas_without_explicit_semantic_slots() -> None:
    model = SparseDialogueTransducer(max_schemas=32, max_candidates=8)
    learned = model.fit(_pairs(1_000, seed=1910))
    heldout = _pairs(128, seed=1911)
    predictions = [model.transduce(row.user) for row in heldout]
    assert learned <= 8
    assert all(prediction.text == row.assistant for prediction, row in zip(predictions, heldout))
    assert max(prediction.candidates for prediction in predictions) <= 8
    assert model.report()["explicit_semantic_slots_used"] is False


def test_unseen_surface_shift_abstains_instead_of_hallucinating() -> None:
    model = SparseDialogueTransducer(max_schemas=32, max_candidates=8)
    model.fit(_pairs(1_000, seed=1912))
    shifted = _pairs(64, seed=1913, shifted=True)
    predictions = [model.transduce(row.user) for row in shifted]
    assert all(prediction.text is None for prediction in predictions)
    assert all(prediction.mechanism == "abstain-unseen-surface" for prediction in predictions)


def test_save_restore_preserves_induced_transduction_programs() -> None:
    model = SparseDialogueTransducer(max_schemas=32, max_candidates=8)
    model.fit(_pairs(1_000, seed=1914))
    restored = SparseDialogueTransducer.from_bytes(model.to_bytes())
    row = _pairs(1, seed=1915)[0]
    assert restored.transduce(row.user).text == row.assistant
    assert restored.report()["complete_response_selection_used"] is False
