from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from .dialogue_cognition import (
    ConversationalCognitiveEngine,
    DialogueReply,
    DialogueState,
)


_STOP_WORDS = {
    "今日は", "昨日", "最近", "なんか", "ちょっと", "かなり", "だけど", "けど", "だから",
    "それ", "これ", "あれ", "その", "この", "こういう", "どう", "どうすれば", "どうしたら",
    "思う", "思って", "言って", "話", "こと", "もの", "ところ", "感じ", "自分", "私", "僕",
    "です", "ます", "だよ", "なんだ", "だった", "してる", "している", "なって", "なった",
}
_GENERIC_FRAGMENTS = (
    "なるほど", "もう少し詳しく", "その後はどうなった", "簡単に割り切れない", "何の話",
)
_TOPIC_DIMENSIONS = {
    "仕事": ("期限", "優先順位", "相手との関係", "負担"),
    "上司": ("依頼の期限", "断りにくさ", "優先順位", "負担"),
    "ランニング": ("前半のペース", "呼吸", "脚の疲労", "補給"),
    "マラソン": ("ペース", "脚の疲労", "補給", "回復"),
    "AI": ("精度", "計算量", "メモリ", "汎化"),
    "モデル": ("精度", "計算量", "メモリ", "汎化"),
    "研究": ("仮説", "反証", "再現性", "次の実験"),
    "ゲーム": ("操作性", "面白さ", "分かりやすさ", "再プレイ性"),
    "旅行": ("日程", "移動", "予算", "一緒に行く人"),
}


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text).strip("。.!！?？")


def _normalize_clause(text: str, limit: int = 48) -> str:
    value = re.sub(r"^(?:今日は|昨日|最近|そういえば)", "", _compact(text)).lstrip("、,")
    value = re.sub(r"(?:だったよ|だよ|なんだ|んだ|でさ|だね|です|ます|よ|ね|さ)$", "", value)
    return value[:limit]


def _option_label(text: str) -> str:
    value = _normalize_clause(text, 32)
    value = re.sub(r"(?:を)?(?:直す|改善する|伸ばす|進める|強化する)$", "", value)
    return value or _normalize_clause(text, 32)


def _char_ngrams(text: str, n: int = 2) -> set[str]:
    compact = _compact(text)
    return {compact[index:index + n] for index in range(max(0, len(compact) - n + 1))}


def _content_terms(text: str) -> tuple[str, ...]:
    chunks = re.findall(r"[一-龥々ァ-ヶーA-Za-z0-9]{2,18}", _compact(text))
    output: list[str] = []
    for chunk in chunks:
        parts = re.split(r"(?:したら|すると|だから|なので|けれど|だけど|なのに|だったら)", chunk)
        for part in parts:
            part = part.strip()
            if len(part) < 2 or part in _STOP_WORDS:
                continue
            if part not in output:
                output.append(part)
    return tuple(sorted(output, key=lambda value: (-len(value), value))[:8])


@dataclass(frozen=True, slots=True)
class UtteranceFrame:
    text: str
    topic: str | None
    emotion: str
    question_type: str
    actor: str | None
    timing: str | None
    conflict_choice: str | None
    feared_outcome: str | None
    chosen_action: str | None
    key_terms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Candidate:
    text: str
    strategy: str
    score: float = 0.0
    reasons: tuple[str, ...] = ()


