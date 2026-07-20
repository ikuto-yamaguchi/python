from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence

import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class CloseConfig:
    model_id: str = "loiccabannes/MambaSan-130m-instruct"
    max_state_tokens: int = 224
    max_prompt_tokens: int = 448
    max_new_tokens: int = 64
    closure_dim: int = 96
    margin: float = 0.65
    head_steps: int = 320
    head_lr: float = 3e-3
    state_batch_size: int = 4
    seed: int = 29


class ObligationSettlementEnergy(nn.Module):
    """Energy of an answer closing an unresolved recurrent obligation.

    The prompt-ending state is projected into an obligation vector.  The state
    transition produced by appending an answer is projected into a settlement
    vector.  A valid answer should align the two; an unrelated answer should
    leave high energy.  This is deliberately not a task classifier and does
    not receive task names or answer labels.
    """

    def __init__(self, hidden_size: int, closure_dim: int):
        super().__init__()
        self.obligation = nn.Sequential(
            nn.Linear(hidden_size, closure_dim, bias=False),
            nn.Tanh(),
            nn.Linear(closure_dim, closure_dim, bias=False),
        )
        self.settlement = nn.Sequential(
            nn.Linear(hidden_size, closure_dim, bias=False),
            nn.Tanh(),
            nn.Linear(closure_dim, closure_dim, bias=False),
        )
        self.residual_gate = nn.Sequential(
            nn.Linear(hidden_size * 2, closure_dim),
            nn.Sigmoid(),
        )

    def energy(self, open_state: torch.Tensor, closed_state: torch.Tensor) -> torch.Tensor:
        delta = closed_state - open_state
        obligation = F.normalize(self.obligation(open_state), dim=-1)
        settlement = F.normalize(self.settlement(delta), dim=-1)
        gate = self.residual_gate(torch.cat([open_state, delta], dim=-1))
        residual = (obligation - settlement) * gate
        return residual.square().sum(-1)

    def ranking_loss(
        self,
        open_state: torch.Tensor,
        positive_closed: torch.Tensor,
        negative_closed: torch.Tensor,
        margin: float,
    ) -> dict[str, torch.Tensor]:
        positive = self.energy(open_state, positive_closed)
        negative = self.energy(open_state, negative_closed)
        ranking = F.relu(margin + positive - negative).mean()
        calibration = positive.mean() + F.relu(0.20 - negative).mean()
        loss = ranking + 0.25 * calibration
        return {
            "loss": loss,
            "positive_energy": positive.mean().detach(),
            "negative_energy": negative.mean().detach(),
            "ranking_accuracy": (positive < negative).float().mean().detach(),
        }


