from pathlib import Path
import tempfile
import unittest

from minimal_predictive_lm.ravel_1g_model import (
    KnowledgeDocument,
    Ravel1GConfig,
    Ravel1GModel,
)


class Ravel1GModelTest(unittest.TestCase):
    def test_default_capacity_is_real_and_below_limit(self) -> None:
        config = Ravel1GConfig()
        self.assertEqual(config.logical_bytes, 990_000_000)
        self.assertEqual(
            sum(region.size for region in config.resolved_regions()),
            990_000_000,
        )
        self.assertLess(config.logical_bytes, 1_000_000_000)

    def test_training_writes_distributed_regions_and_is_deterministic(self) -> None:
        config = Ravel1GConfig.scaled_for_tests(4_000_000)
        documents = [
            KnowledgeDocument(
                "加熱",
                "水を加熱すると温度が上がる。鉄を加熱しても温度が上がる。",
            ),
            KnowledgeDocument(
                "冷却",
                "水を冷却すると温度が下がる。鉄を冷却しても温度が下がる。",
            ),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ravel.bin"
            with Ravel1GModel.create(path, config) as model:
                stats = model.train(documents)
                first = model.score_options(
                    "銅を加熱すると何が上がるか",
                    ("温度", "質量", "名前", "色"),
                )[0]
                second = model.score_options(
                    "銅を加熱すると何が上がるか",
                    ("温度", "質量", "名前", "色"),
                )[0]
                report = model.resource_report()
                self.assertEqual(first, second)
                self.assertEqual(stats.documents, 2)
                self.assertGreater(
                    report["region_stats"]["entities"]["writes"],
                    0,
                )
                self.assertGreater(
                    report["region_stats"]["programs"]["writes"],
                    0,
                )
                self.assertGreater(
                    report["region_stats"]["residual"]["writes"],
                    0,
                )
                self.assertEqual(path.stat().st_size, 4_000_000)

    def test_model_reopens_with_same_scores(self) -> None:
        config = Ravel1GConfig.scaled_for_tests(4_000_000)
        documents = [
            KnowledgeDocument(
                "光合成",
                "植物は光合成で酸素を放出する。葉緑体で光エネルギーを利用する。",
            )
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ravel.bin"
            with Ravel1GModel.create(path, config) as model:
                model.train(documents)
                expected = model.score_options(
                    "植物が光合成で放出する気体",
                    ("酸素", "窒素", "水素", "ヘリウム"),
                )[0]
            with Ravel1GModel(path, config) as reopened:
                actual = reopened.score_options(
                    "植物が光合成で放出する気体",
                    ("酸素", "窒素", "水素", "ヘリウム"),
                )[0]
            self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
