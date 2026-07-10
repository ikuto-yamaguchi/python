from __future__ import annotations

import json
from pathlib import Path

from .unified_machine import IndexedProgram, Rule, SearchResult, State, SymbolTable, shortest_program


def _result_payload(result: SearchResult, symbols: SymbolTable) -> dict[str, object]:
    return {
        "objective_bits": result.objective_bits,
        "expanded_states": result.expanded_states,
        "generated_states": result.generated_states,
        "rule_checks": result.rule_checks,
        "rule_applications": result.rule_applications,
        "peak_frontier": result.peak_frontier,
        "trace": list(result.state.trace),
        "output": [symbols.decode(symbol) for symbol in result.state.output],
    }


def coding_task(symbols: SymbolTable) -> dict[str, object]:
    """Repair f(x)=a*x+b from tests using the shared sparse runtime."""

    xs = [-2, -1, 0, 1, 2, 5]
    ys = [3 * x + 1 for x in xs]
    initial_facts = {symbols.fact("program", "unset")}
    initial_facts.update(symbols.fact("test", str(index)) for index in range(len(xs)))

    rules: list[Rule] = []
    for coefficient in range(-4, 5):
        for bias in range(-4, 5):
            passing = {
                symbols.fact("pass", str(index))
                for index, (x_value, expected) in enumerate(zip(xs, ys))
                if coefficient * x_value + bias == expected
            }
            description_bits = (
                3
                + abs(coefficient).bit_length()
                + abs(bias).bit_length()
                + int(coefficient < 0)
                + int(bias < 0)
            )
            output = symbols.intern(f"def f(x): return {coefficient} * x + {bias}")
            rules.append(
                Rule(
                    name=f"patch:a={coefficient},b={bias}",
                    require=frozenset({symbols.fact("program", "unset")}),
                    add=frozenset(
                        {symbols.fact("program", str(coefficient), str(bias)), *passing}
                    ),
                    remove=frozenset({symbols.fact("program", "unset")}),
                    emit=(output,),
                    cost_bits=description_bits,
                )
            )

    def goal(state: State) -> bool:
        return all(symbols.fact("pass", str(index)) in state.facts for index in range(len(xs)))

    result = shortest_program(State(frozenset(initial_facts)), IndexedProgram(rules), goal)
    payload = _result_payload(result, symbols)
    payload["tests"] = len(xs)
    payload["candidate_patches"] = len(rules)
    return payload


def writing_task(symbols: SymbolTable) -> dict[str, object]:
    """Create a constrained paragraph with the same sparse rewrite substrate."""

    initial = State(
        frozenset(
            {
                symbols.fact("stage", "intro"),
                symbols.fact("need", "goal"),
                symbols.fact("need", "method"),
                symbols.fact("need", "caveat"),
                symbols.fact("tone", "professional"),
            }
        )
    )
    rules = [
        Rule(
            "write:intro-concise",
            require=frozenset(
                {
                    symbols.fact("stage", "intro"),
                    symbols.fact("need", "goal"),
                    symbols.fact("tone", "professional"),
                }
            ),
            add=frozenset(
                {
                    symbols.fact("stage", "method"),
                    symbols.fact("covered", "goal"),
                }
            ),
            remove=frozenset({symbols.fact("stage", "intro")}),
            emit=(
                symbols.intern(
                    "本研究は、言語処理に必要な記憶量と演算量の下限を明らかにする。"
                ),
            ),
            cost_bits=8,
        ),
        Rule(
            "write:intro-verbose",
            require=frozenset(
                {
                    symbols.fact("stage", "intro"),
                    symbols.fact("need", "goal"),
                    symbols.fact("tone", "professional"),
                }
            ),
            add=frozenset(
                {
                    symbols.fact("stage", "method"),
                    symbols.fact("covered", "goal"),
                }
            ),
            remove=frozenset({symbols.fact("stage", "intro")}),
            emit=(
                symbols.intern(
                    "本研究では、言語処理システムが本質的に必要とする記憶量ならびに計算量の理論的下限を体系的に検討する。"
                ),
            ),
            cost_bits=14,
        ),
        Rule(
            "write:method",
            require=frozenset(
                {
                    symbols.fact("stage", "method"),
                    symbols.fact("need", "method"),
                    symbols.fact("covered", "goal"),
                }
            ),
            add=frozenset(
                {
                    symbols.fact("stage", "caveat"),
                    symbols.fact("covered", "method"),
                }
            ),
            remove=frozenset({symbols.fact("stage", "method")}),
            emit=(
                symbols.intern(
                    "予測誤差から必要な状態と書換え規則だけを追加し、すべてのコストをビット単位で測定する。"
                ),
            ),
            cost_bits=10,
        ),
        Rule(
            "write:caveat",
            require=frozenset(
                {
                    symbols.fact("stage", "caveat"),
                    symbols.fact("need", "caveat"),
                    symbols.fact("covered", "method"),
                }
            ),
            add=frozenset(
                {
                    symbols.fact("stage", "done"),
                    symbols.fact("covered", "caveat"),
                }
            ),
            remove=frozenset({symbols.fact("stage", "caveat")}),
            emit=(
                symbols.intern("ただし、新しい知識が持つ情報量そのものは削減できない。"),
            ),
            cost_bits=7,
        ),
    ]

    def goal(state: State) -> bool:
        return all(
            symbols.fact("covered", item) in state.facts
            for item in ("goal", "method", "caveat")
        )

    return _result_payload(shortest_program(initial, IndexedProgram(rules), goal), symbols)


