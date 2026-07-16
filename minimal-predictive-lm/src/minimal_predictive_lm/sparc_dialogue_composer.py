from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
import hashlib
import json
import re
import zlib
from typing import Iterable, Mapping, Sequence

from .sparc_language import ReplyResult


_SLOT_ORDER = (
    "subject",
    "answer",
    "evidence",
    "caveat",
    "old_value",
    "new_value",
    "source",
    "next_focus",
)

_PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")
_JA_FOLLOWUP = (
    "それについて",
    "その話",
    "詳しく",
    "もう少し",
    "理由も",
    "根拠も",
)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _anchors(text: str) -> tuple[str, ...]:
    compact = _normalise(text).replace(" ", "")
    output: set[str] = set()
    for size in (2, 3, 4):
        for index in range(max(0, len(compact) - size + 1)):
            piece = compact[index : index + size]
            if not piece.isdigit():
                output.add(f"N{size}:{piece}")
    if compact:
        output.add(f"H:{compact[: min(5, len(compact))]}")
        output.add(f"T:{compact[-min(5, len(compact)): ]}")
    return tuple(sorted(output))


@dataclass(frozen=True)
class DialoguePlan:
    intent: str
    subject: str = ""
    answer: str = ""
    evidence: str = ""
    caveat: str = ""
    old_value: str = ""
    new_value: str = ""
    source: str = ""
    next_focus: str = ""
    confidence: float = 1.0

    def slots(self) -> dict[str, str]:
        return {
            name: _normalise(str(getattr(self, name)))
            for name in _SLOT_ORDER
            if _normalise(str(getattr(self, name)))
        }


@dataclass(frozen=True)
class DialogueDemonstration:
    plan: DialoguePlan
    response: str


@dataclass(frozen=True)
class SurfaceTemplate:
    template_id: int
    intent: str
    required_slots: tuple[str, ...]
    optional_slots: tuple[str, ...]
    surface: str
    examples: int
    anchors: tuple[str, ...]


@dataclass(frozen=True)
class CompositionResult:
    text: str
    mechanism: str
    confidence: float
    candidates: int
    feature_reads: int
    template_id: int | None


