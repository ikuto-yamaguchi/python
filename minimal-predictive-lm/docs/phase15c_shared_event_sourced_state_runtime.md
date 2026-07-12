# Phase 15c: shared event-sourced state runtime

## Question

Can four apparently different public tasks share one state-transition runtime rather than four task-name solvers?

## Representation

Each raw prompt is compiled into:

1. an initial typed state;
2. a sequence of events;
3. a query projection.

The runtime operations are:

- stack: `push`, `pop`;
- vector: `turn`, `move_relative`, `move_absolute`;
- mapping: `swap`;
- partial order: `less`, `rank`.

Queries emit missing stack closers, test whether a vector returned to the origin, map an agent's final value to an option, or resolve an ordinal proposition. No benchmark task name is passed to the runtime.

## Result

Eight independent held-out prompts across brackets, robots, API-token ownership, service ownership, job queues, and version ordering pass. On the public Phase 15a suite, logical ordering, swap tracking, navigation, and stack completion each improve from 0/40 to 40/40. Date understanding remains 0/40 by design.

Overall accuracy rises from 0% to 80%, with 160 answered and all 160 correct. The original public 200/200 remains unchanged.

## Limitation

The shared runtime is only 223 bytes, but the four surface compilers were human-designed after inspecting public formats. This demonstrates reusable internal state, not autonomous parser induction or broad language understanding.
