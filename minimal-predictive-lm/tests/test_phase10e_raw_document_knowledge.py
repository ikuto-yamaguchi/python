from __future__ import annotations

import unittest

from minimal_predictive_lm.phase10e_experiment import run
from minimal_predictive_lm.raw_document_knowledge import (
    ContextObservation,
    RawDocument,
    build_raw_knowledge_index,
    extract_claims,
    learn_context_trust,
)


class RawDocumentKnowledgeTests(unittest.TestCase):
    def test_bilingual_extraction_preserves_spans(self) -> None:
        documents = [
            RawDocument(
                "ja",
                "official",
                "science",
                2026,
                "前置き。item_1のcolorはredです。後置き。",
            ),
            RawDocument(
                "en",
                "official",
                "science",
                2026,
                "Note: item_2's color is blue. End.",
            ),
        ]
        claims = extract_claims(documents)
        self.assertEqual(
            [(claim.subject, claim.value) for claim in claims],
            [("item_1", "red"), ("item_2", "blue")],
        )
        for claim in claims:
            self.assertGreater(claim.span_end, claim.span_start)
            self.assertIn("#", claim.provenance)

    def test_copy_lineage_collapses_to_one_origin(self) -> None:
        documents = [
            RawDocument(
                "root",
                "blog",
                "science",
                2026,
                "item_1のcolorはredです。",
            ),
            RawDocument(
                "copy",
                "blog",
                "science",
                2026,
                "item_1のcolorはredです。",
                "root",
            ),
        ]
        claims = extract_claims(documents)
        self.assertEqual(len({claim.origin for claim in claims}), 1)

    def test_unknown_query_abstains_without_reads(self) -> None:
        observations = [
            ContextObservation(
                "official",
                "science",
                "recent",
                True,
            )
        ]
        contextual, global_trust = learn_context_trust(
            observations
        )
        index = build_raw_knowledge_index(
            (),
            contextual,
            global_trust,
        )
        answer = index.answer("missing", "color")
        self.assertTrue(answer.abstained)
        self.assertEqual(answer.claim_reads, 0)

    def test_phase10e_metrics_and_gates(self) -> None:
        payload = run()
        extraction = payload["raw_extraction"]
        policies = payload["policies"]
        global_policy = policies["global_independent"]
        correlated = policies[
            "contextual_correlated_exhaustive"
        ]
        voi = policies["contextual_correlated_voi"]

        self.assertEqual(extraction["precision"], 1.0)
        self.assertEqual(extraction["recall"], 1.0)
        self.assertTrue(
            extraction["provenance_spans_preserved"]
        )
        self.assertLess(
            global_policy["selective_accuracy"],
            correlated["selective_accuracy"],
        )
        self.assertEqual(
            correlated["selective_accuracy"],
            1.0,
        )
        self.assertEqual(voi["selective_accuracy"], 1.0)
        self.assertGreaterEqual(voi["coverage"], 0.65)
        self.assertLess(
            voi["claim_reads"],
            correlated["claim_reads"],
        )
        self.assertFalse(payload["stage_c"]["stage_c_ready"])
        self.assertEqual(
            payload["stage_c"]["readiness_points_after"],
            8,
        )


if __name__ == "__main__":
    unittest.main()
