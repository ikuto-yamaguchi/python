from __future__ import annotations

from io import BytesIO
import hashlib
import unittest
import zipfile

from minimal_predictive_lm.generic_quantifier import (
    QuantifiedExample,
    QuantityObservation,
    induce_generic_quantifier,
)
from minimal_predictive_lm.wordnet_ontology import (
    OntologyBackedQuantifier,
    WordNetNounOntology,
)


def _line(
    offset: int,
    lemma: str,
    hypernym: int | None = None,
) -> str:
    if hypernym is None:
        return f"{offset:08d} 00 n 01 {lemma} 0 000 | {lemma}\n"
    return (
        f"{offset:08d} 00 n 01 {lemma} 0 001 @ {hypernym:08d} n 0000 | {lemma}\n"
    )


def _fixture_zip() -> bytes:
    data = "".join(
        (
            _line(1, "entity"),
            _line(2, "object", 1),
            _line(3, "animal", 2),
            _line(4, "dog", 3),
            _line(5, "food", 2),
            _line(6, "fruit", 5),
            _line(7, "apple", 6),
            _line(8, "instrument", 2),
            _line(9, "flute", 8),
            _line(10, "vegetable", 5),
            _line(11, "broccoli", 10),
        )
    ).encode("utf-8")
    exceptions = b"dogs dog\napples apple\nflutes flute\ninstruments instrument\n"
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("dict/data.noun", data)
        archive.writestr("dict/noun.exc", exceptions)
    return buffer.getvalue()


def _quantifier():
    return induce_generic_quantifier(
        (
            QuantityObservation("a", 1),
            QuantityObservation("an", 1),
            QuantityObservation("one", 1),
            QuantityObservation("two", 2),
            QuantityObservation("three", 3),
        ),
        (
            QuantifiedExample(
                "I have two servers and a router. How many objects do I have?",
                3,
            ),
        ),
    )


class Phase14aWordNetOntologyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = _fixture_zip()
        fixture_sha256 = hashlib.sha256(self.payload).hexdigest()
        self.ontology = WordNetNounOntology.from_zip_bytes(
            self.payload,
            expected_sha256=fixture_sha256,
        )

    def test_parses_noun_hypernym_graph_and_returns_proof(self) -> None:
        decision = self.ontology.is_a("dogs", "animals")
        self.assertIs(decision.value, True)
        self.assertEqual(
            tuple(row[0] for row in self.ontology.proof_lemmas(decision)),
            ("dog", "animal"),
        )

    def test_known_nonmember_is_false_and_unknown_item_is_unknown(self) -> None:
        self.assertIs(self.ontology.is_a("flute", "fruit").value, False)
        unknown = self.ontology.is_a("quorp", "animal")
        self.assertIsNone(unknown.value)
        self.assertEqual(unknown.reason, "item-unresolved")

    def test_generic_compound_and_plural_normalization(self) -> None:
        self.assertIs(self.ontology.is_a("heads of broccoli", "vegetables").value, True)
        self.assertIn("broccoli", self.ontology.lemma_candidates("heads of broccoli"))

    def test_quantifier_counts_true_members_and_excludes_known_false_members(self) -> None:
        program = OntologyBackedQuantifier(_quantifier(), self.ontology)
        prompt = (
            "I have two dogs, an apple, and a flute. "
            "How many animals do I have?"
        )
        self.assertEqual(program.answer(prompt), 2)
        self.assertEqual([row.value for row in program.last_decisions], [True, False, False])

    def test_quantifier_abstains_when_membership_is_unresolved(self) -> None:
        program = OntologyBackedQuantifier(_quantifier(), self.ontology)
        prompt = "I have two quorps and an apple. How many animals do I have?"
        interval = program.identifiability_interval(prompt)
        self.assertIsNotNone(interval)
        assert interval is not None
        self.assertEqual((interval.minimum, interval.maximum), (0, 2))
        self.assertIsNone(program.answer(prompt))

    def test_cache_and_checksum_are_accounted(self) -> None:
        self.ontology.is_a("dog", "animal")
        first = self.ontology.metrics()
        self.ontology.is_a("dog", "animal")
        second = self.ontology.metrics()
        self.assertEqual(first.cache_entries, 1)
        self.assertEqual(second.cache_hits, 1)
        self.assertEqual(second.source_sha256, hashlib.sha256(self.payload).hexdigest())
        self.assertGreater(second.cache_bits, 0)

    def test_checksum_mismatch_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WordNetNounOntology.from_zip_bytes(self.payload, expected_sha256="0" * 64)


if __name__ == "__main__":
    unittest.main()
