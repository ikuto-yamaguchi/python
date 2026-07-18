from __future__ import annotations

from dataclasses import dataclass
import re

from .sparc_highschool_latent_state_graph import LatentStateGraphResult
from .sparc_highschool_question_grounding import QuestionGroundedWorldLearner


@dataclass(frozen=True)
class DiscourseWorkspaceResult:
    accepted: bool
    grounded: LatentStateGraphResult
    targets: tuple[str, ...]
    selected_states: tuple[tuple[str, str, int, int], ...]
    answer: str
    mechanism: str
    focus_reused: bool


class DiscourseEvidenceWorkspaceLearner(QuestionGroundedWorldLearner):
    """Maintain one bounded verified evidence focus across Japanese dialogue turns.

    The workspace stores only an entity selected from a successfully verified latent
    world component. A later information request may reuse that component when no
    entity is explicitly selected, while an explicit unique component replaces the
    focus. Ambiguous or unsupported turns clear the focus and abstain. This is one
    shared discourse/evidence mechanism rather than a pronoun or sentence-template
    table.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._discourse_focus: tuple[str, ...] = ()
        self.discourse_turns = 0
        self.discourse_focus_reuses = 0
        self.discourse_focus_switches = 0
        self.discourse_abstentions = 0
        self.discourse_evidence_reads = 0

    def reset_discourse(self) -> None:
        self._discourse_focus = ()

    @staticmethod
    def _unsupported_entity_mentions(question: str, entities: tuple[str, ...]) -> tuple[str, ...]:
        """Detect explicit entity-family mentions unsupported by the verified graph.

        Entity identifiers are induced strings. Their trailing compact identifier is
        separated from the shared lexical stem, then the question is scanned for
        other members of that same family. This rejects an explicit unseen target
        without a hand-written entity list or question-template routing.
        """
        unsupported: set[str] = set()
        for entity in entities:
            stem = re.sub(r"[0-9A-Za-z０-９Ａ-Ｚａ-ｚ]+$", "", entity)
            if not stem or stem == entity:
                continue
            pattern = re.compile(re.escape(stem) + r"[0-9A-Za-z０-９Ａ-Ｚａ-ｚ]+")
            for match in pattern.finditer(question):
                candidate = match.group(0)
                if candidate not in entities:
                    unsupported.add(candidate)
        return tuple(sorted(unsupported))

    def answer_discourse_grounded_world(self, text: str) -> DiscourseWorkspaceResult:
        sentences = tuple(self._sentences(text))
        if len(sentences) < 2:
            self.reset_discourse()
            return self._d_abstain("abstain-missing-discourse-question")
        question = sentences[-1]
        body = "。".join(sentences[:-1]) + "。"
        grounded = self.infer_latent_state_graph(body)
        if not grounded.accepted or not grounded.verified:
            self.reset_discourse()
            return self._d_abstain("abstain-unverified-discourse-world", grounded)

        entities = tuple(sorted({subject for subject, _relation, _node, _value in grounded.recovered_states}))
        self.discourse_evidence_reads += len(entities)
        explicit = self._question_targets(question, entities)
        unsupported = self._unsupported_entity_mentions(question, entities)
        reused = False
        if unsupported:
            self.reset_discourse()
            return self._d_abstain("abstain-unsupported-explicit-discourse-target", grounded, unsupported)
        if len(explicit) == 1:
            targets = explicit
            if self._discourse_focus and self._discourse_focus != targets:
                self.discourse_focus_switches += 1
            self._discourse_focus = targets
        elif len(explicit) == 0 and len(self._discourse_focus) == 1 and self._discourse_focus[0] in entities:
            targets = self._discourse_focus
            reused = True
            self.discourse_focus_reuses += 1
        else:
            self.reset_discourse()
            return self._d_abstain("abstain-ambiguous-discourse-evidence", grounded, explicit)

        selected = tuple(row for row in grounded.recovered_states if row[0] == targets[0])
        if not selected:
            self.reset_discourse()
            return self._d_abstain("abstain-no-focused-discourse-evidence", grounded, targets)

        self.discourse_turns += 1
        details = "、".join(f"時点{node}は{value}" for _subject, _relation, node, value in selected)
        answer = (
            f"検算済みの同じ証拠グラフでは、{targets[0]}の{details}です。"
            "観測位置まで世界遷移を再実行し、この回答に必要な成分だけを保持しました。"
        )
        return DiscourseWorkspaceResult(
            True,
            grounded,
            targets,
            selected,
            answer,
            "shared-bounded-discourse-evidence-workspace",
            reused,
        )

    def _d_abstain(self, mechanism, grounded=None, targets=()):
        self.discourse_abstentions += 1
        empty = grounded or self._abstain("abstain-discourse-without-world")
        return DiscourseWorkspaceResult(False, empty, tuple(targets), (), "", mechanism, False)

    def report(self):
        result = super().report()
        result.update({
            "shared_bounded_discourse_evidence_workspace": True,
            "discourse_turns": self.discourse_turns,
            "discourse_focus_reuses": self.discourse_focus_reuses,
            "discourse_focus_switches": self.discourse_focus_switches,
            "discourse_abstentions": self.discourse_abstentions,
            "discourse_evidence_reads": self.discourse_evidence_reads,
            "task_name_supplied": False,
            "domain_name_supplied": False,
        })
        return result
