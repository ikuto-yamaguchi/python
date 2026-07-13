# CAP-SEM-001: weakly supervised relational meaning invariance

## Ability definition

Induce latent relation classes, synonym equivalence, and inverse direction from tokenized clauses paired only with final truth labels. Reuse the induced meaning map to answer unseen multi-hop relation queries.

This is managed as a capability rather than a new phase. Its evidence remains valid independently of later experiments, and later semantic work must reuse or supersede the same runtime under an explicit resource comparison.

## Training signal

The learner receives 288 records containing:

- one tokenized fact clause;
- one tokenized query clause;
- a final Boolean answer.

The records do not contain canonical relation names, relation IDs, forward/inverse labels, parse trees, or proof traces. The learner forms equivalence classes from answer signatures, induces inverse pairs, and assigns arbitrary latent relation IDs.

## Held-out gate

The 128 held-out records use entity names never present in training and relation chains of length two through five. The gate also applies three metamorphic transformations:

- replace every relation phrase with a learned synonym;
- rename every entity consistently;
- reverse the order of all fact clauses.

A literal exact-record memorizer is frozen as the weak baseline.

## Hard budgets

- learned payload: at most 4,096 bytes;
- compressed executable description: at most 200,000 bits;
- training computation: at most 200,000 counted operations;
- average inference: at most 128 counted operations per record.

The executable measure compresses the Python code objects of the learner and semantic runtime together with the learned payload reported separately. It is a Python-version-specific engineering measure, not a universal Kolmogorov complexity claim.

## Passing conditions

- held-out accuracy at least 95%;
- at least 25 percentage points above exact memorization;
- at least 95% under every metamorphic transformation;
- predictions invariant under synonym substitution, entity renaming, and fact reordering;
- all hard resource budgets satisfied.

## Claim boundary

Passing demonstrates controlled semantic class induction and compositional transfer after clause boundaries and argument slots have already been supplied. It does not demonstrate raw Japanese parsing, unrestricted meaning understanding, world knowledge, dialogue, high-school intelligence, or LLM parity.

## Next capability

`CAP-SEM-002` must remove the supplied clause and argument slots. It should learn a raw Japanese surface-to-event bridge from continuous text while keeping the `CAP-SEM-001` latent relation runtime frozen. A new task-specific semantic solver is not acceptable evidence.
