from pathlib import Path

from minimal_predictive_lm.phase19a_general_learning_reality_gate import (
    CorpusFile,
    Merge,
    apply_one_merge,
    collect_corpus,
    encode,
    learn_merges,
    run_gate,
    stable_rank,
)


def _write_corpus(root: Path) -> None:
    rows = {
        "src/a.py": "def add(a, b):\n    return a + b\n" * 300,
        "src/b.py": "def mul(a, b):\n    return a * b\n" * 300,
        "src/c.py": "class Box:\n    value = 1\n" * 300,
        "docs/a.md": "日本語の文章から規則を学習する。知識を圧縮する。\n" * 300,
        "docs/b.md": "未知の問題では断定せず棄権する。検証可能性を保つ。\n" * 300,
        "docs/c.md": "学習量が増えると未見データの予測が改善するか測る。\n" * 300,
        "data/a.json": '{"kind":"math","value":1,"ok":true}\n' * 300,
        "data/b.json": '{"kind":"text","value":2,"ok":false}\n' * 300,
        "data/c.yml": "kind: code\nvalue: 3\nok: true\n" * 300,
        "tests/a.py": "def test_add():\n    assert 1 + 1 == 2\n" * 300,
        "tests/b.py": "def test_mul():\n    assert 2 * 3 == 6\n" * 300,
        "docs/d.md": "同じ学習器を変更せずに複数領域へ転移する。\n" * 300,
        "data/d.json": '{"kind":"mixed","items":[1,2,3]}\n' * 300,
        "src/d.py": "def reverse(xs):\n    return xs[::-1]\n" * 300,
        "docs/e.md": "世界知識や対話能力はまだ未達である。\n" * 300,
    }
    for name, content in rows.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_merge_application_and_encoding():
    merge = Merge(97, 98, 256, 3)
    assert apply_one_merge([97, 98, 97], merge) == [256, 97]
    assert encode(b"abab", (merge,)) == (256, 256)


def test_rank_is_stable():
    assert stable_rank("docs/a.md") == stable_rank("docs/a.md")
    assert stable_rank("docs/a.md") != stable_rank("docs/b.md")


def test_collect_is_file_disjoint_and_stratified(tmp_path: Path):
    _write_corpus(tmp_path)
    train, heldout = collect_corpus(tmp_path, total_limit=200_000)
    assert train and heldout
    assert not ({row.path for row in train} & {row.path for row in heldout})
    assert {"code", "prose", "structured"}.issubset({row.domain for row in heldout})


def test_merges_are_induced_from_data():
    files = (
        CorpusFile("a", "code", b"abcabcabcabc", 1),
        CorpusFile("b", "prose", b"abcabcabcabc", 2),
    )
    merges = learn_merges(files, max_merges=4, minimum_count=2)
    assert merges
    assert merges[0].count >= 2


def test_gate_reports_honest_claim_boundary(tmp_path: Path):
    _write_corpus(tmp_path)
    result = run_gate(tmp_path)
    assert result["high_school_intelligence"] is False
    assert result["general_llm_parity"] is False
    assert len(result["scaling"]) == 3
    assert result["checks"]["heldout_is_file_disjoint"]
    assert result["checks"]["mixed_domains_present"]
