from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .meci_core import QuotientByteModel


@dataclass(frozen=True)
class DialogueRecord:
    user: str
    assistant: str


def encode_dialogue(records: Iterable[DialogueRecord]) -> bytes:
    chunks: list[bytes] = []
    for record in records:
        chunks.append(f"<U>{record.user}\n<A>{record.assistant}\n".encode("utf-8"))
    return b"".join(chunks)


def load_jsonl(path: str | Path) -> list[DialogueRecord]:
    records: list[DialogueRecord] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if "user" not in row or "assistant" not in row:
            raise ValueError(f"line {line_number} requires user and assistant fields")
        records.append(DialogueRecord(str(row["user"]), str(row["assistant"])))
    if not records:
        raise ValueError("training file contains no dialogue records")
    return records


class MECIChat:
    """Executable chat surface over the non-neural quotient byte model."""

    def __init__(self, max_order: int = 16) -> None:
        self.model = QuotientByteModel(max_order=max_order)

    def fit(self, records: Iterable[DialogueRecord]) -> "MECIChat":
        self.model.fit(encode_dialogue(records))
        return self

    def reply(self, user_text: str, max_new_bytes: int = 160) -> str:
        prompt = f"<U>{user_text}\n<A>".encode("utf-8")
        generated = self.model.generate(prompt, max_new_bytes=max_new_bytes, stop=b"\n")
        return generated.rstrip(b"\n").decode("utf-8", errors="replace")
