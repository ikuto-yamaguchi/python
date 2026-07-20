from __future__ import annotations

import random

from .orbit_operator import TransitionEpisode

MECHANISMS = {
    "raise": {
        "train": ("{a} に {c} を上乗せする", "{a} を {c} 増やす"),
        "heldout": "{a} へ {c} を加算する",
        "arity": 1,
    },
    "assign": {
        "train": ("{a} を {c} に固定する", "{a} の値を {c} へ置き換える"),
        "heldout": "{a} を {c} と指定する",
        "arity": 1,
    },
    "mirror": {
        "train": ("{a} を基準 {c} の反対側へ写す", "{a} を中心 {c} で反転する"),
        "heldout": "{a} を軸 {c} に関して鏡映する",
        "arity": 1,
    },
    "transfer": {
        "train": ("{a} から {b} へ {c} を移す", "{b} は {a} から {c} を受け取る"),
        "heldout": "{a} から {b} に {c} を振り替える",
        "arity": 2,
    },
    "copy_plus": {
        "train": ("{a} に {c} を足した値を {b} に記録する", "{b} は {a} より {c} 大きい値になる"),
        "heldout": "{a} と {c} の和を {b} へ複写する",
        "arity": 2,
    },
    "swap": {
        "train": ("{a} と {b} の値を交換する", "{b} と {a} を入れ替える"),
        "heldout": "{a} と {b} の内容を取り替える",
        "arity": 2,
    },
}


def apply_named(
    mechanism: str,
    before: dict[str, int],
    a: str,
    b: str,
    control: int,
) -> dict[str, int]:
    after = dict(before)
    if mechanism == "raise":
        after[a] += control
    elif mechanism == "assign":
        after[a] = control
    elif mechanism == "mirror":
        after[a] = 2 * control - before[a]
    elif mechanism == "transfer":
        after[a] -= control
        after[b] += control
    elif mechanism == "copy_plus":
        after[b] = before[a] + control
    elif mechanism == "swap":
        after[a], after[b] = before[b], before[a]
    else:
        raise ValueError(mechanism)
    return after


def transition(
    mechanism: str,
    template: str,
    rng: random.Random,
    index: int,
    *,
    corrupt: bool = False,
    noise_entities: int = 0,
) -> TransitionEpisode:
    arity = int(MECHANISMS[mechanism]["arity"])
    a, b = f"対象{index}甲", f"対象{index}乙"
    control = rng.randint(2, 97)
    before = {a: rng.randint(100, 900)}
    if arity == 2:
        before[b] = rng.randint(100, 900)
    for extra in range(noise_entities):
        before[f"雑音{index}_{extra}"] = rng.randint(-1000, 1000)
    after = apply_named(mechanism, before, a, b, control)
    if corrupt:
        target = a if arity == 1 or rng.random() < 0.5 else b
        after[target] += rng.choice((-7, 5, 11))
    return TransitionEpisode(
        template.format(a=a, b=b, c=control),
        before,
        after,
        f"{mechanism}:{index}",
    )


def build_training(
    examples_per_surface: int,
    seed: int,
    noise_rate: float = 0.0,
) -> tuple[TransitionEpisode, ...]:
    rng = random.Random(seed)
    rows = []
    index = 0
    for mechanism, specification in MECHANISMS.items():
        for template in specification["train"]:
            for _ in range(examples_per_surface):
                rows.append(
                    transition(
                        mechanism,
                        template,
                        rng,
                        index,
                        corrupt=rng.random() < noise_rate,
                        noise_entities=3,
                    )
                )
                index += 1
    rng.shuffle(rows)
    return tuple(rows)
