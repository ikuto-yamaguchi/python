# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-28 by K3-B
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 0: loop initialization / baseline selection**

- A evidence: 未投入
- B theory: B001完了
- C preregistration: 未投入
- D reproduction: 未開始
- E integration decision: 未投入
- New architecture permission: **禁止継続**

## Current top hypothesis

Block Attention Residuals can improve training quality/compute efficiency in an approximately 100M dense Transformer without losing the CPU inference and memory Pareto.

Status: **追加検証候補・未採用**

## Evidence boundary

- Kimi K3 uses AttnRes together with KDA and Stable LatentMoE; K3 aggregate gains cannot be attributed to AttnRes alone.
- Attention Residuals primary report provides scaling evidence at approximately 194M–528M activated parameters and a 48B-total/3B-active run.
- Evidence below approximately 194M from the original authors is not established.
- Official repository currently exposes paper/overview, not reproducible training code.
- Public 100M/0.6B implementations are unofficial and require independent reproduction.

## Completed artifacts

- `theory/B001_BLOCK_ATTNRES_SMALL_SCALE_AUDIT.md`
  - parameter/FLOPs/state-memory/communication/sequence/quantization/CPU audit
  - small-scale failure conditions
  - 100M-class minimum ablation handoff
  - C/D/E acceptance criteria

## Current single bottleneck

A reproducible, commit-pinned 80M–120M standard PreNorm baseline and an equally controlled Block AttnRes `N=4` manifest have not been preregistered.

## Completion condition for next cycle

C must produce one executable manifest fixing:

- architecture and exact parameter count
- dataset and immutable digest
- tokenizer
- optimizer/schedule/token budget
- seeds `17/29/43`
- baseline vs Block AttnRes single change
- validation and CPU measurement commands
- failure and stop rules

## Stop conditions

Do not proceed to a new architecture if any of the following holds:

- baseline is not reproducible
- more than one architectural variable changes
- data/token budget differs between conditions
- resource metrics cannot be recorded
- only unofficial reported scores are available without raw reproduction

## Next handoffs

- A: audit the exact AttnRes scaling setup and identify immutable code/model artifacts; distinguish author evidence from unofficial results.
- C: create the minimum preregistration specified in B001.
- D: do not train until C manifest exists; prepare environment pin and measurement harness only.
- E: keep Block AttnRes at `追加検証`; prioritize this single bottleneck rather than opening KDA/MoE experiments in parallel.
