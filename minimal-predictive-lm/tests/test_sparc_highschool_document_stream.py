import random
import unittest

from minimal_predictive_lm.sparc_highschool_general import World
from minimal_predictive_lm.sparc_highschool_document_stream import IndependentDocumentLearner


def corpus():
    texts = [
        "水は物質である", "酸素は気体である", "鉄は金属である", "正方形は図形である",
        "江戸幕府は政権である", "鎌倉幕府は政権である",
        "水というものは物質に分類される", "酸素というものは気体に分類される",
        "鉄というものは金属に分類される", "正方形というものは図形に分類される",
        "歴史上の江戸幕府は一つの政権だった", "歴史上の鎌倉幕府は一つの政権だった",
        "歴史上の室町幕府は一つの政権だった",
        "物質の仲間に数えられるものが水だ", "気体の仲間に数えられるものが酸素だ",
        "金属の仲間に数えられるものが鉄だ", "図形の仲間に数えられるものが正方形だ",
        "水を分類すると物質に入る", "酸素を分類すると気体に入る",
        "鉄を分類すると金属に入る", "正方形を分類すると図形に入る",
        "東京は日本に位置する", "パリはフランスに位置する", "ローマはイタリアに位置する",
        "日本に位置する都市が東京だ", "フランスに位置する都市がパリだ", "イタリアに位置する都市がローマだ",
        "東京の所在国は日本である", "パリの所在国はフランスである", "ローマの所在国はイタリアである",
        "今日は静かな雨が降る", "春には花が咲く",
    ]
    rows = [(text, f"D{index:03d}") for index, text in enumerate(texts)]
    random.Random(17).shuffle(rows)
    return rows


class IndependentDocumentLearnerTests(unittest.TestCase):
    def test_discovers_two_relations_without_group_labels(self):
        learner = IndependentDocumentLearner()
        result = learner.learn_independent_documents(corpus())
        self.assertEqual(result.relation_clusters, 2)
        world = learner.learned_document_world()
        kind_relations = {relation for subject, relation, obj in world.facts if (subject, obj) in {("水", "物質"), ("酸素", "気体"), ("鉄", "金属")}}
        location_relations = {relation for subject, relation, obj in world.facts if (subject, obj) in {("東京", "日本"), ("パリ", "フランス"), ("ローマ", "イタリア")}}
        self.assertEqual(len(kind_relations), 1)
        self.assertEqual(len(location_relations), 1)
        self.assertNotEqual(kind_relations, location_relations)
        self.assertFalse(learner.report()["paraphrase_group_labels_supplied"])

    def test_composes_unseen_surface_from_independent_documents(self):
        learner = IndependentDocumentLearner()
        learner.learn_independent_documents(corpus())
        result = learner.apply("銅は金属に分類される", World())
        self.assertTrue(result.accepted)
        self.assertTrue(any(subject == "銅" and obj == "金属" for subject, _relation, obj in result.world.facts))

    def test_retains_source_grounded_document_world(self):
        learner = IndependentDocumentLearner()
        learner.learn_independent_documents(corpus())
        fact = next(fact for fact in learner.document_facts if fact[0] == "水" and fact[2] == "物質")
        self.assertGreaterEqual(len(learner.document_sources[fact]), 3)

    def test_serialization_preserves_stream_schemas(self):
        learner = IndependentDocumentLearner()
        learner.learn_independent_documents(corpus())
        restored = IndependentDocumentLearner.from_bytes(learner.to_bytes())
        result = restored.apply("大阪は日本に位置する", World())
        self.assertTrue(result.accepted)
        self.assertTrue(any(subject == "大阪" and obj == "日本" for subject, _relation, obj in result.world.facts))


if __name__ == "__main__":
    unittest.main()
