# Capability-unit research management

The project no longer advances by an open-ended sequence of phases. Historical phase identifiers remain immutable evidence references, but new research is organized by stable capability IDs.

## Required record for every capability

Each capability must define:

1. a behavioral ability rather than a benchmark or implementation feature;
2. a falsifiable held-out gate;
3. a frozen weak baseline and a stronger reference baseline when available;
4. distribution-shift and metamorphic tests;
5. executable total description length in bits;
6. training and inference computation as separate ledgers;
7. dependencies on earlier capabilities;
8. an explicit claim boundary and unresolved failure modes.

A capability does not pass merely because a new handler solves a task. The learned mechanism must transfer across at least one independently held-out axis such as entity identity, composition length, surface form, document domain, or temporal distance.

## Capability families

- `CAP-GL`: learning reusable structure from data without task labels.
- `CAP-XFER`: transfer to held-out domains or distributions.
- `CAP-MEM`: causal memory and state retention.
- `CAP-SEM`: meaning, grounding, reference, and entailment.
- `CAP-REASON`: reusable reasoning operators and proof traces.
- `CAP-KNOW`: acquisition, conflict handling, provenance, and forgetting.
- `CAP-GEN`: generation, dialogue, instruction following, and self-correction.

## Resource accounting

Model size is not reported only as parameter count. The primary measure is the compressed executable description plus learned payload, reported in bits. Training operations and inference operations are recorded separately so that a smaller stored model cannot hide an expensive search procedure.

## Current semantic program

`CAP-SEM-001` is the first capability-native experiment. It asks whether relation classes, synonym equivalence, and inverse direction can be induced from final truth labels without exposing canonical semantic labels, then transferred to unseen entity names and unseen multi-hop compositions.

The next target is `CAP-SEM-002`: raw Japanese clause and argument grounding. It must remove the supplied clause slots used by `CAP-SEM-001`, learn from continuous text, and retain the same semantic runtime and resource ledger rather than introducing a new task-specific solver.
