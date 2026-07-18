from __future__ import annotations

from . import sparc_hs18_worker as base
from .generic_causal_judgement_v2 import GenericCausalJudgementV2


base.GenericCausalJudgement = GenericCausalJudgementV2
main = base.main


if __name__ == "__main__":
    main()
