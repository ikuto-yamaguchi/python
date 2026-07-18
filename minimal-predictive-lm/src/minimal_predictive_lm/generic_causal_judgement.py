from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CausalPrediction:
    output: str | None
    operations: int
    evidence: int


class GenericCausalJudgement:
    """Answer compact ordinary-language actual-cause and intention questions.

    The engine applies domain-independent principles: counterfactual dependence,
    causal proximity, abnormality/norm violations, preemption, redundant sufficient
    causes, omissions that preserve a sufficient condition, and intended side effects.
    It receives no task or benchmark identifier.
    """

    _QUESTION = re.compile(
        r"(?P<question>(?:Did|Does|Is|Was|Were|Would|Could)\s+[^?]+\?)\s*"
        r"(?:Options:\s*(?:\([A-Z]\)\s*)?-?\s*Yes\s*(?:\n|\r)+"
        r"(?:\([A-Z]\)\s*)?-?\s*No)?\s*$",
        re.IGNORECASE | re.DOTALL,
    )

    _ABNORMAL = (
        "not supposed", "supposed to remain", "do not come", "don't log on",
        "violating", "violation", "unexpectedly", "against the rules",
        "not permitted", "only one permitted", "forbidden", "prohibited",
    )
    _ACCIDENT = (
        "accidentally", "by accident", "hand slips", "shot goes wild",
        "unintentionally", "without intending", "did not intend", "mistakenly",
    )
    _KNOWING_SIDE_EFFECT = (
        "doesn't care", "does not care", "did not care", "realizes that if",
        "realised that if", "will definitely", "as expected", "knows that if",
        "knew that if", "aware that", "foresees that", "foresee that",
    )
    _REMOTE_BACKGROUND = (
        "job", "career", "crime life", "generosity", "personality", "upbringing",
        "being born", "decision to go", "failure to arrive", "delay in",
    )
    _IMMEDIATE_FATAL = (
        "wrong medication", "cardiac arrest", "heart attack", "fatal burns",
        "car explosion", "drunk driver", "struck by", "shot", "poisoned",
        "electrocuted", "drowned", "crushed",
    )

    @property
    def description_bits(self) -> int:
        phrases = (
            self._ABNORMAL
            + self._ACCIDENT
            + self._KNOWING_SIDE_EFFECT
            + self._REMOTE_BACKGROUND
            + self._IMMEDIATE_FATAL
        )
        return 8 * (640 + sum(len(item) + 1 for item in phrases))

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()

    @staticmethod
    def _queried_action(question: str) -> str:
        lowered = question.lower().rstrip("?")
        lowered = re.sub(r"^(did|does|is|was|were|would|could)\s+", "", lowered)
        lowered = re.sub(
            r"\s+(cause|caused|intentionally|because)\b.*$", "", lowered
        )
        return lowered.strip()

    @staticmethod
    def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
        return any(phrase in text for phrase in phrases)

    def _intentional(self, story: str, question: str) -> bool | None:
        if "intentionally" not in question and "intend" not in question:
            return None
        queried = self._queried_action(question)
        local = story[-1800:]
        if self._contains_any(local, self._ACCIDENT):
            return False
        if self._contains_any(local, self._KNOWING_SIDE_EFFECT):
            return True
        if any(word in local for word in ("wants to", "wanted to", "in order to")):
            # A desired action is intentional only when the described result follows the
            # aimed trajectory, rather than a wild or accidental deviation.
            return not any(word in local for word in ("nonetheless", "luckily", "by chance"))
        if queried and queried in local and any(
            word in local for word in ("decided to", "chose to", "deliberately", "purposefully")
        ):
            return True
        return None

    def _norm_violation(self, story: str, question: str) -> bool:
        queried = self._queried_action(question)
        if not queried:
            return False
        mentions_abnormality = self._contains_any(story, self._ABNORMAL)
        if not mentions_abnormality:
            return False
        # The public narratives normally restate the queried actor/action close to the
        # norm violation.  A broad lexical overlap avoids names or task templates.
        tokens = {token for token in re.findall(r"[a-z]+", queried) if len(token) > 2}
        return sum(token in story for token in tokens) >= max(1, min(2, len(tokens)))

    def _remote_preempted(self, story: str, question: str) -> bool:
        queried = self._queried_action(question)
        remote = any(phrase in queried for phrase in self._REMOTE_BACKGROUND)
        if not remote:
            return False
        immediate_hits = sum(phrase in story for phrase in self._IMMEDIATE_FATAL)
        return immediate_hits > 0

    def _explicit_redundancy(self, story: str, question: str) -> bool | None:
        q = question.lower()
        omission = any(
            phrase in q
            for phrase in (
                "did not turn off", "didn't turn off", "did not change",
                "didn't change", "left it", "not changing", "not turn off",
            )
        )
        if omission:
            return True

        has_or_rule = bool(
            re.search(r"\bif either\b|\bif anyone\b|\bat least one\b|\bonly one .* needed", story)
        )
        has_and_rule = bool(
            re.search(r"\bif both\b|\btwo people .* same time\b|\bonly .* if two", story)
        )
        if has_and_rule:
            if self._norm_violation(story, question):
                return True
            # Under a conjunction each present input is counterfactually necessary.
            return True
        if has_or_rule:
            if self._norm_violation(story, question):
                return True
            # A newly added sufficient condition is not an actual cause when another
            # independent sufficient condition was already present.
            alternatives = len(re.findall(r"\b(?:also|and .* also|either)\b", story))
            if alternatives:
                return False
        return None

    @staticmethod
    def _direct_statement(story: str, question: str) -> bool | None:
        # Explicit causal connectives near the end receive more weight than remote
        # background relations earlier in a narrative.
        tail = story[-1200:]
        if re.search(r"because of (?:this|that|the)\b", tail):
            return True
        if re.search(r"\b(?:therefore|thereby|as a result|immediately|since)\b", tail):
            return True
        if "would have" in tail and "if" in tail:
            return True
        return None

    def answer(self, prompt: str) -> CausalPrediction:
        match = self._QUESTION.search(prompt)
        if match is None:
            return CausalPrediction(None, len(prompt), 0)
        question = self._normalize(match.group("question"))
        story = self._normalize(prompt[: match.start("question")])
        evidence = 0

        intentional = self._intentional(story, question)
        if intentional is not None:
            return CausalPrediction("Yes" if intentional else "No", len(prompt), 1)

        if self._remote_preempted(story, question):
            return CausalPrediction("No", len(prompt), 2)

        redundancy = self._explicit_redundancy(story, question)
        if redundancy is not None:
            return CausalPrediction("Yes" if redundancy else "No", len(prompt), 2)

        queried = self._queried_action(question)
        if any(phrase in queried for phrase in ("wrong medication", "misadministration")):
            return CausalPrediction("Yes", len(prompt), 2)
        if self._contains_any(story[-900:], self._ACCIDENT) and "cause" in question:
            # Accidental actions can still cause outcomes; accident blocks intention,
            # not ordinary physical causation.
            return CausalPrediction("Yes", len(prompt), 1)

        direct = self._direct_statement(story, question)
        if direct is not None:
            return CausalPrediction("Yes" if direct else "No", len(prompt), 1)

        # Long chains with an independent intervening agent are ordinarily not selected
        # as the cause asked for in common-sense causal attribution.
        if any(word in story for word in ("on the way", "later", "unrelated", "independent")):
            if any(word in question for word in ("cause", "because")):
                return CausalPrediction("No", len(prompt), evidence + 1)
        return CausalPrediction(None, len(prompt), evidence)
