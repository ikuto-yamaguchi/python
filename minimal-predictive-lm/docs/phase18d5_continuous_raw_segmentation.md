# Phase 18d-5: continuous raw-stream segmentation

Phase 18d-4 still received an array of already segmented sequences. Phase 18d-5 provides one continuous string containing every training record.

The learner is not told which punctuation character separates records or which separates fields. It collects punctuation candidates from the raw stream, tests every ordered pair, parses all atoms, and retains only grammars whose complete record set admits an exact latent-program partition. Selection minimizes the number and total cost of latent programs; behaviorally distinct tied grammars are rejected.

After the initial grammar and seven latent programs are frozen, five more records are appended as raw text. The same code must retain all old behavior fingerprints and discover an eighth behavior. Held-out queries are routed with a raw local support record rather than a task name.

Metamorphic testing renames the delimiters from comma/semicolon to tilde/vertical-bar. The inferred roles and latent behavior fingerprints must remain unchanged. A malformed tail, one punctuation kind, and behaviorally ambiguous support must abstain.

This phase does not learn an unrestricted tokenizer. Integer signs and JSON quoted-string syntax are fixed lexical atoms, delimiter candidates are single punctuation characters, and the type system, DSL, exact-partition objective, next-field target, and minimum support are human-designed.
