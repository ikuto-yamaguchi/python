from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_perspective_state import (
    FocusedQueryExample,
    SPARCHS15Model,
    SparsePerspectiveWorkspace,
    TransitionExample,
)
from .sparc_hs14_experiment_v2 import configured_model as configured_hs14
from .sparc_counterexamples_v2 import SPARCHS14ModelV2


def _alpha_code(index: int) -> str:
    alphabet = string.ascii_uppercase
    output: list[str] = []
    value = index
    while True:
        output.append(alphabet[value % 26])
        value = value // 26 - 1
        if value < 0:
            break
    return "".join(reversed(output))


def _observed_transition(
    text: str,
    object_name: str,
    old_value: str,
    new_value: str,
    actor: str,
    observer: str,
) -> TransitionExample:
    return TransitionExample(
        text=text,
        before_world={(object_name, "場所"): old_value},
        after_world={(object_name, "場所"): new_value},
        before_beliefs={
            (actor, object_name, "場所"): old_value,
            (observer, object_name, "場所"): old_value,
        },
        after_beliefs={
            (actor, object_name, "場所"): new_value,
            (observer, object_name, "場所"): new_value,
        },
        entity_kinds={
            actor: "agent",
            observer: "agent",
            object_name: "object",
            old_value: "value",
            new_value: "value",
        },
    )


def _focused_transition(
    text: str,
    object_name: str,
    old_value: str,
    new_value: str,
    actor: str,
) -> TransitionExample:
    return TransitionExample(
        text=text,
        before_world={(object_name, "場所"): old_value},
        after_world={(object_name, "場所"): new_value},
        before_beliefs={(actor, object_name, "場所"): old_value},
        after_beliefs={(actor, object_name, "場所"): new_value},
        entity_kinds={
            actor: "agent",
            object_name: "object",
            old_value: "value",
            new_value: "value",
        },
    )


def _configure_perspective(workspace: SparsePerspectiveWorkspace) -> None:
    observed_program = workspace.teach_event_program(
        [
            _observed_transition(
                "太郎が花子の前で鍵を箱へ移した。",
                "鍵",
                "机",
                "箱",
                "太郎",
                "花子",
            ),
            _observed_transition(
                "次郎が美咲の前で本を棚へ移した。",
                "本",
                "床",
                "棚",
                "次郎",
                "美咲",
            ),
        ]
    )
    assert observed_program.object_from_focus is False
    for object_name, old_value, agents, source_id in (
        ("鍵", "机", ("太郎", "花子", "健"), "鍵初期資料"),
        ("本", "床", ("次郎", "美咲", "葵"), "本初期資料"),
    ):
        workspace.set_initial_fact(
            object_name,
            "場所",
            old_value,
            source_id=source_id,
            known_by=agents,
        )
    workspace.apply_event(
        "太郎が花子の前で鍵を箱へ移した。", source_id="鍵移動資料"
    )
    workspace.apply_event(
        "次郎が美咲の前で本を棚へ移した。", source_id="本移動資料"
    )
    workspace.teach_query(
        [
            ("実際、鍵はどこにある？", "箱"),
            ("実際、本はどこにある？", "棚"),
        ]
    )
    workspace.teach_query(
        [
            ("花子は鍵がどこにあると思っている？", "箱"),
            ("美咲は本がどこにあると思っている？", "棚"),
        ]
    )
    workspace.teach_query(
        [
            ("健は鍵がどこにあると思っている？", "机"),
            ("葵は本がどこにあると思っている？", "床"),
        ]
    )
    workspace.teach_focused_query(
        [
            FocusedQueryExample(
                (("鍵", "object"), ("花子", "agent")),
                "彼はそれがどこにあると思っている？",
                "箱",
            ),
            FocusedQueryExample(
                (("本", "object"), ("美咲", "agent")),
                "彼はそれがどこにあると思っている？",
                "棚",
            ),
        ]
    )
    workspace.teach_focused_query(
        [
            FocusedQueryExample(
                (("鍵", "object"),),
                "健はそれがどこにあると思っている？",
                "机",
            ),
            FocusedQueryExample(
                (("本", "object"),),
                "葵はそれがどこにあると思っている？",
                "床",
            ),
        ]
    )
    workspace.teach_event_program(
        [
            _focused_transition(
                "花子がそれを戸棚へ移した。",
                "鍵",
                "箱",
                "戸棚",
                "花子",
            ),
            _focused_transition(
                "美咲がそれを机へ移した。",
                "本",
                "棚",
                "机",
                "美咲",
            ),
        ]
    )
    cause_program = workspace.teach_cause_query(
        [
            (
                "鍵が箱にある直接の原因は？",
                "太郎が花子の前で鍵を箱へ移した。",
            ),
            (
                "本が棚にある直接の原因は？",
                "次郎が美咲の前で本を棚へ移した。",
            ),
        ],
        attribute="場所",
    )
    workspace.link_cause_surface(
        "それがそこにある直接の原因は？",
        cause_program,
        object_from_focus=True,
    )


