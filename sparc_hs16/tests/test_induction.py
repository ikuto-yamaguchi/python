from __future__ import annotations

import random
import unittest

from sparc_hs16.induction import NumericDemonstration, NumericMechanismBank
from sparc_hs16.model import SparseMemory


class ProgramInductionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = SparseMemory()
        self.bank = NumericMechanismBank(self.memory)

    def test_product_program_from_examples(self) -> None:
        program = self.bank.learn(
            "distance",
            [
                NumericDemonstration("時速30kmで2時間進む距離は？", "60"),
                NumericDemonstration("時速45kmで3時間進む距離は？", "135"),
                NumericDemonstration("時速12kmで5時間進む距離は？", "60"),
                NumericDemonstration("時速80kmで4時間進む距離は？", "320"),
            ],
        )
        self.assertIn(program.expression, {"(n0*n1)", "(n1*n0)"})
        rng = random.Random(1818)
        for _ in range(100):
            speed, hours = rng.randint(1, 120), rng.randint(1, 12)
            solved = self.bank.solve(f"時速{speed}kmで{hours}時間進む距離は？")
            self.assertIsNotNone(solved)
            self.assertEqual(solved[0], str(speed * hours))

    def test_two_step_program_from_examples(self) -> None:
        program = self.bank.learn(
            "inventory",
            [
                NumericDemonstration("在庫10個に3箱、各4個を追加すると？", "22"),
                NumericDemonstration("在庫7個に5箱、各2個を追加すると？", "17"),
                NumericDemonstration("在庫20個に2箱、各8個を追加すると？", "36"),
                NumericDemonstration("在庫1個に9箱、各3個を追加すると？", "28"),
            ],
        )
        self.assertIn(program.expression, {"(n0+(n1*n2))", "((n1*n2)+n0)"})
        for base, boxes, each in [(4, 6, 7), (50, 3, 9), (2, 11, 5)]:
            solved = self.bank.solve(f"在庫{base}個に{boxes}箱、各{each}個を追加すると？")
            self.assertIsNotNone(solved)
            self.assertEqual(solved[0], str(base + boxes * each))

    def test_serialization_round_trip(self) -> None:
        self.bank.learn(
            "distance",
            [
                NumericDemonstration("時速30kmで2時間進む距離は？", "60"),
                NumericDemonstration("時速45kmで3時間進む距離は？", "135"),
                NumericDemonstration("時速12kmで5時間進む距離は？", "60"),
            ],
        )
        restored = NumericMechanismBank.from_dict(self.memory, self.bank.to_dict())
        solved = restored.solve("時速73kmで6時間進む距離は？")
        self.assertIsNotNone(solved)
        self.assertEqual(solved[0], "438")
        self.assertLess(restored.serialized_bytes(), 10_000)


if __name__ == "__main__":
    unittest.main()
