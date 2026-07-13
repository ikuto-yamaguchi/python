from pathlib import Path
import tempfile

from minimal_predictive_lm.phase19a_general_learning_reality_gate import collect_corpus, learn_merges
from minimal_predictive_lm.phase19b_cross_file_span_gate import build_span_tasks, run_gate


def _write_corpus(root: Path) -> None:
    samples = {
        "code": (".py", "def transform(value):\n    return value + 1\n\nclass Engine:\n    pass\n"),
        "prose": (".md", "# 設計メモ\nこの研究は予測と圧縮を統合する。\n未知の文脈を復元する。\n"),
        "structured": (".json", '{"name":"alpha","value":1,"enabled":true,"items":[1,2,3]}\n'),
    }
    for domain, (suffix, text) in samples.items():
        for index in range(30):
            directory = root / domain
            directory.mkdir(exist_ok=True)
            payload = (text.replace("alpha", f"alpha{index}").replace("value + 1", f"value + {index % 4 + 1}")) * 12
            (directory / f"sample_{index}{suffix}").write_text(payload, encoding="utf-8")


def test_tasks_are_file_disjoint_and_nontrivial():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        _write_corpus(root)
        train, heldout = collect_corpus(root, total_limit=1_000_000)
        tasks = build_span_tasks(heldout)
        assert tasks
        assert all(len(task.candidates) == 8 for task in tasks)
        assert all(task.target in task.candidates for task in tasks)
        assert not ({row.path for row in train} & {row.path for row in heldout})


def test_task_order_is_deterministic():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        _write_corpus(root)
        _, heldout = collect_corpus(root, total_limit=1_000_000)
        assert build_span_tasks(heldout) == build_span_tasks(tuple(reversed(heldout)))


def test_merges_are_learned_without_task_labels():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        _write_corpus(root)
        train, _ = collect_corpus(root, total_limit=1_000_000)
        merges = learn_merges(train)
        assert merges
        assert all(merge.token >= 256 for merge in merges)


def test_gate_has_explicit_claim_boundary():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        _write_corpus(root)
        result = run_gate(root)
        assert result["high_school_intelligence"] is False
        assert result["general_llm_parity"] is False
        assert result["tasks"] > 0


def test_candidates_are_same_length_and_unique():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        _write_corpus(root)
        _, heldout = collect_corpus(root, total_limit=1_000_000)
        for task in build_span_tasks(heldout):
            assert len(set(task.candidates)) == len(task.candidates)
            assert {len(candidate) for candidate in task.candidates} == {len(task.target)}
