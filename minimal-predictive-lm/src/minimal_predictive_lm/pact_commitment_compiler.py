from __future__ import annotations

import hashlib
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from typing import Sequence

import torch
from torch import nn
from torch.nn import functional as F

_TOKEN_RE = re.compile(r"[0-9０-９.,]+|[A-Za-z]+|[一-龥々〆ヵヶぁ-んァ-ンー]+|[^\s]")
_SENTENCE_RE = re.compile(r"(?<=[。！？!?])")
_JANOME = None


def analyze_tokens(text: str) -> list[tuple[str, str]]:
    global _JANOME
    try:
        if _JANOME is None:
            from janome.tokenizer import Tokenizer
            _JANOME = Tokenizer()
        rows = []
        for token in _JANOME.tokenize(text.strip()):
            surface = token.surface.strip()
            if surface:
                rows.append((surface, token.part_of_speech.split(",", 1)[0]))
        return rows
    except Exception:
        return [(token, "未知語") for token in _TOKEN_RE.findall(text.strip())]


def tokenize(text: str) -> list[str]:
    return [surface for surface, _ in analyze_tokens(text)]


def ngrams(text: str, min_n: int = 2, max_n: int = 4) -> list[str]:
    compact = re.sub(r"\s+", " ", text.strip())
    out: list[str] = []
    for n in range(min_n, max_n + 1):
        out.extend(compact[i:i+n] for i in range(max(0, len(compact) - n + 1)))
    return out


def stable_hash(value: str, buckets: int) -> int:
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little") % buckets


def split_sentences(text: str) -> list[str]:
    return [x.strip() for x in _SENTENCE_RE.split(text) if x.strip()]


@dataclass(frozen=True)
class Pair:
    prompt: str
    response: str


@dataclass
class Config:
    hash_buckets: int = 16384
    embedding_dim: int = 96
    commitment_atoms: int = 64
    top_atoms: int = 4
    max_templates: int = 12000
    epochs: int = 5
    batch_size: int = 192
    learning_rate: float = 2e-3
    seed: int = 17
    retrieval_candidates: int = 96
    max_response_chars: int = 520


@dataclass
class SlotSpec:
    token: str
    kind: str
    occurrence: int
    relative_position: float
    left: str
    right: str


@dataclass
class TemplateRecord:
    prompt: str
    response: str
    template: str
    slots: list[SlotSpec]
    prompt_ids: list[int]
    response_ids: list[int]
    prompt_atom: int = -1
    response_atom: int = -1


