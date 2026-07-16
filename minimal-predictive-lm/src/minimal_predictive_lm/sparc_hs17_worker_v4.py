from __future__ import annotations

from . import sparc_hs17_worker_v2 as _worker
from .english_role_compiler_v4 import EnglishRoleReferenceResolverV4

_worker.EnglishRoleReferenceResolverV2 = EnglishRoleReferenceResolverV4
main = _worker.main


if __name__ == "__main__":
    main()
