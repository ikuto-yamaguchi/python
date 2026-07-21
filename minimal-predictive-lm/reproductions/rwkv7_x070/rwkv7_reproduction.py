from __future__ import annotations

import argparse
import io
import json
import random
import resource
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import torch
torch.set_num_threads(1)
from torch import Tensor, nn
import torch.nn.functional as F


TOKENS = [
    "<pad>", "<bos>", "<eos>", "記録", "更新", "質問", "回答", "は", "の", "色", "。", "？",
    "葵", "蓮", "凛", "空", "海", "森", "赤", "青", "緑", "白", "黒", "黄",
    "雑音", "静か", "速い", "丸い", "遠い", "近い",
]
TOKEN_TO_ID = {token: i for i, token in enumerate(TOKENS)}
PAD_ID = TOKEN_TO_ID["<pad>"]
BOS_ID = TOKEN_TO_ID["<bos>"]
NAMES = ["葵", "蓮", "凛", "空", "海", "森"]
COLORS = ["赤", "青", "緑", "白", "黒", "黄"]
DISTRACTORS = ["静か", "速い", "丸い", "遠い", "近い"]


def encode(tokens: Sequence[str]) -> list[int]:
    return [TOKEN_TO_ID[token] for token in tokens]


def make_example(rng: random.Random, depth: int, held_out: bool) -> tuple[list[int], int]:
    # Evaluation uses independent episodes; held_out adds an assignment perturbation.
    names = rng.sample(NAMES, 4)
    colors = rng.sample(COLORS, 4)
    if held_out:
        colors = colors[1:] + colors[:1]
    state = dict(zip(names, colors))
    tokens = ["<bos>"]
    for name in names:
        tokens += ["記録", name, "は", state[name], "。"]
    for _ in range(depth):
        if rng.random() < 0.75:
            name = rng.choice(names)
            color = rng.choice(COLORS)
            state[name] = color
            tokens += ["更新", name, "は", color, "。"]
        else:
            tokens += ["雑音", rng.choice(DISTRACTORS), "。"]
    query = rng.choice(names)
    tokens += ["質問", query, "の", "色", "は", "？", "回答", state[query], "<eos>"]
    ids = encode(tokens)
    return ids, len(ids) - 2


class StateTrackingDataset(torch.utils.data.Dataset):
    def __init__(self, size: int, seed: int, held_out: bool, depth: int = 8) -> None:
        rng = random.Random(seed)
        self.examples = [make_example(rng, depth=depth, held_out=held_out) for _ in range(size)]

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> tuple[Tensor, int]:
        ids, answer_position = self.examples[index]
        return torch.tensor(ids, dtype=torch.long), answer_position


def collate(batch: Sequence[tuple[Tensor, int]]) -> tuple[Tensor, Tensor, Tensor]:
    max_len = max(len(ids) for ids, _ in batch)
    inputs = torch.full((len(batch), max_len - 1), PAD_ID, dtype=torch.long)
    targets = torch.full_like(inputs, -100)
    answer_indices = torch.empty(len(batch), dtype=torch.long)
    for row, (ids, answer_position) in enumerate(batch):
        inputs[row, : len(ids) - 1] = ids[:-1]
        targets[row, : len(ids) - 1] = ids[1:]
        answer_indices[row] = answer_position - 1
    return inputs, targets, answer_indices


@dataclass
class LayerState:
    att_x: Tensor
    att_kv: Tensor
    ffn_x: Tensor


