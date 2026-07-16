from __future__ import annotations

import json

from . import sparc_hs10_experiment as _experiment
from .sparc_role_induction_v3 import SPARCHS10ModelV3

# Reuse the exact failed run's capability and 20k-document scale gates while
# replacing only the competition policy. This prevents an easier second test.
_experiment.SPARCHS10ModelV2 = SPARCHS10ModelV3
configured_model = _experiment.configured_model
run_experiment = _experiment.run_experiment


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
