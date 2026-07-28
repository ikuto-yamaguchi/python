# C003 — D003-GHA exact dependency / provenance gate amendment

Date: 2026-07-29
Role: K3-C
Branch: `research/intelligence-swarm-reconstruction-001`
Status: **environment/import stageのみ実行許可。model測定・学習は禁止**

## 1. 目的

C002の科学条件、候補、architecture、閾値を変更せず、local sandboxの`BLOCKED_ENV`を回避するため、D003の依存解決とimport検証だけをGitHub Actionsの固定CPU環境へ移す。

単一仮説:

> GitHub Actions上の固定Python 3.11 CPU runnerで、非公式候補`wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`とTransformers`42791a34fdeae197f60f11ace3807c81f44b0729`の依存グラフをsilent substitutionなしで解決し、再実行可能なprovenanceと内部API import証拠を保存できる。

本stageはBlock AttnResの品質、速度、メモリ、量子化、学習安定性を評価しない。

## 2. Workflow契約

- trigger: `workflow_dispatch`のみ
- branch guard: `research/intelligence-swarm-reconstruction-001`
- permissions: `contents: read`
- runner: GitHub-hosted Linux x86_64 CPU runner。実行時のimage label、image version、runner name、runner OS、architectureを保存する
- Python: `3.11.x`。実解決patch versionを保存する
- cache: 初回canonical runではpip/cacheを無効化する。再実行でcacheを使う場合はcache keyとrestore hitを記録し、初回結果と混在させない
- network: GitHub repositoryとPython package indexへの取得のみ。dataset、tokenizer、checkpoint、W&B、外部benchmark取得は禁止
- timeout: environment stageは30分以内

## 3. Source固定

必須:

- canonical repository branch SHA
- candidate repository/commit
- candidate modeling file SHA256
- official reference repository/commit
- Transformers repository/commit
- checkout後の`git status --porcelain`が空
- submoduleの有無とSHA

branch headを候補commitとして代用してはならない。

## 4. Dependency固定

環境構築は次の順序とする。

1. Python 3.11を準備
2. isolated virtual environmentを作成
3. pip/setuptools/wheelのversionを記録
4. exact PyTorch CPU buildを1つ解決して固定
5. Transformersをgit commit `42791a34fdeae197f60f11ace3807c81f44b0729`から導入
6. tokenizers、safetensors、huggingface-hub、numpy等のtransitive dependencyをresolver結果どおり固定
7. `pip install --report resolver-report.json`または同等のresolver reportを保存
8. `pip freeze --all`を保存
9. installed distribution、wheel/source archive、checked-out sourceのSHA256を保存

CはPyTorch/tokenizersの版を推測指定しない。Dが一度解決したexact buildをmanifest lockへ反映し、次回以降は同じversion/hashを要求する。

## 5. 必須import gate

以下を個別にimportし、module path、object type、source file SHA256を記録する。

- `transformers.masking_utils.create_causal_mask`
- `transformers.modeling_layers.GradientCheckpointingLayer`
- `transformers.modeling_utils.merge_with_config_defaults`
- `transformers.modeling_utils.capture_outputs`または固定commitで定義された正確な公開位置
- candidateが使用するQwen3 config/model/attention/MLP/RMSNorm classes
- candidate modeling module全体

似た名前の別APIへの置換、monkey patch、dynamic fallbackは禁止。

## 6. Compatibility patch

C002と同様に最大1件のみ許可する。

許可:

- import pathまたはAPI wiringの機械的修正
- model equation、shape、initialization、source construction、block transition、routing priorに影響しない修正

必須証拠:

- patchなしの失敗log
- unified diff
- patch SHA256
- before/after file SHA256
- semantic no-change explanation

禁止:

- `partial_block` reset追加
- recency bias削除
- gate削除
- source list変更
- model forward式変更

これらはC004の別variantで扱う。

## 7. 二段階gate

### Stage E — environment/import

本C003で許可する唯一のstage。

PASS条件:

- branch guard合格
- source commit/checksum固定
- Python 3.11 exact patch保存
- exact dependency graph保存
- required imports全件PASS
- candidate module import PASS
- dirty treeなし
- artifact checksum作成

### Stage M — model semantic/resource

C004 manifestが存在し、Stage EがPASSしたartifact SHAを入力として明示的に指定した場合だけ許可する。Stage Eの同一workflow runから自動継続してはならない。

## 8. 判定

- `ENV_PASS`: 全条件合格。C004 semantic traceへ進行可能
- `ENV_RETRY`: DNS、package index、GitHub outage、runner一時障害。科学的判定に使わない
- `ENV_PATH_STOP`: 最大1件の許可patch後も固定commit/APIを構築不能、またはprovenance保存不能。停止対象は非公式候補経路のみ
- `ENV_PROTOCOL_FAIL`: branch guard、hash、artifact、禁止取得などprotocol違反。結果を無効化して修正後に再実行

## 9. 必須artifact

- `run-context.json`
- `repository-provenance.json`
- `python-environment.json`
- `resolver-report.json`
- `pip-freeze.txt`
- `dependency-checksums.sha256`
- `required-imports.json`
- `source-and-patch.json`
- raw install/import logs
- `D003_GHA_environment_summary.json`
- artifact全体の`checksums.sha256`

artifact retentionは最低30日。summaryにはartifact名、workflow run ID、branch SHA、判定、全checksumを含める。

## 10. 実行禁止

本stageでは以下を禁止する。

- model instantiate/forward/backward
- dataset/tokenizer/checkpoint取得
- optimizer step、S1–S3
- CPU timing/RSS比較
- quantization
- new architecture
- KDA/MoE/別K3 component

ENV_PASSはBlock AttnResの採用、実装正当性、軽量性を意味しない。