class RWKV7TimeMix(nn.Module):
    """Readable recurrent RWKV-7 x070 TimeMix.

    The state update follows the official RNN demo:
      S_t = S_{t-1} * w + S_{t-1} @ (-kk outer kk*a) + v outer k
    """

    def __init__(self, dim: int, head_size: int, layer_id: int, n_layer: int, delta_enabled: bool = True) -> None:
        super().__init__()
        if dim % head_size:
            raise ValueError("dim must be divisible by head_size")
        self.dim = dim
        self.head_size = head_size
        self.n_head = dim // head_size
        self.layer_id = layer_id
        self.delta_enabled = delta_enabled

        ratio = layer_id / max(1, n_layer - 1)
        base_mix = torch.linspace(0.05, 0.95, dim)
        for name, offset in (("x_r", 0.00), ("x_w", 0.05), ("x_k", 0.10), ("x_v", 0.15), ("x_a", 0.20), ("x_g", 0.25)):
            value = (base_mix + offset * (1.0 - ratio)).clamp(0.0, 1.0)
            setattr(self, name, nn.Parameter(value))

        rank = max(4, dim // 4)
        self.w1 = nn.Linear(dim, rank, bias=False)
        self.w2 = nn.Linear(rank, dim, bias=False)
        self.a1 = nn.Linear(dim, rank, bias=False)
        self.a2 = nn.Linear(rank, dim, bias=False)
        self.g1 = nn.Linear(dim, rank, bias=False)
        self.g2 = nn.Linear(rank, dim, bias=False)
        self.v1 = nn.Linear(dim, rank, bias=False)
        self.v2 = nn.Linear(rank, dim, bias=False)

        self.w0 = nn.Parameter(torch.linspace(-1.5, 0.5, dim))
        self.a0 = nn.Parameter(torch.zeros(dim))
        self.v0 = nn.Parameter(torch.zeros(dim))
        self.k_k = nn.Parameter(torch.ones(dim))
        self.k_a = nn.Parameter(torch.ones(dim))
        self.r_k = nn.Parameter(torch.zeros(self.n_head, head_size))

        self.receptance = nn.Linear(dim, dim, bias=False)
        self.key = nn.Linear(dim, dim, bias=False)
        self.value = nn.Linear(dim, dim, bias=False)
        self.output = nn.Linear(dim, dim, bias=False)
        self.ln_x_weight = nn.Parameter(torch.ones(dim))
        self.ln_x_bias = nn.Parameter(torch.zeros(dim))

    def forward(self, x: Tensor, x_prev: Tensor, state: Tensor, v_first: Tensor | None) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        batch = x.shape[0]
        xx = x_prev - x
        xr = x + xx * self.x_r
        xw = x + xx * self.x_w
        xk = x + xx * self.x_k
        xv = x + xx * self.x_v
        xa = x + xx * self.x_a
        xg = x + xx * self.x_g

        r = self.receptance(xr)
        w_logits = self.w0 + self.w2(torch.tanh(self.w1(xw)))
        w = torch.exp(-0.606531 * torch.sigmoid(w_logits))
        k = self.key(xk)
        v = self.value(xv)
        a = torch.sigmoid(self.a0 + self.a2(self.a1(xa)))
        g = self.g2(torch.sigmoid(self.g1(xg)))

        kk = (k * self.k_k).view(batch, self.n_head, self.head_size)
        kk = F.normalize(kk, dim=-1, p=2.0).reshape(batch, self.dim)
        k = k * (1.0 + (a - 1.0) * self.k_a)

        if self.layer_id == 0 or v_first is None:
            v_first = v
        else:
            v = v + (v_first - v) * torch.sigmoid(self.v0 + self.v2(self.v1(xv)))

        v_h = v.view(batch, self.n_head, self.head_size)
        k_h = k.view(batch, self.n_head, self.head_size)
        r_h = r.view(batch, self.n_head, self.head_size)
        kk_h = kk.view(batch, self.n_head, self.head_size)
        a_h = a.view(batch, self.n_head, self.head_size)

        vk = v_h.unsqueeze(-1) @ k_h.unsqueeze(-2)
        if self.delta_enabled:
            ab = (-kk_h).unsqueeze(-1) @ (kk_h * a_h).unsqueeze(-2)
            state = state * w.view(batch, self.n_head, 1, self.head_size) + state @ ab + vk
        else:
            state = state * w.view(batch, self.n_head, 1, self.head_size) + vk

        out = (state @ r_h.unsqueeze(-1)).squeeze(-1).reshape(batch, self.dim)
        out = F.group_norm(out, self.n_head, self.ln_x_weight, self.ln_x_bias, eps=64e-5)
        bonus = ((r_h * k_h * self.r_k).sum(dim=-1, keepdim=True) * v_h).reshape(batch, self.dim)
        return self.output((out + bonus) * g), x, state, v_first


class RWKV7ChannelMix(nn.Module):
    def __init__(self, dim: int) -> None:
        super().__init__()
        self.x_k = nn.Parameter(torch.linspace(0.1, 0.9, dim))
        hidden = dim * 3
        self.key = nn.Linear(dim, hidden, bias=False)
        self.value = nn.Linear(hidden, dim, bias=False)

    def forward(self, x: Tensor, x_prev: Tensor) -> tuple[Tensor, Tensor]:
        k = x + (x_prev - x) * self.x_k
        return self.value(F.relu(self.key(k)).square()), x


class RWKV7Block(nn.Module):
    def __init__(self, dim: int, head_size: int, layer_id: int, n_layer: int, delta_enabled: bool) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(dim)
        self.ln2 = nn.LayerNorm(dim)
        self.att = RWKV7TimeMix(dim, head_size, layer_id, n_layer, delta_enabled)
        self.ffn = RWKV7ChannelMix(dim)

    def forward(self, x: Tensor, state: LayerState, v_first: Tensor | None) -> tuple[Tensor, LayerState, Tensor]:
        att_out, att_x, att_kv, v_first = self.att(self.ln1(x), state.att_x, state.att_kv, v_first)
        x = x + att_out
        ffn_out, ffn_x = self.ffn(self.ln2(x), state.ffn_x)
        x = x + ffn_out
        return x, LayerState(att_x, att_kv, ffn_x), v_first


class TinyRWKV7LM(nn.Module):
    def __init__(self, vocab_size: int, dim: int = 32, n_layer: int = 2, head_size: int = 8, delta_enabled: bool = True) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.dim = dim
        self.n_layer = n_layer
        self.head_size = head_size
        self.embedding = nn.Embedding(vocab_size, dim)
        self.blocks = nn.ModuleList([
            RWKV7Block(dim, head_size, i, n_layer, delta_enabled) for i in range(n_layer)
        ])
        self.ln_out = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, vocab_size, bias=False)
        self.head.weight = self.embedding.weight

    def initial_state(self, batch_size: int, device: torch.device | None = None) -> list[LayerState]:
        device = device or self.embedding.weight.device
        dtype = self.embedding.weight.dtype
        n_head = self.dim // self.head_size
        return [
            LayerState(
                torch.zeros(batch_size, self.dim, device=device, dtype=dtype),
                torch.zeros(batch_size, n_head, self.head_size, self.head_size, device=device, dtype=torch.float32),
                torch.zeros(batch_size, self.dim, device=device, dtype=dtype),
            )
            for _ in range(self.n_layer)
        ]

    def step(self, token: Tensor, state: list[LayerState]) -> tuple[Tensor, list[LayerState]]:
        x = self.embedding(token)
        v_first = None
        new_state: list[LayerState] = []
        for block, layer_state in zip(self.blocks, state):
            x, next_state, v_first = block(x, layer_state, v_first)
            new_state.append(next_state)
        return self.head(self.ln_out(x)), new_state

    def forward(self, tokens: Tensor, state: list[LayerState] | None = None) -> tuple[Tensor, list[LayerState]]:
        batch, length = tokens.shape
        state = self.initial_state(batch, tokens.device) if state is None else state
        logits = []
        for index in range(length):
            step_logits, state = self.step(tokens[:, index], state)
            logits.append(step_logits)
        return torch.stack(logits, dim=1), state

    def state_elements(self, batch_size: int = 1) -> int:
        return sum(s.att_x.numel() + s.att_kv.numel() + s.ffn_x.numel() for s in self.initial_state(batch_size))


