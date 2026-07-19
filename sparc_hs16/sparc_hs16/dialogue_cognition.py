from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from typing import Iterable, Sequence


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text).strip("。.!！?？")


def _stable_choice(options: Sequence[str], seed: str) -> str:
    digest = hashlib.blake2b(seed.encode("utf-8"), digest_size=4).digest()
    return options[int.from_bytes(digest, "little") % len(options)]


@dataclass(frozen=True, slots=True)
class DialogueReply:
    text: str
    act: str
    confidence: float
    evidence: tuple[str, ...] = ()


@dataclass(slots=True)
class TopicNode:
    name: str
    salience: float = 1.0
    mentions: int = 1
    last_turn: int = 0
    propositions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DialogueState:
    facts: dict[str, str] = field(default_factory=dict)
    likes: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    topics: dict[str, TopicNode] = field(default_factory=dict)
    topic_stack: list[str] = field(default_factory=list)
    current_topic: str | None = None
    last_user_proposition: str | None = None
    last_assistant_question: str | None = None
    affect: str = "neutral"
    history: deque[tuple[str, str]] = field(default_factory=lambda: deque(maxlen=256))
    turn: int = 0

    def append(self, role: str, text: str) -> None:
        self.history.append((role, text))

    def to_dict(self) -> dict:
        return {
            "facts": dict(self.facts),
            "likes": list(self.likes),
            "dislikes": list(self.dislikes),
            "goals": list(self.goals),
            "topics": {key: asdict(value) for key, value in self.topics.items()},
            "topic_stack": list(self.topic_stack),
            "current_topic": self.current_topic,
            "last_user_proposition": self.last_user_proposition,
            "last_assistant_question": self.last_assistant_question,
            "affect": self.affect,
            "history": list(self.history),
            "turn": self.turn,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DialogueState":
        state = cls()
        state.facts = {str(k): str(v) for k, v in data.get("facts", {}).items()}
        state.likes = [str(v) for v in data.get("likes", [])]
        state.dislikes = [str(v) for v in data.get("dislikes", [])]
        state.goals = [str(v) for v in data.get("goals", [])]
        state.topics = {
            str(key): TopicNode(
                name=str(row.get("name", key)),
                salience=float(row.get("salience", 1.0)),
                mentions=int(row.get("mentions", 1)),
                last_turn=int(row.get("last_turn", 0)),
                propositions=[str(v) for v in row.get("propositions", [])],
            )
            for key, row in data.get("topics", {}).items()
        }
        state.topic_stack = [str(v) for v in data.get("topic_stack", [])]
        state.current_topic = data.get("current_topic")
        state.last_user_proposition = data.get("last_user_proposition")
        state.last_assistant_question = data.get("last_assistant_question")
        state.affect = str(data.get("affect", "neutral"))
        state.history = deque(
            ((str(role), str(text)) for role, text in data.get("history", [])),
            maxlen=256,
        )
        state.turn = int(data.get("turn", 0))
        return state


class DialogueActPolicy:
    ACTS = ("acknowledge", "empathize", "clarify", "recall", "correct", "explore", "advise", "greet")

    def __init__(self) -> None:
        self.counts: dict[str, Counter[str]] = {}
        self.priors: Counter[str] = Counter()

    @staticmethod
    def features(text: str, state: DialogueState) -> tuple[str, ...]:
        compact = _compact(text)
        features = []
        if re.search(r"疲れ|つら|しんど|悲し|不安|怖|怒|むかつ|落ち込", compact):
            features.append("negative-affect")
        if re.search(r"嬉し|楽し|よかった|最高|うまくいった", compact):
            features.append("positive-affect")
        if re.search(r"違う|訂正|じゃなくて|ではなく", compact):
            features.append("correction")
        if "?" in text or "？" in text or re.search(r"覚えて|何だっけ|どこ|誰|どう思う|どうすれば|なぜ", compact):
            features.append("question")
        if re.search(r"それ|その話|さっき|あれ|こっち", compact):
            features.append("anaphora")
        if re.search(r"どうすれば|どうしたら|アドバイス|助けて", compact):
            features.append("advice-request")
        if re.search(r"こんにちは|こんばんは|おはよう|やあ|はじめまして", compact):
            features.append("greeting")
        if state.current_topic:
            features.append("has-topic")
        if state.last_assistant_question:
            features.append("continuation")
        return tuple(sorted(set(features))) or ("statement",)

    def train(self, demonstrations: Iterable[tuple[str, str]]) -> None:
        state = DialogueState()
        for text, act in demonstrations:
            self.priors[act] += 1
            for feature in self.features(text, state):
                self.counts.setdefault(feature, Counter())[act] += 1

    def choose(self, text: str, state: DialogueState) -> str:
        features = self.features(text, state)
        hard = {
            "correction": "correct",
            "greeting": "greet",
            "advice-request": "advise",
            "negative-affect": "empathize",
        }
        for feature, act in hard.items():
            if feature in features:
                return act
        if "question" in features:
            return "recall" if re.search(r"覚えて|何だっけ|私の名前|好きな|嫌いな|目標|どこに住", _compact(text)) else "explore"
        if "anaphora" in features and not state.current_topic:
            return "clarify"
        return "acknowledge"


class ConversationalCognitiveEngine:
    NEGATIVE = ("疲れ", "つら", "しんど", "悲し", "不安", "怖", "怒", "むかつ", "落ち込")
    POSITIVE = ("嬉し", "楽し", "よかった", "最高", "うまくいった")
    TOPIC_HINTS = (
        "仕事", "上司", "旅行", "長野", "彼女", "妹", "家族", "ランニング", "マラソン",
        "AI", "モデル", "研究", "ゲーム", "食事", "体調", "病院", "お金", "投資",
    )

    def __init__(self, state: DialogueState | None = None) -> None:
        self.state = state or DialogueState()
        self.policy = DialogueActPolicy()
        self.policy.train((
            ("今日は仕事で疲れた", "empathize"),
            ("ちょっと不安なんだ", "empathize"),
            ("私の名前を覚えてる？", "recall"),
            ("さっきの話は何だっけ？", "recall"),
            ("それってどういうこと？", "explore"),
            ("どうすればいいと思う？", "advise"),
            ("彼女じゃなくて妹だよ", "correct"),
            ("こんにちは", "greet"),
            ("今日は公園を走った", "acknowledge"),
        ))

    def start_new_session(self) -> None:
        self.state.topics.clear()
        self.state.topic_stack.clear()
        self.state.current_topic = None
        self.state.last_user_proposition = None
        self.state.last_assistant_question = None
        self.state.affect = "neutral"
        self.state.history.clear()

    def respond(self, text: str) -> DialogueReply:
        raw = _clean(text)
        self.state.turn += 1
        for node in self.state.topics.values():
            node.salience *= 0.92
        self.state.append("user", raw)

        for handler in (self._learn_explicit, self._recall_query, self._apply_correction, self._topic_return):
            reply = handler(raw)
            if reply is not None:
                return self._finish(reply)

        compact = _compact(raw)
        if re.search(r"それ|あれ|その件|こういうとき", compact) and self.state.current_topic is None:
            return self._finish(DialogueReply("何を指しているか特定できなかった。話題を一言だけ教えて。", "clarify-reference", 0.0))

        self._update_affect(raw)
        topic = self._infer_topic(raw)
        if topic:
            self._activate_topic(topic, raw)
        elif self.state.current_topic:
            node = self.state.topics[self.state.current_topic]
            if raw not in node.propositions:
                node.propositions.append(raw)
                del node.propositions[:-12]
            self.state.last_user_proposition = raw

        act = self.policy.choose(raw, self.state)
        return self._finish(self._realize(raw, act, topic or self.state.current_topic))

    def _finish(self, reply: DialogueReply) -> DialogueReply:
        self.state.append("assistant", reply.text)
        self.state.last_assistant_question = reply.text if reply.text.endswith(("？", "?")) else None
        return reply

    def _activate_topic(self, topic: str, proposition: str) -> None:
        node = self.state.topics.get(topic)
        if node is None:
            node = TopicNode(topic, last_turn=self.state.turn)
            self.state.topics[topic] = node
        else:
            node.salience += 1.0
            node.mentions += 1
            node.last_turn = self.state.turn
        if proposition not in node.propositions:
            node.propositions.append(proposition)
            del node.propositions[:-12]
        if self.state.current_topic and self.state.current_topic != topic:
            self.state.topic_stack.append(self.state.current_topic)
            del self.state.topic_stack[:-16]
        self.state.current_topic = topic
        self.state.last_user_proposition = proposition

    def _infer_topic(self, text: str) -> str | None:
        compact = _compact(text)
        if re.search(r"旅行|行く予定|泊まる予定|観光", compact):
            return "旅行"
        matches: list[str] = []
        for hint in self.TOPIC_HINTS:
            if re.fullmatch(r"[ァ-ヶー]+", hint):
                if re.search(rf"(?<![ァ-ヶー]){re.escape(hint)}(?![ァ-ヶー])", compact):
                    matches.append(hint)
            elif hint.lower() in compact.lower():
                matches.append(hint)
        if matches:
            return max(matches, key=len)
        if self.state.current_topic and not re.search(r"そういえば|話は変わる|別の話|ところで", compact):
            return None
        nounish = re.findall(r"[一-龥ァ-ヶA-Za-z]{2,12}", compact)
        stop = {"今日は", "それは", "これは", "なんか", "ちょっと", "だけど", "だから", "について", "みたい", "どうして", "こういうとき"}
        candidates = [word for word in nounish if word not in stop]
        return candidates[0] if candidates else None

    def _update_affect(self, text: str) -> None:
        compact = _compact(text)
        if any(word in compact for word in self.NEGATIVE):
            self.state.affect = "negative"
        elif any(word in compact for word in self.POSITIVE):
            self.state.affect = "positive"
        else:
            self.state.affect = "neutral"

    def _learn_explicit(self, text: str) -> DialogueReply | None:
        compact = _compact(text)
        patterns = (
            (r"(?:私|僕)の名前は(.+?)(?:です|だ)?$", "名前"),
            (r"(?:私|僕)は(.+?)に住んで(?:います|いる)$", "居住地"),
            (r"(?:私|僕)の仕事は(.+?)(?:です|だ)?$", "仕事"),
        )
        for pattern, key in patterns:
            match = re.fullmatch(pattern, compact)
            if match:
                value = match.group(1)
                self.state.facts[key] = value
                self._activate_topic(key, text)
                return DialogueReply(f"うん、{key}は{value}なんだね。覚えておく。", "learn-fact", 1.0, (f"{key}={value}",))
        like = re.search(r"(?:私|僕)は?(.+?)が(?:好き|大好き)(?:です)?$", compact)
        if like:
            value = like.group(1)
            if value not in self.state.likes:
                self.state.likes.append(value)
            self.state.dislikes = [item for item in self.state.dislikes if item != value]
            self._activate_topic(value, text)
            return DialogueReply(f"{value}が好きなんだね。今後の話でもその好みを踏まえるよ。", "learn-preference", 1.0, (value,))
        dislike = re.search(r"(?:私|僕)は?(.+?)が(?:嫌い|苦手)(?:です)?$", compact)
        if dislike:
            value = dislike.group(1)
            if value not in self.state.dislikes:
                self.state.dislikes.append(value)
            self.state.likes = [item for item in self.state.likes if item != value]
            self._activate_topic(value, text)
            return DialogueReply(f"{value}は苦手なんだね。そこは勧めないように覚えておく。", "learn-preference", 1.0, (value,))
        goal = re.search(r"(?:私の|僕の)?目標は(.+?)(?:です|だ)?$", compact)
        if goal:
            value = goal.group(1)
            if value not in self.state.goals:
                self.state.goals.append(value)
            self._activate_topic(value, text)
            return DialogueReply(f"目標は「{value}」だね。覚えておく。", "learn-goal", 1.0, (value,))
        return None

    def _recall_query(self, text: str) -> DialogueReply | None:
        compact = _compact(text)
        if re.search(r"名前.*覚えて|私の名前|僕の名前", compact):
            value = self.state.facts.get("名前")
            return DialogueReply(f"{value}だよ。" if value else "まだ名前は聞いていないよ。", "recall", 1.0 if value else 0.0)
        if re.search(r"どこ.*住|居住地", compact):
            value = self.state.facts.get("居住地")
            return DialogueReply(f"{value}に住んでいると覚えているよ。" if value else "住んでいる場所はまだ聞いていないよ。", "recall", 1.0 if value else 0.0)
        if "誕生日" in compact:
            value = self.state.facts.get("誕生日")
            return DialogueReply(f"誕生日は{value}だよ。" if value else "誕生日はまだ聞いていないよ。", "recall", 1.0 if value else 0.0)
        if re.search(r"好き.*覚えて|好きなもの|好み", compact):
            if self.state.likes:
                return DialogueReply("好きなのは" + "、".join(self.state.likes) + "だよ。", "recall", 1.0, tuple(self.state.likes))
            return DialogueReply("好きなものはまだ聞いていないよ。", "recall", 0.0)
        if re.search(r"目標.*覚えて|私の目標|僕の目標", compact):
            if self.state.goals:
                return DialogueReply("目標は「" + "、".join(self.state.goals) + "」だよ。", "recall", 1.0, tuple(self.state.goals))
            return DialogueReply("目標はまだ聞いていないよ。", "recall", 0.0)
        if re.search(r"何の話|さっきの話.*何|直前.*何", compact):
            if self.state.current_topic:
                node = self.state.topics[self.state.current_topic]
                detail = node.propositions[-1] if node.propositions else self.state.current_topic
                return DialogueReply(f"{self.state.current_topic}の話だよ。直近では「{detail}」と言っていた。", "recall-topic", 1.0, (self.state.current_topic, detail))
            return DialogueReply("まだ続いている話題はないよ。", "recall-topic", 0.0)
        return None

    def _apply_correction(self, text: str) -> DialogueReply | None:
        compact = _compact(text)
        match = re.search(r"(.+?)(?:じゃなくて|ではなく)(.+?)(?:だよ|です|だった)?$", compact)
        if not match:
            return None
        old, new = match.group(1), match.group(2)
        changed = False
        for key, value in list(self.state.facts.items()):
            if old in value or value in old:
                self.state.facts[key] = new
                changed = True
        for collection in (self.state.likes, self.state.dislikes, self.state.goals):
            for index, value in enumerate(collection):
                if old in value or value in old:
                    collection[index] = new
                    changed = True
        if old in self.state.topics:
            node = self.state.topics.pop(old)
            node.name = new
            self.state.topics[new] = node
            if self.state.current_topic == old:
                self.state.current_topic = new
            changed = True
        if self.state.last_user_proposition and old in self.state.last_user_proposition:
            self.state.last_user_proposition = self.state.last_user_proposition.replace(old, new)
            changed = True
        if self.state.current_topic:
            node = self.state.topics[self.state.current_topic]
            if text not in node.propositions:
                node.propositions.append(text)
                del node.propositions[:-12]
            self.state.last_user_proposition = text
        else:
            self._activate_topic(new, text)
        return DialogueReply(f"了解。{old}ではなく{new}なんだね。前の情報は訂正しておく。", "correct", 1.0 if changed else 0.8, (old, new))

    def _topic_return(self, text: str) -> DialogueReply | None:
        compact = _compact(text)
        if not re.search(r"さっきの|その話|前の話|戻ろう|続き", compact):
            return None
        explicit = next((topic for topic in self.state.topics if topic in compact), None)
        topic = explicit or self.state.current_topic or (self.state.topic_stack[-1] if self.state.topic_stack else None)
        if topic is None:
            return DialogueReply("どの話を指しているか分からない。話題を一言だけ教えて。", "clarify-reference", 0.0)
        self.state.current_topic = topic
        node = self.state.topics[topic]
        detail = node.propositions[-1] if node.propositions else topic
        return DialogueReply(f"うん、{topic}の話に戻ろう。直近は「{detail}」というところだったね。続きはどうなった？", "resume-topic", 1.0, (topic, detail))

    def _realize(self, text: str, act: str, topic: str | None) -> DialogueReply:
        compact = _compact(text)
        if act == "greet":
            return DialogueReply(_stable_choice(("こんにちは。今日はどんな感じ？", "やあ。今日は何の話をしようか？"), text), "greet", 1.0)
        if act == "empathize":
            if "疲れ" in compact or "しんど" in compact:
                base = "それは疲れるね。"
            elif "不安" in compact or "怖" in compact:
                base = "それは不安になるよね。"
            elif "怒" in compact or "むかつ" in compact:
                base = "それは腹が立つのも無理ないよ。"
            else:
                base = "それはつらかったね。"
            question = f"{topic}のことで、いちばん負担だったのはどの部分？" if topic else "いちばん負担だったのはどの部分？"
            return DialogueReply(base + question, "empathize", 0.95, tuple(filter(None, (topic,))))
        if act == "advise":
            if not topic:
                return DialogueReply("状況がまだ少し曖昧だね。何についての助言が必要か、一言で教えて。", "clarify", 0.4)
            return DialogueReply(f"{topic}についてなら、まず『今すぐ変えられること』と『相手に確認が必要なこと』を分けるのがよさそう。今いちばん困っている点は何？", "advise", 0.75, (topic,))
        if act == "clarify":
            return DialogueReply("『それ』が何を指しているか特定できなかった。話題を一言だけ教えて。", "clarify", 0.0)
        if act == "explore":
            if re.search(r"どう思う", compact):
                return DialogueReply(f"今の話だけなら、{topic or 'その件'}は簡単に割り切れないと思う。あなた自身は、何がいちばん引っかかっている？", "explore", 0.7, tuple(filter(None, (topic,))))
            return DialogueReply(f"なるほど、{topic or 'そのこと'}の話なんだね。もう少し詳しく聞かせて。", "explore", 0.7, tuple(filter(None, (topic,))))
        if act == "recall":
            return DialogueReply("覚えている範囲を確認したけれど、質問の対象を特定できなかった。何についてか一言だけ教えて。", "clarify-recall", 0.2)
        if act == "correct":
            return DialogueReply("訂正内容を特定できなかった。『AではなくB』の形でもう一度教えて。", "clarify-correction", 0.2)
        if self.state.affect == "positive":
            return DialogueReply("それはよかったね。うまくいったのは、どの部分が大きかった？", "celebrate", 0.9, tuple(filter(None, (topic,))))
        follow = _stable_choice(("それで、どう感じた？", "その後はどうなった？", "もう少し詳しく聞かせて。"), text + str(self.state.turn))
        lead = f"{topic}の話だね。" if topic else "なるほど。"
        return DialogueReply(f"{lead}{follow}", "acknowledge", 0.65, tuple(filter(None, (topic, self.state.last_user_proposition))))

    def serialized_bytes(self) -> int:
        return len(json.dumps(self.state.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    def to_dict(self) -> dict:
        return {"format": "sparc-hs20-dialogue-v1", "state": self.state.to_dict()}

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationalCognitiveEngine":
        if data.get("format") != "sparc-hs20-dialogue-v1":
            raise ValueError("unsupported dialogue format")
        return cls(DialogueState.from_dict(data["state"]))
