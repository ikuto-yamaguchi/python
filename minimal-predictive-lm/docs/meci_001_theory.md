# MECI-001: operational quotient theory

MECI is a non-neural machine. Knowledge is stored as executable programs, not dense learned matrices, and experience is represented only by distinctions required by declared cognitive queries.

## Scope

A machine cannot honestly be claimed fastest and smallest for every computable environment. The claim here is relative to a declared executable query family Q, error tolerance epsilon, and resource budget B.

Let H be observable histories, Q_B the cognitive tests executable within B, and A_B(h,q) the required answer or action. Define:

```text
h ~_B h' iff A_B(h,q) = A_B(h',q) for every q in Q_B.
```

The MECI state is the equivalence class [h]_B. Adding a demonstrated capability may refine the quotient; unsupported distinctions are not stored.

## Theorem 1: memory lower bound

Let N_B be the number of classes in H / ~_B. Any exact agent answering every query in Q_B must have at least N_B distinguishable internal states. Otherwise two histories from different classes collide and their separating query is answered incorrectly.

Therefore worst-case working-state memory is at least:

```text
ceil(log2 N_B) bits.
```

A canonical quotient index uses exactly this many bits, apart from a fixed machine-description constant. MECI attains the finite-class task-relative state-memory lower bound.

The theorem is related to Myhill-Nerode minimization, predictive-state representations, causal states, and bisimulation. The novelty candidate is a budget-indexed quotient over heterogeneous executable queries spanning prediction, answer generation, planning, and action.

## Theorem 2: update decision lower bound

For a current state and observation, let D be the distribution over next operational states. Any binary branch dispatcher has expected decision depth at least H(D). A Huffman dispatcher has expected depth below H(D)+1.

Thus MECI can attain the expected state-dispatch lower bound within one binary decision when D is known. This is a dispatcher bound, not a claim that arbitrary reasoning programs run in constant time.

## Learning

MECI begins with coarse states. A state splits only when an executable query or observed consequence separates two histories. The separating program is retained as a certificate for the split. Histories with identical answer rows merge.

The machine stores a quotient-state identifier, prefix-coded state transitions, executable response and action programs, and only the scratch data required by the selected program.

Program discovery remains the central unsolved problem. The theorems minimize representation and dispatch after the relevant distinctions and programs have been found; they do not make universal program search cheap.