@dataclass
class RunMetrics:
    architecture: str
    seed: int
    train_examples: int
    parameters: int
    model_bytes: int
    recurrent_state_bytes: int
    peak_rss_kib: int
    train_seconds: float
    answer_accuracy: float
    stress_answer_accuracy: float
    validation_nll: float
    token_latency_ms: float
    full_softmax_candidates: int
    recurrent_state_reads: int


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def evaluate(model: TinyRWKV7LM, loader: torch.utils.data.DataLoader) -> tuple[float, float]:
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    correct = 0
    count = 0
    with torch.no_grad():
        for inputs, targets, answer_indices in loader:
            logits, _ = model(inputs)
            loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), targets.reshape(-1), ignore_index=-100, reduction="sum")
            total_loss += float(loss)
            total_tokens += int(targets.ne(-100).sum())
            rows = torch.arange(inputs.shape[0])
            answer_logits = logits[rows, answer_indices]
            answer_targets = targets[rows, answer_indices]
            correct += int((answer_logits.argmax(dim=-1) == answer_targets).sum())
            count += inputs.shape[0]
    return correct / max(1, count), total_loss / max(1, total_tokens)


def serialized_size(model: nn.Module) -> int:
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    return buffer.tell()


def benchmark_token_latency(model: TinyRWKV7LM, steps: int = 128) -> float:
    model.eval()
    token = torch.tensor([BOS_ID])
    state = model.initial_state(1)
    with torch.no_grad():
        for _ in range(16):
            _, state = model.step(token, state)
        start = time.perf_counter()
        for index in range(steps):
            token = torch.tensor([(index % (len(TOKENS) - 1)) + 1])
            _, state = model.step(token, state)
        elapsed = time.perf_counter() - start
    return elapsed * 1000.0 / steps


