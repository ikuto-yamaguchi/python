# Phase 18d-6: UTF-8 byte codec and latent-program induction

## Question

Can the Phase 18d-5 learner remove its fixed JSON integer/string atom parser and explicit type labels, receiving only UTF-8 bytes while still recovering boundaries, numeric symbol values, latent tasks, and next-value programs?

## Input

Training is stored as one hexadecimal byte string. After decoding the storage wrapper, the learner receives only UTF-8 bytes. It is not given record boundaries, field boundaries, task IDs, task count, integer values, or type labels.

Numeric values are represented by single private-use Unicode glyphs from an unknown contiguous codepoint system. The learner searches the possible zero codepoint jointly with both delimiter roles and the latent program partition. Multi-character UTF-8 fields remain text atoms.

## Identification

The stream mixes addition, subtraction, multiplication, maximum, upper-case conversion, lower-case conversion, and string reversal. Translation-invariant maximum examples alone cannot identify the numeric zero: many offsets remain behaviorally equivalent. Addition, subtraction, and multiplication examples break that symmetry, leaving one codebook.

A codepoint-shift metamorphic test moves every numeric glyph by 37 codepoints. The recovered zero moves by the same amount while the induced program fingerprint remains unchanged.

## Gates

- Recover one record separator, one field separator, and the generated numeric zero.
- Recover seven initial latent programs and an eighth program after appending bytes, with no source change.
- Pass all 16 support-routed masked predictions.
- Preserve the previously learned program fingerprint after continual learning.
- Reject invalid UTF-8, streams with insufficient separator structure, offset-nonidentifiable evidence, and ambiguous support.
- Keep audit labels, atom values, and type labels outside the learner path.

## Claim boundary

The experiment learns a delimiter grammar and a contiguous private-use numeric symbol offset from bytes. It does not learn arbitrary atom syntax, general tokenization, an open type system, natural language, code, or world knowledge. UTF-8 validation, the private-use single-codepoint codec family, final-field prediction, the primitive DSL, exact cover, and minimum support remain human-designed.
