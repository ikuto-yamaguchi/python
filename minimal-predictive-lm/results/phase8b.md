# Phase 8b results: latent roles and operations from interaction traces

No intent label or entity/location type label is supplied to the main learner.
SET/GET operations are inferred from state differences and responses; argument
positions induce two reusable symbol roles.

- traces: **9**
- inferred operations: **9**
- key-role purity: **100.0%**
- value-role purity: **100.0%**

## Representation competition

| hypothesis | program bits | validation accuracy | lifetime objective |
|---|---:|---:|---:|
| exact_surface | 2082 | 50.0% | 4,130 |
| untyped_symbols | 163 | 75.0% | 1,964 |
| two_latent_roles | 163 | 100.0% | 953 |

Selected: **two_latent_roles**.

The untyped parser accepts a role-reversed command that the two-role
representation rejects. The exact parser cannot transfer to held-out
combinations. The two-role hypothesis pays one role bit per observed symbol
and wins the full error-plus-description objective.

## Factor away unnecessary linguistic intents

- remember/move/query surface program: **202 bits**
- SET/GET state-operation program: **163 bits**

Declarative remembering and imperative moving both produce the same SET
transition, so preserving two separate internal intents is unnecessary for
this world model.

## New-symbol bootstrap

One observed transition introduces `予備部品` and `棚A` for **130 new symbol bits**.
No rule bits are added. Subsequent commands using the new symbols score **100.0%**.

## Limitation

This is still a one-relation deterministic micro-world. The learner observes
state transitions and responses, and the surface hypothesis language is
restricted. It has not discovered arbitrary predicates or goals from raw
open-domain interaction.
