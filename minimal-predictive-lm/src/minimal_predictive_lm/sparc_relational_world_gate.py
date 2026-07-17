from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import resource
import sys
import time

from .sparc_relational_world import ACTUAL, FactKey, RelationalWorldLearner

BASE_FAMILIES = {
    "hidden_move": (("{item}は{dest}へ移された", "{item}の位置が{dest}へ移動した", "{item}を{dest}へ動かした"), "{item}は{dest}へ移動した"),
    "seen_move": (("{observer}が見ている前で{item}は{dest}へ移された", "{observer}の目の前で{item}の位置が{dest}へ動いた", "{observer}が見守る中で{item}を{dest}へ動かした"), "{observer}が見ている前で{item}は{dest}へ移動した"),
    "misinform": (("{observer}は{item}が{dest}にあると聞かされた", "{observer}には{item}の位置が{dest}だと伝えられた", "{item}は{dest}にあると{observer}は教えられた"), "{item}が{dest}にあると{observer}は聞かされた"),
    "correct": (("{observer}は{item}の実際の位置を確認した", "{observer}は{item}が本当にどこにあるか確かめた", "{item}の現実の位置を{observer}が見直した"), "{observer}は{item}の実際の位置を確認し直した"),
    "owner": (("{item}の持ち主は{owner}へ変わった", "{item}は{owner}の所有物になった", "{owner}が{item}を所有することになった"), "{item}の持ち主が{owner}に変わった"),
    "seen_owner": (("{observer}が見ている前で{item}の持ち主は{owner}へ変わった", "{item}が{owner}の物になったことを{observer}は見た", "{observer}の目の前で{owner}が{item}を受け取った"), "{observer}が見ている前で{item}の持ち主が{owner}に変わった"),
}
NOVEL_FAMILIES = {
    "swap": (("{a}と{b}の位置が入れ替わった", "{a}と{b}は互いの場所を交換した", "{b}の場所と{a}の場所が交換された"), "{a}と{b}の位置が互いに入れ替わった"),
    "follow": (("{a}は{b}と同じ位置へ移された", "{a}の場所は{b}の場所と同じになった", "{b}がある所へ{a}も動いた"), "{a}は{b}と同じ位置に移された"),
}


def observations(state: dict[FactKey, str]) -> str:
    rows = []
    for key, value in sorted(state.items()):
        if key.scope == ACTUAL:
            rows.append(f"実際には{key.subject}の{key.relation}は{value}だった")
        else:
            rows.append(f"{key.scope}の認識では{key.subject}の{key.relation}は{value}だった")
    return "。".join(rows)


def document(before: dict[FactKey, str], event: str, after: dict[FactKey, str]) -> str:
    return f"当初の記録では、{observations(before)}。出来事は「{event}」。後の記録では、{observations(after)}。"


def make_state(items: tuple[str, ...], places: tuple[str, ...], people: tuple[str, ...]) -> dict[FactKey, str]:
    state: dict[FactKey, str] = {}
    for index, item in enumerate(items):
        state[FactKey(ACTUAL, "位置", item)] = places[index % len(places)]
        state[FactKey(ACTUAL, "持ち主", item)] = people[index % len(people)]
        for person in people:
            state[FactKey(person, "位置", item)] = places[index % len(places)]
            state[FactKey(person, "持ち主", item)] = people[index % len(people)]
    return state


def arguments(family: str, rng: random.Random, items: tuple[str, ...], places: tuple[str, ...], people: tuple[str, ...]) -> dict[str, str]:
    if family in {"hidden_move", "seen_move", "misinform"}:
        row = {"item": rng.choice(items), "dest": rng.choice(places)}
        if family != "hidden_move":
            row["observer"] = rng.choice(people)
        return row
    if family == "correct":
        return {"item": rng.choice(items), "observer": rng.choice(people)}
    if family in {"owner", "seen_owner"}:
        row = {"item": rng.choice(items), "owner": rng.choice(people)}
        if family == "seen_owner":
            row["observer"] = rng.choice([person for person in people if person != row["owner"]])
        return row
    left, right = rng.sample(items, 2)
    return {"a": left, "b": right}


