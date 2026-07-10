from minimal_predictive_lm.phase6c_experiment import run


def test_horizon_changes_the_best_representation() -> None:
    payload = run()
    winners = {
        row["queries_per_task"]: row["winner"]
        for row in payload["horizon_frontier"]
    }
    assert winners[2] == "exact_cache"
    assert winners[4] == "shared_hybrid"
    assert winners[16] == "shared_hybrid"


def test_lifetime_global_selection_beats_myopic_commit_and_late_migration() -> None:
    costs = run()["policy_lifetime_costs"]
    assert costs["global_lifetime_selection"] < costs["rolling_reoptimization"]
    assert costs["rolling_reoptimization"] < costs["local_commit"]


def test_shared_rule_transfers_to_unseen_tasks() -> None:
    payload = run()
    costs = payload["heldout_costs"]
    assert costs["shared_schema"] < costs["exact_cache"]
    assert payload["heldout_ratio"] > 20
