from __future__ import annotations

from functools import lru_cache

from .english_causal_compiler import CausalAnswer, _norm
from .english_causal_compiler_v2 import _last_question_v2
from .english_causal_compiler_v3_runtime import EnglishCausalResolverV3Runtime
from .sparse_causal_curriculum import build_sparse_causal_curriculum
from .sparse_causal_induction import SparseCausalPrototypeModel
from .sparse_causal_routing import train_routed_sparse_causal_prototypes


@lru_cache(maxsize=1)
def build_sparse_causal_model() -> SparseCausalPrototypeModel:
    return train_routed_sparse_causal_prototypes(build_sparse_causal_curriculum())


class EnglishCausalResolverV4:
    """Learned local prototype routing plus the bounded structural lattice."""

    def __init__(self, model: SparseCausalPrototypeModel | None = None) -> None:
        self.model = model or build_sparse_causal_model()
        self.symbolic = EnglishCausalResolverV3Runtime()
        self.description_bits = self.model.description_bits + self.symbolic.description_bits
        self.benchmark_task_name_branches = 0
        self.domain_specific_handlers = 0

    def answer(self, prompt: str) -> CausalAnswer:
        query = _normalised_question(prompt)
        if not query or (
            "cause" not in query
            and "intentional" not in query
            and "because" not in query
        ):
            return CausalAnswer(None, 1, None, 0)

        learned = self.model.predict(prompt)
        symbolic = self.symbolic.answer(prompt)
        operations = learned.feature_reads + symbolic.operations

        if learned.answer is None:
            return CausalAnswer(
                symbolic.output,
                operations,
                symbolic.family,
                symbolic.confidence,
            )
        if symbolic.output is None:
            return CausalAnswer(
                learned.answer,
                operations,
                f"learned:{learned.operator}",
                3,
            )
        if learned.answer == symbolic.output:
            return CausalAnswer(
                symbolic.output,
                operations,
                f"consensus:{learned.operator}:{symbolic.family}",
                max(4, symbolic.confidence),
            )

        if learned.score >= 0.20 and learned.margin >= 0.035:
            return CausalAnswer(
                learned.answer,
                operations,
                f"learned-override:{learned.operator}",
                4,
            )
        return CausalAnswer(
            symbolic.output,
            operations,
            f"symbolic-retained:{symbolic.family}",
            symbolic.confidence,
        )


def _normalised_question(prompt: str) -> str:
    return _norm(_last_question_v2(prompt))