class UtteranceFrameParser:
    NEGATIVE = ("疲れ", "つら", "しんど", "不安", "怖", "怒", "むかつ", "落ち込", "困", "重い")
    POSITIVE = ("嬉し", "楽し", "よかった", "最高", "うまくいった", "褒め")

    def parse(self, text: str, state: DialogueState) -> UtteranceFrame:
        compact = _compact(text)
        topic = state.current_topic
        actor_match = re.search(r"(上司|同僚|部下|先生|友達|家族|彼女|妹|兄|姉|親|相手)", compact)
        timing_match = re.search(r"(帰る直前|出発直前|締切直前|前半|後半|朝|昼|夜|直前|直後)", compact)
        conflict = re.search(
            r"(.{1,18}?)(?:たら|ると)(.{1,28}?)(?:そう|かも)(?:で|だから)[、,]?(?:結局)?(.{1,24})",
            compact,
        )
        if any(word in compact for word in self.NEGATIVE):
            emotion = "negative"
        elif any(word in compact for word in self.POSITIVE):
            emotion = "positive"
        else:
            emotion = "neutral"
        if re.search(r"どうすれば|どうしたら|アドバイス|助けて", compact):
            question_type = "advice"
        elif re.search(r"どっち|どちら", compact):
            question_type = "choice"
        elif re.search(r"どう思う|意見", compact):
            question_type = "opinion"
        elif "?" in text or "？" in text or re.search(r"なぜ|何|どこ|誰|覚えて", compact):
            question_type = "question"
        else:
            question_type = "statement"
        return UtteranceFrame(
            text=text,
            topic=topic,
            emotion=emotion,
            question_type=question_type,
            actor=actor_match.group(1) if actor_match else None,
            timing=timing_match.group(1) if timing_match else None,
            conflict_choice=_normalize_clause(conflict.group(1), 20) if conflict else None,
            feared_outcome=_normalize_clause(conflict.group(2), 28) if conflict else None,
            chosen_action=_normalize_clause(conflict.group(3), 24) if conflict else None,
            key_terms=_content_terms(text),
        )


