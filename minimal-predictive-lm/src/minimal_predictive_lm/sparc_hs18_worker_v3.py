from __future__ import annotations

from . import sparc_hs18_worker as _worker
from .english_causal_compiler_v3_runtime import EnglishCausalResolverV3Runtime

_worker.EnglishCausalResolver = EnglishCausalResolverV3Runtime
main = _worker.main


if __name__ == "__main__":
    main()
