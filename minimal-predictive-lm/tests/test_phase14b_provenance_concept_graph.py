from __future__ import annotations

import unittest

from minimal_predictive_lm.provenance_concept_graph import (
    DocumentObservation,
    ProvenanceOverlayOntology,
    induce_provenance_graph,
)
from minimal_predictive_lm.wordnet_ontology import NounSynset, WordNetNounOntology


def _wordnet_fixture() -> WordNetNounOntology:
    synsets = {
        1: NounSynset(1, ("entity",), ()),
        2: NounSynset(2, ("artifact",), (1,)),
        3: NounSynset(3, ("network_device",), (2,)),
        4: NounSynset(4, ("router",), (3,)),
        5: NounSynset(5, ("mammal",), (1,)),
        6: NounSynset(6, ("whale",), (5,)),
        7: NounSynset(7, ("fish",), (1,)),
        8: NounSynset(8, ("food",), (1,)),
        9: NounSynset(9, ("vegetable",), (8,)),
        10: NounSynset(10, ("garlic",), (8,)),
        11: NounSynset(11, ("fruit",), (8,)),
        12: NounSynset(12, ("berry",), (11,)),
        13: NounSynset(13, ("cloudberry",), (12,)),
    }
    lemma_to_synsets = {
        lemma: (offset,)
        for offset, synset in synsets.items()
        for lemma in synset.lemmas
    }
    return WordNetNounOntology(
        synsets=synsets,
        lemma_to_synsets=lemma_to_synsets,
        exceptions={},
        source_bytes=123,
        source_sha256="fixture",
    )


def _documents() -> tuple[DocumentObservation, ...]:
    return (
        DocumentObservation(
            "allium-paper",
            "Allium vegetables include garlic and onion. Allium vegetables are vegetables.",
            "https://arxiv.org/abs/2409.11187",
        ),
        DocumentObservation(
            "software-handbook",
            "A router is a kind of network device. Network devices are artifacts.",
        ),
        DocumentObservation(
            "berry-guide",
            "A cloudberry is a berry. Berries are fruits.",
        ),
        DocumentObservation(
            "animal-guide",
            "Every whale is a mammal. A whale is not a fish.",
        ),
    )


class Phase14bProvenanceConceptGraphTests(unittest.TestCase):
    def test_raw_documents_form_transitive_cross_domain_paths(self) -> None:
        graph = induce_provenance_graph(_documents())
        self.assertIs(graph.query("garlic", "vegetable").value, True)
        self.assertIs(graph.query("router", "artifact").value, True)
        self.assertIs(graph.query("cloudberries", "fruits").value, True)
        self.assertIs(graph.query("whale", "mammal").value, True)
        self.assertIs(graph.query("whale", "fish").value, False)
        self.assertEqual(len(graph.source_ids), 4)

    def test_kind_of_is_parsed_as_relation_not_literal_parent_text(self) -> None:
        graph = induce_provenance_graph(_documents())
        decision = graph.query("router", "network device")
        self.assertIs(decision.value, True)
        self.assertEqual([(edge.child, edge.parent) for edge in decision.proof], [("router", "network_device")])

    def test_document_positive_fills_wordnet_open_world_gap(self) -> None:
        base = _wordnet_fixture()
        self.assertIs(base.is_a("garlic", "vegetable").value, False)
        overlay = ProvenanceOverlayOntology(base, induce_provenance_graph(_documents()))
        decision = overlay.is_a("garlic", "vegetable")
        self.assertIs(decision.value, True)
        self.assertEqual(decision.reason, "document-positive-fills-open-world-gap")
        self.assertEqual(len(decision.graph_proof), 2)

    def test_explicit_document_negative_conflicting_with_wordnet_abstains(self) -> None:
        base = _wordnet_fixture()
        graph = induce_provenance_graph(
            (DocumentObservation("bad-source", "A whale is not a mammal."),)
        )
        decision = ProvenanceOverlayOntology(base, graph).is_a("whale", "mammal")
        self.assertIsNone(decision.value)
        self.assertIn("conflicts", decision.reason)

    def test_positive_and_negative_documents_conflict_and_abstain(self) -> None:
        graph = induce_provenance_graph(
            (
                DocumentObservation("source-a", "A whale is a fish."),
                DocumentObservation("source-b", "A whale is not a fish."),
            )
        )
        decision = graph.query("whale", "fish")
        self.assertIsNone(decision.value)
        self.assertEqual(decision.reason, "conflicting-document-evidence")
        self.assertEqual(len(decision.proof), 2)

    def test_provenance_and_cache_have_nonzero_description_cost(self) -> None:
        graph = induce_provenance_graph(_documents())
        overlay = ProvenanceOverlayOntology(_wordnet_fixture(), graph)
        overlay.is_a("garlic", "vegetable")
        overlay.is_a("garlic", "vegetable")
        self.assertGreater(graph.description_bits, 0)
        self.assertGreater(overlay.cache_bits, 0)
        self.assertEqual(overlay.cache_hits, 1)


if __name__ == "__main__":
    unittest.main()
