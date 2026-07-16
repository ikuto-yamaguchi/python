from __future__ import annotations

from . import sparc_hs18_worker as _worker
from .english_causal_compiler_v3 import EnglishCausalResolverV3

_worker.EnglishCausalResolver = EnglishCausalResolverV3
main = _worker.main


if __name__ == "__main__":
    main()
