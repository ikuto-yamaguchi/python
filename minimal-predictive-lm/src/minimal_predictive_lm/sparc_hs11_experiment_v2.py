from __future__ import annotations

import json

from . import sparc_hs11_experiment as _experiment
from .sparc_cross_domain_plans_v2 import SPARCHS11ModelV2

# Preserve the exact integrated and 100k-evidence experiment. Replace only the
# subject-routing mechanism that failed at scale.
_experiment.SPARCHS11Model = SPARCHS11ModelV2
configured_model = _experiment.configured_model
run_experiment = _experiment.run_experiment


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
