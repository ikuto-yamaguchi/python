from __future__ import annotations

from dataclasses import dataclass

from .sparc_highschool_latent_state_graph import LatentStateGraphLearner, LatentStateGraphResult


@dataclass(frozen=True)
class QuestionGroundedResult:
    accepted: bool
    grounded: LatentStateGraphResult
    targets: tuple[str, ...]
    selected_states: tuple[tuple[str, str, int, int], ...]
    answer: str
    mechanism: str


class QuestionGroundedWorldLearner(LatentStateGraphLearner):
    """Ground an open Japanese question to evidence in the shared world graph.

    Candidate entities come only from learned transitions and observations.  The
    final utterance is matched against those entities without task/domain labels;
    exactly one referenced connected component must be supported.  The underlying
    bidirectional solver and verifier remain unchanged.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.question_groundings = 0
        self.question_grounding_abstentions = 0
        self.question_entity_reads = 0
        self.question_selected_states = 0

    def answer_question_grounded_world(self, text: str) -> QuestionGroundedResult:
        sentences = tuple(self._sentences(text))
        if len(sentences) < 2:
            return self._q_abstain("abstain-missing-question")
        question = sentences[-1]
        body = "。".join(sentences[:-1]) + "。"
        grounded = self.infer_latent_state_graph(body)
        if not grounded.accepted or not grounded.verified:
            return self._q_abstain("abstain-unverified-world", grounded)

        entities = tuple(sorted({subject for subject, _relation, _node, _value in grounded.recovered_states}))
        self.question_entity_reads += len(entities)
        targets = tuple(entity for entity in entities if entity and entity in question)
        if len(targets) != 1:
            return self._q_abstain("abstain-ambiguous-question-target", grounded, targets)

        selected = tuple(row for row in grounded.recovered_states if row[0] == targets[0])
        if not selected:
            return self._q_abstain("abstain-no-supported-target-state", grounded, targets)
        self.question_groundings += 1
        self.question_selected_states += len(selected)
        details = "、".join(f"時点{node}は{value}" for _subject, _relation, node, value in selected)
        answer = f"{targets[0]}について同じ世界遷移を前後から照合すると、{details}です。観測まで再実行して検算しました。"
        return QuestionGroundedResult(True, grounded, targets, selected, answer, "shared-question-grounded-world-graph")

    def _q_abstain(self, mechanism, grounded=None, targets=()):
        self.question_grounding_abstentions += 1
        empty = grounded or self._abstain("abstain-question-grounding-without-world")
        return QuestionGroundedResult(False, empty, tuple(targets), (), "", mechanism)

    def report(self):
        result = super().report()
        result.update({
            "shared_question_grounding": True,
            "question_groundings": self.question_groundings,
            "question_grounding_abstentions": self.question_grounding_abstentions,
            "question_entity_reads": self.question_entity_reads,
            "question_selected_states": self.question_selected_states,
            "task_name_supplied": False,
            "domain_name_supplied": False,
        })
        return result