def agent_task(symbols: SymbolTable) -> dict[str, object]:
    """Plan environment actions using exactly the same facts and rewrites."""

    edges = [
        ("lab", "hall"),
        ("hall", "vault"),
        ("vault", "hall"),
        ("hall", "lab"),
    ]
    facts = {
        symbols.fact("at", "agent", "lab"),
        symbols.fact("at", "key", "vault"),
    }
    facts.update(symbols.fact("edge", source, target) for source, target in edges)

    rules: list[Rule] = []
    for source, target in edges:
        rules.append(
            Rule(
                f"move:{source}->{target}",
                require=frozenset(
                    {
                        symbols.fact("at", "agent", source),
                        symbols.fact("edge", source, target),
                    }
                ),
                add=frozenset({symbols.fact("at", "agent", target)}),
                remove=frozenset({symbols.fact("at", "agent", source)}),
                cost_bits=1,
            )
        )
    rules.append(
        Rule(
            "pickup:key",
            require=frozenset(
                {
                    symbols.fact("at", "agent", "vault"),
                    symbols.fact("at", "key", "vault"),
                }
            ),
            add=frozenset({symbols.fact("has", "agent", "key")}),
            remove=frozenset({symbols.fact("at", "key", "vault")}),
            cost_bits=1,
        )
    )

    result = shortest_program(
        State(frozenset(facts)),
        IndexedProgram(rules),
        lambda state: symbols.fact("has", "agent", "key") in state.facts,
    )
    return _result_payload(result, symbols)


def run() -> dict[str, object]:
    symbols = SymbolTable()
    tasks = {
        "coding": coding_task(symbols),
        "writing": writing_task(symbols),
        "agent": agent_task(symbols),
    }
    return {
        "core_primitives": ["MATCH", "DELETE", "ADD", "EMIT", "CHOOSE_MIN"],
        "shared_symbol_count": symbols.count,
        "runtime_bits_per_symbol": symbols.runtime_bits_per_symbol,
        "tasks": tasks,
    }


def render_markdown(payload: dict[str, object]) -> str:
    tasks = payload["tasks"]
    lines = [
        "# Phase 5a results: one sparse substrate for coding, writing, and agency",
        "",
        "This experiment does not add separate memory, reasoning, writing, coding, and agent modules.",
        "All three tasks are compiled into the same five runtime primitives:",
        "",
        "`MATCH / DELETE / ADD / EMIT / CHOOSE_MIN`",
        "",
        f"One canonical symbol table contains **{payload['shared_symbol_count']} symbols** ",
        f"(**{payload['runtime_bits_per_symbol']} bits per symbol ID**).",
        "",
        "| task | objective bits | expanded | rule checks | applications | trace |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, result in tasks.items():
        lines.append(
            f"| {name} | {result['objective_bits']} | {result['expanded_states']} | "
            f"{result['rule_checks']} | {result['rule_applications']} | "
            f"`{' -> '.join(result['trace'])}` |"
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "### Coding",
            "",
            "```python",
            tasks["coding"]["output"][0],
            "```",
            "",
            "### Writing",
            "",
            "".join(tasks["writing"]["output"]),
            "",
            "### Agent",
            "",
            "`" + " -> ".join(tasks["agent"]["trace"]) + "`",
            "",
            "## Interpretation",
            "",
            "The point is not that these tiny tasks are difficult. The result tests an anti-bloat",
            "architecture rule: a capability must be expressed as data and rewrites over one",
            "canonical state, rather than bringing its own hidden representation and execution engine.",
            "",
            "Stacks, counters, memories, planners, creativity operators, AST edits, and tool calls",
            "are initially macros over the same substrate. A macro becomes a native primitive only",
            "when lifetime MDL shows that the saved model bits, memory traffic, and operations exceed",
            "the added opcode, compiler, and representation costs across the target workload.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase5a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "phase5a.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