class CandidateGenerator:
    def generate(
        self,
        base: DialogueReply,
        frame: UtteranceFrame,
        state: DialogueState,
    ) -> tuple[Candidate, ...]:
        candidates: list[Candidate] = [Candidate(base.text, "hs20-base")]
        summary = _normalize_clause(frame.text)
        topic = frame.topic or (frame.key_terms[0] if frame.key_terms else None)
        dimensions = _TOPIC_DIMENSIONS.get(frame.topic or "", ())
        context_summary = summary
        event_summary = summary
        if frame.timing:
            event_summary = summary.replace(frame.timing, "", 1).lstrip("に、,")
        prior_text = ""
        if state.current_topic and state.current_topic in state.topics:
            propositions = state.topics[state.current_topic].propositions
            if len(propositions) >= 2:
                prior_text = propositions[-2]
                if frame.question_type != "statement":
                    context_summary = _normalize_clause(prior_text)
        conflict_choice = frame.conflict_choice
        feared_outcome = frame.feared_outcome
        chosen_action = frame.chosen_action
        if prior_text and not (conflict_choice and feared_outcome and chosen_action):
            previous_conflict = re.search(
                r"(.{1,18}?)(?:たら|ると)(.{1,28}?)(?:そう|かも)(?:で|だから)[、,]?(?:結局)?(.{1,24})",
                _compact(prior_text),
            )
            if previous_conflict:
                conflict_choice = _normalize_clause(previous_conflict.group(1), 20)
                feared_outcome = _normalize_clause(previous_conflict.group(2), 28)
                chosen_action = _normalize_clause(previous_conflict.group(3), 24)

        alternatives: tuple[str, str] | None = None
        for choice_source in (frame.text, prior_text):
            if not choice_source:
                continue
            for pattern in (
                r"(.{2,28}?)と(.{2,28}?)のどちら",
                r"(.{2,28}?)か[、,]?(.{2,28}?)か(?:で迷|迷って|どっち|どちら)",
            ):
                choice_match = re.search(pattern, _compact(choice_source))
                if choice_match:
                    alternatives = (
                        _normalize_clause(choice_match.group(1), 28),
                        _normalize_clause(choice_match.group(2), 28),
                    )
                    break
            if alternatives:
                break

        if base.act == "empathize":
            if conflict_choice and feared_outcome and chosen_action:
                candidates.extend((
                    Candidate(
                        f"{feared_outcome}のが気になって、{chosen_action}んだね。"
                        f"選択そのものより、断りにくい状況に置かれたことが消耗したんじゃない？",
                        "conflict-empathy",
                    ),
                    Candidate(
                        f"{summary}んだね。{feared_outcome}ことと、{chosen_action}ことのどちらが今は重い？",
                        "contrast-question",
                    ),
                ))
            else:
                actor_focus = f"{frame.actor}とのやり取り" if frame.actor else (topic or "その出来事")
                candidates.extend((
                    Candidate(
                        f"『{summary}』という状況なんだね。{actor_focus}で気力まで削られた感じかな。体の疲れと気持ちの疲れ、今はどちらが大きい？",
                        "specific-empathy",
                    ),
                    Candidate(
                        f"それはしんどいね。{summary}という状況なら、疲れるのは自然だと思う。何がいちばん負担だった？",
                        "normalize-and-focus",
                    ),
                ))

        if base.act in {"acknowledge", "explore", "celebrate"}:
            if conflict_choice and feared_outcome and chosen_action:
                candidates.append(Candidate(
                    f"{feared_outcome}のが気になって、{chosen_action}んだね。"
                    "断るか引き受けるかの二択に追い込まれたこと自体が負担だったように見える。",
                    "conflict-reflection",
                ))
            if frame.timing and (frame.actor or frame.topic in {"仕事", "上司"} or "直前" in frame.timing):
                candidates.append(Candidate(
                    f"{frame.timing}に{event_summary}のは対応しづらいね。予定が崩れたことと、相手に断りにくかったことのどちらが大きかった？",
                    "timing-impact",
                ))
            if frame.emotion == "positive":
                candidates.append(Candidate(
                    f"{summary}のはちゃんと前進だね。何が効いたのか一つでも言葉にしておくと、次も再現しやすくなる。今回は何がいちばん良かった？",
                    "celebrate-and-consolidate",
                ))
            if topic in {"ランニング", "マラソン"} and frame.question_type in {"question", "opinion"} and "息" in context_summary and "脚" in context_summary:
                candidates.append(Candidate(
                    "息は保てているのに脚だけ動かなくなるなら、心肺より脚の局所疲労か、前半のペースが速すぎる可能性が高そう。"
                    "まず前半を少し落とし、脚が重くなり始める距離が後ろへずれるか比べると切り分けやすい。",
                    "causal-hypothesis",
                ))
            if dimensions:
                left, right = dimensions[0], dimensions[1]
                candidates.append(Candidate(
                    f"{context_summary}。{topic or 'その件'}では、{left}と{right}を分けて考えると原因が見えやすい。今の感覚ではどちらが近い？",
                    "topic-dimensions",
                ))
            candidates.extend((
                Candidate(
                    f"『{context_summary}』ということなんだね。そこでは『何が起きたか』より『何が予想と違ったか』が気になる。いちばん意外だったのはどこ？",
                    "prediction-error-focus",
                ),
                Candidate(
                    f"{context_summary}という状況なんだね。次に変えたいのは結果そのもの、それともそこに至る過程？",
                    "goal-focus",
                ),
            ))

        if base.act == "advise" or frame.question_type == "advice":
            if conflict_choice and feared_outcome and chosen_action:
                candidates.append(Candidate(
                    f"次は『{conflict_choice}か{chosen_action}か』の二択にしないのがよさそう。"
                    "今抱えている予定と追加依頼を並べて、どちらを優先するか相手に決めてもらえば、"
                    f"{feared_outcome}リスクを抑えながら全部を背負わずに済む。",
                    "counterfactual-advice",
                ))
            candidates.extend((
                Candidate(
                    f"{topic or 'その件'}なら、まず事実・制約・希望の三つに分ける。"
                    "そのうえで、いちばん小さく試せて後戻りできる行動を一つ選ぶのが現実的だと思う。",
                    "reversible-step-advice",
                ),
                Candidate(
                    f"今すぐ全部を解決しようとせず、{summary}の中で自分が変えられる部分を一つだけ決めよう。"
                    "相手の判断が必要な部分は、選択肢を二つにして確認すると進めやすい。",
                    "control-boundary-advice",
                ),
            ))

        if frame.question_type == "choice":
            if alternatives:
                left_option, right_option = alternatives
                foundation_terms = ("操作", "分かり", "表現", "入力", "理解", "安全", "基礎")
                if any(term in right_option for term in foundation_terms):
                    foundation, enhancement = right_option, left_option
                elif any(term in left_option for term in foundation_terms):
                    foundation, enhancement = left_option, right_option
                else:
                    foundation, enhancement = left_option, right_option
                foundation_label = _option_label(foundation)
                enhancement_label = _option_label(enhancement)
                candidates.append(Candidate(
                    f"今の情報なら、まず『{foundation}』を優先する。『{enhancement}』を進めても、"
                    f"{foundation_label}が弱いと良さを受け取ってもらえないから。{foundation_label}の最低基準を通した後に、"
                    f"{enhancement_label}を伸ばす順番がいいと思う。",
                    "ordered-choice",
                ))
            candidates.append(Candidate(
                "二者択一に見えるけれど、先に失敗したときの損失が大きい方を潰すのがよさそう。"
                "その後でもう一方を伸ばせるなら、その順番がいちばん戻りやすい。",
                "risk-first-choice",
            ))

        if re.search(r"試してみる|やってみる|決めたい|進めたい", _compact(frame.text)):
            if topic in {"ランニング", "マラソン"}:
                candidates.append(Candidate(
                    "いいと思う。次の2回は距離とコースをそろえて、変えるのは前半のペースだけにしよう。"
                    "脚が重くなり始めた距離を記録すれば、前半の入りが原因か比較しやすい。",
                    "commitment-experiment",
                ))
            elif topic in {"研究", "AI", "モデル"}:
                candidates.append(Candidate(
                    "順番を検証可能にしよう。まず表現学習だけを変えた版、次に会話プランナーだけを変えた版を作り、"
                    "同じ隠し会話で比較すれば、どちらが効いたか切り分けられる。",
                    "commitment-experiment",
                ))
            elif topic in {"仕事", "上司"}:
                candidates.append(Candidate(
                    "次に備えて、追加依頼を受けたときの一文を先に決めておくと試しやすい。"
                    "『今の作業とどちらを優先しますか』と確認し、相手の反応と残業時間を記録しよう。",
                    "commitment-experiment",
                ))
            else:
                candidates.append(Candidate(
                    "試すなら、一度に一つだけ変えて、前後で何を比べるかも先に決めておこう。"
                    "結果が悪くても、原因を切り分けられる実験になる。",
                    "commitment-experiment",
                ))

        if base.act in {"recall", "recall-topic", "correct", "resume-topic", "clarify-reference", "clarify"}:
            return tuple(candidates)

        return tuple(candidates)


