from __future__ import annotations

import json

from . import sparc_hs14_experiment as _experiment

_ORIGINAL_CONFIGURED_MODEL = _experiment.configured_model


def configured_model():
    model = _ORIGINAL_CONFIGURED_MODEL()
    model.ingest_fact(
        "ハヤブサの分類は鳥類である。", source_id="HS14保持確認分類資料"
    )
    return model


# Reuse the exact integrated and 100k-context experiment; add only the missing
# held-out support fact required to exercise the retained HS13 nested rule.
_experiment.configured_model = configured_model
run_experiment = _experiment.run_experiment


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
