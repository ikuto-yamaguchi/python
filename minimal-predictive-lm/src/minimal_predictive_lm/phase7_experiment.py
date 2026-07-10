from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .conversation_agent import (
    CanonicalConversationAgent,
    CanonicalV1Agent,
    LiteralAgent,
    ResidualRewriteAgent,
    seed_facts,
)


EpisodeFactory = Callable[[], tuple[object, list[tuple[str, str]]]]


def _episodes() -> list[tuple[str, EpisodeFactory]]:
    episodes: list[tuple[str, EpisodeFactory]] = []

    def add(name: str, agent_factory: Callable[[], object], turns: list[tuple[str, str]]) -> None:
        episodes.append((name, lambda af=agent_factory, ts=turns: (af(), list(ts))))

    add(
        "explicit-memory-query",
        CanonicalConversationAgent,
        [
            ("青い箱は倉庫にあります。", "青い箱は倉庫にあります"),
            ("青い箱はどこにありますか？", "青い箱は倉庫にあります"),
        ],
    )
    add(
        "explicit-move-query",
        CanonicalConversationAgent,
        [
            ("工具を棚Bに移してください。", "工具を棚Bに移しました"),
            ("工具はどこにありますか？", "工具は棚Bにあります"),
        ],
    )
    add(
        "pronoun-and-ellipsis",
        CanonicalConversationAgent,
        [
            ("試作品は棚Aにある。", "試作品は棚Aにあります"),
            ("それを検査室へ移して。", "試作品を検査室に移しました"),
            ("今どこ？", "試作品は検査室にあります"),
        ],
    )
    add(
        "correction",
        CanonicalConversationAgent,
        [
            ("鍵は保管庫にあります。", "鍵は保管庫にあります"),
            ("いや、保管庫じゃなくて事務室。", "鍵を事務室に移しました"),
            ("鍵はどこ？", "鍵は事務室にあります"),
        ],
    )
    add(
        "compound-instruction",
        CanonicalConversationAgent,
        [
            ("部品Xは倉庫1に置いてある。", "部品Xは倉庫1にあります"),
            ("部品Xを作業台へ運んでから、場所を教えて。", "部品Xは作業台にあります"),
        ],
    )
    add(
        "unseen-proper-name",
        CanonicalConversationAgent,
        [
            ("火威青は第七码頭にあります。", "火威青は第七码頭にあります"),
            ("火威青を北研究棟へ移動して。", "火威青を北研究棟に移しました"),
            ("火威青は今どこ？", "火威青は北研究棟にあります"),
        ],
    )
    add(
        "social-direct-path",
        CanonicalConversationAgent,
        [("ありがとう！", "どういたしまして")],
    )
    add(
        "task-with-recovery",
        CanonicalConversationAgent,
        [
            (
                "transform関数をテストに通るよう修正して。",
                "隠しテストで失敗しました",
            ),
        ],
    )
    return episodes


def run_agent_benchmark(agent_type: type) -> dict[str, object]:
    results = []
    passed_turns = 0
    total_turns = 0
    for name, factory in _episodes():
        _unused, turns = factory()
        agent = agent_type()
        transcript = []
        episode_passed = True
        for user_text, expected_fragment in turns:
            response = agent.respond(user_text)
            passed = expected_fragment in response
            total_turns += 1
            passed_turns += int(passed)
            episode_passed = episode_passed and passed
            transcript.append(
                {
                    "user": user_text,
                    "assistant": response,
                    "expected_fragment": expected_fragment,
                    "passed": passed,
                }
            )
        repo_ok = True
        if name == "task-with-recovery" and isinstance(agent, CanonicalConversationAgent):
            repo_ok, _ = agent.state.repo.run_tests(include_hidden=True)
            episode_passed = episode_passed and repo_ok
        results.append(
            {
                "name": name,
                "passed": episode_passed,
                "repo_ok": repo_ok,
                "transcript": transcript,
                "ledger": vars(agent.state.ledger),
                "fact_bits": agent.state.facts.approximate_bits(),
            }
        )
    return {
        "passed_turns": passed_turns,
        "total_turns": total_turns,
        "turn_accuracy": passed_turns / total_turns,
        "passed_episodes": sum(int(row["passed"]) for row in results),
        "total_episodes": len(results),
        "episodes": results,
    }


