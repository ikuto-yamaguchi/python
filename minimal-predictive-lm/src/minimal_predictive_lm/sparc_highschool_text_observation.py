from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import re
from typing import Iterable

from .sparc_highschool_general import Edit, Program, SparseGeneralLearner, World, _clean


_NUMBER = re.compile(r"-?\d+")
_OBS_SLOT = re.compile(r"<(S|N)>")


@dataclass(frozen=True)
class ObservationResult:
    world: World
    accepted: int
    abstained: int
    mechanisms: tuple[str, ...]


class TextObservationLearner(SparseGeneralLearner):
    """Extends the integrated learner with text-only world induction.

    Public teaching methods receive Japanese strings only. Opaque relation IDs and
    compact ``World`` objects are proposed internally from repeated observations.
    The inherited latent-program executor remains the single downstream mechanism.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fact_program_ids: set[str] = set()
        self.numeric_observation_patterns: dict[str, set[str]] = {}
        self.next_text_relation = 0
        self.next_numeric_relation = 0
        self.text_observation_groups = 0
        self.text_worlds_built = 0
        self.text_observation_abstentions = 0
        self.entity_pair_hypotheses = 0
        self.typed_numeric_overrides = 0

    @staticmethod
    def _substrings(text: str, lo: int = 1, hi: int = 24) -> set[str]:
        text = _clean(text)
        return {
            text[index:index + width]
            for width in range(lo, min(hi, len(text)) + 1)
            for index in range(max(0, len(text) - width + 1))
        }

    @staticmethod
    def _position_score(candidate: str, rows: tuple[str, ...]) -> float:
        positions = [
            row.find(candidate) / max(1, len(row) - len(candidate))
            for row in rows
        ]
        mean = sum(positions) / len(positions)
        variance = sum((position - mean) ** 2 for position in positions) / len(positions)
        return len(candidate) ** 2 + 3.0 * variance + 0.2 * len(set(candidate))

    def _discover_pair(self, sentences: Iterable[str]) -> tuple[str, str]:
        rows = tuple(_clean(sentence) for sentence in sentences)
        if len(rows) < 3 or any(not row for row in rows):
            raise ValueError("at least three non-empty paraphrases are required")
        common = set.intersection(*(self._substrings(row) for row in rows))
        scored: list[tuple[float, str]] = []
        for candidate in common:
            if any(row.count(candidate) != 1 for row in rows):
                continue
            scored.append((self._position_score(candidate, rows), candidate))
        scored.sort(key=lambda item: (-item[0], -len(item[1]), item[1]))
        self.entity_pair_hypotheses += len(scored[:80])
        best: tuple[float, str, str] | None = None
        for (left_score, left), (right_score, right) in combinations(scored[:80], 2):
            if left in right or right in left:
                continue
            valid = True
            for row in rows:
                left_index = row.find(left)
                right_index = row.find(right)
                if left_index < 0 or right_index < 0:
                    valid = False
                    break
                if not (
                    left_index + len(left) <= right_index
                    or right_index + len(right) <= left_index
                ):
                    valid = False
                    break
            if not valid:
                continue
            candidate = (left_score + right_score, left, right)
            if best is None or candidate > best:
                best = candidate
        if best is None:
            raise ValueError("could not induce two recurring observation values")
        _, left, right = best
        first = rows[0]
        return (left, right) if first.find(left) <= first.find(right) else (right, left)

    def _discover_numeric_pair(self, sentences: Iterable[str]) -> tuple[str, str]:
        rows = tuple(_clean(sentence) for sentence in sentences)
        if len(rows) < 3 or any(not row for row in rows):
            raise ValueError("at least three non-empty paraphrases are required")
        shared_numbers = set.intersection(*(set(_NUMBER.findall(row)) for row in rows))
        shared_numbers = {
            value for value in shared_numbers
            if all(row.count(value) == 1 for row in rows)
        }
        if len(shared_numbers) != 1:
            raise ValueError("numeric paraphrases must share exactly one integer value")
        number = next(iter(shared_numbers))
        common = set.intersection(*(self._substrings(row) for row in rows))
        candidates: list[tuple[float, str]] = []
        for candidate in common:
            if _NUMBER.fullmatch(candidate) or candidate in number or number in candidate:
                continue
            if any(row.count(candidate) != 1 for row in rows):
                continue
            valid = True
            for row in rows:
                entity_index = row.find(candidate)
                number_index = row.find(number)
                if not (
                    entity_index + len(candidate) <= number_index
                    or number_index + len(number) <= entity_index
                ):
                    valid = False
                    break
            if valid:
                candidates.append((self._position_score(candidate, rows), candidate))
        candidates.sort(key=lambda item: (-item[0], -len(item[1]), item[1]))
        self.entity_pair_hypotheses += len(candidates[:80])
        if not candidates:
            raise ValueError("could not induce the numeric observation entity")
        return candidates[0][1], number

    @staticmethod
    def _abstract_pair(text: str, first: str, second: str, markers=("<V0>", "<V1>")) -> str:
        text = _clean(text)
        hits = sorted(
            [(text.find(first), len(first), markers[0]), (text.find(second), len(second), markers[1])],
            key=lambda item: item[0],
        )
        if any(index < 0 for index, _length, _marker in hits):
            raise ValueError("induced value is missing from a paraphrase")
        output: list[str] = []
        cursor = 0
        for index, length, marker in hits:
            output.append(text[cursor:index])
            output.append(marker)
            cursor = index + length
        output.append(text[cursor:])
        return "".join(output)

    def learn_fact_observation_group(self, sentences: Iterable[str]) -> str:
        rows = tuple(sentences)
        subject, obj = self._discover_pair(rows)
        relation = f"TR{self.next_text_relation}"
        self.next_text_relation += 1
        edit = Edit("add_fact", relation, 0, 1)
        signature = self._signature((edit,))
        program_id = f"P{self.next_program}"
        self.next_program += 1
        patterns = {self._abstract_pair(row, subject, obj) for row in rows}
        self.programs[program_id] = Program(program_id, signature, (edit,), patterns)
        self.fact_program_ids.add(program_id)
        self.training_episodes += 1
        self.text_observation_groups += 1
        return relation

    @staticmethod
    def _compile_numeric_observation(pattern: str) -> re.Pattern[str]:
        parts = re.split(r"(<S>|<N>)", pattern)
        output = ""
        seen: set[str] = set()
        for part in parts:
            match = _OBS_SLOT.fullmatch(part)
            if match:
                name = match.group(1)
                if name in seen:
                    output += rf"(?P={name})"
                elif name == "N":
                    output += r"(?P<N>-?\d+)"
                    seen.add(name)
                else:
                    output += r"(?P<S>.+?)"
                    seen.add(name)
            else:
                output += re.escape(part)
        return re.compile("^" + output + "$")

    def learn_numeric_observation_group(self, sentences: Iterable[str]) -> str:
        rows = tuple(sentences)
        subject, number = self._discover_numeric_pair(rows)
        relation = f"NR{self.next_numeric_relation}"
        self.next_numeric_relation += 1
        patterns = {
            self._abstract_pair(row, subject, number, ("<S>", "<N>"))
            for row in rows
        }
        self.numeric_observation_patterns[relation] = patterns
        self.text_observation_groups += 1
        return relation

    def _observe_fact(self, sentence: str):
        normalized = _clean(sentence)
        candidates = []
        reads = 0
        for program_id in sorted(self.fact_program_ids):
            program = self.programs[program_id]
            edit = program.edits[0]
            for pattern in program.patterns:
                reads += len(pattern)
                match = self._compile(pattern).fullmatch(normalized)
                if not match:
                    continue
                subject = match.groupdict().get("V0", "")
                obj = match.groupdict().get("V1", "")
                if (
                    subject
                    and obj
                    and subject != obj
                    and not _NUMBER.fullmatch(subject)
                    and not _NUMBER.fullmatch(obj)
                ):
                    specificity = len(pattern.replace("<V0>", "").replace("<V1>", ""))
                    candidates.append((specificity, edit.relation, subject, obj))
        candidates.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
        self.last_feature_reads += reads
        if not candidates:
            return None
        if len(candidates) > 1 and candidates[0][0] == candidates[1][0] and candidates[0][1:] != candidates[1][1:]:
            return None
        _specificity, relation, subject, obj = candidates[0]
        return subject, relation, obj

    def _observe_number(self, sentence: str):
        normalized = _clean(sentence)
        candidates = []
        reads = 0
        for relation, patterns in self.numeric_observation_patterns.items():
            for pattern in patterns:
                reads += len(pattern)
                match = self._compile_numeric_observation(pattern).fullmatch(normalized)
                if not match:
                    continue
                subject = match.group("S")
                value = int(match.group("N"))
                specificity = len(pattern.replace("<S>", "").replace("<N>", ""))
                candidates.append((specificity, relation, subject, value))
        candidates.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
        self.last_feature_reads += reads
        if not candidates:
            return None
        if len(candidates) > 1 and candidates[0][0] == candidates[1][0] and candidates[0][1:] != candidates[1][1:]:
            return None
        _specificity, relation, subject, value = candidates[0]
        return subject, relation, value

    def observe_world(self, sentences: Iterable[str]) -> ObservationResult:
        facts: set[tuple[str, str, str]] = set()
        numbers: dict[tuple[str, str], int] = {}
        accepted = 0
        abstained = 0
        mechanisms: list[str] = []
        self.last_feature_reads = 0
        for sentence in sentences:
            fact = self._observe_fact(sentence)
            number = self._observe_number(sentence)
            if number is not None:
                subject, relation, value = number
                numbers[(subject, relation)] = value
                accepted += 1
                if fact is not None:
                    self.typed_numeric_overrides += 1
                    mechanisms.append("typed-numeric-observation")
                else:
                    mechanisms.append("induced-numeric-observation")
            elif fact is not None:
                facts.add(fact)
                accepted += 1
                mechanisms.append("induced-fact-observation")
            else:
                abstained += 1
                mechanisms.append("abstain-observation")
        self.text_worlds_built += 1
        self.text_observation_abstentions += abstained
        return ObservationResult(World.from_parts(facts, numbers), accepted, abstained, tuple(mechanisms))

    def teach_event_from_text(
        self,
        event_text: str,
        before_observations: Iterable[str],
        after_observations: Iterable[str],
    ) -> str:
        before = self.observe_world(before_observations)
        after = self.observe_world(after_observations)
        if before.abstained or after.abstained or not (before.accepted and after.accepted):
            raise ValueError("all transition observations must be grounded by induced schemas")
        return self.teach(event_text, before.world, after.world)

    def report(self):
        result = super().report()
        result.update({
            "text_observation_groups": self.text_observation_groups,
            "text_worlds_built": self.text_worlds_built,
            "text_observation_abstentions": self.text_observation_abstentions,
            "entity_pair_hypotheses": self.entity_pair_hypotheses,
            "fact_observation_programs": len(self.fact_program_ids),
            "numeric_observation_relations": len(self.numeric_observation_patterns),
            "typed_numeric_overrides": self.typed_numeric_overrides,
            "relation_ids_supplied_by_caller": False,
            "grounded_worlds_supplied_by_caller": False,
            "text_only_transition_teaching": True,
        })
        return result
