# RESET-E042 — Non-termination and constrained performance maximization

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Decision

R0の主目的を、監査規則の追加から、固定されたparameter/frame/runtime制約下で公開baseline性能を最大化する研究へ戻す。

## Prohibited completion pattern

次の形式でiterationを閉じることを禁止する。

> 検証した。性能が出なかった。失敗だった。終了。

低性能、CI failure、artifact欠落は終了条件ではなく、次の原因診断入力である。

## Required cycle

失敗後は必ず次を連続して行う。

1. failure classification
2. evidence-backed root-cause ranking
3. single-factor minimal correction
4. same-budget rerun
5. adoption/rejection/stopping decision

停止は事前登録されたbudget、連続反証、再現不能な外部条件、または期待改善/計算コスト比による候補切替の場合だけ許可する。

## Active experiment order

1. official-fidelity reconstruction
2. action-collapse diagnosis
3. optimization budget allocation
4. parameter-neutral capacity allocation
5. fusion timing ablation

screeningはseed 1、有望案だけseeds 1/7/19で確認する。採用には同一frame/parameter budgetで平均改善と最低seed非悪化を要求する。

## Governance freeze

D015〜D035を凍結する。実benchmark bundleが具体的な監査欠陥を示すまで新規auditorを追加しない。prior-art追加だけのiterationも禁止する。

## Claims

- external learned public baseline: not reproduced
- R0.2: not reproduced
- R0.3: rejected
- RQ-001: narrowed, not adopted
- new intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not reached
