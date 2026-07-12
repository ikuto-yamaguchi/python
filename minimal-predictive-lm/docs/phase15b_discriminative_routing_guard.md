# Phase 15b: discriminative routing guard

## Problem

The Phase 13 sequence-ordering program was induced only from positive examples. Its cue set included `these`, which is common in many non-ordering instructions. On the frozen Phase 15a suite this caused forty unsupported navigation answers.

## Method

Four controlled non-ordering prompts are supplied as negative routing evidence. Candidate cue conjunctions of up to three words are enumerated. A valid cue set must occur in every positive ordering example and no negative example; MDL selects the shortest valid set.

The selected cue is `sort`. No navigation word, task name, or benchmark example is used.

## Result

All forty false-positive navigation answers disappear. The system abstains on all 200 unsupported Phase 15a examples, while the original Phase 14b public suite remains 200/200.

This phase improves selective calibration only. It gains no new reasoning capability.
