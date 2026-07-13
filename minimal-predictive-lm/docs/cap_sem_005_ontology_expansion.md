# CAP-SEM-005: ontology expansion from data

## Ability definition

Detect relation expressions that cannot be represented by the frozen four-code ontology, allocate a new directed inverse relation pair, and use the same generic graph search for multi-hop inference.

The learner must first test every unknown expression against all existing codes. Expressions that exactly match an existing relation are absorbed into that code and must not expand the ontology. Only the residual statement/query behavior matrix may create new classes.

## Training signal

The learner receives raw controlled-Japanese single-fact documents with final Boolean labels:

- novel statement expressions contrasted with every frozen query code in both argument orders;
- novel query expressions contrasted with every frozen statement code;
- novel statement/query expressions contrasted with each other to reveal same and inverse behavior.

No new code number, inverse label, relation name, or ontology-size target is supplied.

## Generic ontology learner

For residual expressions, the learner:

1. builds same-direction and reversed-direction behavioral matrices;
2. induces query classes from distinct columns;
3. maps statement expressions to one same class and one inverse class;
4. requires an involutive, non-self inverse mapping;
5. allocates adjacent even/odd codes after the highest frozen code.

The inference runtime uses a dictionary indexed by `code // 2`, rather than the fixed two-element graph tuple from CAP-SEM-001. It has no branch naming or special-casing the new relation.

## Gates

- one new inverse pair and eight new marker mappings;
- 128 unseen two-to-five-hop documents using the new pair with old-relation distractors;
- entity/template/fact-order shift and complete marker renaming;
- exact raw-text memorization baseline;
- exact prediction equivalence with the old runtime on all legacy held-out records;
- a duplicated old relation must map to existing codes without ontology growth;
- incomplete inverse evidence, contradictory behavior, and unregistered expressions must be rejected;
- frozen CAP-SEM-001 payload and CAP-SEM-002 surface bridge;
- payload, training-compute, and inference-compute limits.

## Claim boundary

This is genuine ontology-size growth, but the new relation still shares the same directed, transitive graph algebra as the old relations. The calibration corpus is synthetic and behaviorally complete. It does not discover arbitrary relation algebra, non-transitive concepts, world knowledge, natural Japanese ontology, or Japanese high-school intelligence.

## Next capability

`CAP-SEM-006` must induce a relation with a different algebraic law—such as symmetric, non-transitive, or state-changing behavior—while selecting or extending the runtime from data rather than adding a relation-specific branch.
