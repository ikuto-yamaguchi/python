# Phase 18c-2: raw Japanese bridge to the multiplicative core

## Goal

Compile short Japanese quantity statements into the Phase 18c-1 dimension-checked product graph for three relation families:

- speed, distance, and time,
- concentration, solution mass, and solute mass,
- quantity, total price, and unit price.

## Fixed surface layer

The parser fixes sentence splitting, the forms `CUEはNUMBER UNITである` and `CUEを求めよ`, and a small unit inventory. It extracts exactly two known facts and one requested quantity. It does not contain a solver.

## Learned lexicon

Eighteen recurring cue phrases must be mapped to nine semantic roles. Units make most roles unique, but four `g` cues can denote either solution mass or solute mass, leaving 16 lexical hypotheses. Eighteen calibration problems, covering all three possible unknown positions, must select one lexicon. The resulting structured case is solved and verified by Phase 18c-1.

## Gates

- speed, concentration, and unit-price domains,
- product, left factor, and right factor as the unknown,
- fractions, decimals, percentages, cue variants, and fact-order shifts,
- frozen held-out values across 18 problems,
- exact proof replay,
- ambiguous mass lexicon rejection,
- unknown cues, extra numeric facts, unit-role mismatch, mixed relations, and multiple questions,
- whole-text memorizer coverage zero,
- number-and-unit bag upper bound 50%,
- altered answer/proof rejection.

## Claim boundary

This is a controlled Japanese language bridge. All cue phrases appear during calibration, syntax and units are fixed, and no unit conversion is performed. It is not unseen-word understanding, free Japanese parsing, general nonlinear reasoning, or high-school intelligence.
