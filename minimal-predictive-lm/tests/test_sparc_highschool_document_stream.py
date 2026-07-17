import random
import unittest

from minimal_predictive_lm.sparc_highschool_general import World
from minimal_predictive_lm.sparc_highschool_document_stream import IndependentDocumentLearner


def corpus():
    texts = [
        "水は物質である", "酸素は気体である", "鉄は金属である", "正方形は図形である",
        "江戸幕府は政権である", "鎌倉幕府は政権である",
        "ルネサンスは文化運動である", "産業革命は社会変化である",
        "水というものは物質に分類される", "酸素というものは気体に分類される",
        "鉄というものは金属に分類される", "正方形というものは図形に分類される",
        "歴史上の江戸幕府は一つの政権だった", "歴史上の鎌倉幕府は一つの政権だった",
        "歴史上の室町幕府は一つの政権だった", "歴史上のルネサンスは一つの文化運動だった",
        "歴史上の産業革命は一つの社会変化だった",
        "物質の仲間に数えられるものが水だ", "気体の仲間に数えられるものが酸素だ",
        "金属の仲間に数えられるものが鉄だ", "図形の仲間に数えられるものが正方形だ",
        "水を分類すると物質に入る", "酸素を分類すると気体に入る",
        "鉄を分類すると金属に入る", "正方形を分類すると図形に入る",
        "東京は日本に位置する", "パリはフランスに位置する", "ローマはイタリアに位置する", "ベルリンはドイツに位置する",
        "日本に位置する都市が東京だ", "フランスに位置する都市がパリだ", "イタリアに位置する都市がローマだ", "ドイツに位置する都市がベルリンだ",
        "東京の所在国は日本である", "パリの所在国はフランスである", "ローマの所在国はイタリアである", "ベルリンの所在国はドイツである",
        "今日は静かな雨が降る", "春には花が咲く",
    ]
    rows = [(text, f"D{index:03d}") for index, text in enumerate(texts)]
    random.Random(17).shuffle(rows)
    return rows


def oriented_fact(world, left, right):
    direct = [fact for fact in world.facts if fact[0] == left and fact[2] == right]
    reverse = [fact for fact in world.facts if fact[0] == right and fact[2] == left]
    rows = direct + reverse
    if len(rows) != 1:
        raise AssertionError(f"expected one opaque oriented fact for {left}/{right}: {rows}")
    return rows[0]


class IndependentDocumentLearnerTests(unittest.TestCase):
    def test_discovers_two_relations_without_group_labels(self):
        learner = IndependentDocumentLearner()
        result = learner.learn_independent_documents(corpus(), min_support=4)
        self.assertEqual(result.relation_clusters, 2)
        world = learner.learned_document_world()
        kind = oriented_fact(world, "水", "物質")
        location = oriented_fact(world, "東京", "日本")
        self.assertNotEqual(kind[1], location[1])
        self.assertEqual(len(learner.document_facts), 13)
        self.assertFalse(learner.report()["paraphrase_group_labels_supplied"])

    def test_composes_unseen_surface_from_independent_documents(self):
        learner = IndependentDocumentLearner()
        learner.learn_independent_documents(corpus(), min_support=4)
        reference = oriented_fact(learner.learned_document_world(), "水", "物質")
        result = learner.apply("銅は金属に分類される", World())
        self.assertTrue(result.accepted)
        expected = ("銅", reference[1], "金属") if reference[0] == "水" else ("金属", reference[1], "銅")
        self.assertIn(expected, result.world.facts)

    def test_retains_source_grounded_document_world(self):
        learner = IndependentDocumentLearner()
        learner.learn_independent_documents(corpus(), min_support=4)
        fact = oriented_fact(learner.learned_document_world(), "水", "物質")
        self.assertGreaterEqual(len(learner.document_sources[fact]), 4)

    def test_serialization_preserves_stream_schemas(self):
        learner = IndependentDocumentLearner()
        learner.learn_independent_documents(corpus(), min_support=4)
        reference = oriented_fact(learner.learned_document_world(), "東京", "日本")
        restored = IndependentDocumentLearner.from_bytes(learner.to_bytes())
        result = restored.apply("大阪は日本に位置する", World())
        self.assertTrue(result.accepted)
        expected = ("大阪", reference[1], "日本") if reference[0] == "東京" else ("日本", reference[1], "大阪")
        self.assertIn(expected, result.world.facts)


if __name__ == "__main__":
    unittest.main()
