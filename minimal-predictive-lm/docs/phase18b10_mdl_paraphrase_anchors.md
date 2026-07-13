# Phase 18b-10: MDL paraphrase anchors

Phase 18b-9 only accepts exact learned relation spans. Phase 18b-10 adds nine answer-grounded extension spans and searches for a minimum-description set of recurring, role-pure character anchors.

The fixed morpheme splitter removes placeholders and a small function-word list. Candidate anchors are induced from longest common substrings between same-role content chunks, must recur in at least two spans, and must not occur in another role. All candidate subsets are enumerated; the unique minimum UTF-8-byte cover is retained.

Held-out problems use complete relation spans never seen in either the base or extension set, but each contains one learned anchor. The exact-span baseline must have zero coverage while the anchor model must retain exact answers and independently replayable proofs.

Negative controls require abstention for conflicting anchors, no anchor, a rate anchor in the wrong structural arity, and a completely unseen synonym. Removing any selected anchor must reduce frozen held-out coverage.

This is controlled surface-morpheme recombination. It is not semantic synonym understanding, unrestricted Japanese parsing, or high-school intelligence.