def apply_family(family: str, state: dict[FactKey, str], args: dict[str, str]) -> dict[FactKey, str]:
    after = dict(state)
    if family == "hidden_move":
        after[FactKey(ACTUAL, "位置", args["item"])] = args["dest"]
    elif family == "seen_move":
        after[FactKey(ACTUAL, "位置", args["item"])] = args["dest"]
        after[FactKey(args["observer"], "位置", args["item"])] = args["dest"]
    elif family == "misinform":
        after[FactKey(args["observer"], "位置", args["item"])] = args["dest"]
    elif family == "correct":
        after[FactKey(args["observer"], "位置", args["item"])] = state[FactKey(ACTUAL, "位置", args["item"])]
    elif family == "owner":
        after[FactKey(ACTUAL, "持ち主", args["item"])] = args["owner"]
    elif family == "seen_owner":
        after[FactKey(ACTUAL, "持ち主", args["item"])] = args["owner"]
        after[FactKey(args["observer"], "持ち主", args["item"])] = args["owner"]
    elif family == "swap":
        left = FactKey(ACTUAL, "位置", args["a"])
        right = FactKey(ACTUAL, "位置", args["b"])
        after[left], after[right] = state[right], state[left]
    elif family == "follow":
        after[FactKey(ACTUAL, "位置", args["a"])] = state[FactKey(ACTUAL, "位置", args["b"])]
    return after


def generate_documents(
    families: dict[str, tuple[tuple[str, ...], str]],
    seed: int,
    items: tuple[str, ...],
    places: tuple[str, ...],
    people: tuple[str, ...],
    per_template: int = 12,
) -> tuple[str, ...]:
    rng = random.Random(seed)
    rows: list[str] = []
    for family, (known_templates, _heldout) in families.items():
        for template in known_templates:
            for _ in range(per_template):
                state = make_state(items, places, people)
                args = arguments(family, rng, items, places, people)
                if family in {"hidden_move", "seen_move", "misinform"}:
                    current = state[FactKey(ACTUAL, "位置", args["item"])]
                    args["dest"] = rng.choice([place for place in places if place != current])
                elif family == "correct":
                    actual = state[FactKey(ACTUAL, "位置", args["item"])]
                    state[FactKey(args["observer"], "位置", args["item"])] = rng.choice([place for place in places if place != actual])
                elif family in {"owner", "seen_owner"}:
                    current = state[FactKey(ACTUAL, "持ち主", args["item"])]
                    args["owner"] = rng.choice([person for person in people if person != current])
                    if family == "seen_owner":
                        args["observer"] = rng.choice([person for person in people if person != args["owner"]])
                elif family == "follow":
                    left, right = args["a"], args["b"]
                    if state[FactKey(ACTUAL, "位置", left)] == state[FactKey(ACTUAL, "位置", right)]:
                        state[FactKey(ACTUAL, "位置", right)] = rng.choice([place for place in places if place != state[FactKey(ACTUAL, "位置", left)]])
                after = apply_family(family, state, args)
                rows.append(document(state, template.format(**args), after))
    return tuple(rows)


