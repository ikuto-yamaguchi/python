# R0.1 SILG/RTFM Reproduction Cycle 010

## Scope

This cycle advances only the pinned public SILG/RTFM recurrent reproduction. It adds no new model architecture or toy mechanism and makes no capability or novelty claim.

## Evidence inspected

The latest completed canonical workflow before this change was run `30109823906` on commit `fd5b26da1a8896f51e1ee0fc6e4fc046a1733466`.

- conclusion: success
- artifact id: `8603337664`
- artifact digest: `sha256:8a51c8d54bb312a060b02d71c3302810636a73516ca297808e2a26b08fa65a9a`
- artifact size: `73,386,715 bytes`
- public source pins remained SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de` and RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`.

The 2,048-frame matched result remained an undertrained diagnostic:

| Method | Win rate | Mean return | Mean length |
|---|---:|---:|---:|
| Correct | 0.0000 | -2.2037 | 61.18 |
| Random | 0.0667 | -1.1513 | 15.23 |
| Language-blind | 0.0000 | -2.2547 | 63.73 |
| State-only | 0.0167 | -2.1187 | 58.60 |

The initial-instance streams matched across all methods. Correct remained below random and did not establish language use.

## Reproduction improvements implemented

### 1. Staged public training budget

The canonical workflow now requests `32,768` frames per seed instead of `2,048`, retaining:

- official SILG `multi` recurrent model;
- official V-trace learner and optimizer path;
- seeds `1,7,19`;
- CPU-only execution;
- source/checkpoint/log hashes;
- the existing deterministic RNG patch only.

This is still far below the official default `100,000,000` frames and is classified as staged reproduction, not paper-scale reproduction.

### 2. Matched language-shuffle control

The fixed-instance evaluator now includes `language_shuffle` in addition to Correct, Random, Language-blind and State-only.

For each seed, the language fields `wiki`, `wiki_len`, `task`, and `task_len` are replaced by a cyclically permuted donor episode while current state, valid actions and environment dynamics remain unchanged. Donor episode index is `(episode_index + 1) mod episode_count`.

### 3. Episode-level paired export

The evaluator now records every method/seed/episode result with:

- episode seed;
- immutable initial-instance fingerprint;
- donor seed for language shuffle;
- win;
- return;
- episode length.

It additionally exports Correct-minus-control paired episode gaps. This removes dependence on aggregate-only comparisons and prepares the output for the strict evaluation contract.

## Validation

- updated evaluator passes `python -m py_compile`;
- branch remains `research/intelligence-swarm-reconstruction-001`;
- no new PR chain or branch was created;
- no future state, reward, completed trajectory or gold action is exposed;
- pretrained language model remains disabled.

## Current status

The `32,768`-frame workflow has been submitted by commits `5101fd3c8823347ea5a91cbd3ae0dad472254245` and `fae049e09c7819d3bbf8cf827a2dade37b4c8a64`. A completed artifact was not yet available when this report was written.

Classification:

`staged_public_recurrent_reproduction_submitted / result_pending / capability_progress_not_claimed`

## Next decision

After the workflow completes:

1. verify all three checkpoints and full hashes;
2. verify all five methods share all 60 initial-instance fingerprints;
3. compare Correct against Random, Language-blind and Language-shuffle at episode level;
4. record model bytes, maximum RSS, training wall time and CPU inference latency;
5. continue budget scaling only if competence improves without violating the declared resource ceiling.

- public capability baseline: not yet reproduced
- novelty: not established
- capability progress: not recognized
- high-school-level intelligence: not achieved
