from __future__ import annotations

import re
from dataclasses import dataclass, field


_SENTENCE_SPLIT = re.compile(r"[。.!！]+")


def _clean(value: str) -> str:
    return re.sub(r"\s+", "", value).strip("、,。.!！?？")


@dataclass(frozen=True, slots=True)
class ReadingAnswer:
    answer: str
    proof: tuple[str, ...]
    confidence: float = 1.0


@dataclass
class StoryState:
    events: list[tuple[str, str, str, str]] = field(default_factory=list)
    transfers: list[tuple[str, str, str]] = field(default_factory=list)
    locations: dict[str, str] = field(default_factory=dict)
    attributes: dict[tuple[str, str], str] = field(default_factory=dict)
    before: set[tuple[str, str]] = field(default_factory=set)
    causes: dict[str, str] = field(default_factory=dict)
    raw_sentences: list[str] = field(default_factory=list)


class JapaneseReadingReasoner:
    """Deterministic proof-producing reasoner for compact Japanese prose.

    It extracts event, location, transfer, comparison and causal relations from
    previously unseen names and values. Answers are returned only when a proof
    can be reconstructed from the passage; otherwise the reasoner abstains.
    """

    QUERY_MARKERS = ("\n問:", "\n質問:", " 問:", " 質問:")

    def can_handle(self, text: str) -> bool:
        return "本文:" in text and ("問:" in text or "質問:" in text)

    def solve(self, text: str) -> ReadingAnswer | None:
        passage, question = self._split(text)
        if not passage or not question:
            return None
        state = self._parse_passage(passage)
        return self._answer(state, _clean(question))

    def _split(self, text: str) -> tuple[str, str]:
        body = text.split("本文:", 1)[1]
        positions = [(body.find(marker), marker) for marker in self.QUERY_MARKERS if body.find(marker) >= 0]
        if not positions:
            match = re.search(r"(?:問|質問):", body)
            if not match:
                return "", ""
            return body[: match.start()], body[match.end() :]
        index, marker = min(positions, key=lambda item: item[0])
        return body[:index], body[index + len(marker) :]

    def _parse_passage(self, passage: str) -> StoryState:
        state = StoryState()
        for raw in _SENTENCE_SPLIT.split(passage):
            sentence = _clean(raw)
            if not sentence:
                continue
            state.raw_sentences.append(sentence)
            self._parse_sentence(state, sentence)
        self._close_order(state)
        return state

    def _parse_sentence(self, state: StoryState, sentence: str) -> None:
        causal = re.fullmatch(r"(.+?)(?:ので|ため)、?(.+)", sentence)
        if causal:
            cause, effect = _clean(causal.group(1)), _clean(causal.group(2))
            state.causes[effect] = cause
            self._parse_sentence(state, effect)
            return

        comparison = re.fullmatch(r"(.+?)は(.+?)より(先|後)に(.+?)(?:した|着いた|到着した)", sentence)
        if comparison:
            subject, other, relation, action = map(_clean, comparison.groups())
            if relation == "先":
                state.before.add((subject, other))
            else:
                state.before.add((other, subject))
            state.events.append((subject, "比較", other, action))
            return

        transfer = re.fullmatch(r"(.+?)は(.+?)に(.+?)を(渡した|貸した|贈った|返した)", sentence)
        if transfer:
            subject, receiver, obj, verb = map(_clean, transfer.groups())
            state.transfers.append((subject, receiver, obj))
            state.events.append((subject, verb, obj, receiver))
            return

        placement = re.fullmatch(r"(.+?)は(.+?)を(.+?)に(置いた|入れた|移した|隠した)", sentence)
        if placement:
            subject, obj, location, verb = map(_clean, placement.groups())
            state.locations[obj] = location
            state.events.append((subject, verb, obj, location))
            return

        movement = re.fullmatch(r"(.+?)は(.+?)(?:へ|に)(行った|向かった|到着した|戻った|移動した)", sentence)
        if movement:
            subject, location, verb = map(_clean, movement.groups())
            state.locations[subject] = location
            state.events.append((subject, verb, location, ""))
            return

        state_change = re.fullmatch(r"(.+?)は(.+?)(?:になった|だった|である)", sentence)
        if state_change:
            subject, value = map(_clean, state_change.groups())
            state.attributes[(subject, "状態")] = value
            state.events.append((subject, "状態", value, ""))
            return

        transitive = re.fullmatch(r"(.+?)は(.+?)を(.+?)(?:した|読んだ|食べた|買った|選んだ|作った|調べた|訪れた)", sentence)
        if transitive:
            subject, obj, verb = map(_clean, transitive.groups())
            state.events.append((subject, verb, obj, ""))
            return

    def _close_order(self, state: StoryState) -> None:
        changed = True
        while changed:
            changed = False
            additions: set[tuple[str, str]] = set()
            for left, middle in state.before:
                for middle2, right in state.before:
                    if middle == middle2 and left != right and (left, right) not in state.before:
                        additions.add((left, right))
            if additions:
                state.before.update(additions)
                changed = True

    def _answer(self, state: StoryState, question: str) -> ReadingAnswer | None:
        match = re.fullmatch(r"(.+?)はどこ(?:へ|に)(?:行った|向かった|到着した|移動した)?", question)
        if match:
            entity = _clean(match.group(1))
            location = state.locations.get(entity)
            if location:
                return ReadingAnswer(f"{location}です。", (f"{entity}の場所={location}",))

        match = re.fullmatch(r"(.+?)はどこに(?:置かれた|入れられた|移された|隠された)?", question)
        if match:
            obj = _clean(match.group(1))
            location = state.locations.get(obj)
            if location:
                return ReadingAnswer(f"{location}です。", (f"{obj}の場所={location}",))

        match = re.fullmatch(r"誰が(.+?)を(?:渡した|貸した|贈った|返した)", question)
        if match:
            obj = _clean(match.group(1))
            for giver, receiver, candidate in reversed(state.transfers):
                if candidate == obj:
                    return ReadingAnswer(f"{giver}です。", (f"{giver}→{receiver}:{obj}",))

        match = re.fullmatch(r"(.+?)は誰に(.+?)を(?:渡した|貸した|贈った|返した)", question)
        if match:
            giver, obj = map(_clean, match.groups())
            for candidate_giver, receiver, candidate_obj in reversed(state.transfers):
                if candidate_giver == giver and candidate_obj == obj:
                    return ReadingAnswer(f"{receiver}です。", (f"{giver}→{receiver}:{obj}",))

        match = re.fullmatch(r"誰が(.+?)を(.+)", question)
        if match:
            obj, verb = map(_clean, match.groups())
            for subject, candidate_verb, candidate_obj, _ in reversed(state.events):
                if candidate_obj == obj and self._verb_matches(candidate_verb, verb):
                    return ReadingAnswer(f"{subject}です。", (f"{subject}:{candidate_verb}:{obj}",))

        if question in {"誰が最初だった", "誰が先だった", "最初に到着したのは誰"}:
            nodes = {value for pair in state.before for value in pair}
            candidates = [node for node in nodes if not any(other != node and (other, node) in state.before for other in nodes)]
            if len(candidates) == 1:
                winner = candidates[0]
                return ReadingAnswer(f"{winner}です。", tuple(f"{a}<{b}" for a, b in sorted(state.before)))

        match = re.fullmatch(r"(.+?)と(.+?)ではどちらが先", question)
        if match:
            left, right = map(_clean, match.groups())
            if (left, right) in state.before:
                return ReadingAnswer(f"{left}です。", (f"{left}<{right}",))
            if (right, left) in state.before:
                return ReadingAnswer(f"{right}です。", (f"{right}<{left}",))

        match = re.fullmatch(r"なぜ(.+)", question)
        if match:
            target = _clean(match.group(1))
            for effect, cause in state.causes.items():
                if target == effect or target in effect or effect in target:
                    return ReadingAnswer(f"{cause}からです。", (f"{cause}→{effect}",))

        match = re.fullmatch(r"(.+?)の最初の行動は何", question)
        if match:
            subject = _clean(match.group(1))
            for event_subject, verb, obj, destination in state.events:
                if event_subject == subject:
                    detail = obj if not destination else f"{obj}・{destination}"
                    return ReadingAnswer(f"{detail}を{verb}ことです。", (f"最初:{subject}:{verb}:{detail}",))

        match = re.fullmatch(r"(.+?)の最後の行動は何", question)
        if match:
            subject = _clean(match.group(1))
            for event_subject, verb, obj, destination in reversed(state.events):
                if event_subject == subject:
                    detail = obj if not destination else f"{obj}・{destination}"
                    return ReadingAnswer(f"{detail}を{verb}ことです。", (f"最後:{subject}:{verb}:{detail}",))

        return None

    @staticmethod
    def _verb_matches(stored: str, queried: str) -> bool:
        stem = queried.removesuffix("した").removesuffix("のは誰")
        return stored == queried or stored in queried or stem in stored or stored in stem
