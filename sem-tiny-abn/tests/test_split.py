from sem_tiny_abn.utils import split_rows


def test_group_split_has_no_group_leakage():
    rows = []
    for group_index in range(12):
        for label in ("OK", "NG"):
            rows.append({"sem": f"s_{group_index}_{label}.png", "design": f"d_{group_index}_{label}.png", "label": label, "group": f"g{group_index}"})
    train, val, info = split_rows(rows, val_ratio=0.25, seed=42)
    assert not ({row["group"] for row in train} & {row["group"] for row in val})
    assert info["mode"] == "group_aware"
    assert {row["label"] for row in train} == {"OK", "NG"}
    assert {row["label"] for row in val} == {"OK", "NG"}


def test_explicit_split_is_respected():
    rows = [
        {"sem": "a", "design": "a", "label": "OK", "split": "train"},
        {"sem": "b", "design": "b", "label": "NG", "split": "train"},
        {"sem": "c", "design": "c", "label": "OK", "split": "val"},
        {"sem": "d", "design": "d", "label": "NG", "split": "val"},
    ]
    train, val, info = split_rows(rows, 0.2, 1)
    assert len(train) == 2 and len(val) == 2
    assert info["mode"] == "explicit_split_column"
