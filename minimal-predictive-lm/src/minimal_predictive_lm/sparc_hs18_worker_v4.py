from __future__ import annotations

from . import sparc_hs18_worker as base
from .hybrid_causal_judgement import HybridCausalJudgement


base.GenericCausalJudgement = HybridCausalJudgement.from_environment
main = base.main


if __name__ == "__main__":
    main()
