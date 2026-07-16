# SPARC-HS10: weakly supervised structural discourse-role induction

HS10 removes the requirement that every new document contain fixed cue words such as `なぜなら`, `例えば`, `しかし`, or `したがって`.

## Learning mechanism

1. Cue-rich bootstrap documents provide weak role labels through the existing HS9 parser.
2. Cue words are removed before role features are learned, preventing direct cue memorisation.
3. Each role stores sparse character-fragment, suffix, length and relative-position evidence.
4. Role-to-role transition counts are learned from complete documents.
5. A bounded Viterbi pass combines local feature evidence with structural consistency for an unseen document.
6. The induced roles are inserted into the existing HS9 reverse-indexed discourse graph.

The role inventory remains small and explicit, but role assignment for new prose is learned from examples rather than requiring the original cue expressions.

## Resource contract

- seven role candidates per sentence;
- no corpus scan during classification;
- no Transformer, softmax attention, backpropagation through history or growing KV cache;
- local dynamic programming proportional to document length and the square of the seven-role inventory;
- existing HS9 per-target reverse edge indices remain unchanged.

## Claim boundary

HS10 is weakly supervised discourse-role induction, not unrestricted semantic understanding. It targets cue-free paraphrase transfer and structural consistency. Implicit irony, literary intent and arbitrary long-range discourse remain outside this stage.
