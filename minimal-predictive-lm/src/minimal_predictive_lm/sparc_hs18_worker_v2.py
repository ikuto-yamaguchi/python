from __future__ import annotations

from . import sparc_hs18_worker as _worker
from .english_causal_compiler_v2 import EnglishCausalResolverV2

_worker.EnglishCausalResolver = EnglishCausalResolverV2
main = _worker.main


if __name__ == "__main__":
    main()
