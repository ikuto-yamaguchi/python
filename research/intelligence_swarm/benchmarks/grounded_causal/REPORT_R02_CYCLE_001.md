# R0.2 Environment-first representation baseline — cycle 001

## Scope

Gaddy & Klein (ACL 2019)の二段階方式を、SILG trajectoryへ接続可能な再現harnessとして実装した。新規機構ではない。

1. environment phase: `E(s,s') -> z`, `D(s,z) -> s'` とaction分類を言語なしtransitionで学習
2. language phase: `L(c) -> z`をpretrained decoderへ接続
3. end-to-end control: 同じlanguage encoder / decoder規模をinstruction dataだけで学習
4. controls: language-blind / language-shuffle

原論文ではconditional autoencoderのencoderとdecoderの両方へ初期stateを与え、有限bottleneckへtransition abstractionを学習する。言語phaseではpretrained decoderを固定または初期値として利用する。

## Public implementation audit

- SILG official repository: `vzhong/silg`
- public code URL commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- package: `silg==0.0.1`
- Python: `>=3.7.10`
- official requirements are mostly unpinned: `gym>=0.15.4`, `torch`, `torchvision`, `pyyaml`, `expman`, `submitit`; exact pin is `py-getch==1.0.1`
- experiment entrypoint: `run_exp.py`; local launch: `python launch.py --local --envs rtfm`
- learner is TorchBeast/V-trace style and sets `OMP_NUM_THREADS=1`
- individual environment installation and environment-data download are required

## Added reproducible assets

- `environment_first_baseline.py`
- `export_silg_trajectories.py`
- `make_r02_fixture.py`
- `requirements-r02.txt`
- `SMOKE_SUMMARY_R02_001.json`

## Local three-seed smoke test

Python 3.13.5、PyTorch 2.10.0+cpu、1 thread。synthetic fixtureのみであり、SILG再現値でも能力証拠でもない。

| method | action accuracy | task success | next-state MSE | model bytes | train sec | CPU ms/item |
|---|---:|---:|---:|---:|---:|---:|
| environment-first | 0.5028 | 0.0042 | 0.2123 | 116,384 | 1.0915 | 0.0441 |
| end-to-end | 0.4097 | 0.2069 | 0.1095 | 107,840 | 0.9040 | 0.0437 |

Environment-first language-blind action accuracyは0.2528、language-shuffleは0.2667。End-to-endの両controlは0.2333。

fixtureではenvironment-firstはaction分類を改善したが、task successとstate predictionはend-to-endより悪い。研究判断には使用せず、pipelineが3 seedで動作し、control・model bytes・RSS・training/inference timeを出力できたことのみを確認した。

Mean peak RSS: 388,859 KiB。1GB未満だが弱いスマートフォン実機は未検証。

## Exact blocker

実行sandboxは外部DNSを解決できず、GitHub cloneとACL software archive downloadが失敗した。SILG/RTFM環境、environment data、互換Python 3.7/3.8 runtimeも存在しないため、公開SILG task successは未測定。

Failure class: `initial_public_environment_installation_failure`。

## Next executable step

```bash
git clone https://github.com/vzhong/silg.git
cd silg
git checkout 2af07578e1264029a240fcfb78d4ac0aea16f5de
bash install_envs.sh
pip install -r requirements.txt
pip install -e .
bash download_env_data.sh
OMP_NUM_THREADS=1 python launch.py --local --envs rtfm
```

その後、seed 1/7/19・同一RTFM splitで公式baseline、environment-first、end-to-end、random、language-blind、state-only、language-shuffle、transition-shuffleを比較する。

## Status

- Public SILG baseline reproduced: no
- R0.2 harness implemented and smoke-tested: yes
- Novelty/capability claim: none
- High-school-level intelligence: not passed