def train_one(architecture: str, seed: int, train_examples: int, epochs: int = 2) -> RunMetrics:
    seed_everything(seed)
    model = TinyRWKV7LM(
        len(TOKENS), dim=16, n_layer=1, head_size=8,
        delta_enabled=architecture == "rwkv7",
    )
    train_set = StateTrackingDataset(train_examples, seed * 1009 + train_examples, held_out=False, depth=5)
    valid_set = StateTrackingDataset(128, 910_000 + seed, held_out=True, depth=5)
    stress_set = StateTrackingDataset(128, 920_000 + seed, held_out=True, depth=16)
    generator = torch.Generator().manual_seed(seed)
    train_loader = torch.utils.data.DataLoader(train_set, batch_size=32, shuffle=True, generator=generator, collate_fn=collate)
    valid_loader = torch.utils.data.DataLoader(valid_set, batch_size=64, shuffle=False, collate_fn=collate)
    stress_loader = torch.utils.data.DataLoader(stress_set, batch_size=64, shuffle=False, collate_fn=collate)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=0.01)

    model.train()
    started = time.perf_counter()
    for _ in range(epochs):
        for inputs, targets, answer_indices in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(inputs)
            token_loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), targets.reshape(-1), ignore_index=-100)
            rows = torch.arange(inputs.shape[0])
            answer_loss = F.cross_entropy(logits[rows, answer_indices], targets[rows, answer_indices])
            loss = 0.35 * token_loss + 0.65 * answer_loss
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
    train_seconds = time.perf_counter() - started
    accuracy, nll = evaluate(model, valid_loader)
    stress_accuracy, _ = evaluate(model, stress_loader)
    return RunMetrics(
        architecture=architecture,
        seed=seed,
        train_examples=train_examples,
        parameters=sum(p.numel() for p in model.parameters()),
        model_bytes=serialized_size(model),
        recurrent_state_bytes=model.state_elements(1) * 4,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        train_seconds=train_seconds,
        answer_accuracy=accuracy,
        stress_answer_accuracy=stress_accuracy,
        validation_nll=nll,
        token_latency_ms=benchmark_token_latency(model),
        full_softmax_candidates=len(TOKENS),
        recurrent_state_reads=model.state_elements(1),
    )


