# CAP-GEN-002 scalable recurrent core

## Why this iteration exists

The previous critical path optimized tiny serialized symbolic payloads. Those mechanisms remain useful as optional program and verification components, but a roughly two-kilobyte learned payload has no demonstrated route to Japanese high-school intelligence.

This iteration changes the priority:

1. build a model that can scale to the capacity required by broad language and curriculum learning;
2. keep the runtime non-Transformer and resource-accounted;
3. judge success by frozen multi-domain transfer, not by payload size or synthetic micro-gates;
4. reduce model size only after capability is preserved.

## Architecture

`MultiScaleRecurrentCore` is the first executable replacement foundation.

- UTF-8 byte-pair hashing feeds a shared trainable embedding table.
- A low-rank recurrent transition replaces quadratic self-attention.
- Four interleaved decay rates preserve immediate, sentence, paragraph, and longer-lived state.
- One shared next-byte decoder is trained across mixed raw streams.
- A task-name-free associative episodic memory stores explicit learned experiences.
- Existing sparse programs and verification machinery can later be attached as an external execution layer rather than treated as the entire intelligence model.

The current reference trainer updates the shared decoder while the recurrent feature generator remains fixed. That is intentionally only the first executable baseline. The next architecture iteration must make embeddings and recurrent factors trainable and then measure external transfer on `CAP-GEN-001`.

## Capacity profiles

| profile | planned persistent state | planned training peak | role |
|---|---:|---:|---|
| CI smoke | 673,152 bytes | about 2.8 MiB | mechanics only; explicitly not a high-school candidate |
| local RTX 4060 | 176,169,472 bytes | about 1.21 GiB | first serious local candidate |
| next scale | 731,922,944 bytes | about 4.90 GiB | promotion after demonstrated transfer |

These figures include embedding, recurrent, decoder, and episodic-memory allocations represented by the profile. They do not claim that 168 MiB or 698 MiB is sufficient. Capacity is increased when the integrated evidence requires it, up to the actual local hardware limit.

## Promotion rule

The smoke test proves only that the shared recurrent mechanism executes and learns from mixed Japanese raw text. It cannot promote a high-school claim.

The architecture enters the main critical path only after all of the following are measured:

- the same checkpoint is used on all fifteen axis-blind public axes;
- aggregate and minimum-axis scores both improve;
- no axis-specific parser, solver, prompt template, or task-name branch is added;
- at least five prospectively frozen axes show transfer;
- persistent state, optimizer state, activations, training bytes, and inference operations are reported;
- the Japanese high-school gate remains false until the complete frozen curriculum and practical-work criteria pass.

## Immediate next experiment

1. Train the embeddings, low-rank recurrence, and decoder jointly on mixed raw Japanese, mathematics, science, code, and explanatory lessons.
2. Distill recurrent state into reusable event and variable bindings without adding domain routes.
3. Attach sparse program execution only when the shared latent state requests verification.
4. Run the unchanged `CAP-GEN-001` scorer.
5. Keep the architecture only when multiple unrelated axes improve together; otherwise pivot the shared representation or objective under the existing stop rules.