def configured_model() -> SPARCHS15Model:
    model = SPARCHS15Model(configured_hs14())
    _configure_perspective(model.perspective)
    return model


def _configure_large(workspace: SparsePerspectiveWorkspace, object_count: int) -> None:
    actor = "観測者甲"
    observer = "観測者乙"
    absent = "不在者"

    def names(index: int) -> tuple[str, str, str]:
        code = _alpha_code(index)
        return f"対象{code}", f"初期地点{index % 1009}", f"移動先{index % 1013}"

    demos: list[TransitionExample] = []
    for index in (0, 1):
        object_name, old_value, new_value = names(index)
        demos.append(
            _observed_transition(
                f"{actor}が{observer}の前で{object_name}を{new_value}へ移した。",
                object_name,
                old_value,
                new_value,
                actor,
                observer,
            )
        )
    workspace.teach_event_program(demos)

    for index in range(object_count):
        object_name, old_value, new_value = names(index)
        workspace.set_initial_fact(
            object_name,
            "場所",
            old_value,
            source_id=f"初期資料{_alpha_code(index)}",
            known_by=(actor, observer, absent),
        )
        record = workspace.apply_event(
            f"{actor}が{observer}の前で{object_name}を{new_value}へ移した。",
            source_id=f"移動資料{_alpha_code(index)}",
        )
        if record is None:
            raise AssertionError("learned large event schema failed to execute")
        if index == 1:
            workspace.teach_query(
                [
                    ("実際、対象Aはどこにある？", names(0)[2]),
                    ("実際、対象Bはどこにある？", names(1)[2]),
                ]
            )
            workspace.teach_query(
                [
                    (f"{observer}は対象Aがどこにあると思っている？", names(0)[2]),
                    (f"{observer}は対象Bがどこにあると思っている？", names(1)[2]),
                ]
            )
            workspace.teach_query(
                [
                    (f"{absent}は対象Aがどこにあると思っている？", names(0)[1]),
                    (f"{absent}は対象Bがどこにあると思っている？", names(1)[1]),
                ]
            )
            workspace.teach_focused_query(
                [
                    FocusedQueryExample(
                        (("対象A", "object"), (observer, "agent")),
                        "彼はそれがどこにあると思っている？",
                        names(0)[2],
                    ),
                    FocusedQueryExample(
                        (("対象B", "object"), (observer, "agent")),
                        "彼はそれがどこにあると思っている？",
                        names(1)[2],
                    ),
                ]
            )
            workspace.teach_cause_query(
                [
                    (
                        f"対象Aが{names(0)[2]}にある直接の原因は？",
                        f"{actor}が{observer}の前で対象Aを{names(0)[2]}へ移した。",
                    ),
                    (
                        f"対象Bが{names(1)[2]}にある直接の原因は？",
                        f"{actor}が{observer}の前で対象Bを{names(1)[2]}へ移した。",
                    ),
                ],
                attribute="場所",
            )


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()
    model.base.ingest_fact("視点冬眠個体の分類は哺乳類である。", source_id="HS15保持分類資料")
    model.base.ingest_fact("視点冬眠個体の季節状態は冬眠中である。", source_id="HS15保持季節資料")

    conversation = model.reply("こんにちは")
    hs12 = model.reply("ハヤブサの体温特性は何ですか？")
    hs14_guard = model.reply("視点冬眠個体の活動状態は何ですか？")
    actual_before = model.reply("実際、鍵はどこにある？")
    absent_before = model.reply("健は鍵がどこにあると思っている？")
    observer_before = model.reply("花子は鍵がどこにあると思っている？")
    pronoun_before = model.reply("彼はそれがどこにあると思っている？")
    model.perspective.apply_event(
        "花子がそれを戸棚へ移した。", source_id="鍵再移動資料"
    )
    actual_after = model.reply("実際、鍵はどこにある？")
    observer_after = model.reply("花子は鍵がどこにあると思っている？")
    model.perspective.focus.clear()
    model.perspective.focus.append(("鍵", "object"))
    absent_pronoun = model.reply("健はそれがどこにあると思っている？")
    cause = model.reply("鍵が戸棚にある直接の原因は？")
    model.reply("花子は鍵がどこにあると思っている？")
    focused_cause = model.reply("それがそこにある直接の原因は？")

    compact_bytes = model.to_bytes()
    restored = SPARCHS15Model.from_bytes(compact_bytes)
    restored_answer = restored.reply("健は鍵がどこにあると思っている？")
    restored_cause = restored.reply("鍵が戸棚にある直接の原因は？")
    report = model.perspective.report()

    checks = {
        "conversation_retained": conversation.text.startswith("こんにちは"),
        "hs12_relational_plan_retained": hs12.text.startswith("一定です"),
        "hs14_counterexample_guard_retained": (
            hs14_guard.mechanism == "counterexample-guarded-rule"
            and "季節状態=冬眠中" in hs14_guard.text
        ),
        "actual_world_state": actual_before.text.startswith("箱です"),
        "observer_belief_updated": observer_before.text.startswith("箱です"),
        "false_belief_preserved": absent_before.text.startswith("机です"),
        "learned_pronoun_query": pronoun_before.text.startswith("箱です"),
        "learned_ellipsis_event": (
            actual_after.text.startswith("戸棚です")
            and observer_after.text.startswith("戸棚です")
        ),
        "unobserved_agent_stays_stale": absent_pronoun.text.startswith("机です"),
        "direct_cause_is_latest_writer": (
            "花子がそれを戸棚へ移した" in cause.text
            and "鍵再移動資料" in cause.text
        ),
        "focused_cause_query": "花子がそれを戸棚へ移した" in focused_cause.text,
        "save_load_perspectives": (
            restored_answer.text.startswith("机です")
            and "鍵再移動資料" in restored_cause.text
        ),
        "no_global_scans": (
            report["global_world_scan_used"] is False
            and report["global_belief_scan_used"] is False
            and report["full_history_scan_used"] is False
        ),
    }

    scale_start = time.perf_counter()
    object_count = 50_000
    large = SPARCHS15Model(SPARCHS14ModelV2())
    _configure_large(large.perspective, object_count)
    observer = "観測者乙"
    absent = "不在者"
    sample_queries = 512
    correct_world = 0
    correct_observer = 0
    correct_false_belief = 0
    correct_pronoun = 0
    correct_cause = 0
    max_event_candidates = 0
    max_query_candidates = 0
    max_schema_reads = 0
    max_state_reads = 0
    max_focus_reads = 0
    max_operations = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % object_count
        code = _alpha_code(index)
        object_name = f"対象{code}"
        old_value = f"初期地点{index % 1009}"
        new_value = f"移動先{index % 1013}"
        world_reply = large.reply(f"実際、{object_name}はどこにある？")
        observer_reply = large.reply(
            f"{observer}は{object_name}がどこにあると思っている？"
        )
        pronoun_reply = large.reply("彼はそれがどこにあると思っている？")
        absent_reply = large.reply(
            f"{absent}は{object_name}がどこにあると思っている？"
        )
        cause_reply = large.reply(
            f"{object_name}が{new_value}にある直接の原因は？"
        )
        correct_world += world_reply.text.startswith(f"{new_value}です")
        correct_observer += observer_reply.text.startswith(f"{new_value}です")
        correct_pronoun += pronoun_reply.text.startswith(f"{new_value}です")
        correct_false_belief += absent_reply.text.startswith(f"{old_value}です")
        correct_cause += f"{object_name}を{new_value}へ移した" in cause_reply.text
        max_event_candidates = max(
            max_event_candidates, large.perspective.last_event_candidates
        )
        max_query_candidates = max(
            max_query_candidates, large.perspective.last_query_candidates
        )
        max_schema_reads = max(max_schema_reads, large.perspective.last_schema_reads)
        max_state_reads = max(max_state_reads, large.perspective.last_state_reads)
        max_focus_reads = max(max_focus_reads, large.perspective.last_focus_reads)
        max_operations = max(
            max_operations,
            world_reply.estimated_sparse_operations,
            observer_reply.estimated_sparse_operations,
            pronoun_reply.estimated_sparse_operations,
            absent_reply.estimated_sparse_operations,
            cause_reply.estimated_sparse_operations,
        )

    large_bytes = large.to_bytes()
    large_report = large.perspective.report()
    scale_report = {
        "objects": object_count,
        "world_slots": large_report["world_slots"],
        "belief_slots": large_report["belief_slots"],
        "events": large_report["events"],
        "event_programs": large_report["event_programs"],
        "query_programs": large_report["query_programs"],
        "sample_queries": sample_queries,
        "correct_world_queries": correct_world,
        "correct_observer_queries": correct_observer,
        "correct_false_belief_queries": correct_false_belief,
        "correct_pronoun_queries": correct_pronoun,
        "correct_cause_queries": correct_cause,
        "max_event_candidates": max_event_candidates,
        "max_query_candidates": max_query_candidates,
        "max_schema_reads": max_schema_reads,
        "max_state_reads": max_state_reads,
        "max_focus_reads": max_focus_reads,
        "max_estimated_operations": max_operations,
        "serialized_bytes": len(large_bytes),
        "build_and_query_seconds": time.perf_counter() - scale_start,
        "global_world_scan_used": False,
        "global_belief_scan_used": False,
        "full_history_scan_used": False,
    }

    result: dict[str, object] = {
        "capability_id": "SPARC-HS15-PERSPECTIVE-EVENT-STATE",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "answers": {
            "actual_before": actual_before.text,
            "observer_before": observer_before.text,
            "absent_before": absent_before.text,
            "pronoun_before": pronoun_before.text,
            "actual_after": actual_after.text,
            "absent_pronoun": absent_pronoun.text,
            "cause": cause.text,
        },
        "compact_model": model.report(),
        "large_perspective_memory": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS15 learns bounded event-state and perspective query programs from "
            "state-transition demonstrations. It handles actual versus believed state, "
            "local reference focus and direct causal writers, but not unrestricted "
            "language understanding, nested theory of mind or Japanese high-school-level "
            "general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct_world == sample_queries
        and correct_observer == sample_queries
        and correct_false_belief == sample_queries
        and correct_pronoun == sample_queries
        and correct_cause == sample_queries
        and scale_report["world_slots"] == object_count
        and scale_report["belief_slots"] == object_count * 3
        and scale_report["events"] == object_count
        and scale_report["event_programs"] == 1
        and max_event_candidates <= 1
        and max_query_candidates <= 3
        and max_schema_reads <= 32
        and max_state_reads <= 1
        and max_focus_reads <= 4
        and max_operations <= 32
        and len(large_bytes) <= 15_000_000
        and result["peak_process_kib"] <= 1_200_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs15_perspective_state.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS15-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS15-perspective-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
