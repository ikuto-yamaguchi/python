from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping


@dataclass(frozen=True)
class MasteryDomain:
    domain_id: str
    description: str
    required_accuracy: float = 1.0
    minimum_items: int = 1


REQUIRED_DOMAINS = (
    MasteryDomain("common_test_main", "大学入学共通テスト本試験の全教科・全科目・全設問"),
    MasteryDomain("common_test_makeup", "大学入学共通テスト追試験・再試験の全教科・全科目・全設問"),
    MasteryDomain("national_university_second_stage", "国公立大学二次試験の全大学・全学部・全科目"),
    MasteryDomain("private_university", "私立大学一般選抜の全大学・全学部・全方式・全科目"),
    MasteryDomain("mathematical_proof", "数学の記述解答・証明・採点基準を満たす途中式"),
    MasteryDomain("japanese_long_form", "現代文・古文・漢文の読解、記述、要約、論述"),
    MasteryDomain("science_constructed_response", "物理・化学・生物・地学の計算、説明、実験考察"),
    MasteryDomain("social_studies_constructed_response", "日本史・世界史・地理・公民の資料読解と論述"),
    MasteryDomain("foreign_language_reading", "英語その他外国語の読解・文法・語彙"),
    MasteryDomain("foreign_language_listening", "英語その他外国語のリスニング"),
    MasteryDomain("foreign_language_writing", "英作文・和文英訳・自由英作文"),
    MasteryDomain("information", "情報Iおよび各大学の情報系入試問題"),
    MasteryDomain("essay", "小論文・課題論文・資料型論述"),
    MasteryDomain("interview", "個人面接・集団面接・口頭試問"),
    MasteryDomain("communication", "自然な日本語での長時間・多ターン会話、説明、質問理解、訂正"),
    MasteryDomain("multimodal", "図表、数式、縦書き、画像、音声を含む問題理解"),
)


@dataclass(frozen=True)
class DomainResult:
    correct: int
    total: int
    independently_held_out: bool
    exact_scoring: bool

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


class UniversityExamMasteryContract:
    """Completion contract for the requested intelligence target.

    This is deliberately stricter than ordinary benchmark passing.  A domain
    with no evaluated items, any error, any inspected test target, or any
    approximate-only score keeps the system unfinished.
    """

    @staticmethod
    def evaluate(results: Mapping[str, DomainResult]) -> dict[str, object]:
        checks: dict[str, bool] = {}
        rows: dict[str, object] = {}
        for domain in REQUIRED_DOMAINS:
            result = results.get(domain.domain_id)
            if result is None:
                checks[domain.domain_id] = False
                rows[domain.domain_id] = {
                    "description": domain.description,
                    "evaluated": False,
                    "required_accuracy": domain.required_accuracy,
                }
                continue
            passed = (
                result.total >= domain.minimum_items
                and result.correct == result.total
                and result.accuracy >= domain.required_accuracy
                and result.independently_held_out
                and result.exact_scoring
            )
            checks[domain.domain_id] = passed
            rows[domain.domain_id] = {
                "description": domain.description,
                "evaluated": True,
                "result": asdict(result),
                "accuracy": result.accuracy,
                "required_accuracy": domain.required_accuracy,
                "passed": passed,
            }
        return {
            "target": (
                "全ての大学入試で満点を取り、記述・論述・面接・自由会話を含めて"
                "自然に遂行できる1GB以下の非Transformer知能"
            ),
            "domains": rows,
            "checks": checks,
            "university_exam_mastery_passed": all(checks.values()),
            "highschool_level_passed": all(checks.values()),
            "completion_allowed": all(checks.values()),
        }