class ResponseCritic:
    def score(
        self,
        candidate: Candidate,
        base_act: str,
        frame: UtteranceFrame,
        prior_assistant_turns: Iterable[str],
    ) -> Candidate:
        text = candidate.text
        score = 0.0
        reasons: list[str] = []
        compact = _compact(text)
        matched_terms = [term for term in frame.key_terms if term in compact]
        if matched_terms:
            score += min(3.0, 0.7 * len(matched_terms))
            reasons.append("grounded:" + ",".join(matched_terms[:3]))
        if frame.topic and frame.topic in compact:
            score += 1.2
            reasons.append("topic")
        if 28 <= len(text) <= 150:
            score += 1.0
            reasons.append("useful-length")
        elif len(text) < 18:
            score -= 2.0
            reasons.append("too-short")
        if base_act == "advise" or frame.question_type == "advice":
            if any(term in text for term in ("まず", "次は", "分け", "伝え", "確認", "選ぶ", "決め")):
                score += 2.0
                reasons.append("actionable")
            if text.endswith("？") and not any(term in text for term in ("まず", "次は", "分け", "伝え", "選ぶ")):
                score -= 1.5
                reasons.append("question-only-advice")
        if base_act == "empathize" or frame.emotion == "negative":
            if any(term in text for term in ("疲", "しんど", "不安", "消耗", "自然", "無理")):
                score += 1.0
                reasons.append("affect-fit")
        if frame.emotion == "positive" and any(term in text for term in ("よかった", "前進", "嬉")):
            score += 1.0
            reasons.append("positive-fit")
        strategy_bonus = {
            "conflict-reflection": 2.5,
            "conflict-empathy": 2.0,
            "counterfactual-advice": 3.0,
            "ordered-choice": 3.0,
            "commitment-experiment": 5.0,
            "causal-hypothesis": 4.0,
        }.get(candidate.strategy, 0.0)
        if strategy_bonus:
            score += strategy_bonus
            reasons.append("strategy-bonus")
        if candidate.strategy == "topic-dimensions" and frame.question_type == "statement" and frame.emotion == "neutral":
            score -= 1.5
            reasons.append("premature-analysis")
        generic_hits = sum(fragment in text for fragment in _GENERIC_FRAGMENTS)
        if generic_hits:
            score -= 1.2 * generic_hits
            reasons.append("generic")
        user_grams = _char_ngrams(frame.text)
        reply_grams = _char_ngrams(text)
        echo = len(user_grams & reply_grams) / max(1, len(user_grams | reply_grams))
        if echo > 0.72:
            score -= 2.0
            reasons.append("echo")
        max_repeat = 0.0
        for prior in prior_assistant_turns:
            prior_grams = _char_ngrams(prior)
            repeat = len(reply_grams & prior_grams) / max(1, len(reply_grams | prior_grams))
            max_repeat = max(max_repeat, repeat)
        if max_repeat > 0.55:
            score -= 3.0 * max_repeat
            reasons.append("repetition")
        if frame.question_type in {"advice", "choice", "opinion"} and not any(mark in text for mark in ("。", "だと思う", "よさそう", "優先")):
            score -= 1.0
            reasons.append("indirect")
        return Candidate(text, candidate.strategy, score, tuple(reasons))


