from __future__ import annotations

from . import sparc_hs18_worker as base
from .semantic_hybrid_causal_judgement import SemanticHybridCausalJudgement


base.GenericCausalJudgement = SemanticHybridCausalJudgement.from_environment
main = base.main


if __name__ == "__main__":
    main()
