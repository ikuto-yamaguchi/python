from __future__ import annotations

from .cic_choice_data import ChoiceExample
from . import learned_causal_ranker as ranker
from . import sparc_hs18_learned_gate as gate


def normalized_causal_choice_rows(
    document: dict[str, object], stop: int
) -> list[ChoiceExample]:
    raw_rows = document.get("examples")
    if not isinstance(raw_rows, list):
        raise ValueError("causal document has no examples")
    yes_labels = {"yes", "(a)", "a", "0"}
    no_labels = {"no", "(b)", "b", "1"}
    result: list[ChoiceExample] = []
    for raw in raw_rows[:stop]:
        if not isinstance(raw, dict):
            continue
        prompt = str(raw.get("input", ""))
        target = str(raw.get("target", "")).strip().lower()
        if target in yes_labels:
            answer_index = 0
        elif target in no_labels:
            answer_index = 1
        else:
            raise ValueError(f"unsupported causal target representation at row {len(result)}")
        stem = prompt.split("\nOptions:", 1)[0].strip()
        result.append(ChoiceExample(prompt, stem, ("Yes", "No"), answer_index))
    return result


def main() -> None:
    ranker.causal_choice_rows = normalized_causal_choice_rows
    gate.main()


if __name__ == "__main__":
    main()