class PlannedConversationalEngine:
    """HS21: HS20 discourse state plus candidate generation and self-critique."""

    def __init__(self, base: ConversationalCognitiveEngine | None = None) -> None:
        self.base = base or ConversationalCognitiveEngine()
        self.parser = UtteranceFrameParser()
        self.generator = CandidateGenerator()
        self.critic = ResponseCritic()
        self.last_candidates: tuple[Candidate, ...] = ()

    @property
    def state(self) -> DialogueState:
        return self.base.state

    def start_new_session(self) -> None:
        self.base.start_new_session()
        self.last_candidates = ()

    def respond(self, text: str) -> DialogueReply:
        base_reply = self.base.respond(text)
        if self.state.history and self.state.history[-1] == ("assistant", base_reply.text):
            self.state.history.pop()
        self.state.last_assistant_question = None
        frame = self.parser.parse(text, self.state)
        generated = self.generator.generate(base_reply, frame, self.state)
        prior = [value for role, value in self.state.history if role == "assistant"][-12:]
        scored = tuple(
            self.critic.score(candidate, base_reply.act, frame, prior)
            for candidate in generated
        )
        selected = max(
            scored,
            key=lambda candidate: (candidate.score, candidate.strategy, candidate.text),
        )
        self.last_candidates = tuple(sorted(scored, key=lambda candidate: candidate.score, reverse=True))
        self.state.append("assistant", selected.text)
        self.state.last_assistant_question = selected.text if selected.text.endswith(("？", "?")) else None
        evidence = tuple(selected.reasons) + (f"strategy={selected.strategy}", f"score={selected.score:.3f}")
        return DialogueReply(selected.text, "planned-" + base_reply.act, base_reply.confidence, evidence)

    def serialized_bytes(self) -> int:
        payload = {
            "format": "sparc-hs21-dialogue-planner-v1",
            "base": self.base.to_dict(),
            "last_candidates": [
                {
                    "text": candidate.text,
                    "strategy": candidate.strategy,
                    "score": candidate.score,
                    "reasons": list(candidate.reasons),
                }
                for candidate in self.last_candidates[:8]
            ],
        }
        return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