class MambaSanRuntime:
    """CPU-compatible Hugging Face conversion of an original mamba_ssm checkpoint."""

    def __init__(self, cfg: CloseConfig, cache_dir: Path):
        self.cfg = cfg
        self.cache_dir = cache_dir
        self.snapshot_dir: Path | None = None
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cpu")

    def load(self) -> dict:
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer, MambaConfig, MambaForCausalLM

        torch.manual_seed(self.cfg.seed)
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
        original_config = json.loads(snapshot.joinpath("config.json").read_text())
        d_model = int(original_config["d_model"])
        n_layer = int(original_config["n_layer"])
        vocab_size = int(original_config["vocab_size"])
        multiple = int(original_config.get("pad_vocab_size_multiple", 8))
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
        allowed_missing = {
            key for key in missing if key.endswith(".bias") and "dt_proj" in key
        }
        real_missing = [key for key in missing if key not in allowed_missing]
        if real_missing or unexpected:
            raise RuntimeError(
                f"checkpoint conversion mismatch: missing={real_missing[:8]} "
                f"unexpected={unexpected[:8]}"
            )
        tokenizer = AutoTokenizer.from_pretrained(snapshot, use_fast=False)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token or tokenizer.sep_token or tokenizer.unk_token
        model.config.pad_token_id = tokenizer.pad_token_id
        if tokenizer.eos_token_id is not None:
            model.config.eos_token_id = tokenizer.eos_token_id
        if tokenizer.bos_token_id is not None:
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
            "missing_allowed": sorted(allowed_missing),
        }

    def _require_loaded(self):
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("runtime is not loaded")

    @torch.inference_mode()
    def encode_states(self, texts: Sequence[str], max_tokens: int | None = None) -> torch.Tensor:
        self._require_loaded()
        max_tokens = max_tokens or self.cfg.max_state_tokens
        outputs = []
        for start in range(0, len(texts), self.cfg.state_batch_size):
            batch = list(texts[start : start + self.cfg.state_batch_size])
            tokens = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_tokens,
            )
            result = self.model(
                **tokens,
                output_hidden_states=True,
                use_cache=False,
                return_dict=True,
            )
            hidden = result.hidden_states[-1]
            positions = tokens["attention_mask"].sum(-1).sub(1).clamp_min(0)
            rows = torch.arange(hidden.size(0))
            outputs.append(hidden[rows, positions].float().cpu())
        return torch.cat(outputs, dim=0)

    @staticmethod
    def prompt_variants(prompt: str) -> list[str]:
        return [
            f"質問：{prompt}\n回答：",
            f"指示：{prompt}\n応答：",
            f"ユーザー：{prompt}\nアシスタント：",
        ]

    @torch.inference_mode()
    def generate_candidates(self, prompt: str) -> list[dict]:
        self._require_loaded()
        candidates: list[dict] = []
        settings = [
            {"do_sample": False},
            {"do_sample": True, "temperature": 0.72, "top_p": 0.90},
        ]
        for variant_index, formatted in enumerate(self.prompt_variants(prompt)):
            tokens = self.tokenizer(
                formatted,
                return_tensors="pt",
                truncation=True,
                max_length=self.cfg.max_prompt_tokens,
            )
            input_len = tokens["input_ids"].shape[1]
            for setting_index, setting in enumerate(settings):
                generated = self.model.generate(
                    **tokens,
                    max_new_tokens=self.cfg.max_new_tokens,
                    repetition_penalty=1.12,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    **setting,
                )
                new_ids = generated[0, input_len:]
                text = self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()
                if text and text not in {row["text"] for row in candidates}:
                    candidates.append(
                        {
                            "text": text,
                            "formatted_prompt": formatted,
                            "variant": variant_index,
                            "setting": setting_index,
                        }
                    )
        return candidates

    def copy_package(self, target: Path) -> int:
        self._require_loaded()
        if self.snapshot_dir is None:
            raise RuntimeError("snapshot path is missing")
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(self.snapshot_dir, target)
        return sum(path.stat().st_size for path in target.rglob("*") if path.is_file())


def train_closure_head(
    head: ObligationSettlementEnergy,
    open_states: torch.Tensor,
    positive_states: torch.Tensor,
    negative_states: torch.Tensor,
    cfg: CloseConfig,
) -> dict:
    torch.manual_seed(cfg.seed)
    optimizer = torch.optim.AdamW(head.parameters(), lr=cfg.head_lr, weight_decay=1e-4)
    history = []
    for step in range(cfg.head_steps):
        losses = head.ranking_loss(
            open_states,
            positive_states,
            negative_states,
            cfg.margin,
        )
        optimizer.zero_grad(set_to_none=True)
        losses["loss"].backward()
        torch.nn.utils.clip_grad_norm_(head.parameters(), 1.0)
        optimizer.step()
        if step == 0 or (step + 1) % 40 == 0:
            history.append(
                {"step": step + 1}
                | {key: float(value.detach()) for key, value in losses.items()}
            )
    with torch.no_grad():
        final = head.ranking_loss(
            open_states,
            positive_states,
            negative_states,
            cfg.margin,
        )
    return {
        "history": history,
        "final": {key: float(value) for key, value in final.items()},
        "head_bytes": sum(p.numel() * p.element_size() for p in head.parameters()),
    }


@torch.inference_mode()
def select_by_closure(
    runtime: MambaSanRuntime,
    head: ObligationSettlementEnergy,
    prompt: str,
    candidates: list[dict],
) -> tuple[str, list[dict]]:
    if not candidates:
        return "", []
    open_state = runtime.encode_states([prompt])[0]
    closed_texts = [f"{prompt}\n回答：{row['text']}" for row in candidates]
    closed_states = runtime.encode_states(closed_texts)
    repeated_open = open_state.unsqueeze(0).expand_as(closed_states)
    energies = head.energy(repeated_open, closed_states).tolist()
    scored = []
    for row, energy in zip(candidates, energies):
        scored.append(dict(row) | {"closure_energy": float(energy)})
    scored.sort(key=lambda row: row["closure_energy"])
    return scored[0]["text"], scored


def config_json(cfg: CloseConfig) -> dict:
    return asdict(cfg)
