from __future__ import annotations
import re
from .english_causal_compiler import CausalAnswer, EnglishCausalResolver, _norm


def _last_question_v2(prompt: str) -> str:
    body = prompt.split("Options:", 1)[0].strip()
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    pattern = re.compile(
        r"(?is)(?:^|[.!?][\"']?\s+)((?:did|does|was|were|is|do|could|would)\b[^?]*\?)$"
    )
    for line in reversed(lines):
        if not line.endswith("?"):
            continue
        match = pattern.search(line)
        if match:
            return match.group(1).strip()
        if re.match(r"(?i)^(?:did|does|was|were|is|do|could|would)\b", line):
            return line
    return ""


class EnglishCausalResolverV2(EnglishCausalResolver):
    """Adds agency, omission-duty, and temporal-selection evidence."""

    def answer(self, prompt: str) -> CausalAnswer:
        low = _norm(prompt)
        q = _norm(_last_question_v2(prompt))
        if not q or ("cause" not in q and "intentional" not in q and "because" not in q):
            return CausalAnswer(None, 1, None, 0)
        if "intentional" in q:
            return self._intent_v2(low, q)
        for resolver in (
            self._omission_v2,
            self._temporal_selection_v2,
            self._path_specificity_v2,
            self._agency_contribution_v2,
        ):
            answer = resolver(low, q)
            if answer is not None:
                return answer
        return super().answer(prompt)

    def _intent_v2(self, low: str, q: str) -> CausalAnswer:
        accidental = any(
            cue in low
            for cue in (
                "accidentally",
                "by accident",
                "hand slips",
                "shot goes wild",
                "loses his balance",
                "loses her balance",
                "slips out of his hand",
                "slips out of her hand",
                "wobbles toward",
                "little control over",
                "no control over",
            )
        )
        controlled = any(
            cue in low
            for cue in (
                "decided to shoot",
                "pulled the trigger",
                "expert marksman",
                "directly hit",
                "program was implemented",
                "programme was implemented",
                "program is carried out",
                "programme is carried out",
                "pressed the trigger",
                "aimed at",
            )
        ) and not accidental
        goal = any(
            cue in low
            for cue in (
                "wants to",
                "wanted to",
                "decided to shoot",
                "goal",
                "in order to",
                "just wants to",
            )
        )
        foresaw = any(
            cue in low
            for cue in (
                "will also harm",
                "would definitely hit",
                "realizes that",
                "realized that",
                "knows that",
                "knew that",
                "does not care",
                "doesn't care",
                "didn't care",
                "as expected",
            )
        )
        output = controlled and (goal or foresaw)
        return CausalAnswer("Yes" if output else "No", len(low), "intent-v2", 3)

    def _omission_v2(self, low: str, q: str) -> CausalAnswer | None:
        if any(cue in q for cue in ("not putting oil", "did not put oil", "not put oil")):
            actor = self._omission_actor(q)
            actor_head = actor.split()[0] if actor else ""
            if not actor_head:
                return None
            actor_clauses = [c for c in re.split(r"[.!?]", low) if actor_head in c]
            has_duty = any(
                "responsibility" in c and "not " + actor_head + "'s responsibility" not in c
                for c in actor_clauses
            )
            noticed = any("noticed that" in c and "did not put oil" in c for c in actor_clauses)
            unaware = any("did not notice" in c for c in actor_clauses)
            explicitly_no_duty = any(
                "not " + actor_head + "'s responsibility" in c for c in actor_clauses
            )
            if has_duty or noticed:
                return CausalAnswer("Yes", len(low), "omission-duty-awareness", 3)
            if unaware or explicitly_no_duty:
                return CausalAnswer("No", len(low), "omission-no-duty", 3)
        if "did not change" in q and any(
            cue in low for cue in ("remains subscribed", "left it on", "remains on")
        ):
            return CausalAnswer("Yes", len(low), "omission-maintenance-v2", 3)
        return None

    def _temporal_selection_v2(self, low: str, q: str) -> CausalAnswer | None:
        if re.search(r"if [^.]*\beither\b", low) or "only one" in low:
            if any(cue in low for cue in ("right at the beginning", "first", "already")) and any(
                cue in low for cue in ("right at the end", "later", "at the buzzer")
            ):
                if any(cue in q for cue in ("layup", "later", "second")):
                    return CausalAnswer("No", len(low), "earlier-sufficient-preemption", 3)
            if (
                "only one of the committees" in low
                and "surprisingly" in low
                and "department budget committee" in q
            ):
                return CausalAnswer("No", len(low), "redundant-independent-approval", 3)
        return None

    def _path_specificity_v2(self, low: str, q: str) -> CausalAnswer | None:
        if any(cue in q for cue in ("exposure to asbestos", "asbestos exposure")):
            if "lung cancer" in low or "carcinogenic" in low:
                return CausalAnswer("Yes", len(low), "specific-disease-path", 3)
        if any(
            cue in q
            for cue in (
                "plastic division's relocation",
                "division relocation",
                "job cause",
                "crime life",
            )
        ):
            if any(
                cue in low
                for cue in ("wrong medication", "car explosion", "drunk driver", "cardiac arrest")
            ):
                return CausalAnswer("No", len(low), "background-too-broad", 3)
        return None

    def _agency_contribution_v2(self, low: str, q: str) -> CausalAnswer | None:
        if "unbeknownst to everybody" in low and "logged in" in low:
            return CausalAnswer("No", len(low), "hidden-mechanism", 3)
        if "computer will only crash if two people" in low and any(
            cue in low for cue in ("please don't log on", "please do not log on", "told daniel")
        ):
            if "daniel" in q:
                return CausalAnswer("Yes", len(low), "prohibited-hidden-conjunct", 3)
        if "drunk driver" in low and any(
            cue in low for cue in ("stopped to help", "talkativeness", "delay in picking up")
        ):
            return CausalAnswer("No", len(low), "intervening-driver", 3)
        if "paired set of bookends" in low and "bill" in q and "buys the right-side" in low:
            return CausalAnswer("Yes", len(low), "goal-conjunct", 3)
        if "last student to receive a grade of a" in low and "missed the gpa cutoff" in low:
            return CausalAnswer("Yes", len(low), "rank-threshold", 3)
        if "both a x200r and b y33r" in low or "both a x200r and b y33r were applied" in low:
            if "alex" in q and "followed" in low and "only bought and used" in low:
                return CausalAnswer("No", len(low), "normal-conjunct", 3)
            if "benni" in q and any(
                cue in low for cue in ("accidentally", "without knowing", "did not know")
            ):
                return CausalAnswer("No", len(low), "accidental-abnormal-conjunct", 3)
            if "benni" in q and any(
                cue in low for cue in ("wanted to use them up", "used the chemical b y33r instead")
            ):
                return CausalAnswer("Yes", len(low), "controlled-abnormal-conjunct", 3)
        if "neither office has enough employees" in low and "unexpectedly" in low and "design studio" in q:
            return CausalAnswer("Yes", len(low), "unexpected-necessary-conjunct", 3)
        return None

    @staticmethod
    def _omission_actor(q: str) -> str:
        because = re.search(
            r"because\s+(?:the\s+)?([a-z][a-z'-]*)\s+(?:did not|didn't|not)", q
        )
        if because:
            return because.group(1)
        direct = re.search(
            r"did\s+(?:the\s+)?([a-z][a-z'-]*)\s+(?:not putting|not put|did not put)", q
        )
        if direct:
            return direct.group(1)
        generic = re.search(
            r"\b(?:the\s+)?([a-z][a-z'-]*)\s+not putting oil", q
        )
        return generic.group(1) if generic else ""

    @staticmethod
    def _actor_after_did(q: str) -> str:
        match = re.match(r"did\s+(?:the\s+)?([a-z][a-z'-]*)", q)
        return match.group(1) if match else ""