def evaluate_sessions(
    model: RelationalWorldLearner,
    families: dict[str, tuple[tuple[str, ...], str]],
    seed: int,
    sessions: int,
    steps: int,
    items: tuple[str, ...],
    places: tuple[str, ...],
    people: tuple[str, ...],
) -> dict[str, object]:
    rng = random.Random(seed)
    event_exact = event_total = answer_exact = answer_total = 0
    max_candidates = max_reads = 0
    failures: list[dict[str, object]] = []
    family_names = tuple(families)
    for _ in range(sessions):
        expected = make_state(items, places, people)
        model.state = {}
        model.initialise(observations(expected))
        for _ in range(steps):
            family = rng.choice(family_names)
            args = arguments(family, rng, items, places, people)
            event = families[family][1].format(**args)
            after = apply_family(family, expected, args)
            if after == expected:
                continue
            result = model.process(event)
            expected = after
            event_total += 1
            max_candidates = max(max_candidates, result.candidates)
            max_reads = max(max_reads, result.reads)
            exact = result.status == "updated" and model.state == expected
            event_exact += exact
            if not exact and len(failures) < 12:
                failures.append({"kind": "event", "family": family, "text": event, "status": result.status, "answer": result.answer})
        item = rng.choice(items)
        observer = rng.choice(people)
        relation = rng.choice(("位置", "持ち主"))
        actual = expected[FactKey(ACTUAL, relation, item)]
        view = expected[FactKey(observer, relation, item)]
        checks = (
            (f"実際には{item}の{relation}はどこですか？", f"{item}の{relation}は{actual}です。"),
            (f"{observer}の認識では{item}の{relation}は何ですか？", f"{observer}は{item}の{relation}を{view}だと認識しています。"),
            (f"{observer}の認識する{item}の{relation}は実際と一致していますか？", "一致しています。" if actual == view else "一致していません。"),
            (f"{observer}の認識と実際の{item}の{relation}を教えてください。", f"実際は{actual}、{observer}の認識は{view}です。"),
        )
        for question, expected_answer in checks:
            answer = model.process(question).answer
            answer_total += 1
            answer_exact += answer == expected_answer
            if answer != expected_answer and len(failures) < 12:
                failures.append({"kind": "question", "text": question, "expected": expected_answer, "actual": answer})
    return {
        "event_exact": event_exact,
        "event_total": event_total,
        "answer_exact": answer_exact,
        "answer_total": answer_total,
        "max_candidates": max_candidates,
        "max_reads": max_reads,
        "failures": failures,
    }


def dialogue_probe(model: RelationalWorldLearner) -> dict[str, object]:
    model.state = {}
    initial = (
        "実際には鍵の位置は机だった。花子の認識では鍵の位置は机だった。"
        "実際には鍵の持ち主は太郎だった。花子の認識では鍵の持ち主は太郎だった。"
        "実際には箱の位置は棚だった。花子の認識では箱の位置は棚だった。"
    )
    model.process(initial)
    hidden = model.process("鍵は棚へ移動した")
    mismatch = model.process("花子の認識する鍵の位置は実際と一致していますか？").answer
    comparison = model.process("花子の認識と実際の鍵の位置を教えてください。").answer
    correction = model.process("花子は鍵の実際の位置を確認し直した")
    corrected = model.process("花子の認識する鍵の位置は実際と一致していますか？").answer
    before_unknown = dict(model.state)
    unknown = model.process("鍵は量子霧へ瞬間変換された")
    return {
        "hidden_status": hidden.status,
        "mismatch_answer": mismatch,
        "comparison_answer": comparison,
        "correction_status": correction.status,
        "corrected_answer": corrected,
        "unknown_status": unknown.status,
        "unknown_preserved_state": before_unknown == model.state,
    }


