from __future__ import annotations

import re
from dataclasses import dataclass, field


def _clean(text: str) -> str:
    return re.sub(r"\s+", "", text).strip("。.!！?？")


@dataclass(frozen=True, slots=True)
class ConversationReply:
    answer: str
    mechanism: str
    confidence: float = 1.0


@dataclass
class ConversationState:
    facts: dict[str, str] = field(default_factory=dict)
    likes: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    history: list[tuple[str, str]] = field(default_factory=list)
    max_history: int = 256

    def append(self, role: str, text: str) -> None:
        self.history.append((role, text))
        if len(self.history) > self.max_history:
            del self.history[: len(self.history) - self.max_history]

    def to_dict(self) -> dict:
        return {
            "facts": self.facts,
            "likes": self.likes,
            "dislikes": self.dislikes,
            "goals": self.goals,
            "history": [list(item) for item in self.history],
            "max_history": self.max_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationState":
        return cls(
            facts={str(k): str(v) for k, v in data.get("facts", {}).items()},
            likes=[str(value) for value in data.get("likes", [])],
            dislikes=[str(value) for value in data.get("dislikes", [])],
            goals=[str(value) for value in data.get("goals", [])],
            history=[(str(role), str(text)) for role, text in data.get("history", [])],
            max_history=int(data.get("max_history", 256)),
        )


class ConsistentConversationEngine:
    """Bounded stateful dialogue with explicit correction semantics.

    The engine prioritizes the newest user correction, keeps positive and
    negative preferences disjoint, and answers only from traceable state.
    """

    def __init__(self, state: ConversationState | None = None) -> None:
        self.state = state or ConversationState()

    def respond(self, text: str) -> ConversationReply | None:
        raw = text.strip()
        compact = _clean(raw)
        if not compact:
            return None
        reply = self._query(compact)
        if reply is None:
            reply = self._learn(compact)
        if reply is not None:
            self.state.append("user", raw)
            self.state.append("assistant", reply.answer)
        return reply

    def _learn(self, text: str) -> ConversationReply | None:
        correction = re.fullmatch(r"(?:違う|訂正)[、,:：]*(.+?)ではなく(.+)", text)
        if correction:
            old, new = map(_clean, correction.groups())
            changed = self._replace_value(old, new)
            if changed:
                return ConversationReply(f"訂正しました。{new}として覚えます。", "conversation-correction")
            self.state.facts["最新訂正"] = new
            return ConversationReply(f"訂正内容を{new}として覚えました。", "conversation-correction")

        patterns = [
            (r"私の名前は(.+?)(?:です|だ)?", "名前"),
            (r"私は(.+?)に住んで(?:います|いる)", "居住地"),
            (r"私の誕生日は(.+?)(?:です|だ)?", "誕生日"),
            (r"私の仕事は(.+?)(?:です|だ)?", "仕事"),
        ]
        for pattern, key in patterns:
            match = re.fullmatch(pattern, text)
            if match:
                value = _clean(match.group(1))
                self.state.facts[key] = value
                return ConversationReply(f"{key}は{value}ですね。覚えました。", "conversation-fact-learning")

        like = re.fullmatch(r"私は(.+?)が好き(?:です)?", text)
        if like:
            value = _clean(like.group(1))
            self._add_unique(self.state.likes, value)
            self._remove(self.state.dislikes, value)
            return ConversationReply(f"{value}が好きなのですね。覚えました。", "conversation-preference-learning")

        dislike = re.fullmatch(r"私は(.+?)が嫌い(?:です)?", text)
        if dislike:
            value = _clean(dislike.group(1))
            self._add_unique(self.state.dislikes, value)
            self._remove(self.state.likes, value)
            return ConversationReply(f"{value}が苦手なのですね。覚えました。", "conversation-preference-learning")

        goal = re.fullmatch(r"(?:私の)?目標は(.+?)(?:です|だ)?", text)
        if goal:
            value = _clean(goal.group(1))
            self._add_unique(self.state.goals, value)
            return ConversationReply(f"目標は{value}ですね。覚えました。", "conversation-goal-learning")

        return None

    def _query(self, text: str) -> ConversationReply | None:
        query_map = {
            "私の名前は": "名前",
            "私の居住地は": "居住地",
            "私はどこに住んでいる": "居住地",
            "私の誕生日は": "誕生日",
            "私の仕事は": "仕事",
        }
        for query, key in query_map.items():
            if text == query:
                value = self.state.facts.get(key)
                if value is None:
                    return ConversationReply(f"{key}はまだ聞いていません。", "conversation-calibrated-unknown", 0.0)
                return ConversationReply(f"{value}です。", "conversation-state-recall")

        if text in {"私が好きなのは", "私の好きなものは"}:
            if not self.state.likes:
                return ConversationReply("好きなものはまだ聞いていません。", "conversation-calibrated-unknown", 0.0)
            return ConversationReply("、".join(self.state.likes) + "です。", "conversation-state-recall")

        if text in {"私が嫌いなのは", "私の嫌いなものは"}:
            if not self.state.dislikes:
                return ConversationReply("嫌いなものはまだ聞いていません。", "conversation-calibrated-unknown", 0.0)
            return ConversationReply("、".join(self.state.dislikes) + "です。", "conversation-state-recall")

        if text in {"私の目標は", "目標を覚えている"}:
            if not self.state.goals:
                return ConversationReply("目標はまだ聞いていません。", "conversation-calibrated-unknown", 0.0)
            return ConversationReply("、".join(self.state.goals) + "です。", "conversation-state-recall")

        if text in {"直前に私が言ったことは", "さっき私が言ったことは"}:
            for role, value in reversed(self.state.history):
                if role == "user":
                    return ConversationReply(value, "conversation-history-recall")
            return ConversationReply("まだ会話履歴がありません。", "conversation-calibrated-unknown", 0.0)

        if text == "私について覚えていることは":
            parts = [f"{key}は{value}" for key, value in self.state.facts.items() if key != "最新訂正"]
            if self.state.likes:
                parts.append("好きなものは" + "、".join(self.state.likes))
            if self.state.dislikes:
                parts.append("苦手なものは" + "、".join(self.state.dislikes))
            if self.state.goals:
                parts.append("目標は" + "、".join(self.state.goals))
            if not parts:
                return ConversationReply("まだあなたについて確実に覚えている情報はありません。", "conversation-calibrated-unknown", 0.0)
            return ConversationReply("。".join(parts) + "。", "conversation-state-summary")

        return None

    def _replace_value(self, old: str, new: str) -> bool:
        changed = False
        for key, value in list(self.state.facts.items()):
            if value == old:
                self.state.facts[key] = new
                changed = True
        for collection in (self.state.likes, self.state.dislikes, self.state.goals):
            for index, value in enumerate(collection):
                if value == old:
                    collection[index] = new
                    changed = True
        self._deduplicate_state()
        return changed

    def _deduplicate_state(self) -> None:
        self.state.likes = list(dict.fromkeys(self.state.likes))
        self.state.dislikes = [value for value in dict.fromkeys(self.state.dislikes) if value not in self.state.likes]
        self.state.goals = list(dict.fromkeys(self.state.goals))

    @staticmethod
    def _add_unique(values: list[str], value: str) -> None:
        if value not in values:
            values.append(value)

    @staticmethod
    def _remove(values: list[str], value: str) -> None:
        while value in values:
            values.remove(value)
