from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location(
    "exp", Path(__file__).with_name("variable_preserving_intervention_quotient.py")
)
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)


def test_identity_rename_and_composition():
    model = exp.Quot()
    model.fit(exp.mk(1, 128))
    assert model.pred("未知甲は棚Aにある。", "未知甲を棚Bへ移す。")[0] == "未知甲は棚Bにある。"
    current = model.pred("未知甲は棚Aにある。", "未知甲を棚Bへ移す。")[0]
    assert model.pred(current, "未知甲を棚Cへ移す。")[0] == "未知甲は棚Cにある。"


def test_unseen_paraphrase_is_not_claimed():
    model = exp.Quot()
    model.fit(exp.mk(1, 128))
    assert model.pred("未知甲は棚Aにある。", "棚Bへ未知甲を運んで。")[0] is None
