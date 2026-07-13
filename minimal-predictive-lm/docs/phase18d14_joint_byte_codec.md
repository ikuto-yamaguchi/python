# Phase 18d-14: joint byte codec and primitive invention

Phase 18d-13 still decoded UTF-8 before learning symbols. Phase 18d-14 receives a hex-encoded byte stream that is deliberately invalid UTF-8 and jointly selects:

1. record and field separator roles,
2. a byte-to-symbol codec/chunking hypothesis,
3. reusable primitives that compress residual behavior.

The codec hypothesis space contains single-byte atoms, a mixed-width tagged codec, and a distinct fixed-width two-byte prefixed codec. The task stream contains known operations, two unknown operations, and one-off noise. No task IDs, record count, input/output field names, codec parameters, or primitive parameters are supplied.

A candidate codec must yield complete two-field records with both letter and anonymous-symbol alphabets. The decoded stream is then processed causally. Reusable affine index and affine element behaviors are promoted only with cross-alphabet support and positive MDL gain.

Required controls:

- the original bytes must be invalid UTF-8;
- changing separators, marker byte, and tagged payload origin must preserve the learned primitives;
- re-encoding the same records with the separate fixed-width pair codec must recover that codec family and the same primitives;
- single-alphabet, truncated-tag, and malformed-hex streams must be rejected;
- audit labels must not enter the learner API.

This removes a fixed UTF-8 decoder but not all representation assumptions. Codec families, two-field grammar, high control-byte search, primitive meta-grammar, and MDL policy remain human-designed.
