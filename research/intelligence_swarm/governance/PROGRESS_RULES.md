# Progress, Falsification, and Freeze Rules

## 進歩と呼べるもの

進歩は、未知条件の外部能力について次を満たす場合だけ認定する。

- Correct条件がshuffle/random baselineを実質的に上回る。
- 複数seedで方向が再現する。
- 既知surfaceだけでなく、Rename、未知語順、別表現、自由日本語、別領域の少なくとも一部へ転移する。
- 内部unitが予測、実行、inverse query、介入の複数用途へ再利用される。
- 改善が答え漏洩、問題別分岐、固定ontology、手書きslot、テンプレート、検索で説明できない。

## 診断であって進歩ではないもの

- 候補数、entropy、記述長の減少
- graph、family、assembly、grammar、tensor、eigenmode、attractorの形成
- 収束率、棄権率、安全化
- in-sample圧縮、観測後差分の補完
- lesion profileやsynergyが形成されたが外部能力差がない場合
- modelが小さい、速いだけの場合

## 仮説族の凍結

同じ根本前提を共有する方式が、次のどちらかを満たしたらEは仮説族を凍結する。

1. 3系列以上で、Correctとshuffle/randomの外部能力差を生まない。
2. 同一系列で5サイクル以上、未知条件の外部能力を改善しない。

凍結後は、node、cell、address、trace、family、assemblyなど名称を変えただけの再試行を禁止する。

## 再開条件

凍結族は、次をすべて示す新証拠がある場合だけ再開できる。

- 根本前提が以前と何が違うかを一文で説明できる。
- 以前の支配的失敗へ直接作用する新しい観測または学習信号がある。
- 小規模pilotでCorrectとshuffle/randomに能力差がある。
- 旧実装の後段選別を増やしただけではない。

## 研究段階変更

反証結果が下流機構ではなく上流表現の未成立を示した場合、次仮説は下流機構の改良ではなく上流stageへ戻す。実装なしのメタ分析・評価再設計・仮説族凍結も正規の研究サイクルとする。

## 失敗分類

- Acquisition failure: 取得直後から能力0。
- Retention failure: 取得直後は成功し、干渉後に低下。
- Surface memorization: 既知形式でのみ成功し、shuffleとの差または未知転移がない。
- Semantic transfer: 未知形式でCorrectがbaselineを上回り、同じunitが複数用途へ再利用される。
