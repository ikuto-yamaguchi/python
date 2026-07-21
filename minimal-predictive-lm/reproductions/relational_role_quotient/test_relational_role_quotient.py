from relational_role_quotient import RoleQuotient, make_episode, run_one
import random


def test_role_induction_is_deterministic():
    rng = random.Random(1)
    seqs = [make_episode(rng, "memory", False, 2)[0] for _ in range(12)]
    a = RoleQuotient(); a.train(seqs)
    b = RoleQuotient(); b.train(seqs)
    assert a.roles == b.roles


def test_unknown_tokens_do_not_leak_answers():
    rng = random.Random(7)
    seqs = [make_episode(rng, "memory", False, 2)[0] for _ in range(24)]
    m = RoleQuotient(); m.train(seqs)
    seq, answer = make_episode(random.Random(19), "memory", True, 2)
    pos = seq.index("回答")
    pred, _ = m.predict(seq[:pos + 1], quotient=True)
    assert pred != answer


def test_full_run_preserves_claim_boundary():
    row = run_one("role_quotient", 1, 96)
    assert row.model_bytes < 1_000_000_000
    assert row.free_gate == 0.0
