# SPARC-HS13: learned perspective and event-state workspace

HS13 targets three weaknesses that directly block natural conversation: state change, reference focus, and the difference between the actual world and another person's belief.

## Architecture

- Event programs are induced from repeated before/after state demonstrations. The learner compares sparse world and belief slots, discovers the changed attribute, identifies which textual agent slots received the update, and removes concrete names into a reusable surface schema.
- A second learned event program can omit the object slot. At execution it reactivates the most recent object from a fixed-size focus workspace, allowing surfaces such as `それを戸棚へ移した` without scanning the conversation history.
- Actual facts and per-agent beliefs are separate sparse key-value slots. An observed move updates only the world and the agents selected by the learned event program. Unobserving agents keep their previous belief.
- Query programs are induced by finding the actual-world or belief slot that explains multiple demonstrated answers. Focused query programs are learned from demonstrations where the agent or object is omitted.
- Direct causal attribution uses the event that last wrote the queried state slot. It reports the previous and new values and the source ID.

## Resource rule

Inference routes through a few learned schemas, one direct state slot, and at most the fixed focus workspace. It does not scan all objects, beliefs, events, or prior dialogue turns. There is no Transformer, softmax attention, growing KV cache, or dense global state update.

## Claim boundary

HS13 is a bounded event-state and first-order perspective model. It does not yet support nested beliefs such as “A thinks that B believes…”, unrestricted event language, counterfactual narratives, or Japanese high-school-level general intelligence. The integrated public reasoning gate must be rerun before any broader claim.
