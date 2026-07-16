import json

from minimal_predictive_lm.cic_jsts_data import JSTS_OPTIONS, load_jsts_dataset, stable_jsts_split


def test_load_jsts_as_halfstep_candidates(tmp_path) -> None:
    path = tmp_path / "jsts.jsonl"
    path.write_text(
        json.dumps(
            {
                "sentence1": "道路をバスが走っている。",
                "sentence2": "大きな車両が道を進んでいる。",
                "label": 4.4,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    rows = load_jsts_dataset(path)
    assert len(rows) == 1
    assert rows[0].target == 4.4
    assert rows[0].choice.options == JSTS_OPTIONS
    assert rows[0].choice.answer_index == 9
    assert rows[0].choice.stem.startswith("文1：")
    assert "\n文2：" in rows[0].choice.stem


def test_jsts_split_is_deterministic(tmp_path) -> None:
    path = tmp_path / "jsts.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(
                {
                    "sentence1": f"文A{index}",
                    "sentence2": f"文B{index}",
                    "label": (index % 11) / 2,
                },
                ensure_ascii=False,
            )
            for index in range(40)
        ),
        encoding="utf-8",
    )
    rows = load_jsts_dataset(path)
    assert stable_jsts_split(rows) == stable_jsts_split(rows)
