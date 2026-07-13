# Phase 18d-13: raw UTF-8 multi-primitive invention

Phase 18d-12 still received typed records with explicit `input` and `output` fields. Phase 18d-13 replaces them with one hex-encoded UTF-8 stream. The learner must recover separator roles, complete records, and two different reusable transformations before predicting later examples.

The data file contains only campaign metadata, `stream_hex`, and audit labels. The labels are never accepted by the learner. Numeric-list-like values are represented by anonymous Private Use Unicode glyph sequences; ordinary string values use ASCII letters. Neither representation is declared to the learner as a type.

The grammar search tries every ordered pair of non-payload symbols and accepts only a complete two-field segmentation. The residual learner then searches:

- affine index transducers, `y_i = x[(a i + b) mod n]`;
- element-wise affine transducers, `y_i = s x_i + c`;
- a lookup control.

A primitive needs support across both ASCII-letter and Private-Use alphabets, positive MDL gain, and a unique top probe behavior. Identity-equivalent lookup behavior is rejected.

The frozen experiment requires the stream to recover 48 records and promote two primitives at positions 15 and 20: index `(1,1)` and element `(1,1)`. Twenty-one future hidden records are reserved for post-promotion evaluation. Replacing both separators and shifting every Private Use glyph must preserve the recovered primitive behaviors.

This is not unrestricted raw-byte learning. UTF-8 decoding, the two-field grammar family, payload alphabet gate, primitive families, parameter ranges, probe set, and MDL rule remain human-designed. The learner operates on Unicode codepoints after decoding and does not establish natural-language understanding, LLM-like generality, or high-school intelligence.
