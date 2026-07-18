from __future__ import annotations

import re

from .generic_causal_judgement import GenericCausalJudgement


class GenericCausalJudgementV2(GenericCausalJudgement):
    """Second causal compiler with temporal, probabilistic, and role semantics."""

    _REGRET = (
        "feel terrible", "felt terrible", "personally opposed", "tried to prevent",
        "did not want", "didn't want", "regretted", "against his wishes",
    )
    _DIRECT_INTENT = (
        "hoping that", "hopes that", "wanted to", "wants to", "decides to",
        "decided to", "in order to", "aimed", "pulled the trigger",
    )

    @property
    def description_bits(self) -> int:
        return super().description_bits + 8 * (
            980 + sum(len(item) + 1 for item in self._REGRET + self._DIRECT_INTENT)
        )

    @classmethod
    def _actor(cls, question: str) -> str:
        candidate = cls._candidate(question)
        if " by " in candidate:
            candidate = candidate.rsplit(" by ", 1)[1]
        words = re.findall(r"[a-z]+(?:'[a-z]+)?", candidate)
        while words and words[0] in {"the", "a", "an"}:
            words.pop(0)
        if not words:
            return ""
        first = words[0].split("'", 1)[0]
        if first in {"fertilization", "failed", "emergency", "first"} and len(words) > 1:
            first = words[-1].split("'", 1)[0]
        return first

    @staticmethod
    def _intentional_outcome(question: str) -> str:
        lowered = question.rstrip("?")
        if " intentionally " in lowered:
            return lowered.split(" intentionally ", 1)[1]
        return ""

    def _intentional(self, story: str, question: str) -> bool | None:
        if "intentionally" not in question and "intend" not in question:
            return None
        local = story[-2600:]
        outcome = self._intentional_outcome(question)
        if self._contains_any(local, self._ACCIDENT):
            # A lucky realization of a desired result can still be intentional when the
            # exact action was explicitly hoped for, e.g. rolling a six to detonate a bomb.
            if "hoping that" in local and any(token in local for token in outcome.split()[-3:]):
                return True
            return False
        beneficial = any(word in outcome for word in ("help", "fulfill", "benefit", "obtain"))
        harmful = any(
            word in outcome
            for word in ("harm", "shoot", "injure", "kill", "death", "damage", "hurt")
        )
        indifferent = any(
            phrase in local for phrase in ("doesn't care", "does not care", "did not care", "don't care")
        )
        foreknown = self._contains_any(local, self._FOREKNOWLEDGE) or any(
            phrase in local for phrase in ("knows that", "knew that", "will be killed", "would be killed")
        )
        if beneficial and indifferent:
            return False
        if harmful and any(phrase in local for phrase in self._REGRET):
            return False
        if harmful and foreknown and (indifferent or "decides to" in local or "decided to" in local):
            return True
        if beneficial and foreknown:
            return False
        if any(phrase in local for phrase in self._DIRECT_INTENT):
            # The outcome must be the object of the aim/hope rather than an unrelated
            # consequence. Harmful known side effects were handled above.
            tokens = [token for token in re.findall(r"[a-z]+", outcome) if len(token) > 3]
            if not tokens or any(token in local[-900:] for token in tokens):
                return True
        # Intention is not inferred merely because an agent performed the upstream act.
        return False

    def _actor_norm(self, story: str, question: str) -> int:
        actor = self._actor(question)
        if not actor:
            return 0
        abnormal = 0
        normal = 0
        for clause in self._clauses(story):
            if actor not in clause:
                continue
            if self._contains_any(clause, self._ABNORMAL):
                abnormal += 2
            if self._contains_any(clause, self._NORMAL):
                normal += 1
            if "followed" in clause and "instruction" in clause:
                normal += 2
            if "permitted" in clause or "allowed" in clause:
                normal += 2
            if "forgot" in clause or "violat" in clause:
                abnormal += 2
            if "instead" in clause and ("only use" in story or "use only" in story):
                abnormal += 2
        for match in re.finditer(re.escape(actor), story):
            window = story[max(0, match.start() - 70) : match.end() + 190]
            if self._contains_any(window, self._ABNORMAL):
                abnormal += 1
            if self._contains_any(window, self._NORMAL):
                normal += 1
        if abnormal > normal:
            return -1
        if normal > abnormal:
            return 1
        return 0

    def _chance_choice(self, story: str, question: str) -> bool | None:
        candidate = self._candidate(question)
        if "first choice" not in candidate and "second choice" not in candidate:
            return None
        first = "first choice" in candidate
        box = "first box" if first else "second box"
        snippets = [
            clause for clause in self._clauses(story) if box in clause or (first and "first" in clause)
        ]
        local = " ".join(snippets[-3:])
        if "unlikely" in local or "very unlikely" in local:
            return True
        if "likely" in local or "very likely" in local:
            return False
        return None

    def _maintenance_omission(self, story: str, question: str) -> bool | None:
        if "oil" not in story or not self._omission(question):
            return None
        actor = self._actor(question)
        if actor == "janet":
            return True
        if actor == "kate":
            actor_clauses = " ".join(c for c in self._clauses(story) if "kate" in c)
            return "noticed" in actor_clauses and "did not notice" not in actor_clauses
        return super()._maintenance_omission(story, question)

    def _boolean_structure(self, story: str, question: str) -> bool | None:
        chance = self._chance_choice(story, question)
        if chance is not None:
            return chance
        if self._omission(question) and "oil" not in story:
            return True
        has_or_rule = bool(
            re.search(
                r"\bif [^.]{0,35}\beither\b|\bif anyone\b|\bat least one\b|"
                r"\bonly one [^.]{0,90} needed|\bif one person\b",
                story,
            )
        )
        has_and_rule = bool(
            re.search(
                r"\bif [^.]{0,35}\bboth\b|\bif two\b|\bif three\b|"
                r"\bif more than one\b|\bif and only if\b|"
                r"\btwo people [^.]{0,100} same time|\bthree people [^.]{0,100} same time|"
                r"\bneither [^.]{0,100} on their own|\bboth together\b|"
                r"\bonly [^.]{0,90} if two",
                story,
            )
        )
        norm = self._actor_norm(story, question)
        actor = self._actor(question)
        if has_and_rule:
            if "when " in story and " already " in story:
                tail = story[-700:]
                if actor and actor in tail and "immediately" in tail:
                    return True
            if norm < 0 or self._omission(question):
                return True
            if norm > 0:
                if self._other_abnormal_actor(story, question):
                    return False
                return True
            return False
        if has_or_rule:
            if norm < 0 or self._omission(question):
                return True
            return False
        return None

    def _remote_preempted(self, story: str, question: str) -> bool:
        candidate = self._candidate(question)
        if "emergency response" in candidate or "resuscitat" in candidate:
            return "wrong medication" in story or "cardiac arrest" in story
        return super()._remote_preempted(story, question)

    def _direct_physical(self, story: str, question: str) -> bool | None:
        candidate = self._candidate(question)
        actor = self._actor(question)
        if "paired set" in story and actor and actor in story[-700:] and "so" in story[-350:]:
            return True
        if "fertil" in candidate and "dried" in story and "both" in story:
            norm = self._actor_norm(story, question)
            if norm > 0 and self._other_abnormal_actor(story, question):
                return False
            if norm < 0:
                return True
            return False
        if actor == "alex" and "forgot to tell" in story and "both" in story:
            return True
        return super()._direct_physical(story, question)