class HashedCommitmentEncoder(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.prompt_embedding = nn.Embedding(cfg.hash_buckets, cfg.embedding_dim)
        self.response_embedding = nn.Embedding(cfg.hash_buckets, cfg.embedding_dim)
        self.prompt_gate = nn.Embedding(cfg.hash_buckets, 1)
        self.response_gate = nn.Embedding(cfg.hash_buckets, 1)
        self.atoms = nn.Parameter(torch.randn(cfg.commitment_atoms, cfg.embedding_dim) * 0.08)
        self.temperature = nn.Parameter(torch.tensor(0.0))

    def _encode(self, ids: torch.Tensor, mask: torch.Tensor, side: str) -> torch.Tensor:
        embedding = self.prompt_embedding if side == "prompt" else self.response_embedding
        gate = self.prompt_gate if side == "prompt" else self.response_gate
        values = embedding(ids)
        weights = torch.sigmoid(gate(ids).squeeze(-1)) * mask.float()
        total = (values * weights.unsqueeze(-1)).sum(1)
        denom = weights.sum(1, keepdim=True).clamp_min(1.0)
        return F.normalize(total / denom, dim=-1)

    def encode_prompt(self, ids: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        return self._encode(ids, mask, "prompt")

    def encode_response(self, ids: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        return self._encode(ids, mask, "response")

    def atom_distribution(self, vectors: torch.Tensor) -> torch.Tensor:
        atoms = F.normalize(self.atoms, dim=-1)
        logits = vectors @ atoms.T / self.temperature.exp().clamp(0.3, 3.0)
        top_values, top_indices = logits.topk(min(self.cfg.top_atoms, logits.size(-1)), dim=-1)
        sparse = torch.full_like(logits, -1e9)
        sparse.scatter_(1, top_indices, top_values)
        return sparse.softmax(-1)

    def loss(
        self,
        prompt_ids: torch.Tensor,
        prompt_mask: torch.Tensor,
        response_ids: torch.Tensor,
        response_mask: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        p = self.encode_prompt(prompt_ids, prompt_mask)
        r = self.encode_response(response_ids, response_mask)
        logits = p @ r.T / 0.08
        labels = torch.arange(logits.size(0), device=logits.device)
        contrast = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) * 0.5
        p_atoms = self.atom_distribution(p)
        r_atoms = self.atom_distribution(r)
        align = F.mse_loss(p_atoms, r_atoms)
        usage = ((p_atoms.mean(0) + r_atoms.mean(0)) * 0.5).clamp_min(1e-8)
        diversity = (usage * usage.log()).sum() + math.log(self.cfg.commitment_atoms)
        return {
            "loss": contrast + 0.35 * align + 0.02 * diversity,
            "contrast": contrast.detach(),
            "align": align.detach(),
            "diversity": diversity.detach(),
        }


class PACTCompiler:
    """Compile utterances from learned commitment transactions.

    The neural component learns a cross-utterance commitment space. The compiler
    induces response programs by replacing informative spans shared with the
    prompt with bindable slots. At inference it retrieves by commitment
    compatibility, rebinds slots from the current utterance, and only emits a
    completed candidate after compatibility scoring.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.encoder = HashedCommitmentEncoder(cfg)
        self.records: list[TemplateRecord] = []
        self.inverted: dict[int, list[int]] = defaultdict(list)
        self.idf: dict[int, float] = {}
        self.token_idf: dict[str, float] = {}
        self.device = torch.device("cpu")

    def feature_ids(self, text: str) -> list[int]:
        ids = [stable_hash(g, self.cfg.hash_buckets) for g in ngrams(text)]
        ids.extend(
            stable_hash(f"ACT:{token}", self.cfg.hash_buckets)
            for token in tokenize(text)
            if token in {"?", "？", "!", "！", "。", ":", "："}
        )
        return ids or [0]

    @staticmethod
    def _slot_kind(token: str) -> str:
        if re.fullmatch(r"[0-9０-９.,]+", token):
            return "number"
        if re.fullmatch(r"[A-Za-z]+", token):
            return "latin"
        if len(token) >= 2:
            return "content"
        return "symbol"

    def induce_template(self, pair: Pair) -> tuple[str, list[SlotSpec]]:
        p_rows = analyze_tokens(pair.prompt)
        p_tokens = [surface for surface, _ in p_rows]
        r_tokens = tokenize(pair.response)
        p_counts = Counter(p_tokens)
        pos_by_surface = {surface: pos for surface, pos in p_rows}
        candidates = set()
        for token in p_counts:
            kind = self._slot_kind(token)
            pos = pos_by_surface.get(token, "")
            informative = pos == "名詞" or kind in {"number", "latin"}
            if informative and (kind == "number" or self.token_idf.get(token, 0.0) >= 2.0):
                candidates.add(token)
        shared = sorted(
            {t for t in r_tokens if t in candidates},
            key=lambda x: (
                self._slot_kind(x) != "number",
                -self.token_idf.get(x, 0.0),
                -len(x),
                x,
            ),
        )[:6]
        template = pair.response
        slots: list[SlotSpec] = []
        for index, token in enumerate(shared):
            positions = [i for i, value in enumerate(p_tokens) if value == token]
            if not positions:
                continue
            pos = positions[0]
            marker = f"{{{{S{index}}}}}"
            template = template.replace(token, marker)
            slots.append(
                SlotSpec(
                    token=token,
                    kind=self._slot_kind(token),
                    occurrence=0,
                    relative_position=pos / max(1, len(p_tokens) - 1),
                    left=p_tokens[pos - 1] if pos else "",
                    right=p_tokens[pos + 1] if pos + 1 < len(p_tokens) else "",
                )
            )
        return template, slots

    def build_records(self, pairs: Sequence[Pair]) -> None:
        self.records.clear()
        limit = min(len(pairs), self.cfg.max_templates)
        selected = list(pairs[:limit])
        token_df = Counter()
        for pair in selected:
            token_df.update(set(tokenize(pair.prompt)))
        self.token_idf = {
            token: math.log((limit + 1) / (count + 1)) + 1.0
            for token, count in token_df.items()
        }
        for pair in selected:
            template, slots = self.induce_template(pair)
            self.records.append(
                TemplateRecord(
                    prompt=pair.prompt,
                    response=pair.response,
                    template=template,
                    slots=slots,
                    prompt_ids=self.feature_ids(pair.prompt),
                    response_ids=self.feature_ids(pair.response),
                )
            )
        df = Counter()
        for record in self.records:
            df.update(set(record.prompt_ids))
        total = max(1, len(self.records))
        self.idf = {
            fid: math.log((total + 1) / (count + 1)) + 1
            for fid, count in df.items()
        }
        self.inverted.clear()
        for index, record in enumerate(self.records):
            for fid in set(record.prompt_ids):
                self.inverted[fid].append(index)

    def _batch(
        self,
        records: Sequence[TemplateRecord],
        side: str,
        indices: Sequence[int],
    ) -> tuple[torch.Tensor, torch.Tensor]:
        seqs = [
            records[i].prompt_ids if side == "prompt" else records[i].response_ids
            for i in indices
        ]
        max_len = min(320, max(len(x) for x in seqs))
        ids = torch.zeros(len(seqs), max_len, dtype=torch.long)
        mask = torch.zeros(len(seqs), max_len, dtype=torch.bool)
        for row, seq in enumerate(seqs):
            seq = seq[:max_len]
            ids[row, :len(seq)] = torch.tensor(seq)
            mask[row, :len(seq)] = True
        return ids.to(self.device), mask.to(self.device)

    def train(
        self,
        pairs: Sequence[Pair],
        device: torch.device | str = "cpu",
    ) -> dict:
        torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
        random.seed(self.cfg.seed)
        torch.manual_seed(self.cfg.seed)
        self.device = torch.device(device)
        self.encoder.to(self.device)
        self.build_records(pairs)
        optimizer = torch.optim.AdamW(
            self.encoder.parameters(),
            lr=self.cfg.learning_rate,
            weight_decay=1e-4,
        )
        order = list(range(len(self.records)))
        history: list[dict] = []
        for epoch in range(self.cfg.epochs):
            random.Random(self.cfg.seed + epoch).shuffle(order)
            totals = Counter()
            batches = 0
            self.encoder.train()
            for start in range(0, len(order), self.cfg.batch_size):
                idx = order[start:start + self.cfg.batch_size]
                if len(idx) < 2:
                    continue
                p_ids, p_mask = self._batch(self.records, "prompt", idx)
                r_ids, r_mask = self._batch(self.records, "response", idx)
                losses = self.encoder.loss(p_ids, p_mask, r_ids, r_mask)
                optimizer.zero_grad(set_to_none=True)
                losses["loss"].backward()
                torch.nn.utils.clip_grad_norm_(self.encoder.parameters(), 1.0)
                optimizer.step()
                for key, value in losses.items():
                    totals[key] += float(value.detach())
                batches += 1
            history.append(
                {key: value / max(1, batches) for key, value in totals.items()}
                | {"epoch": epoch + 1}
            )
        self._assign_atoms()
        model_bytes = sum(
            p.numel() * p.element_size() for p in self.encoder.parameters()
        )
        memory_bytes = sum(
            len(r.template.encode("utf-8")) + len(r.prompt.encode("utf-8"))
            for r in self.records
        )
        return {
            "history": history,
            "model_bytes": model_bytes,
            "memory_bytes": memory_bytes,
            "records": len(self.records),
            "total_bytes": model_bytes + memory_bytes,
        }

    @torch.no_grad()
    def _encode_texts(
        self,
        texts: Sequence[str],
        side: str,
        batch_size: int = 256,
    ) -> torch.Tensor:
        self.encoder.eval()
        outputs = []
        for start in range(0, len(texts), batch_size):
            seqs = [
                self.feature_ids(x)[:320]
                for x in texts[start:start + batch_size]
            ]
            max_len = max(len(x) for x in seqs)
            ids = torch.zeros(
                len(seqs), max_len, dtype=torch.long, device=self.device
            )
            mask = torch.zeros(
                len(seqs), max_len, dtype=torch.bool, device=self.device
            )
            for row, seq in enumerate(seqs):
                ids[row, :len(seq)] = torch.tensor(seq, device=self.device)
                mask[row, :len(seq)] = True
            out = (
                self.encoder.encode_prompt(ids, mask)
                if side == "prompt"
                else self.encoder.encode_response(ids, mask)
            )
            outputs.append(out.cpu())
        return torch.cat(outputs, dim=0)

    @torch.no_grad()
    def _assign_atoms(self) -> None:
        if not self.records:
            return
        prompts = self._encode_texts([r.prompt for r in self.records], "prompt")
        responses = self._encode_texts([r.response for r in self.records], "response")
        self._prompt_vectors = prompts
        self._response_vectors = responses
        self.encoder.to("cpu")
        atoms = F.normalize(self.encoder.atoms.detach().cpu(), dim=-1)
        self.encoder.to(self.device)
        p_atoms = (prompts @ atoms.T).argmax(-1).tolist()
        r_atoms = (responses @ atoms.T).argmax(-1).tolist()
        for record, pa, ra in zip(self.records, p_atoms, r_atoms):
            record.prompt_atom = int(pa)
            record.response_atom = int(ra)

    def _lexical_candidates(self, prompt: str) -> list[int]:
        scores = Counter()
        for fid in set(self.feature_ids(prompt)):
            weight = self.idf.get(fid, 1.0)
            for index in self.inverted.get(fid, ()):
                scores[index] += weight
        return [
            idx
            for idx, _ in scores.most_common(self.cfg.retrieval_candidates * 2)
        ]

    @staticmethod
    def _content_tokens(text: str) -> list[str]:
        out = []
        for token, pos in analyze_tokens(text):
            kind = PACTCompiler._slot_kind(token)
            if pos == "名詞" or kind in {"number", "latin"}:
                out.append(token)
        return out

    def _bind_slot(self, spec: SlotSpec, prompt: str, used: set[str]) -> str:
        tokens = self._content_tokens(prompt)
        if not tokens:
            return spec.token
        typed = [
            t
            for t in tokens
            if self._slot_kind(t) == spec.kind and t not in used
        ]
        candidates = typed or [t for t in tokens if t not in used] or tokens
        if spec.token in candidates:
            return spec.token
        target = int(round(spec.relative_position * max(0, len(candidates) - 1)))
        return candidates[min(target, len(candidates) - 1)]

    def instantiate(self, record: TemplateRecord, prompt: str) -> str:
        text = record.template
        used: set[str] = set()
        for index, spec in enumerate(record.slots):
            value = self._bind_slot(spec, prompt, used)
            used.add(value)
            text = text.replace(f"{{{{S{index}}}}}", value)
        return text.strip()[:self.cfg.max_response_chars]

    @staticmethod
    def _degenerate(text: str) -> bool:
        if len(text.strip()) < 4:
            return True
        if len(set(text)) / max(1, len(text)) < 0.08:
            return True
        if re.search(r"(.)\1{7,}", text):
            return True
        return False

    @torch.no_grad()
    def respond(self, prompt: str, top_n: int = 8) -> tuple[str, dict]:
        if not self.records:
            raise RuntimeError("model is not trained")
        self.encoder.eval()
        p_vec = self._encode_texts([prompt], "prompt")[0]
        lexical = self._lexical_candidates(prompt)
        semantic_scores = self._response_vectors @ p_vec
        sem_top = semantic_scores.topk(
            min(self.cfg.retrieval_candidates, len(self.records))
        ).indices.tolist()
        candidate_ids = list(
            dict.fromkeys(
                lexical[:self.cfg.retrieval_candidates] + sem_top
            )
        )
        if not candidate_ids:
            candidate_ids = sem_top
        prompt_tokens = set(self._content_tokens(prompt))
        candidates = []
        for idx in candidate_ids:
            record = self.records[idx]
            output = self.instantiate(record, prompt)
            if self._degenerate(output):
                continue
            compatibility = float(self._response_vectors[idx] @ p_vec)
            prompt_similarity = float(self._prompt_vectors[idx] @ p_vec)
            lexical_overlap = len(
                prompt_tokens & set(self._content_tokens(output))
            ) / max(1, len(prompt_tokens))
            source_overlap = len(
                prompt_tokens & set(self._content_tokens(record.prompt))
            ) / max(1, len(prompt_tokens))
            atom_bonus = 0.08 if record.response_atom == record.prompt_atom else 0.0
            copy_bonus = min(0.15, 0.025 * len(record.slots))
            sentences = split_sentences(output)
            repetition = 1.0 - len(set(sentences)) / max(1, len(sentences))
            score = (
                0.62 * prompt_similarity
                + 0.52 * compatibility
                + 0.38 * source_overlap
                + 0.28 * lexical_overlap
                + atom_bonus
                + copy_bonus
                - 0.15 * repetition
            )
            candidates.append(
                (score, idx, output, compatibility, lexical_overlap)
            )
        if not candidates:
            return (
                "申し訳ありません。内容を十分に理解できませんでした。",
                {"abstained": True},
            )
        candidates.sort(reverse=True)
        best = candidates[0]
        return best[2], {
            "abstained": False,
            "score": best[0],
            "source_index": best[1],
            "compatibility": best[3],
            "lexical_overlap": best[4],
            "top_candidates": [
                {
                    "score": row[0],
                    "source_index": row[1],
                    "output": row[2],
                }
                for row in candidates[:top_n]
            ],
        }

    @torch.no_grad()
    def nearest_prompt_response(self, prompt: str) -> str:
        p = self._encode_texts([prompt], "prompt")[0]
        index = int((self._prompt_vectors @ p).argmax())
        return self.records[index].response[:self.cfg.max_response_chars]

    def state_dict(self) -> dict:
        return {
            "config": asdict(self.cfg),
            "encoder": self.encoder.state_dict(),
            "records": [asdict(r) for r in self.records],
            "idf": self.idf,
        }
