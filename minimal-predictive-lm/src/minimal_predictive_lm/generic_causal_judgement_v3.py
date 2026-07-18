from __future__ import annotations

from .generic_causal_judgement_v2 import GenericCausalJudgementV2


class GenericCausalJudgementV3(GenericCausalJudgementV2):
    """Compare the queried actor with abnormal competing contributors."""

    @property
    def description_bits(self) -> int:
        return super().description_bits + 8 * 260

    def _other_abnormal_actor(self, story: str, question: str) -> bool:
        if super()._other_abnormal_actor(story, question):
            return True
        actor = self._actor(question)
        restricted_choice = "only use" in story or "use only" in story
        for clause in self._clauses(story):
            if actor and actor in clause:
                continue
            if restricted_choice and "instead" in clause:
                return True
            if "violat" in clause or "not supposed" in clause or "not permitted" in clause:
                return True
        return False