def streaming_equivalence() -> float:
    seed_everything(123)
    model = TinyRWKV7LM(len(TOKENS), dim=24, n_layer=2, head_size=8)
    model.eval()
    tokens = torch.tensor([[BOS_ID] + list(range(3, 18))])
    with torch.no_grad():
        full, _ = model(tokens)
        first, state = model(tokens[:, :7])
        second, _ = model(tokens[:, 7:], state)
    return float((full - torch.cat([first, second], dim=1)).abs().max())


def state_size_invariance() -> dict[str, int]:
    model = TinyRWKV7LM(len(TOKENS), dim=32, n_layer=2, head_size=8)
    return {str(length): model.state_elements(1) * 4 for length in (16, 64, 256, 1024)}


def run_experiment(output: Path) -> dict:
    all_metrics: list[RunMetrics] = []
    for train_examples in (128, 512, 1024):
        for seed in (1, 7, 19):
            all_metrics.append(train_one("rwkv7", seed, train_examples, epochs=2))
    for seed in (1, 7, 19):
        all_metrics.append(train_one("rwkv7_no_delta", seed, 1024, epochs=2))

    aggregate: dict[str, dict[str, dict[str, float]]] = {}
    scales_by_architecture = {"rwkv7": (128, 512, 1024), "rwkv7_no_delta": (1024,)}
    for architecture, scales in scales_by_architecture.items():
        aggregate[architecture] = {}
        for scale in scales:
            rows = [m for m in all_metrics if m.architecture == architecture and m.train_examples == scale]
            aggregate[architecture][str(scale)] = {
                "answer_accuracy_mean": statistics.mean(m.answer_accuracy for m in rows),
                "answer_accuracy_min": min(m.answer_accuracy for m in rows),
                "stress_answer_accuracy_mean": statistics.mean(m.stress_answer_accuracy for m in rows),
                "validation_nll_mean": statistics.mean(m.validation_nll for m in rows),
                "train_seconds_mean": statistics.mean(m.train_seconds for m in rows),
                "token_latency_ms_mean": statistics.mean(m.token_latency_ms for m in rows),
                "model_bytes_max": max(m.model_bytes for m in rows),
                "peak_rss_kib_max": max(m.peak_rss_kib for m in rows),
            }

    report = {
        "claim_scope": {
            "reproduced": [
                "RWKV-7 x070 recurrent state update in a readable PyTorch implementation",
                "streaming and one-pass recurrence equivalence",
                "constant recurrent-state size with sequence length",
                "delta-rule ablation on unseen Japanese state-tracking episodes",
            ],
            "not_reproduced": [
                "paper-scale language-model quality",
                "official checkpoint scores",
                "free Japanese dialogue",
                "high-school-level intelligence",
                "physical weak-smartphone latency",
            ],
            "completion": False,
            "highschool_level_passed": False,
            "native_japanese_communication_passed": False,
        },
        "official_reference": {
            "paper": "RWKV-7 Goose with Expressive Dynamic State Evolution, arXiv:2503.14456",
            "code": "BlinkDL/RWKV-LM RWKV-v7/rwkv_v7_demo_rnn.py",
        },
        "streaming_max_abs_error": streaming_equivalence(),
        "state_bytes_by_context_length": state_size_invariance(),
        "chance_answer_accuracy": 1.0 / len(COLORS),
        "aggregate": aggregate,
        "interpretation": {
            "constant_state_reproduced": True,
            "streaming_equivalence_reproduced": True,
            "delta_advantage_reproduced": False,
            "reason": (
                "At 1024 examples the full update improved validation NLL slightly, "
                "but answer accuracy stayed near the 1/6 chance level and did not "
                "consistently beat the equal-parameter no-delta ablation."
            ),
        },
        "runs": [asdict(metric) for metric in all_metrics],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/rwkv7_reproduction_report.json"))
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_experiment(args.output)
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))
    print(f"streaming_max_abs_error={report['streaming_max_abs_error']:.3e}")
    print(f"report={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
