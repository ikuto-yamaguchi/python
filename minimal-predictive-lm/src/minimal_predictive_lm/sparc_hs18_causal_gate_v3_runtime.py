from __future__ import annotations

from . import sparc_hs18_causal_gate_v3 as _gate
from .english_causal_compiler_v3_runtime import EnglishCausalResolverV3Runtime

_gate.EnglishCausalResolverV3 = EnglishCausalResolverV3Runtime
main = _gate.main


if __name__ == "__main__":
    main()
