from __future__ import annotations

import json

from . import sparc_hs8_experiment as _legacy
from .sparc_episodic_focus import SPARCHS8Model, SparseEpisodicRevisionMemory


def configured_model() -> SPARCHS8Model:
    # Reuse the exact HS8 curriculum/document fixture, then restore it through the
    # focus-aware class so the only changed variable is the discourse circuit.
    legacy_model = _legacy.configured_model()
    return SPARCHS8Model.from_bytes(legacy_model.to_bytes())


# The existing experiment already contains the 100k-episode scale test and all
# resource gates. Rebind its model globals so those same tests exercise the new
# focus circuit rather than creating a second, easier benchmark.
_legacy.SPARCHS8Model = SPARCHS8Model
_legacy.SparseEpisodicRevisionMemory = SparseEpisodicRevisionMemory
_legacy.configured_model = configured_model
run_experiment = _legacy.run_experiment


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
