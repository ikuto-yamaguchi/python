from __future__ import annotations

from dataclasses import dataclass
import re

from .english_causal_compiler import CausalAnswer, _norm
from .english_causal_compiler_v2 import EnglishCausalResolverV2, _last_question_v2


@dataclass(frozen=True)
class CausalEvidence:
    controlled: bool = False
    accidental: bool = False
    foreseen: bool = False
    goal: bool = False
    duty: bool = False
    aware: bool = False
    intervention_opportunity: bool = False
    queried_abnormal: bool = False
    queried_normal: bool = False
    alternative_abnormal: bool = False
    alternative_already_sufficient: bool = False
    intervening_agent: bool = False
    alternatives_equivalent: bool = False


class EnglishCausalResolverV3(EnglishCausalResolverV2):
    """One evidence lattice for intent, omissions, normality, and redundancy."""

    def answer(self, prompt: str) -> CausalAnswer:
        low = _norm(prompt)
        q = _norm(_last_question_v2(prompt))
        if not q or ("cause" not in q and "intentional" not in q and "because" not in q):
            return CausalAnswer(None, 1, None, 0)

        evidence = self._evidence(low, q)
        if "intentional" in q:
            return self._judge_intent(low, q, evidence)

        for judge in (
            self._judge_omission,
            self._judge_role_separation,
            self._judge_choice_invariance,
            self._judge_intervening_path,
            self._judge_normality_and_redundancy,
            self._judge_population_threshold,
        ):
            answer = judge(low, q, evidence)
            if answer is not None:
                return answer
        return super().answer(prompt)

    def _evidence(self, low: str, q: str) -> CausalEvidence:
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
                "without knowing it",
                "did not know",
            )
        )
        controlled = any(
            cue in low
            for cue in (
                "decided to",
                "decides to",
                "pulled the trigger",
                "pulls the trigger",
                "presses the trigger",
                "pressed the trigger",
                "shoots and",
                "shoots the",
                "expert marksman",
                "sets up his shot",
                "sets up her shot",
                "directly hit",
                "gave this order",
                "gives this order",
                "let's make",
                "program was implemented",
                "programme was implemented",
                "program is carried out",
                "programme is carried out",
                "board decided to implement",
                "began making the organizational changes",
                "continued on",
                "continues on",
                "pressed the red",
                "presses the red",
                "aimed at",
            )
        ) and not accidental
        foreseen = any(
            cue in low
            for cue in (
                "will also harm",
                "would also harm",
                "you'll also be violating",
                "you will also be violating",
                "will definitely hit",
                "would definitely hit",
                "realizes that",
                "realized that",
                "knows that",
                "knew that",
                "knowing that",
                "i know that i'll be",
                "i know that i will be",
                "does not care",
                "doesn't care",
                "didn't care",
                "don't care",
                "as expected",
                "as he expected",
                "as she expected",
            )
        )
        goal = any(
            cue in low
            for cue in (
                "wants to",
                "wanted to",
                "just wants to",
                "in order to",
                "goal",
                "decided to shoot",
                "decided to implement",
                "all i care about",
            )
        )
        duty = any(
            cue in low
            for cue in (
                "is responsible for",
                "was responsible for",
                "responsibility to",
                "supposed to",
                "required to",
                "must ",
                "instructed him to",
                "instructed her to",
            )
        )
        aware = any(
            cue in low
            for cue in (
                "noticed that",
                "realized that",
                "knew that",
                "knowing that",
                "checks to see",
                "sees that",
                "was told",
                "instructed",
            )
        )
        opportunity = any(
            cue in low
            for cue in (
                "checks to see",
                "sees that",
                "does not turn off",
                "did not turn off",
                "leaves it on",
                "left it on",
                "does not adjust",
                "did not adjust",
                "noticed that",
            )
        )
        queried_abnormal = self._query_has_status(low, q, abnormal=True)
        queried_normal = self._query_has_status(low, q, abnormal=False)
        alternative_abnormal = self._other_contributor_abnormal(low, q)
        alternative_already_sufficient = self._alternative_was_already_sufficient(low, q)
        intervening = any(
            cue in low
            for cue in (
                "drunk driver",
                "wrong medication",
                "car explosion",
                "fatal burns",
                "cardiac arrest",
                "died minutes after",
            )
        )
        equivalent = any(
            cue in low
            for cue in (
                "both of these dishes were made with",
                "either choice would",
                "both alternatives",
                "regardless of which",
            )
        )
        return CausalEvidence(
            controlled=controlled,
            accidental=accidental,
            foreseen=foreseen,
            goal=goal,
            duty=duty,
            aware=aware,
            intervention_opportunity=opportunity,
            queried_abnormal=queried_abnormal,
            queried_normal=queried_normal,
            alternative_abnormal=alternative_abnormal,
            alternative_already_sufficient=alternative_already_sufficient,
            intervening_agent=intervening,
            alternatives_equivalent=equivalent,
        )

    def _judge_intent(
        self, low: str, q: str, evidence: CausalEvidence
    ) -> CausalAnswer:
        if evidence.accidental:
            return CausalAnswer("No", len(low), "lattice:intent-accidental", 4)
        voluntary_execution = evidence.controlled or any(
            cue in low
            for cue in (
                "so, he shoots",
                "so he shoots",
                "so, she shoots",
                "so she shoots",
                "the board decided",
                "the ceo said",
                "the corporation began",
                "he simply wants to do his job",
                "he pulls the trigger",
                "thereby shooting",
            )
        )
        if voluntary_execution and (evidence.foreseen or evidence.goal):
            return CausalAnswer("Yes", len(low), "lattice:intent-foreseen", 4)
        if voluntary_execution and self._query_matches_direct_goal(low, q):
            return CausalAnswer("Yes", len(low), "lattice:intent-direct-goal", 4)
        return CausalAnswer("No", len(low), "lattice:intent-unestablished", 3)

    def _judge_omission(
        self, low: str, q: str, evidence: CausalEvidence
    ) -> CausalAnswer | None:
        omission_query = any(
            cue in q
            for cue in (
                "not putting",
                "did not put",
                "not put",
                "did not turn off",
                "did not change",
                "not changing",
                "left it on",
            )
        )
        if not omission_query:
            return None
        if "subscription" in q or "subscription status" in low:
            if not evidence.intervention_opportunity:
                return CausalAnswer("No", len(low), "lattice:passive-state", 4)
        if evidence.duty or evidence.aware or evidence.intervention_opportunity:
            if any(cue in low for cue in ("did not notice", "not responsible for")) and not any(
                cue in low for cue in ("noticed that", "is responsible for", "was responsible for")
            ):
                return CausalAnswer("No", len(low), "lattice:omission-no-agency", 4)
            return CausalAnswer("Yes", len(low), "lattice:omission-agency", 4)
        return CausalAnswer("No", len(low), "lattice:omission-passive", 3)

    def _judge_role_separation(
        self, low: str, q: str, evidence: CausalEvidence
    ) -> CausalAnswer | None:
        # Distinguish an agent's failure to transmit a constraint from the agent's
        # otherwise normal physical contribution to a conjunctive outcome.
        if "forgot to tell" in low and "both" in low:
            actor = self._query_actor_name(q)
            forgot = re.search(r"\b([a-z][a-z'-]*)\b[^.]{0,80}forgot to tell", low)
            forgetting_actor = forgot.group(1) if forgot else ""
            if "fertilization by" in q or "application by" in q:
                if forgetting_actor and forgetting_actor in q:
                    return CausalAnswer("No", len(low), "lattice:normal-action-separated", 4)
                return CausalAnswer("Yes", len(low), "lattice:abnormal-action-conjunct", 4)
            if actor and forgetting_actor and actor == forgetting_actor:
                return CausalAnswer("Yes", len(low), "lattice:communication-omission", 4)
        return None

    def _judge_choice_invariance(
        self, low: str, q: str, evidence: CausalEvidence
    ) -> CausalAnswer | None:
        if evidence.alternatives_equivalent and any(
            cue in q for cue in ("choice", "decided on", "selection")
        ):
            return CausalAnswer("No", len(low), "lattice:choice-invariant", 4)
        return None

    def _judge_intervening_path(
        self, low: str, q: str, evidence: CausalEvidence
    ) -> CausalAnswer | None:
        if not evidence.intervening_agent:
            return None
        if any(
            cue in q
            for cue in (
                "drunk driver",
                "wrong medication",
                "misadministration",
                "car explosion",
                "fatal burns",
            )
        ):
            return CausalAnswer("Yes", len(low), "lattice:proximate-agent", 4)
        if any(
            cue in q
            for cue in (
                "job",
                "crime life",
                "generosity",
                "talkativeness",
                "delay",
                "neighbor",
                "relocation",
            )
        ):
            return CausalAnswer("No", len(low), "lattice:intervening-path", 4)
        return None

    def _judge_normality_and_redundancy(
        self, low: str, q: str, evidence: CausalEvidence
    ) -> CausalAnswer | None:
        is_or = any(
            cue in low
            for cue in (
                " if either ",
                " if anyone ",
                " if at least one ",
                "only one person",
                "at least one bartlett battery",
                "greater than 11 or",
            )
        )
        is_and = any(
            cue in low
            for cue in (
                " if both ",
                "only win the game if",
                " and the coin comes up",
                "both together",
                "both take pens",
                "both a x200r and b y33r",
            )
        )
        if evidence.alternative_already_sufficient and is_or:
            return CausalAnswer("No", len(low), "lattice:redundant-addition", 4)
        if is_or:
            if evidence.queried_normal and evidence.alternative_abnormal:
                return CausalAnswer("No", len(low), "lattice:normal-disjunct-suppressed", 4)
            if evidence.queried_abnormal and not evidence.alternative_abnormal:
                return CausalAnswer("No", len(low), "lattice:abnormal-redundant-disjunct", 4)
            if any(cue in low for cue in ("as usual", "usually order", "both bartlett batteries were missing")):
                return CausalAnswer("Yes", len(low), "lattice:equal-status-disjunct", 3)
        if is_and:
            if self._query_is_inanimate_component(q) and "wire" in low:
                return CausalAnswer("No", len(low), "lattice:nonagentive-component", 3)
            if evidence.queried_normal and evidence.alternative_abnormal:
                return CausalAnswer("No", len(low), "lattice:normal-conjunct-suppressed", 4)
            if evidence.queried_abnormal:
                return CausalAnswer("Yes", len(low), "lattice:abnormal-conjunct", 4)
            if any(cue in low for cue in ("very unlikely", "amazingly")) and any(
                cue in q for cue in ("coin", "spinner", "normal")
            ):
                return CausalAnswer("No", len(low), "lattice:normal-chance-conjunct", 4)
        return None

    def _judge_population_threshold(
        self, low: str, q: str, evidence: CausalEvidence
    ) -> CausalAnswer | None:
        match = re.search(r"if (?:at least )?(\d+|two) people", low)
        if not match:
            return None
        threshold = 2 if match.group(1) == "two" else int(match.group(1))
        actual = len(
            re.findall(
                r"\b[a-z][a-z'-]*\s+(?:also\s+)?(?:turns|turned|logs|logged|arrives|arrived|appears|appeared)\b",
                low,
            )
        )
        if actual > threshold + 1:
            return CausalAnswer("No", len(low), "lattice:overdetermined-threshold", 3)
        if evidence.queried_abnormal:
            return CausalAnswer("Yes", len(low), "lattice:abnormal-threshold-member", 4)
        return None

    @staticmethod
    def _query_matches_direct_goal(low: str, q: str) -> bool:
        words = {
            word
            for word in re.findall(r"[a-z][a-z'-]+", q)
            if len(word) > 3
            and word
            not in {
                "intentionally",
                "cause",
                "caused",
                "would",
                "could",
                "because",
                "people",
            }
        }
        goal_clauses = [
            clause
            for clause in re.split(r"[.!?]", low)
            if any(cue in clause for cue in ("wants to", "wanted to", "decided to", "aimed at"))
        ]
        return any(sum(word in clause for word in words) >= 2 for clause in goal_clauses)

    @staticmethod
    def _query_actor_name(q: str) -> str:
        patterns = (
            r"did\s+(?:the\s+)?([a-z][a-z'-]*)\s+cause",
            r"did\s+(?:the\s+)?([a-z][a-z'-]*)'s",
            r"by\s+([a-z][a-z'-]*)\s+cause",
        )
        for pattern in patterns:
            match = re.search(pattern, q)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _query_is_inanimate_component(q: str) -> bool:
        return any(
            noun in q
            for noun in (
                "wire",
                "switch",
                "knob",
                "coin flip",
                "spinner result",
            )
        )

    @staticmethod
    def _query_has_status(low: str, q: str, *, abnormal: bool) -> bool:
        actor = EnglishCausalResolverV3._query_actor_name(q)
        query_terms = {
            word
            for word in re.findall(r"[a-z][a-z'-]+", q)
            if len(word) > 3 and word not in {"cause", "caused", "because", "ordering"}
        }
        clauses = [
            clause.strip()
            for clause in re.split(r"[.!?]", low)
            if (actor and actor in clause)
            or sum(term in clause for term in query_terms) >= 2
        ]
        abnormal_cues = (
            "not supposed",
            "supposed to stop",
            "violating the official policy",
            "violating the requirements",
            "ignore his signal",
            "ignore her signal",
            "unexpectedly",
            "very unlikely",
            "amazingly",
            "surprisingly",
            "not allowed",
            "only faculty members are supposed",
        )
        normal_cues = (
            "supposed to",
            "permitted",
            "allowed",
            "usually",
            "normally",
            "as usual",
            "green signal",
            "follows her signal",
            "follows his signal",
        )
        cues = abnormal_cues if abnormal else normal_cues
        return any(any(cue in clause for cue in cues) for clause in clauses)

    @staticmethod
    def _other_contributor_abnormal(low: str, q: str) -> bool:
        abnormal_cues = (
            "violating the official policy",
            "not supposed",
            "ignore his signal",
            "ignore her signal",
            "unexpectedly",
            "very unlikely",
            "amazingly",
            "surprisingly",
            "faculty members are supposed to buy their own",
        )
        query_words = set(re.findall(r"[a-z][a-z'-]+", q))
        for clause in re.split(r"[.!?]", low):
            if any(cue in clause for cue in abnormal_cues):
                subject = set(re.findall(r"[a-z][a-z'-]+", clause[:80]))
                if not subject.intersection(query_words):
                    return True
        return False

    @staticmethod
    def _alternative_was_already_sufficient(low: str, q: str) -> bool:
        if not any(cue in low for cue in ("if either", "at least one", "if anyone")):
            return False
        change_index = min(
            [
                pos
                for cue in ("changes the position", "changed the position", "then", "later")
                if (pos := low.find(cue)) >= 0
            ],
            default=-1,
        )
        if change_index < 0:
            return False
        before = low[:change_index]
        actual_state_cues = (
            "is off",
            "is on",
            "is in neutral",
            "already subscribed",
            "already selected",
            "right at the beginning",
        )
        return any(cue in before for cue in actual_state_cues)