def run_open_form_probe(agent_type: type) -> dict[str, object]:
    probes = [
        ("青い箱は倉庫にあります。", "青い箱は倉庫にあります"),
        ("青い箱、たしか倉庫だったよね？", "青い箱は倉庫にあります"),
        ("例の試作品は棚Aにあります。", "例の試作品は棚Aにあります"),
        ("例の試作品、検査室にお願い。", "例の試作品を検査室に移しました"),
        ("どこやったっけ？", "例の試作品は検査室にあります"),
        ("工具は作業台にあります。", "工具は作業台にあります"),
        ("工具、棚Bに持ってっといて。", "工具を棚Bに移しました"),
        ("transform、テスト落ちてるからいい感じに直しといて。", "全テストに成功しました"),
    ]
    agent = agent_type()
    transcript = []
    passed = 0
    for user_text, expected in probes:
        response = agent.respond(user_text)
        ok = expected in response
        passed += int(ok)
        transcript.append(
            {
                "user": user_text,
                "assistant": response,
                "expected_fragment": expected,
                "passed": ok,
            }
        )
    return {
        "passed": passed,
        "total": len(probes),
        "accuracy": passed / len(probes),
        "transcript": transcript,
    }


def run_shifted_open_form_probe(agent_type: type) -> dict[str, object]:
    probes = [
        ("青い箱は倉庫にあります。", "青い箱は倉庫にあります"),
        ("青い箱って倉庫だっけ？", "青い箱は倉庫にあります"),
        ("試作品は棚Aにあります。", "試作品は棚Aにあります"),
        ("試作品を検査室の方にやっといて。", "試作品を検査室に移しました"),
        ("今どこ置いた？", "試作品は検査室にあります"),
        ("工具は作業台にあります。", "工具は作業台にあります"),
        ("工具は棚Bへお願いできる？", "工具を棚Bに移しました"),
        ("transformの落ちてるテスト、直せる？", "全テストに成功しました"),
    ]
    agent = agent_type()
    transcript = []
    passed = 0
    for user_text, expected in probes:
        response = agent.respond(user_text)
        ok = expected in response
        passed += int(ok)
        transcript.append(
            {
                "user": user_text,
                "assistant": response,
                "expected_fragment": expected,
                "passed": ok,
            }
        )
    return {
        "passed": passed,
        "total": len(probes),
        "accuracy": passed / len(probes),
        "transcript": transcript,
    }


def run_scaling() -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for count in (16, 64, 256, 1024, 4096):
        literal = LiteralAgent()
        seed_facts(literal, count)
        literal.state.facts.reads = 0
        literal.respond(f"物{count - 1}はどこにありますか？")

        canonical = CanonicalConversationAgent()
        seed_facts(canonical, count)
        canonical.state.facts.reads = 0
        canonical.respond(f"物{count - 1}はどこにありますか？")

        rows.append(
            {
                "facts": count,
                "scan_query_reads": literal.state.facts.reads,
                "indexed_query_reads": canonical.state.facts.reads,
                "scan_state_bits": literal.state.facts.approximate_bits(),
                "indexed_state_bits": canonical.state.facts.approximate_bits(),
            }
        )
    return rows


