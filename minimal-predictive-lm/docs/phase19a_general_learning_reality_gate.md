# Phase 19a: general-learning reality gate

## Purpose

Phase 18d proved increasingly autonomous representation and primitive induction on controlled streams, but did not establish LLM-like scaling or Japanese high-school intelligence. Phase 19a is a falsification gate rather than another capability demo.

The learner is frozen. It automatically collects `.py`, `.md`, `.json`, `.yml`, and `.yaml` files from the repository, makes a deterministic file-disjoint split inside each domain, and learns only by next-token likelihood on raw bytes.

## Gate

Training data is nested at 25%, 50%, and 100%. For every scale the same procedure:

1. induce up to 64 byte-pair symbols from training files only;
2. train a third-order token Markov model;
3. evaluate unchanged held-out files;
4. amortize the learned dictionary payload into held-out bits per byte.

The experiment fails unless all conditions hold:

- code, prose, and structured-data held-out domains are all present;
- held-out files are completely disjoint from training files;
- held-out size is at least 16 KiB;
- held-out bits per byte improve monotonically as data grows;
- the learned dictionary model beats a raw-byte trigram under the same split;
- no task labels or answer annotations are supplied.

## Why this is stricter

Passing controlled task suites can be caused by a hand-designed hypothesis space. This gate asks whether a single self-supervised learner extracts reusable statistical structure from mixed repository data and shows a positive scaling curve on unseen files.

A failure is preserved as a red CI result. It means the current route has not yet demonstrated even this small prerequisite for LLM-like general learning.

## Claim boundary

Passing does **not** demonstrate Japanese language understanding, dialogue, world knowledge, long-horizon reasoning, coding competence, high-school-level intelligence, or parity with an LLM. It demonstrates only mixed-domain next-token/compression scaling on this repository.