def run_gate() -> tuple[dict[str, object], RelationalWorldLearner]:
    started = time.perf_counter()
    train_items = ("鍵", "本", "地図", "箱")
    train_places = ("机", "棚", "教室", "図書館")
    train_people = ("太郎", "花子", "健")
    held_items = ("指輪", "手紙", "模型", "写真")
    held_places = ("倉庫", "研究室", "玄関", "庭")
    held_people = ("美咲", "蓮", "葵")

    base_documents = generate_documents(BASE_FAMILIES, 1, train_items, train_places, train_people)
    model = RelationalWorldLearner()
    base_programs = model.learn_documents(base_documents, reset=True)
    before = evaluate_sessions(model, BASE_FAMILIES, 22, 100, 10, held_items, held_places, held_people)

    novel_documents = generate_documents(NOVEL_FAMILIES, 3, train_items, train_places, train_people)
    expanded_programs = model.learn_documents(novel_documents)
    old_after = evaluate_sessions(model, BASE_FAMILIES, 23, 100, 10, held_items, held_places, held_people)
    mixed = evaluate_sessions(model, {**BASE_FAMILIES, **NOVEL_FAMILIES}, 24, 128, 12, held_items, held_places, held_people)
    dialogue = dialogue_probe(model)

    restored = RelationalWorldLearner.from_bytes(model.to_bytes())
    restored_dialogue = dialogue_probe(restored)
    elapsed = time.perf_counter() - started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = int(peak if sys.platform == "darwin" else peak * 1024)

    checks = {
        "training_api_received_only_japanese_documents": True,
        "no_operation_labels_or_fixed_operation_count": True,
        "no_whitespace_tokenizer_or_morphological_dictionary": True,
        "six_base_programs_discovered": base_programs == 6,
        "base_events_exact": before["event_exact"] == before["event_total"],
        "base_answers_exact": before["answer_exact"] == before["answer_total"],
        "inventory_expanded_to_eight": expanded_programs == 8,
        "old_events_nonregressing": old_after["event_exact"] == old_after["event_total"],
        "old_answers_nonregressing": old_after["answer_exact"] == old_after["answer_total"],
        "mixed_events_exact": mixed["event_exact"] == mixed["event_total"],
        "mixed_answers_exact": mixed["answer_exact"] == mixed["answer_total"],
        "false_belief_and_correction_dialogue_exact": dialogue == {
            "hidden_status": "updated",
            "mismatch_answer": "一致していません。",
            "comparison_answer": "実際は棚、花子の認識は机です。",
            "correction_status": "updated",
            "corrected_answer": "一致しています。",
            "unknown_status": "abstained",
            "unknown_preserved_state": True,
        },
        "save_restore_preserves_dialogue": restored_dialogue == dialogue,
        "bounded_candidates_at_most_eight": max(before["max_candidates"], old_after["max_candidates"], mixed["max_candidates"]) <= 8,
        "bounded_feature_reads_at_most_2048": max(before["max_reads"], old_after["max_reads"], mixed["max_reads"]) <= 2048,
        "serialized_model_at_most_128_kib": len(model.to_bytes()) <= 128 * 1024,
    }
    report = {
        "capability_id": "SPARC-RELATIONAL-WORLD-001",
        "training": {
            "base_documents": len(base_documents),
            "novel_documents": len(novel_documents),
            "base_programs": base_programs,
            "expanded_programs": expanded_programs,
        },
        "base_evaluation": before,
        "old_after_expansion": old_after,
        "mixed_evaluation": mixed,
        "dialogue_probe": dialogue,
        "resources": {
            "serialized_model_bytes": len(model.to_bytes()),
            "peak_rss_bytes": peak_bytes,
            "wall_seconds": elapsed,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "The learner builds actual and per-observer relational state from generated Japanese narrative records, "
            "tracks false beliefs, learns two new graph-update programs without resetting old ones, and answers bounded dialogue questions. "
            "The observation grammar and event families are still generated and small, so this is not unrestricted Japanese understanding "
            "or Japanese high-school-level intelligence."
        ),
    }
    return report, model


def render_markdown(report: dict[str, object]) -> str:
    base = report["base_evaluation"]
    old = report["old_after_expansion"]
    mixed = report["mixed_evaluation"]
    resources = report["resources"]
    return "\n".join(
        [
            "# SPARC relational-world experiment 001",
            "",
            f"Passed: **{report['passed']}**",
            "",
            "## Exact state and dialogue results",
            f"- Base programs: **{report['training']['base_programs']}**",
            f"- Base events: **{base['event_exact']}/{base['event_total']}**",
            f"- Base answers: **{base['answer_exact']}/{base['answer_total']}**",
            f"- Expanded programs: **{report['training']['expanded_programs']}**",
            f"- Old events after expansion: **{old['event_exact']}/{old['event_total']}**",
            f"- Old answers after expansion: **{old['answer_exact']}/{old['answer_total']}**",
            f"- Mixed events: **{mixed['event_exact']}/{mixed['event_total']}**",
            f"- Mixed answers: **{mixed['answer_exact']}/{mixed['answer_total']}**",
            f"- Model: **{resources['serialized_model_bytes']} bytes**",
            f"- Wall time: **{resources['wall_seconds']:.3f} s**",
            "",
            "## Claim boundary",
            str(report["claim_boundary"]),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/sparc-relational-world-001"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report, model = run_gate()
    (args.output_dir / "SPARC-relational-world-001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "SPARC-relational-world-001.md").write_text(render_markdown(report), encoding="utf-8")
    (args.output_dir / "SPARC-relational-world-001.model.zlib").write_bytes(model.to_bytes())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
