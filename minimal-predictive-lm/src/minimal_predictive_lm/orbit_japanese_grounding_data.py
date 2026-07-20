from __future__ import annotations

import random
from typing import Iterable

from .orbit_japanese_grounding_core import Episode, GroundedOrbit
from .orbit_japanese_grounding_dialogue import Dialogue, DialogueTurn, DiscourseOrbit

BOXES_TRAIN = ("赤い箱", "青い箱", "木の箱", "銀の箱", "倉庫A", "倉庫B", "棚一", "棚二")
BOXES_TEST = ("月の箱", "星の箱", "保管庫X", "保管庫Y", "北の棚", "南の棚")
ITEMS_TRAIN = ("りんご", "みかん", "電池", "カード", "ねじ", "コイン")
ITEMS_TEST = ("ビー玉", "切符", "歯車", "石けん")
STATE_STYLES = (
    "{box}には{item}が{n}個あります。",
    "{box}が持つ{item}は{n}個です。",
    "{item}は{box}に{n}個入っています。",
)
STATE_HELDOUT = ("現在、{box}には{item}が合計{n}個あります。",)
TRANSFER_TRAIN = (
    "{src}から{dst}へ{item}を{n}個移した。",
    "{src}は{dst}に{item}を{n}個渡した。",
    "{item}を{n}個、{src}から{dst}へ動かした。",
    "{dst}へ{src}から{item}を{n}個送った。",
)
TRANSFER_TEST = (
    "{src}から{dst}へ{item}を{n}個渡した。",
    "{item}を{n}個、{src}から{dst}へ送った。",
    "{src}は{dst}に{item}を{n}個動かした。",
)
NEGATIVE_TRAIN = (
    "{src}から{dst}へ{item}を{n}個移していない。",
    "{src}は{dst}に{item}を{n}個渡していない。",
)
NEGATIVE_TEST = ("{item}を{n}個、{src}から{dst}へ送っていない。",)


def render(src: str, dst: str, item: str, a: int, b: int, styles: tuple[str, str]) -> str:
    return styles[0].format(box=src, item=item, n=a) + styles[1].format(box=dst, item=item, n=b)


def make_episode(
    rng: random.Random,
    *,
    train: bool,
    noop: bool = False,
    recombined: bool = False,
    heldout_state: bool = False,
) -> Episode:
    boxes, items = (BOXES_TRAIN, ITEMS_TRAIN) if train else (BOXES_TEST, ITEMS_TEST)
    src, dst = rng.sample(boxes, 2)
    item = rng.choice(items)
    a, b = rng.randint(3, 12), rng.randint(0, 8)
    amount = rng.randint(1, min(3, a))
    available = STATE_HELDOUT if heldout_state else STATE_STYLES
    styles = tuple(rng.sample(available, 2)) if len(available) > 1 else (available[0], available[0])
    before = render(src, dst, item, a, b, styles)
    after = before if noop else render(src, dst, item, a - amount, b + amount, styles)
    templates = (
        NEGATIVE_TEST if noop and recombined else
        NEGATIVE_TRAIN if noop else
        TRANSFER_TEST if recombined else
        TRANSFER_TRAIN
    )
    command = rng.choice(templates).format(src=src, dst=dst, item=item, n=amount)
    return Episode(command, before, after)


EXPLICIT = ("{src}から{dst}へ{item}を{n}個移した。", "{src}は{dst}に{item}を{n}個渡した。")
FOLLOWUPS = {
    "REUSE": (("さらに{n}個移した。", "続けて{n}個送った。"), ("続けて{n}個移した。", "さらに{n}個送った。")),
    "SWAP": (("今度は逆に{n}個戻した。", "反対向きへ{n}個送った。"), ("逆に{n}個送った。", "反対向きへ{n}個戻した。")),
    "UNDO": (("さっきの移動を取り消した。", "直前の操作をなかったことにした。"), ("直前の移動を取り消した。", "さっきの操作をなかったことにした。")),
    "NOOP": (("追加では動かしていない。", "続きの移動はしていない。"), ("その後は送っていない。",)),
}


def make_dialogue(rng: random.Random, operator: str, *, train: bool) -> Dialogue:
    boxes, items = (BOXES_TRAIN, ITEMS_TRAIN) if train else (BOXES_TEST, ITEMS_TEST)
    src, dst = rng.sample(boxes, 2)
    item = rng.choice(items)
    a, b = rng.randint(7, 15), rng.randint(0, 6)
    first_amount = rng.randint(1, 3)
    second_amount = rng.randint(1, min(3, a - first_amount))
    styles = tuple(rng.sample(STATE_STYLES, 2))
    zero = render(src, dst, item, a, b, styles)
    one = render(src, dst, item, a - first_amount, b + first_amount, styles)
    first = rng.choice(EXPLICIT).format(src=src, dst=dst, item=item, n=first_amount)
    templates = FOLLOWUPS[operator][0 if train else 1]
    if operator == "REUSE":
        two = render(src, dst, item, a - first_amount - second_amount, b + first_amount + second_amount, styles)
        second = rng.choice(templates).format(n=second_amount)
    elif operator == "SWAP":
        second_amount = rng.randint(1, min(3, b + first_amount))
        two = render(src, dst, item, a - first_amount + second_amount, b + first_amount - second_amount, styles)
        second = rng.choice(templates).format(n=second_amount)
    elif operator == "UNDO":
        two, second = zero, rng.choice(templates)
    else:
        two, second = one, rng.choice(templates)
    return Dialogue((DialogueTurn(first, zero, one), DialogueTurn(second, one, two)))


def accuracy(model: GroundedOrbit, episodes: Iterable[Episode]) -> float:
    rows = list(episodes)
    return sum(model.predict(row.command, row.before)[0] == row.after for row in rows) / len(rows)


def dialogue_accuracy(model: DiscourseOrbit, dialogues: Iterable[Dialogue]) -> float:
    rows = list(dialogues)
    correct = 0
    for dialogue in rows:
        model.reset()
        valid = True
        for turn in dialogue.turns:
            valid &= model.predict_turn(turn.text, turn.before)[0] == turn.after
        correct += int(valid)
    return correct / len(rows)
