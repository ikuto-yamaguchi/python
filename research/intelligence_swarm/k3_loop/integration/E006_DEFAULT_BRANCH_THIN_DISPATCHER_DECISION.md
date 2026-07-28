# E006 — D006 ROUTE_STOP integration decision

Date: 2026-07-29

## Decision

D006の`ROUTE_STOP`を正式に受理する。停止対象はC005のcanonical-branch-only push routeだけであり、Block AttnRes、PB1、依存互換性仮説、品質仮説の棄却ではない。

Block AttnResの分類は維持する。

- classification: `小型化で要再設計・追加検証・未採用`
- implementation path: `Path-WARN`
- C005 route: `ROUTE_STOP / closed`

## Evidence interpretation

同じcanonical branchへのpushで既存workflowは生成された一方、新規`D003 K3 environment gate`だけはamendment commitとnonce-finalization commitの双方でrunが生成されなかった。よって、追加の同型nonce、path-filter調整、広範push triggerは情報利得がなく、無限orchestration監査として禁止する。

GitHub公式仕様では`workflow_dispatch`はworkflow fileがdefault branchに存在する場合だけ受理され、branch以外のrefを指定して実行できる。したがって、default branch上の薄いdispatcherがcanonical branchの固定SHAをcheckoutしてenvironment-only probeを呼ぶ経路は、モデル・候補・評価条件を変えずに実行基盤だけを修正する最小案である。

## Single next hypothesis

> default branchに登録されたenvironment-onlyの薄い`workflow_dispatch` dispatcherが、入力として固定canonical commit SHAとmanifest SHAを要求し、そのSHAをdetached checkoutしてC003 environment/import probeだけを実行すれば、model executionを許可せずに`ENV_PASS / ENV_RETRY / ENV_PATH_STOP / ENV_PROTOCOL_FAIL`を再現可能に分類できる。

## Single bottleneck

**C006 default-branch thin-dispatcher preregistration**

C006完成前にdefault branchを変更、workflowをdispatch、model stageを実行してはならない。

## Authorized work

### A

新しいK3 componentへ移らない。C006/D007で具体的なresolverまたはimport不一致が出た場合だけ一次資料・dependency provenanceを追補する。

### B

exact trace前のCPU crossover、minimum effective scale、Pareto採否を更新しない。PB1の`84/5/89` source-slot契約と解釈境界を維持する。

### C

C006本文とmanifestだけを作成する。次を固定する。

1. default branch上には薄いdispatcherだけを置く
2. dispatcher自身にmodel implementationを複製しない
3. required inputs: canonical branch名、canonical commit SHA、C003/C004/C006 manifest SHA、environment script SHA
4. checkoutは入力SHAへのdetached checkout
5. `training_authorized=false`
6. `model_execution_authorized=false`
7. dataset/tokenizer/checkpoint/quantization禁止
8. environment probe以外のscript実行禁止
9. SHA不一致、branch不一致、dirty tree、allowlist外変更は`ENV_PROTOCOL_FAIL`
10. environment PASSからmodel stageへ自動遷移しない
11. artifact ID、ZIP SHA256、resolver report、freeze、source/dependency hashes、raw logsを必須化
12. 一時障害時の同条件retryは1回だけ
13. default branch変更はPRまたは明示的な単一コミットとして監査可能にする

### D

C006完成後だけ、dispatcherをdefault branchへ導入し、canonical SHAを入力してenvironment-only runを1回起動する。PB1/CR1 instantiateはまだ禁止する。

## Completion conditions

- C006 prose/manifestが一致
- default-branch dispatcherがenvironment-onlyである
- canonical commitと全契約file SHAを入力・検証
- detached checkoutが記録される
- authorization flagsがfalse
- required artifactsとchecksumsが保存される
- run outcomeが機械可読に分類される

## Stop conditions

- default branchへの最小dispatcher導入が権限・policy上不可能: `ROUTE_STOP_DEFAULT_BRANCH`
- dispatcherは起動するが一時的service/network障害: `ENV_RETRY`（同条件1回のみ）
- 最大1件の事前登録済みAPI-wiring-only patch後もsemantic変更なしでdependency/import不成立: `ENV_PATH_STOP`
- SHA/branch/allowlist/authorization/artifact契約違反: `ENV_PROTOCOL_FAIL`

これらはBlock AttnRes機構全体の棄却ではない。ただし`ROUTE_STOP_DEFAULT_BRANCH`成立時は、現在利用可能なGitHub Actions実行経路を停止し、別の実行基盤が明示的に利用可能になるまでP0実験を保留する。

## Pareto status

品質、exact model bytes、active compute、独立peak RSS、学習時間、CPU生成速度、量子化耐性、3-seed安定性は未計測。能力進歩、知能原理、1GB目標達成は主張しない。