def run_long_dialogue_scaling() -> dict[str, int]:
    agent = CanonicalConversationAgent()
    agent.respond("基準箱は保管室にあります。")
    before_bits = agent.state.facts.approximate_bits()
    before_count = agent.state.facts.count
    reads_before = agent.state.facts.reads
    turns = 10_000
    for _ in range(turns):
        response = agent.respond("基準箱はどこ？")
        if "保管室" not in response:
            raise AssertionError("long-dialogue query lost state")
    return {
        "turns": turns,
        "facts_before": before_count,
        "facts_after": agent.state.facts.count,
        "state_bits_before": before_bits,
        "state_bits_after": agent.state.facts.approximate_bits(),
        "fact_reads": agent.state.facts.reads - reads_before,
    }


def run_candidate_search_scaling() -> list[dict[str, int]]:
    rows = []
    for candidates in (8, 32, 128, 512, 2048):
        rows.append(
            {
                "candidates": candidates,
                "candidate_evaluations": 2 * candidates,
                "lower_bound_to_identify_last_without_structure": candidates,
            }
        )
    return rows


def run() -> dict[str, object]:
    literal = run_agent_benchmark(LiteralAgent)
    canonical_v1 = run_agent_benchmark(CanonicalV1Agent)
    canonical = run_agent_benchmark(CanonicalConversationAgent)
    open_form = run_open_form_probe(CanonicalConversationAgent)
    residual_open_form = run_open_form_probe(ResidualRewriteAgent)
    shifted_open_form = run_shifted_open_form_probe(ResidualRewriteAgent)
    scaling = run_scaling()
    long_dialogue = run_long_dialogue_scaling()
    candidate_scaling = run_candidate_search_scaling()
    return {
        "attempts": [
            {
                "name": "v0 literal scan agent",
                "principle": "exact wording, no discourse state, linear fact scan",
                "turn_accuracy": literal["turn_accuracy"],
            },
            {
                "name": "v1 canonical indexed agent",
                "principle": "canonical intents and focus state, but incomplete shared normalization",
                "turn_accuracy": canonical_v1["turn_accuracy"],
            },
            {
                "name": "v2 normalized canonical agent",
                "principle": "shared polite/particle normalization, discourse state, indexed facts, test-feedback retry",
                "turn_accuracy": canonical["turn_accuracy"],
            },
            {
                "name": "v3 residual paraphrase rewrites",
                "principle": "compile only observed open-form failures into four residual rewrites",
                "observed_probe_accuracy": residual_open_form["accuracy"],
                "shifted_probe_accuracy": shifted_open_form["accuracy"],
            },
        ],
        "literal": literal,
        "canonical_v1": canonical_v1,
        "canonical": canonical,
        "open_form_probe": open_form,
        "residual_open_form_probe": residual_open_form,
        "shifted_open_form_probe": shifted_open_form,
        "scaling": scaling,
        "long_dialogue_scaling": long_dialogue,
        "candidate_search_scaling": candidate_scaling,
        "claim_boundary": (
            "This is controlled ordinary-language dialogue and tool-use, not open-domain human-level conversation. "
            "The experiment is intended to expose the first scaling bottlenecks rather than claim LLM parity."
        ),
    }


