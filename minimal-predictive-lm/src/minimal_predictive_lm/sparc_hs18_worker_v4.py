from __future__ import annotations

from . import sparc_hs18_worker as _worker
from .english_causal_compiler_v4 import EnglishCausalResolverV4

_worker.EnglishCausalResolver = EnglishCausalResolverV4
main = _worker.main


if __name__ == "__main__":
    main()
