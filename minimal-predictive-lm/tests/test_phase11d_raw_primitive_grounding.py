from __future__ import annotations

import unittest

from minimal_predictive_lm.phase11d_experiment import run
from minimal_predictive_lm.raw_primitive_grounding import (
    ContextualBypassPrimitive,
    IdentityPrimitive,
    RawResidualObservation,
    VersionedPrimitiveLibrary,
    extract_raw_spans,
    induce_raw_primitive_clusters,
    learn_bypass_token,
    propose_residual_extension,
    raw_primitive_accuracy,
)


class RawPrimitiveGroundingTests(unittest.TestCase):
    def test_extracts_spans_from_multiple_raw_modalities(self) -> None:
        rows = (
            ('入力「alpha」を結果「ALPHA」にした。', ("alpha", "ALPHA")),
            ('- x = "beta"\n+ x = "BETA"', ("beta", "BETA")),
            ("tool input='gamma' output='GAMMA'", ("gamma", "GAMMA")),
            ("symbol `delta` becomes `DELTA`", ("delta", "DELTA")),
        )
        for text, expected in rows:
            with self.subTest(text=text):
                self.assertEqual(
                    tuple(span.value for span in extract_raw_spans(text)),
                    expected,
                )

    def test_discovers_cross_channel_offset_clusters_without_family_labels(self) -> None:
        observations = (
            RawResidualObservation(
                "u1",
                "japanese",
                "入力「sphinx of black quartz judge my vow」"
                "結果「SPHINX OF BLACK QUARTZ JUDGE MY VOW」",
            ),
            RawResidualObservation(
                "u2",
                "code",
                '- x = "the five boxing wizards jump quickly"\n'
                '+ x = "THE FIVE BOXING WIZARDS JUMP QUICKLY"',
            ),
            RawResidualObservation(
                "u3",
                "tool",
                "input='pack my box with five dozen liquor jugs' "
                "output='PACK MY BOX WITH FIVE DOZEN LIQUOR JUGS'",
            ),
            RawResidualObservation(
                "l1",
                "code",
                'source="SPHINX OF BLACK QUARTZ" result="sphinx of black quartz"',
            ),
            RawResidualObservation(
                "l2",
                "tool",
                "input='PACK MY BOX' output='pack my box'",
            ),
            RawResidualObservation(
                "l3",
                "dialogue",
                "応答「RUN TEST NOW」を「run test now」として保存。",
            ),
            RawResidualObservation(
                "noise",
                "test",
                'source="alpha" result="omega"',
            ),
        )
        clusters = induce_raw_primitive_clusters(observations)
        self.assertEqual(len(clusters), 2)
        by_offset = {row.primitive.offset: row for row in clusters}
        self.assertEqual(set(by_offset), {-32, 32})
        clustered = set().union(
            *(set(row.support_observations) for row in clusters)
        )
        self.assertNotIn("noise", clustered)
        self.assertGreaterEqual(len(by_offset[-32].support_channels), 2)
        self.assertGreaterEqual(len(by_offset[32].support_channels), 2)

    def test_residual_extension_repairs_unicode_examples(self) -> None:
        base = induce_raw_primitive_clusters(
            (
                RawResidualObservation(
                    "u1",
                    "japanese",
                    "入力「sphinx of black quartz judge my vow」"
                    "結果「SPHINX OF BLACK QUARTZ JUDGE MY VOW」",
                ),
                RawResidualObservation(
                    "u2",
                    "code",
                    '- x = "the five boxing wizards jump quickly"\n'
                    '+ x = "THE FIVE BOXING WIZARDS JUMP QUICKLY"',
                ),
                RawResidualObservation(
                    "u3",
                    "tool",
                    "input='pack my box with five dozen liquor jugs' "
                    "output='PACK MY BOX WITH FIVE DOZEN LIQUOR JUGS'",
                ),
            )
        )[0].primitive
        shifted = (
            RawResidualObservation(
                "s1",
                "sensor",
                'input="café déjà vu" output="CAFÉ DÉJÀ VU"',
            ),
            RawResidualObservation(
                "s2",
                "tool",
                "input='straße' output='STRASSE'",
            ),
        )
        self.assertEqual(raw_primitive_accuracy(base, shifted), 0.0)
        extended = propose_residual_extension(base, shifted)
        self.assertEqual(raw_primitive_accuracy(extended, shifted), 1.0)
        self.assertIn(("ß", "SS"), extended.replacements)
        self.assertIn(("é", "É"), extended.replacements)

    def test_versioning_rolls_back_overbroad_update_and_accepts_context_split(self) -> None:
        training = (
            RawResidualObservation(
                "u1",
                "japanese",
                "入力「sphinx of black quartz judge my vow」"
                "結果「SPHINX OF BLACK QUARTZ JUDGE MY VOW」",
            ),
            RawResidualObservation(
                "u2",
                "code",
                '- x = "the five boxing wizards jump quickly"\n'
                '+ x = "THE FIVE BOXING WIZARDS JUMP QUICKLY"',
            ),
            RawResidualObservation(
                "u3",
                "tool",
                "input='pack my box with five dozen liquor jugs' "
                "output='PACK MY BOX WITH FIVE DOZEN LIQUOR JUGS'",
            ),
        )
        base = induce_raw_primitive_clusters(training)[0].primitive
        shifted = (
            RawResidualObservation("s1", "sensor", 'input="café" output="CAFÉ"'),
            RawResidualObservation("s2", "tool", "input='straße' output='STRASSE'"),
        )
        conflicts = (
            RawResidualObservation(
                "c1",
                "japanese",
                'mode=verbatim input="keep lower" output="keep lower"',
            ),
            RawResidualObservation(
                "c2",
                "tool",
                "verbatim input='raw command' output='raw command'",
            ),
        )
        library = VersionedPrimitiveLibrary(base, reason="initial raw cluster")
        extension = propose_residual_extension(base, shifted)
        extension_decision = library.stage(
            extension,
            training + shifted,
            reason="unicode extension",
            expected_future_calls=100,
        )
        self.assertTrue(extension_decision.accepted)

        bad = library.stage(
            IdentityPrimitive(),
            training + shifted + conflicts,
            reason="overbroad update",
            expected_future_calls=100,
        )
        self.assertTrue(bad.rolled_back)
        self.assertEqual(library.active.version, 2)

        token = learn_bypass_token(training + shifted, conflicts)
        self.assertEqual(token, "verbatim")
        contextual = ContextualBypassPrimitive(library.active.primitive, token)
        split = library.stage(
            contextual,
            training + shifted + conflicts,
            reason="context split",
            expected_future_calls=100,
        )
        self.assertTrue(split.accepted)
        self.assertEqual(library.active.version, 3)
        self.assertEqual(
            raw_primitive_accuracy(
                library.active.primitive,
                training + shifted + conflicts,
            ),
            1.0,
        )

    def test_phase11d_reports_success_without_open_ended_claim(self) -> None:
        payload = run()
        self.assertTrue(payload["verdict"]["phase11d_success"])
        self.assertTrue(payload["verdict"]["raw_task_family_boundaries_removed"])
        self.assertFalse(payload["verdict"]["open_ended_grounding_achieved"])
        self.assertFalse(payload["verdict"]["stage_c_score_changed"])


if __name__ == "__main__":
    unittest.main()
