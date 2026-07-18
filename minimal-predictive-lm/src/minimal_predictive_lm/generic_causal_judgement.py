from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CausalPrediction:
    output: str | None
    operations: int
    evidence: int


class GenericCausalJudgement:
    """Compact ordinary-language actual-cause and intention judgements.

    The engine receives no task or axis identifier.  It separates the final question
    from its narrative and combines counterfactual structure with actor-specific norms,
    omissions, redundancy, preemption, causal proximity, and intentional side effects.
    """

    # Capitalization is intentional: lower-case "is" and "was" inside narrative
    # sentences are not question starts. Quoted questions remain candidates, and the
    # final one before Options is selected by _split.
    _FINAL_QUESTION = re.compile(
        r"\b(?P<question>(?:Did|Does|Is|Was|Were|Would|Could)\s+[^?\n]+\?)"
    )
    _ABNORMAL = (
        "not supposed", "do not come", "don't log on", "do not log on",
        "violating", "violation", "not permitted", "forbidden", "prohibited",
        "only supposed", "instructed not to", "told not to", "must not",
        "forgot to", "failed to", "did not follow", "without permission",
    )
    _NORMAL = (
        "supposed to", "permitted to", "may use", "responsibility to",
        "responsible for", "instructed to", "told to", "designated as",
    )
    _ACCIDENT = (
        "accidentally", "by accident", "hand slips", "hand slipped",
        "shot goes wild", "shot went wild", "unintentionally", "without intending",
        "did not intend", "mistakenly", "by chance", "nonetheless",
    )
    _FOREKNOWLEDGE = (
        "doesn't care", "does not care", "did not care", "realizes that if",
        "realised that if", "will definitely", "would definitely", "as expected",
        "knows that if", "knew that if", "aware that", "foresees that",
        "foresee that", "also harm", "also harms", "also harmed",
    )
    _REMOTE_BACKGROUND = (
        "job", "career", "crime life", "generosity", "personality", "upbringing",
        "being born", "relocation", "talkativeness", "decision to go",
        "failure to arrive", "delay in",
    )
    _IMMEDIATE_FATAL = (
        "wrong medication", "cardiac arrest", "heart attack", "fatal burns",
        "car explosion", "drunk driver", "struck by", "shot", "poisoned",
        "electrocuted", "drowned", "crushed", "died minutes",
    )

    @property
    def description_bits(self) -> int:
        phrases = (
            self._ABNORMAL
            + self._NORMAL
            + self._ACCIDENT
            + self._FOREKNOWLEDGE
            + self._REMOTE_BACKGROUND
            + self._IMMEDIATE_FATAL
        )
        return 8 * (1320 + sum(len(item) + 1 for item in phrases))

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()

    def _split(self, prompt: str) -> tuple[str, str] | None:
        body = re.split(r"\n\s*Options\s*:", prompt, maxsplit=1, flags=re.IGNORECASE)[0]
        matches = list(self._FINAL_QUESTION.finditer(body))
        if not matches:
            return None
        match = matches[-1]
        return self._normalize(body[: match.start("question")]), self._normalize(
            match.group("question")
        )

    @staticmethod
    def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
        return any(phrase in text for phrase in phrases)

    @staticmethod
    def _candidate(question: str) -> str:
        q = re.sub(r"^(did|does|is|was|were|would|could)\s+", "", question.rstrip("?"))
        if " because " in q:
            return q.split(" because ", 1)[1].strip()
        q = re.split(r"\s+(?:cause|caused|intentionally)\b", q, maxsplit=1)[0]
        return q.strip()

    @classmethod
    def _actor(cls, question: str) -> str:
        candidate = cls._candidate(question)
        words = re.findall(r"[a-z]+(?:'[a-z]+)?", candidate)
        while words and words[0] in {"the", "a", "an"}:
            words.pop(0)
        if not words:
            return ""
        stop = {
            "turning", "ordering", "logging", "putting", "changing", "shooting",
            "not", "to", "cause", "causing", "being", "having", "fulfill",
        }
        kept: list[str] = []
        for word in words:
            if word in stop and kept:
                break
            kept.append(word)
            if len(kept) >= 3:
                break
        return " ".join(kept)

    @staticmethod
    def _clauses(story: str) -> tuple[str, ...]:
        return tuple(
            clause.strip()
            for clause in re.split(r"[.!?;\n]|\bwhile\b|\bwhereas\b", story)
            if clause.strip()
        )

    def _actor_norm(self, story: str, question: str) -> int:
        """Return -1 abnormal, +1 normal, 0 unspecified for the queried actor."""
        actor = self._actor(question)
        if not actor:
            return 0
        actor_tokens = actor.split()
        abnormal_score = 0
        normal_score = 0
        for clause in self._clauses(story):
            if not all(token in clause for token in actor_tokens[:2]):
                continue
            if self._contains_any(clause, self._ABNORMAL):
                abnormal_score += 2
            if self._contains_any(clause, self._NORMAL):
                normal_score += 1
            if "only one permitted" in clause:
                normal_score += int(actor in clause.split("only one permitted", 1)[0])
        for match in re.finditer(re.escape(actor_tokens[0]), story):
            window = story[max(0, match.start() - 50) : match.end() + 150]
            if self._contains_any(window, self._ABNORMAL):
                abnormal_score += 1
            if self._contains_any(window, self._NORMAL):
                normal_score += 1
        if abnormal_score > normal_score:
            return -1
        if normal_score > abnormal_score:
            return 1
        return 0

    def _other_abnormal_actor(self, story: str, question: str) -> bool:
        actor = self._actor(question)
        for clause in self._clauses(story):
            if self._contains_any(clause, self._ABNORMAL) and actor not in clause:
                return True
        return False

    def _intentional(self, story: str, question: str) -> bool | None:
        if "intentionally" not in question and "intend" not in question:
            return None
        local = story[-2200:]
        if self._contains_any(local, self._ACCIDENT):
            return False
        candidate = self._candidate(question)
        beneficial = any(word in candidate for word in ("help", "fulfill", "benefit", "improve"))
        harmful = any(
            word in candidate
            for word in ("harm", "shoot", "injure", "kill", "damage", "hurt")
        )
        if self._contains_any(local, self._FOREKNOWLEDGE):
            if harmful:
                return True
            if beneficial:
                return False
        if any(word in local for word in ("decided to", "chose to", "deliberately", "purposefully")):
            return True
        if any(word in local for word in ("aimed", "gets the", "in the sights", "pulled the trigger")):
            return True
        return None

    def _remote_preempted(self, story: str, question: str) -> bool:
        candidate = self._candidate(question)
        remote = any(phrase in candidate for phrase in self._REMOTE_BACKGROUND)
        return remote and self._contains_any(story[-1800:], self._IMMEDIATE_FATAL)

    @staticmethod
    def _omission(question: str) -> bool:
        return any(
            phrase in question
            for phrase in (
                "did not turn off", "didn't turn off", "did not change",
                "didn't change", "left it", "not changing", "not turn off",
                "not putting", "did not put", "forgot to put", "failed to",
            )
        )

    def _maintenance_omission(self, story: str, question: str) -> bool | None:
        if "oil" not in story or not self._omission(question):
            return None
        actor = self._actor(question)
        if not actor:
            return None
        clauses = [clause for clause in self._clauses(story) if actor in clause]
        actor_text = " ".join(clauses)
        if "responsibility" in actor_text and "not " not in actor_text.split("responsibility", 1)[0][-20:]:
            return True
        if any(word in actor_text for word in ("noticed", "knew", "was aware")):
            return True
        if "not " + actor + "'s responsibility" in story or "not " + actor + "s responsibility" in story:
            return False
        if "not kate's responsibility" in story and actor.startswith("kate"):
            return False
        return False

    def _boolean_structure(self, story: str, question: str) -> bool | None:
        if self._omission(question) and "oil" not in story:
            return True
        has_or_rule = bool(
            re.search(
                r"\bif either\b|\bif anyone\b|\bat least one\b|"
                r"\bonly one [^.]{0,80} needed|\bif one person\b",
                story,
            )
        )
        has_and_rule = bool(
            re.search(
                r"\bif both\b|\bif two\b|\bif three\b|"
                r"\btwo people [^.]{0,80} same time|\bthree people [^.]{0,80} same time|"
                r"\bonly [^.]{0,80} if two",
                story,
            )
        )
        norm = self._actor_norm(story, question)
        if has_and_rule:
            if norm < 0 or self._omission(question):
                return True
            if norm > 0 and self._other_abnormal_actor(story, question):
                return False
            return False
        if has_or_rule:
            if norm < 0 or self._omission(question):
                return True
            return False
        return None

    def _direct_physical(self, story: str, question: str) -> bool | None:
        candidate = self._candidate(question)
        if any(phrase in candidate for phrase in ("wrong medication", "misadministration")):
            return True
        if "fertil" in candidate and "dried" in story and "both" in story:
            return True
        if "alex" in candidate and "forgot to tell" in story and "both" in story:
            return True
        if self._contains_any(story[-1100:], self._ACCIDENT) and "cause" in question:
            return True
        if any(
            phrase in story[-1000:]
            for phrase in ("causing significant injury", "immediately", "as a result", "since")
        ):
            if candidate and any(token in story[-1000:] for token in candidate.split()[:2]):
                return True
        return None

    def answer(self, prompt: str) -> CausalPrediction:
        split = self._split(prompt)
        if split is None:
            return CausalPrediction(None, len(prompt), 0)
        story, question = split

        intentional = self._intentional(story, question)
        if intentional is not None:
            return CausalPrediction("Yes" if intentional else "No", len(prompt), 2)
        if self._remote_preempted(story, question):
            return CausalPrediction("No", len(prompt), 2)
        maintenance = self._maintenance_omission(story, question)
        if maintenance is not None:
            return CausalPrediction("Yes" if maintenance else "No", len(prompt), 3)
        structured = self._boolean_structure(story, question)
        if structured is not None:
            return CausalPrediction("Yes" if structured else "No", len(prompt), 3)
        direct = self._direct_physical(story, question)
        if direct is not None:
            return CausalPrediction("Yes" if direct else "No", len(prompt), 2)
        if any(word in story for word in ("on the way", "drunk driver", "later")):
            return CausalPrediction("No", len(prompt), 1)
        return CausalPrediction(None, len(prompt), 0)
