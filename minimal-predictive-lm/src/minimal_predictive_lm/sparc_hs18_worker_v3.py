from __future__ import annotations

from . import sparc_hs18_worker as base
from .generic_causal_judgement_v3 import GenericCausalJudgementV3


base.GenericCausalJudgement = GenericCausalJudgementV3
main = base.main


if __name__ == "__main__":
    main()