def render_markdown(payload: dict[str, object]) -> str:
    literal = payload["literal"]
    canonical_v1 = payload["canonical_v1"]
    canonical = payload["canonical"]
    open_form = payload["open_form_probe"]
    residual_open = payload["residual_open_form_probe"]
    shifted_open = payload["shifted_open_form_probe"]
    long_dialogue = payload["long_dialogue_scaling"]
    lines = [
        "# Phase 7a results: controlled conversation and instruction following",
        "",
        "This phase asks whether the current minimum-machine line actually scales into interaction,",
        "rather than only solving isolated micro-functions.",
        "",
        "## Trial-and-error attempts",
        "",
        "| attempt | turn accuracy | episode success | main failure |",
        "|---|---:|---:|---|",
        f"| v0 literal scan agent | {literal['turn_accuracy']:.1%} | {literal['passed_episodes']}/{literal['total_episodes']} | paraphrase, pronoun, correction, compound task, tool recovery |",
        f"| v1 canonical indexed agent | {canonical_v1['turn_accuracy']:.1%} | {canonical_v1['passed_episodes']}/{canonical_v1['total_episodes']} | polite variants and sequential separator were not canonicalized |",
        f"| v2 normalized canonical agent | {canonical['turn_accuracy']:.1%} | {canonical['passed_episodes']}/{canonical['total_episodes']} | controlled grammar succeeds; unrestricted paraphrase remains weak |",
        "",
        "## Open-form probe",
        "",
        f"The v2 agent passed **{open_form['passed']}/{open_form['total']} ({open_form['accuracy']:.1%})** colloquial/open-form turns.",
        f"Four residual rewrites raise the observed probe to **{residual_open['accuracy']:.1%}**, but a shifted colloquial probe reaches only **{shifted_open['accuracy']:.1%}**.",
        "This intentionally separate probe shows that perfect controlled-benchmark accuracy is not ordinary human conversation, and patching phrases can overfit.",
        "",
        "## Scaling of fact lookup",
        "",
        "| stored facts | linear scan reads/query | indexed reads/query | state bits |",
        "|---:|---:|---:|---:|",
    ]
    for row in payload["scaling"]:
        lines.append(
            f"| {row['facts']:,} | {row['scan_query_reads']:,} | {row['indexed_query_reads']:,} | {row['indexed_state_bits']:,} |"
        )
    lines.extend(
        [
            "",
            "The direct index keeps query reads constant in this benchmark, while exact fact storage grows",
            "linearly because independent names and locations contain irreducible information.",
            "",
            "## Dialogue-length scaling",
            "",
            f"Across {long_dialogue['turns']:,} repeated relevant queries, persistent fact count stayed at "
            f"{long_dialogue['facts_before']} and state bits stayed at {long_dialogue['state_bits_before']}.",
            "The transcript is not copied into active state; one indexed fact read is paid per query.",
            "",
            "## Code-candidate scaling limitation",
            "",
            "| candidate patches | exhaustive evaluations |",
            "|---:|---:|",
        ]
    )
    for row in payload["candidate_search_scaling"]:
        lines.append(f"| {row['candidates']:,} | {row['candidate_evaluations']:,} |")
    lines.extend(
        [
            "",
            "The current test-feedback task loop is linear in candidate count and therefore does not scale to real repositories.",
            "A structural program synthesizer, admissible bounds, and repository indexing are required before LLM-level coding claims.",
            "",
            "## Successful controlled transcript",
            "",
        ]
    )
    selected = next(row for row in canonical["episodes"] if row["name"] == "pronoun-and-ellipsis")
    for turn in selected["transcript"]:
        lines.append(f"- User: {turn['user']}")
        lines.append(f"- Machine: {turn['assistant']}")
    task = next(row for row in canonical["episodes"] if row["name"] == "task-with-recovery")
    lines.extend(
        [
            "",
            "## Tool task with failure recovery",
            "",
            f"- User: {task['transcript'][0]['user']}",
            f"- Machine: {task['transcript'][0]['assistant']}",
            f"- Tool calls: {task['ledger']['tool_calls']}",
            f"- Candidate evaluations: {task['ledger']['candidate_evaluations']}",
            f"- Final hidden tests: {'PASS' if task['repo_ok'] else 'FAIL'}",
            "",
            "## Honest conclusion",
            "",
            "The architecture now demonstrates multi-turn reference, exact unseen-name retention, correction,",
            "compound instruction execution, and a test-failure/retry loop without a dense neural runtime.",
            "It has **not** demonstrated open-domain conversation, broad instruction understanding, repository-scale",
            "coding, or parity with a high-performance LLM. The dominant bottleneck has moved from fact lookup to",
            "automatic induction of canonical intents, predicates, goals, and reusable programs from unrestricted text.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase7a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "phase7a.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
