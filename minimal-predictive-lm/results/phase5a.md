# Phase 5a results: one sparse substrate for coding, writing, and agency

This experiment does not add separate memory, reasoning, writing, coding, and agent modules.
All three tasks are compiled into the same five runtime primitives:

`MATCH / DELETE / ADD / EMIT / CHOOSE_MIN`

One canonical symbol table contains **117 symbols** (**7 bits per symbol ID**).

| task | objective bits | expanded | rule checks | applications | trace |
|---|---:|---:|---:|---:|---|
| coding | 6 | 21 | 81 | 81 | `patch:a=3,b=1` |
| writing | 25 | 5 | 6 | 6 | `write:intro-concise -> write:method -> write:caveat` |
| agent | 3 | 3 | 5 | 5 | `move:lab->hall -> move:hall->vault -> pickup:key` |

## Outputs

### Coding

```python
def f(x): return 3 * x + 1
```

### Writing

本研究は、言語処理に必要な記憶量と演算量の下限を明らかにする。予測誤差から必要な状態と書換え規則だけを追加し、すべてのコストをビット単位で測定する。ただし、新しい知識が持つ情報量そのものは削減できない。

### Agent

`move:lab->hall -> move:hall->vault -> pickup:key`

## Interpretation

The point is not that these tiny tasks are difficult. The result tests an anti-bloat architecture rule: a capability must be expressed as data and rewrites over one canonical state, rather than bringing its own hidden representation and execution engine.

Stacks, counters, memories, planners, creativity operators, AST edits, and tool calls are initially macros over the same substrate. A macro becomes a native primitive only when lifetime MDL shows that the saved model bits, memory traffic, and operations exceed the added opcode, compiler, and representation costs across the target workload.
