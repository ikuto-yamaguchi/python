# Phase 17f: Linear-time semantic factor induction

## Motivation

Phase 17e proves that lexical direction and template orientation are identifiable
when the verb-template observation graph is connected. Its reference experiment
still enumerates all `2^(V+T)` parameter assignments. That is acceptable for four
verbs and three templates, but it cannot scale.

Phase 17f replaces enumeration with direct graph propagation.

## Constraint system

Every informative observation yields one equation over GF(2):

```text
verb_bit XOR template_bit = observed_surface_direction
```

The equations form a labeled bipartite graph. Fix one root bit to zero in each
connected component and propagate the remaining values by breadth-first search.

For every traversed labeled edge `(u, v, y)`:

```text
value[v] = value[u] XOR y
```

If an already assigned node disagrees with this value, the cycle is contradictory
and the learner rejects the observations.

## Complexity theorem

Let

- `V` be the number of lexical nodes;
- `T` be the number of template nodes;
- `E` be the number of observed edges.

Building the adjacency lists costs `O(E)`. Breadth-first traversal visits each node
once and inspects each undirected edge twice. Therefore induction costs

```text
O(V + T + E)
```

and stores

```text
O(V + T + E)
```

working information.

The experiment counts:

1. one operation for ingesting each observation edge;
2. one operation for each queue node visit;
3. one operation for every adjacency inspection.

Under that explicit accounting, operations are bounded by

```text
3E + V + T
```

## Failure behavior

### Disconnected graph

Each component can be internally solved, but relative coordinates between two
components remain unidentified. The model therefore predicts verb-template pairs
within a component and abstains on cross-component pairs.

It does not pick an arbitrary orientation.

### Contradictory cycle

If the XOR labels around a cycle are inconsistent, no hypothesis in the declared
semantic family can satisfy the observations. The learner raises an inconsistency
error instead of increasing model size or memorizing exceptions.

## Scaling campaign

Generate connected spanning-tree graphs at:

```text
4 verbs x 3 templates
64 x 64
256 x 256
1024 x 1024
```

A spanning tree has `V + T - 1` observed edges, exactly matching the number of
independent semantic bits after quotienting the global coordinate gauge.

At `1024 + 1024` nodes:

- raw enumeration would contain `2^2048` parameter assignments;
- graph induction remains linear in 2,048 nodes and 2,047 observations.

The campaign verifies all observed edges plus representative unobserved
verb-template pairs.

## Preservation test

The graph solver is also trained from the six Phase 17e interventions and evaluated
on the same 12 unseen verb-template compositions with new entity names. Accuracy
and coverage must remain 100%.

This prevents the computational optimization from changing the established
semantic behavior.

## Resource accounting

Report separately:

- logical semantic bits (`V + T - 1` for a connected spanning tree);
- serialized learned model bits;
- induction operations under the declared ledger;
- source bytes for Phase 17d through Phase 17f;
- excluded Python runtime and standard-library substrate.

The logical semantic-bit count is an information lower bound, not total system size.

## Claim boundary

Phase 17f proves computational discoverability for this finite XOR-factorized
semantic family. It does not imply that arbitrary grammar, world models, programs,
or natural-language meanings can be discovered in linear time.

The XOR factorization itself remains a human-selected hypothesis family. Later
campaigns must either learn richer factor structures or report where tractable
identification ends.

## Next gate

The next phase should address statistical rather than computational idealization:

- noisy and contradictory world observations;
- maximum-likelihood or Bayesian recovery;
- a finite-sample recovery bound as a function of noise and graph connectivity;
- calibration and abstention when posterior ambiguity remains;
- comparison of repeated interventions against adding model parameters;
- preservation of linear or near-linear inference in sparse graphs.
