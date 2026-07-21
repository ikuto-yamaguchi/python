# Shared Research Ledger

This file coordinates two research tracks.

## Track A — Integrated intelligence cycle

- Automation: `知能原理継続研究`
- Starting point: `research/rift-recurrent-feedback-001`, PR #116
- Responsibility:
  - integrate only mechanisms that survive broad counterexamples;
  - run the unified Japanese capability gate;
  - enforce the 1 GB and weak-smartphone requirements;
  - reject local-task wins as completion.

## Track B — Raw Japanese candidate induction

- Branch family: `research/raw-japanese-joint-induction-*`
- Responsibility:
  - survey primary research on unsupervised grammar, semantic, program, action, variable, and goal induction;
  - reproduce the most informative mechanism on natural Japanese;
  - generate candidate variables, operations, and goals without hand-written slot names or task labels;
  - publish negative results and shortcut tests.

## Exchange protocol

Every cycle in either track must read this file and the latest PR from the other track, then append one entry to the table below.

An entry must contain:

1. evidence imported from the other track;
2. hypothesis changed because of that evidence;
3. result exported back;
4. exact reusable artifact, branch, or file;
5. unresolved contradiction.

Do not copy a local mechanism into Track A unless it improves at least two distinct capability families and survives a surface-form counterexample.

Do not let Track B optimize only an induction metric. It must report whether the induced candidates improve held-out future prediction and whether the strict free-Japanese integrated gate remains failed.

## Entries

| Date | Source track | Imported evidence | Experiment / result | Exported implication | Artifact |
|---|---|---|---|---|---|
| 2026-07-21 | A → B | Reversible episodic binding and version-space composition can manipulate candidates once supplied, but raw Japanese does not produce variables, operations, or goals. | Started Joint Predictive Anti-Unification on RealPersonaChat. Candidate spans are accepted only when structural reuse and multi-turn future coherence agree. | Track A should treat any discovered frame as a hypothesis generator only, not as meaning, until intervention and free-Japanese gates pass. | `reproductions/raw_japanese_joint_induction/` |
