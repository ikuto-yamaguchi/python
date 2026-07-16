from minimal_predictive_lm.sparc_core import SurprisePropagatedGraph


def test_allocates_structure_not_observations() -> None:
    graph = SurprisePropagatedGraph(code_space=128, active_bits=4, familiarity_threshold=0.5)
    codes = [
        (1, 2, 3, 4),
        (10, 11, 12, 13),
        (20, 21, 22, 23),
    ]
    for _ in range(20):
        for index, code in enumerate(codes):
            graph.observe(code, f"payload-{index}")
    report = graph.report()
    assert report.nodes == 3
    assert report.observations == 60
    assert report.write_fraction < 0.15


def test_noisy_overlap_recalls_and_transition_simulates() -> None:
    graph = SurprisePropagatedGraph(code_space=256, active_bits=6, familiarity_threshold=0.5)
    codes = [
        (1, 2, 3, 4, 5, 6),
        (20, 21, 22, 23, 24, 25),
        (40, 41, 42, 43, 44, 45),
    ]
    for _ in range(4):
        for index, code in enumerate(codes):
            graph.observe(code, f"payload-{index}")
    recalled, similarity, candidates = graph.recall((1, 2, 3, 4, 5, 99))
    assert recalled == "payload-0"
    assert similarity >= 5 / 6
    assert candidates >= 1
    assert graph.simulate(codes[0], 3) == (0, 1, 2)


def test_roundtrip_preserves_local_program() -> None:
    graph = SurprisePropagatedGraph(code_space=128, active_bits=4)
    graph.observe((1, 2, 3, 4), "a")
    graph.observe((10, 11, 12, 13), "b")
    graph.observe((1, 2, 3, 4), "a")
    restored = SurprisePropagatedGraph.from_bytes(graph.to_bytes())
    assert restored.recall((1, 2, 3, 4))[0] == "a"
    assert restored.simulate((1, 2, 3, 4), 2) == (0, 1)
