from __future__ import annotations

import json

from . import sparc_hs12_experiment as _experiment


def _add_causal_chain(model, code: str) -> None:
    model.ingest_fact(
        f"現象{code}は中間{code}を引き起こす。", source_id=f"{code}因果資料1"
    )
    model.ingest_fact(
        f"中間{code}は次段{code}を引き起こす。", source_id=f"{code}因果資料2"
    )
    model.ingest_fact(
        f"次段{code}は結果{code}を引き起こす。", source_id=f"{code}因果資料3"
    )


# Keep the exact integrated and 100k-edge experiment; replace only the causal
# sentence surface so the existing generic parser produces stable endpoint IDs.
_experiment._add_causal_chain = _add_causal_chain
configured_model = _experiment.configured_model
run_experiment = _experiment.run_experiment


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
