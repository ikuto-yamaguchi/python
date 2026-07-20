from __future__ import annotations

import re

import torch

from .pact_commitment_compiler import PACTCompiler, SlotSpec, TemplateRecord, split_sentences


class FastPACTCompiler(PACTCompiler):
    """PACT runtime with one morphological analysis per user utterance."""

    @staticmethod
    def _bind_from_tokens(spec: SlotSpec, tokens: list[str], used: set[str]) -> str:
        if not tokens:
            return spec.token
        typed = [
            token
            for token in tokens
            if PACTCompiler._slot_kind(token) == spec.kind and token not in used
        ]
        candidates = typed or [token for token in tokens if token not in used] or tokens
        if spec.token in candidates:
            return spec.token
        target = int(round(spec.relative_position * max(0, len(candidates) - 1)))
        return candidates[min(target, len(candidates) - 1)]

    def instantiate_from_tokens(
        self,
        record: TemplateRecord,
        prompt_tokens: list[str],
    ) -> str:
        text = record.template
        used: set[str] = set()
        for index, spec in enumerate(record.slots):
            value = self._bind_from_tokens(spec, prompt_tokens, used)
            used.add(value)
            text = text.replace(f"{{{{S{index}}}}}", value)
        return text.strip()[:self.cfg.max_response_chars]

    @torch.no_grad()
    def respond(self, prompt: str, top_n: int = 8) -> tuple[str, dict]:
        if not self.records:
            raise RuntimeError("model is not trained")
        self.encoder.eval()
        p_vec = self._encode_texts([prompt], "prompt")[0]
        lexical = self._lexical_candidates(prompt)[:48]
        semantic_scores = self._response_vectors @ p_vec
        semantic = semantic_scores.topk(
            min(48, len(self.records))
        ).indices.tolist()
        candidate_ids = list(dict.fromkeys(lexical + semantic))[:64]
        if not candidate_ids:
            candidate_ids = semantic[:64]

        prompt_tokens = self._content_tokens(prompt)
        prompt_unique = set(prompt_tokens)
        candidates = []
        for index in candidate_ids:
            record = self.records[index]
            output = self.instantiate_from_tokens(record, prompt_tokens)
            if self._degenerate(output):
                continue
            compatibility = float(self._response_vectors[index] @ p_vec)
            prompt_similarity = float(self._prompt_vectors[index] @ p_vec)
            lexical_overlap = sum(token in output for token in prompt_unique) / max(
                1, len(prompt_unique)
            )
            source_overlap = sum(
                token in record.prompt for token in prompt_unique
            ) / max(1, len(prompt_unique))
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
                (score, index, output, compatibility, lexical_overlap)
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
            "active_candidates": len(candidates),
            "top_candidates": [
                {
                    "score": row[0],
                    "source_index": row[1],
                    "output": row[2],
                }
                for row in candidates[:top_n]
            ],
        }