class SparseDialogueComposer:
    """Bounded Japanese surface composer over explicit semantic slots.

    It learns reusable surface templates by replacing demonstrated slot values
    with placeholders. At inference it retrieves only templates sharing sparse
    anchors with the requested dialogue act and slot signature, then fills a
    previously unseen combination of values. A fixed focus deque supplies
    omitted subjects for follow-up turns; no full conversation scan is used.
    """

    def __init__(
        self,
        *,
        max_templates: int = 4096,
        max_candidates: int = 24,
        focus_turns: int = 32,
    ) -> None:
        self.max_templates = max_templates
        self.max_candidates = max_candidates
        self.focus: deque[tuple[str, str]] = deque(maxlen=focus_turns)
        self.templates: list[SurfaceTemplate] = []
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.last_candidates = 0
        self.last_feature_reads = 0
        self.last_template_id: int | None = None
        self.training_examples = 0

    @staticmethod
    def _abstract_response(plan: DialoguePlan, response: str) -> tuple[str, tuple[str, ...]]:
        surface = _normalise(response)
        slots = plan.slots()
        replacements = sorted(
            ((value, name) for name, value in slots.items()),
            key=lambda row: (-len(row[0]), row[1]),
        )
        used: list[str] = []
        for value, name in replacements:
            if value not in surface:
                continue
            surface = surface.replace(value, "{" + name + "}")
            used.append(name)
        return surface, tuple(sorted(set(used)))

    @staticmethod
    def _template_anchors(
        intent: str,
        required_slots: Sequence[str],
        surface: str,
    ) -> tuple[str, ...]:
        output = {f"I:{intent}"}
        output.update(f"S:{name}" for name in required_slots)
        cleaned = _PLACEHOLDER_RE.sub("", surface)
        output.update(_anchors(cleaned))
        return tuple(sorted(output))

    def fit(self, demonstrations: Iterable[DialogueDemonstration]) -> int:
        grouped: Counter[tuple[str, str, tuple[str, ...]]] = Counter()
        for row in demonstrations:
            surface, used = self._abstract_response(row.plan, row.response)
            if not used:
                continue
            grouped[(row.plan.intent, surface, used)] += 1
            self.training_examples += 1

        ranked = sorted(
            grouped.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1], item[0][2]),
        )
        self.templates.clear()
        self.postings.clear()
        for template_id, ((intent, surface, used), count) in enumerate(
            ranked[: self.max_templates]
        ):
            placeholders = tuple(sorted(set(_PLACEHOLDER_RE.findall(surface))))
            required = tuple(name for name in placeholders if name in used)
            optional = tuple(name for name in placeholders if name not in required)
            anchors = self._template_anchors(intent, required, surface)
            template = SurfaceTemplate(
                template_id,
                intent,
                required,
                optional,
                surface,
                count,
                anchors,
            )
            self.templates.append(template)
            for anchor in anchors:
                self.postings[anchor].add(template_id)
        return len(self.templates)

    def _query_anchors(self, plan: DialoguePlan) -> tuple[str, ...]:
        slots = plan.slots()
        output = {f"I:{plan.intent}"}
        output.update(f"S:{name}" for name in slots)
        if plan.subject:
            output.update(_anchors(plan.subject))
        return tuple(sorted(output))

    def _candidate_templates(self, plan: DialoguePlan) -> list[tuple[float, int]]:
        query = self._query_anchors(plan)
        votes: Counter[int] = Counter()
        reads = 0
        routes = sorted(
            (len(self.postings.get(anchor, ())), anchor)
            for anchor in query
            if self.postings.get(anchor)
        )
        for posting_size, anchor in routes:
            if posting_size > self.max_candidates * 4 and votes:
                continue
            for template_id in self.postings[anchor]:
                votes[template_id] += 1.0 / max(1, posting_size)
                reads += 1
                if reads >= self.max_candidates * 12:
                    break
            if reads >= self.max_candidates * 12:
                break

        slots = plan.slots()
        scored: list[tuple[float, int]] = []
        for template_id, vote in votes.items():
            template = self.templates[template_id]
            if template.intent != plan.intent:
                continue
            if any(name not in slots for name in template.required_slots):
                continue
            overlap = sum(name in slots for name in template.required_slots)
            score = vote + 2.0 * overlap + 0.05 * template.examples
            scored.append((score, template_id))
        scored.sort(key=lambda row: (-row[0], row[1]))
        self.last_candidates = min(len(scored), self.max_candidates)
        self.last_feature_reads = reads + len(scored)
        return scored[: self.max_candidates]

    @staticmethod
    def _render(surface: str, slots: Mapping[str, str]) -> str | None:
        required = set(_PLACEHOLDER_RE.findall(surface))
        if any(not slots.get(name) for name in required):
            return None
        rendered = surface
        for name in required:
            rendered = rendered.replace("{" + name + "}", slots[name])
        rendered = re.sub(r"\s+([、。！？])", r"\1", rendered)
        return _normalise(rendered)

    def _fallback(self, plan: DialoguePlan) -> str:
        slots = plan.slots()
        answer = slots.get("answer", "")
        evidence = slots.get("evidence", "")
        caveat = slots.get("caveat", "")
        source = slots.get("source", "")
        if plan.intent == "correction":
            subject = slots.get("subject", "")
            old_value = slots.get("old_value", "")
            new_value = slots.get("new_value", "")
            text = f"{subject}は、{old_value}ではなく{new_value}です。"
            if evidence:
                text += f" 根拠は{evidence}です。"
            return text
        if plan.intent in {"explain", "answer", "compare", "reason"}:
            parts = [answer or slots.get("subject", "")]
            if evidence:
                parts.append(f"理由は{evidence}です")
            if caveat:
                parts.append(f"ただし、{caveat}")
            if source:
                parts.append(f"出典は{source}です")
            return "。".join(part.rstrip("。") for part in parts if part) + "。"
        if answer:
            return answer if answer.endswith(("。", "！", "？")) else answer + "。"
        return "まだ十分な根拠がありません。"

    def resolve_followup(self, text: str, plan: DialoguePlan) -> DialoguePlan:
        if plan.subject or not any(cue in text for cue in _JA_FOLLOWUP):
            return plan
        if not self.focus:
            return plan
        subject, _intent = self.focus[-1]
        payload = asdict(plan)
        payload["subject"] = subject
        if not payload["next_focus"]:
            payload["next_focus"] = subject
        return DialoguePlan(**payload)

    def compose(self, plan: DialoguePlan, *, user_text: str = "") -> CompositionResult:
        plan = self.resolve_followup(user_text, plan)
        slots = plan.slots()
        candidates = self._candidate_templates(plan)
        for score, template_id in candidates:
            template = self.templates[template_id]
            rendered = self._render(template.surface, slots)
            if rendered is None:
                continue
            self.last_template_id = template_id
            focus = plan.next_focus or plan.subject
            if focus:
                self.focus.append((focus, plan.intent))
            confidence = min(
                1.0,
                max(0.0, plan.confidence) * (0.65 + min(0.35, score / 10)),
            )
            return CompositionResult(
                rendered,
                "learned-slot-template",
                confidence,
                self.last_candidates,
                self.last_feature_reads,
                template_id,
            )

        text = self._fallback(plan)
        self.last_template_id = None
        focus = plan.next_focus or plan.subject
        if focus:
            self.focus.append((focus, plan.intent))
        return CompositionResult(
            text,
            "compositional-fallback",
            max(0.0, min(1.0, plan.confidence * 0.75)),
            self.last_candidates,
            self.last_feature_reads,
            None,
        )

    def reply_result(self, plan: DialoguePlan, *, user_text: str = "") -> ReplyResult:
        result = self.compose(plan, user_text=user_text)
        return ReplyResult(
            result.text,
            result.confidence,
            result.mechanism,
            result.candidates,
            len(plan.slots()),
            result.feature_reads + len(result.text),
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs19-dialogue-composer-v1",
            "max_templates": self.max_templates,
            "max_candidates": self.max_candidates,
            "focus_turns": self.focus.maxlen,
            "training_examples": self.training_examples,
            "templates": [asdict(row) for row in self.templates],
            "focus": list(self.focus),
        }
        return zlib.compress(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseDialogueComposer":
        payload = json.loads(zlib.decompress(data))
        model = cls(
            max_templates=int(payload["max_templates"]),
            max_candidates=int(payload["max_candidates"]),
            focus_turns=int(payload["focus_turns"]),
        )
        model.training_examples = int(payload["training_examples"])
        model.templates = [
            SurfaceTemplate(
                int(row["template_id"]),
                str(row["intent"]),
                tuple(row["required_slots"]),
                tuple(row["optional_slots"]),
                str(row["surface"]),
                int(row["examples"]),
                tuple(row["anchors"]),
            )
            for row in payload["templates"]
        ]
        for template in model.templates:
            for anchor in template.anchors:
                model.postings[anchor].add(template.template_id)
        model.focus.extend(
            (str(subject), str(intent)) for subject, intent in payload["focus"]
        )
        return model

    def report(self) -> dict[str, object]:
        return {
            "templates": len(self.templates),
            "training_examples": self.training_examples,
            "posting_edges": sum(len(rows) for rows in self.postings.values()),
            "focus_items": len(self.focus),
            "focus_capacity": self.focus.maxlen,
            "last_candidates": self.last_candidates,
            "last_feature_reads": self.last_feature_reads,
            "serialized_bytes": len(self.to_bytes()),
            "complete_response_selection_used": False,
            "full_history_scan_used": False,
            "transformer_used": False,
            "growing_kv_cache_used": False,
        }
