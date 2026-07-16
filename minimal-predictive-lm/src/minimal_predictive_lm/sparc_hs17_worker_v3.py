from __future__ import annotations

from . import sparc_hs17_worker_v2 as _worker
from .english_role_compiler_v3 import EnglishRoleReferenceResolverV3

# Preserve the frozen integrated worker order and replace only the shared
# reference compiler implementation.
_worker.EnglishRoleReferenceResolverV2 = EnglishRoleReferenceResolverV3
main = _worker.main


if __name__ == "__main__":
    main()
