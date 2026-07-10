# Phase 7: Scaling toward conversation and instruction following

## Question

Do the minimum-state and minimum-compute ideas still work when the machine must interact over multiple turns, preserve references, follow instructions, use a tool, observe failure, and revise its action?

A successful result must separate three claims:

1. sparse state and direct lookup scale;
2. controlled language understanding works;
3. unrestricted human conversation works.

Passing (1) or (2) must never be reported as passing (3).

## Three reproducible attempts

### v0: literal scan agent

- exact surface templates only;
- no discourse focus;
- facts are scanned linearly;
- no correction, compound instruction, or tool-recovery loop.

This is intentionally weak and exposes the cost of storing facts without a canonical interface.

### v1: canonical indexed agent

- statements, moves, and queries compile to canonical predicates;
- one focus register resolves a small class of pronouns and ellipsis;
- facts use a direct `(relation, subject)` index;
- a toy code task can execute tests, preserve failure evidence, and retry.

The first version omitted shared normalization for polite variants and sequential punctuation. It reached 14/17 turns.

### v2: shared normalization

Instead of adding one handler per failed sentence, polite verb endings, direction particles, and compound separators are normalized before intent matching. This reaches 17/17 on the controlled suite.

### v3: residual paraphrase rewrites

Four observed colloquial failures are compiled into four surface rewrites. They raise the observed colloquial probe from 50% to 100%, but a shifted colloquial probe remains at 50%. This is an explicit overfitting result: memorizing paraphrase residuals is not a scalable route to ordinary conversation.

## Resource measurements

### Fact lookup

The linear store pays `N` fact reads for a worst-case query over `N` facts. The indexed store pays one abstract lookup in this benchmark. Exact persistent storage still grows linearly because independent names and locations contain independent information.

### Dialogue length

Ten thousand repeated queries do not copy the transcript into active state. Only the current exact facts and a small discourse focus remain active. One fact read is paid per query.

This result does not imply that every old turn can be discarded. A turn that introduces a new fact, promise, unresolved goal, or distinction capable of changing a future action must consume state or be archived externally.

### Tool task

The controlled `transform` task deliberately selects a shortest patch that fits visible tests, observes hidden-test failure, stores the failure evidence, retries, and verifies the final patch. It demonstrates a closed action-observation-revision loop, not repository-scale coding.

### Candidate explosion

The current candidate loop is exhaustive. With `K` candidates in the adversarial controlled case, it performs `2K` evaluations. This does not scale to real repositories. The next architecture must synthesize structured candidates, use admissible bounds, retrieve only relevant code, and compile repeated successful search into reusable programs.

## Current conclusion

The following now scale in the controlled experiment:

- exact unseen-name retention;
- active state independent of irrelevant transcript length;
- indexed fact lookup independent of stored fact count;
- multi-turn focus, correction, and compound instructions inside a small grammar;
- a tool-failure/retry loop.

The following do not yet scale:

- unrestricted paraphrase and ambiguity;
- automatic induction of intents, predicates, goals, and reusable programs;
- open-domain knowledge;
- repository-scale code search and patch synthesis;
- creative and explanatory conversation comparable to a high-performance LLM.

The next research target is not a larger hand-written grammar. It is **residual-driven semantic program induction**: histories that require different actions but collapse to one canonical state must generate the smallest new parser feature, predicate, or program schema whose held-out utility exceeds its program bits, state bits, memory traffic, and search cost.

## Claim discipline

Until unrestricted held-out interaction and real task suites are passed under a complete cost ledger, the system is a controlled conversational work machine prototype, not a general LM replacement.
