from __future__ import annotations

import json
import math
from pathlib import Path

import torch

from .close_obligation_energy import CloseConfig, MambaSanRuntime


class MambaPySanRuntime(MambaSanRuntime):
    """Load the same frozen Japanese Mamba through the parallel mamba.py backend."""

    def load(self) -> dict:
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer, MambaConfig, MambaForCausalLM

        torch.manual_seed(self.cfg.seed)
        torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
        snapshot = Path(
            snapshot_download(
                self.cfg.model_id,
                cache_dir=str(self.cache_dir),
                allow_patterns=[
                    "*.bin",
                    "*.json",
                    "*.txt",
                    "*.model",
                    "*.py",
                ],
            )
        )
        self.snapshot_dir = snapshot
        original = json.loads(snapshot.joinpath("config.json").read_text())
        d_model = int(original["d_model"])
        n_layer = int(original["n_layer"])
        vocab_size = int(original["vocab_size"])
        multiple = int(original.get("pad_vocab_size_multiple", 8))
        if vocab_size % multiple:
            vocab_size += multiple - vocab_size % multiple

        config = MambaConfig(
            hidden_size=d_model,
            intermediate_size=d_model * 2,
            time_step_rank=math.ceil(d_model / 16),
            num_hidden_layers=n_layer,
            vocab_size=vocab_size,
            state_size=16,
            conv_kernel=4,
            expand=2,
            use_cache=True,
            use_mambapy=True,
        )
        model = MambaForCausalLM(config)
        weight_files = [
            path
            for path in snapshot.glob("*.bin")
            if path.stat().st_size > 10_000_000
        ]
        if not weight_files:
            raise FileNotFoundError("MambaSan model weight file not found")
        weight_path = max(weight_files, key=lambda path: path.stat().st_size)
        state = torch.load(weight_path, map_location="cpu", weights_only=True)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        if isinstance(state, dict) and "model" in state and isinstance(state["model"], dict):
            state = state["model"]
        missing, unexpected = model.load_state_dict(state, strict=False)
        if missing or unexpected:
            raise RuntimeError(
                f"checkpoint conversion mismatch: missing={missing[:8]} "
                f"unexpected={unexpected[:8]}"
            )
        tokenizer = AutoTokenizer.from_pretrained(snapshot, use_fast=False)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token or tokenizer.unk_token
        model.config.pad_token_id = tokenizer.pad_token_id
        model.config.eos_token_id = tokenizer.eos_token_id
        model.config.bos_token_id = tokenizer.bos_token_id
        model.eval()
        self.model = model
        self.tokenizer = tokenizer
        return {
            "model_id": self.cfg.model_id,
            "source_weight_bytes": weight_path.stat().st_size,
            "snapshot_bytes": sum(
                path.stat().st_size for path in snapshot.rglob("*") if path.is_file()
            ),
            "hidden_size": d_model,
            "layers": n_layer,
            "vocab_size": vocab_size,
            "backend": "mambapy",
        }

    def _chat_prompt(self, prompt: str) -> str:
        self._require_loaded()
        try:
            return self.tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception:
            return f"\n### User:\n{prompt}\n### Assistant:\n"

    @torch.inference_mode()
    def generate_candidates(self, prompt: str) -> list[dict]:
        self._require_loaded()
        formatted = self._chat_prompt(prompt)
        tokens = self.tokenizer(
            formatted,
            return_tensors="pt",
            truncation=True,
            max_length=self.cfg.max_prompt_tokens,
        )
        input_len = tokens["input_ids"].shape[1]
        settings = [
            {"do_sample": False},
            {"do_sample": True, "temperature": 0.75, "top_p": 0.90},
        ]
        candidates = []
        for index, setting in enumerate(settings):
            torch.manual_seed(self.cfg.seed + index)
            generated = self.model.generate(
                **tokens,
                max_new_tokens=self.cfg.max_new_tokens,
                repetition_penalty=1.12,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **setting,
            )
            text = self.tokenizer.decode(
                generated[0, input_len:], skip_special_tokens=True
            ).strip()
            if text and text not in {row["text"] for row in candidates}:
                candidates.append(
                    {
                        "text": text,
                        "formatted_prompt": formatted,
                        "variant": 0,
                        "setting": index,
                    }
                )
        return candidates
