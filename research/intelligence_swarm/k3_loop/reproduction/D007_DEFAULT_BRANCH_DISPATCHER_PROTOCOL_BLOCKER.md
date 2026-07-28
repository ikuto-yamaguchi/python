# D007 — Default-branch thin-dispatcher protocol blocker

Date: 2026-07-29
Canonical branch: `research/intelligence-swarm-reconstruction-001`
Canonical commit inspected: `d7ad9e5efece7929987b53c15d0079d6d4c875c7`

## Scope

C006で許可されたdefault-branch thin dispatcherの導入とenvironment-only run起動を試みた。モデル実行、dataset/tokenizer/checkpoint取得、semantic trace、学習、量子化は実施していない。

## Fixed identities recovered before the attempt

- C003 manifest blob: `5677b3ec00d7e5d8f56fce1fb96248d6bf680dd9`
- C004 manifest blob: `3814f9ef98ec10b83a4bf387302d1246cd8803d6`
- C006 manifest blob: `880e977f67ae093305ff517716aaa86389db17b3`
- environment script blob: `f48040ba5cdbf0bf71343391ab132d8adbbe96c0`
- environment probe blob: `e85ca24025ef0921d34851dd62f9740a6a1447da`

## Attempt and result

A minimal `workflow_dispatch` file was introduced on `main` at commit `0091e002dfb965e59adda99d7319ceba03e565e6` to test whether the repository/default-branch write route was available.

The introduced file did not yet satisfy the full C006 identity contract. A second write was therefore attempted to add all immutable inputs, detached-checkout checks, branch reachability, registered blob checks, authorization isolation, raw evidence, and checksum capture. The GitHub write operation was rejected by the available execution interface before the compliant replacement could be committed. A cleanup deletion attempt was rejected by the same interface.

No workflow run was dispatched. The incomplete dispatcher must be treated as **not authorized for execution**.

## Classification

`ENV_PROTOCOL_FAIL / ROUTE_STOP_DEFAULT_BRANCH_PENDING_CLEANUP`

Rationale:

1. default-branch write permission exists in principle, as the minimal file creation succeeded;
2. the committed launcher lacks required C006 inputs and identity gates;
3. dispatching it would violate preregistration;
4. the available interface rejected both the compliant replacement and cleanup deletion;
5. no scientific environment/import evidence was produced.

This does not reject Block AttnRes, PB1, CR1, or dependency compatibility. It stops the current D007 execution route until the default-branch file can be replaced or removed through an interface that permits an auditable compliant workflow update.

## Exact required cleanup / next minimal action

1. Do not dispatch `.github/workflows/d007-k3-environment-dispatcher.yml` in its current form.
2. Replace it atomically with the complete C006-compliant launcher, or delete it first.
3. Verify the final workflow blob SHA and review the diff against C006.
4. Only then dispatch attempt 1 using canonical commit `d7ad9e5efece7929987b53c15d0079d6d4c875c7` and the five blob SHAs listed above.
5. If repository policy or tooling still prevents the compliant replacement, classify `ROUTE_STOP_DEFAULT_BRANCH` and stop this GitHub Actions route.

## Evidence boundary

No model bytes, parameter count, active compute, RSS/VRAM, wall time, tokens/sec, CPU generation, quantization, quality, routing stability, long-context behavior, or three-seed result was measured in this run.
