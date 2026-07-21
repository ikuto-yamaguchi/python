from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

import torch
from torch import Tensor

TOKENS = [
    "<pad>", "<bos>", "<eos>", "記録", "更新", "質問", "回答", "は", "の", "色", "値",
    "加算", "減算", "偶奇", "反転", "雑音", "。", "？", "次",
    "葵", "蓮", "凛", "空", "海", "森", "赤", "青", "緑", "白", "黒", "黄",
    "0", "1", "2", "3", "4", "5", "偶", "奇", "静か", "速い", "丸い", "遠い", "近い",
]
TOKEN_TO_ID = {token: index for index, token in enumerate(TOKENS)}
PAD_ID = TOKEN_TO_ID["<pad>"]
NAMES = ["葵", "蓮", "凛", "空", "海", "森"]
COLORS = ["赤", "青", "緑", "白", "黒", "黄"]
DIGITS = ["0", "1", "2", "3", "4", "5"]
DISTRACTORS = ["静か", "速い", "丸い", "遠い", "近い"]
TASKS = ("overwrite", "multi_query", "arithmetic", "parity")
WEIGHTED_CHANCE = 7 / 30


def encode(tokens: Sequence[str]) -> list[int]:
    return [TOKEN_TO_ID[token] for token in tokens]


@dataclass
class Example:
    ids: list[int]
    answer_positions: list[int]
    task: str


def make_overwrite(rng: random.Random, depth: int, multi: bool, held_out: bool) -> Example:
    names = rng.sample(NAMES, 4)
    colors = rng.sample(COLORS, 4)
    if held_out:
        colors = colors[2:] + colors[:2]
    state = dict(zip(names, colors))
    tokens = ["<bos>"]
    for name in names:
        tokens += ["記録", name, "は", state[name], "。"]
    for _ in range(depth):
        if rng.random() < 0.72:
            name, color = rng.choice(names), rng.choice(COLORS)
            state[name] = color
            tokens += ["更新", name, "は", color, "。"]
        else:
            tokens += ["雑音", rng.choice(DISTRACTORS), "。"]
    answers = []
    for index, name in enumerate(rng.sample(names, 2 if multi else 1)):
        if index:
            tokens += ["次"]
        tokens += ["質問", name, "の", "色", "は", "？", "回答", state[name]]
        answers.append(len(tokens) - 1)
    tokens += ["<eos>"]
    return Example(encode(tokens), answers, "multi_query" if multi else "overwrite")


def make_arithmetic(rng: random.Random, depth: int, held_out: bool) -> Example:
    value = (rng.randrange(6) + (3 if held_out else 0)) % 6
    tokens = ["<bos>", "値", DIGITS[value], "。"]
    for _ in range(depth):
        if rng.random() < 0.78:
            delta = rng.randrange(1, 6)
            if rng.random() < 0.5:
                value = (value + delta) % 6
                tokens += ["加算", DIGITS[delta], "。"]
            else:
                value = (value - delta) % 6
                tokens += ["減算", DIGITS[delta], "。"]
        else:
            tokens += ["雑音", rng.choice(DISTRACTORS), "。"]
    tokens += ["質問", "値", "は", "？", "回答", DIGITS[value], "<eos>"]
    return Example(encode(tokens), [len(tokens) - 2], "arithmetic")


def make_parity(rng: random.Random, depth: int, held_out: bool) -> Example:
    parity = rng.randrange(2) ^ int(held_out)
    tokens = ["<bos>", "偶奇", "偶" if parity == 0 else "奇", "。"]
    for _ in range(depth):
        if rng.random() < 0.74:
            parity ^= 1
            tokens += ["反転", "。"]
        else:
            tokens += ["雑音", rng.choice(DISTRACTORS), "。"]
    tokens += ["質問", "偶奇", "は", "？", "回答", "偶" if parity == 0 else "奇", "<eos>"]
    return Example(encode(tokens), [len(tokens) - 2], "parity")


def make_example(rng: random.Random, task: str, depth: int, held_out: bool) -> Example:
    if task in ("overwrite", "multi_query"):
        return make_overwrite(rng, depth, task == "multi_query", held_out)
    if task == "arithmetic":
        return make_arithmetic(rng, depth, held_out)
    if task == "parity":
        return make_parity(rng, depth, held_out)
    raise ValueError(task)


class MixedSequenceDataset(torch.utils.data.Dataset):
    def __init__(self, size: int, seed: int, held_out: bool, depth: int = 6) -> None:
        rng = random.Random(seed)
        self.examples = [make_example(rng, TASKS[i % len(TASKS)], depth, held_out) for i in range(size)]
        rng.shuffle(self.examples)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> Example:
        return self.examples[index]


def collate(batch: Sequence[Example]) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    max_len = max(len(example.ids) for example in batch)
    inputs = torch.full((len(batch), max_len - 1), PAD_ID, dtype=torch.long)
    targets = torch.full_like(inputs, -100)
    answer_mask = torch.zeros_like(inputs, dtype=torch.bool)
    task_ids = torch.empty(len(batch), dtype=torch.long)
    for row, example in enumerate(batch):
        ids = torch.tensor(example.ids)
        inputs[row, : len(ids) - 1], targets[row, : len(ids) - 1] = ids[:-1], ids[1:]
        for position in example.answer_positions:
            answer_mask[row, position - 1] = True
        task_ids[row] = TASKS.index(example.task)
    return inputs, targets, answer_mask, task_ids
