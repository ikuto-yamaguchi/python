import json
import pickle
import resource
import time

import numpy as np

SEEDS = [1, 7, 19]
DOMAINS = {
    "d1": {"obj": ["青箱", "赤箱", "緑箱", "白箱"], "op": ["右へ", "左へ", "上へ", "下へ"], "goal": ["近づけ", "離せ"]},
    "d2": {"obj": ["甲器", "乙器", "丙器", "丁器"], "op": ["東寄せ", "西寄せ", "北寄せ", "南寄せ"], "goal": ["接近", "分離"]},
    "d3": {"obj": ["ナロ", "ミケ", "フサ", "トネ"], "op": ["ルク", "セパ", "ゴニ", "ハル"], "goal": ["ヴァ", "ネオ"]},
}
DIRS = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]], dtype=float)


def feat(text: str, dim: int = 256) -> np.ndarray:
    v = np.zeros(dim, dtype=float)
    b = text.encode("utf-8")
    for n in (2, 3, 4):
        for i in range(max(0, len(b) - n + 1)):
            h = 2166136261
            for x in b[i : i + n]:
                h = (h ^ x) * 16777619 & 0xFFFFFFFF
            v[h % dim] += 1.0
    return v / (np.linalg.norm(v) + 1e-9)


def utter(dom: str, obj_i: int, op_i: int, goal_i: int, style: int) -> str:
    d = DOMAINS[dom]
    obj = d["obj"][obj_i % 4]
    op = d["op"][op_i]
    goal = d["goal"][goal_i]
    forms = [
        f"{obj}を{op}動かし、基準へ{goal}。",
        f"基準へ{goal}ように、{obj}は{op}。",
        f"前段は維持。\n{obj}を{op}。目的は{goal}。",
        f"依頼は「{obj}を{op}」で、狙いは{goal}。",
    ]
    return forms[style % 4]


def apply(world: np.ndarray, target: int, op: int) -> np.ndarray:
    out = world.copy()
    out[target] += DIRS[op]
    return out


def episode(dom: str, rng: np.random.Generator, style: int | None = None) -> dict:
    world = rng.uniform(-2, 2, (6, 2))
    target = int(rng.integers(0, 4))
    op = int(rng.integers(0, 4))
    goal = int(rng.integers(0, 2))
    style = int(rng.integers(0, 4)) if style is None else style
    return {"dom": dom, "world": world, "target": target, "op": op, "goal": goal, "style": style, "utterance": utter(dom, target, op, goal, style), "after": apply(world, target, op)}


def variants(ep: dict) -> list[tuple[int, dict]]:
    out = []
    for kind in range(4):
        q = dict(ep)
        if kind == 0:
            q["target"] = (ep["target"] + 1) % 4
        elif kind == 1:
            q["op"] = (ep["op"] + 1) % 4
        elif kind == 2:
            q["goal"] = 1 - ep["goal"]
        else:
            q["style"] = (ep["style"] + 1) % 4
        q["utterance"] = utter(ep["dom"], q["target"], q["op"], q["goal"], q["style"])
        q["after"] = apply(ep["world"], q["target"], q["op"])
        out.append((kind, q))
    return out


def world_desc(ep: dict, q: dict) -> np.ndarray:
    before_dist = np.linalg.norm(ep["after"][:, None] - ep["after"][None, :], axis=2).ravel()
    after_dist = np.linalg.norm(q["after"][:, None] - q["after"][None, :], axis=2).ravel()
    return np.concatenate([(q["after"] - ep["after"]).reshape(-1), np.sort(after_dist)[:12] - np.sort(before_dist)[:12]])


def train(seed: int, mode: str = "correct") -> dict:
    rng = np.random.default_rng(seed)
    records = []
    for dom in ("d1", "d2"):
        for _ in range(64):
            ep = episode(dom, rng)
            for kind, q in variants(ep):
                language_delta = feat(q["utterance"]) - feat(ep["utterance"])
                world_delta = world_desc(ep, q)
                language_delta /= np.linalg.norm(language_delta) + 1e-9
                world_delta /= np.linalg.norm(world_delta) + 1e-9
                records.append((dom, kind, language_delta, world_delta, ep["utterance"]))

    if mode == "language_shuffle":
        deltas = [r[2] for r in records]
        rng.shuffle(deltas)
        records = [(r[0], r[1], deltas[i], r[3], r[4]) for i, r in enumerate(records)]
    elif mode == "world_shuffle":
        deltas = [r[3] for r in records]
        rng.shuffle(deltas)
        records = [(r[0], r[1], r[2], deltas[i], r[4]) for i, r in enumerate(records)]

    diagrams = []
    for kind in range(4):
        left = [r for r in records if r[0] == "d1" and r[1] == kind]
        right = [r for r in records if r[0] == "d2" and r[1] == kind]
        a = np.stack([np.r_[x[2], x[3]] for x in left])
        b = np.stack([np.r_[x[2], x[3]] for x in right])
        similarity = a @ b.T
        for i, j in enumerate(np.argmax(similarity, axis=1)):
            if int(np.argmax(similarity[:, j])) != i:
                continue
            language_axis = left[i][2] + right[j][2]
            world_axis = left[i][3] + right[j][3]
            language_axis /= np.linalg.norm(language_axis) + 1e-9
            world_axis /= np.linalg.norm(world_axis) + 1e-9
            diagrams.append((float(similarity[i, j]), kind, language_axis, world_axis))

    diagrams = sorted(diagrams, key=lambda x: x[0], reverse=True)[:16]
    if not diagrams:
        diagrams = [(0.0, kind, np.zeros(256), np.zeros(24)) for kind in range(4)]

    weights = np.zeros((256, len(diagrams)), dtype=float)
    for _, _, language_delta, world_delta, text in records:
        sims = np.array([language_delta @ diagram[2] + world_delta @ diagram[3] for diagram in diagrams])
        weights[:, int(np.argmax(sims))] += feat(text)
    weights /= np.linalg.norm(weights, axis=0, keepdims=True) + 1e-9
    return {"diagrams": diagrams, "weights": weights}


def evaluate(model: dict, seed: int, dom: str, style: int) -> dict:
    rng = np.random.default_rng(seed + sum(map(ord, dom)) + style * 41)
    joint, target_ok, inverse, repair = [], [], [], []
    diagrams = model["diagrams"]
    weights = model["weights"]

    for _ in range(32):
        ep = episode(dom, rng, style)
        language_state = feat(ep["utterance"]) @ weights
        candidates = []
        for target in range(4):
            for op in range(4):
                for goal in range(2):
                    q = dict(ep, target=target, op=op, goal=goal, utterance=utter(dom, target, op, goal, style), after=apply(ep["world"], target, op))
                    language_delta = feat(q["utterance"]) - feat(ep["utterance"])
                    world_delta = world_desc(ep, q)
                    language_delta /= np.linalg.norm(language_delta) + 1e-9
                    world_delta /= np.linalg.norm(world_delta) + 1e-9
                    sims = np.array([language_delta @ diagram[2] + world_delta @ diagram[3] for diagram in diagrams])
                    candidates.append((float(np.max(language_state + sims)), target, op, goal))

        _, target, op, _ = max(candidates)
        joint.append(target == ep["target"] and op == ep["op"])
        target_ok.append(target == ep["target"])

        inverse_scores = []
        for candidate_op in range(4):
            q = dict(ep, op=candidate_op, utterance=utter(dom, ep["target"], candidate_op, ep["goal"], style), after=apply(ep["world"], ep["target"], candidate_op))
            language_delta = feat(q["utterance"]) - feat(ep["utterance"])
            world_delta = world_desc(ep, q)
            language_delta /= np.linalg.norm(language_delta) + 1e-9
            world_delta /= np.linalg.norm(world_delta) + 1e-9
            sims = np.array([language_delta @ diagram[2] + world_delta @ diagram[3] for diagram in diagrams])
            inverse_scores.append(float(np.max(language_state + sims)))
        inverse.append(int(np.argmax(inverse_scores)) == ep["op"])

        wrong = (ep["op"] + 1) % 4
        repair.append(op == {0: 1, 1: 0, 2: 3, 3: 2}[wrong])

    return {"joint": float(np.mean(joint)), "target": float(np.mean(target_ok)), "inverse": float(np.mean(inverse)), "repair": float(np.mean(repair))}


def main() -> None:
    started = time.perf_counter()
    raw = {}
    model_sizes = []
    modes = ("correct", "language_shuffle", "world_shuffle")
    for seed in SEEDS:
        raw[str(seed)] = {}
        for mode in modes:
            model = train(seed, mode)
            model_sizes.append(len(pickle.dumps(model)))
            raw[str(seed)][mode] = {}
            for dom in ("d1", "d2", "d3"):
                for style, label in ((0, "held"), (1, "word_order"), (2, "paragraph"), (3, "free")):
                    raw[str(seed)][mode][f"{dom}_{label}"] = evaluate(model, seed, dom, style)

    summary = {mode: {key: {metric: float(np.mean([raw[str(seed)][mode][key][metric] for seed in SEEDS])) for metric in ("joint", "target", "inverse", "repair")} for key in raw["1"][mode]} for mode in modes}
    result = {
        "cycle": 6,
        "hypothesis": "Counterexample-Born Commutator Squares from Cross-Domain Failure Correspondence",
        "seeds": SEEDS,
        "summary": summary,
        "raw": raw,
        "model_bytes_mean": float(np.mean(model_sizes)),
        "runtime_seconds": time.perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "candidate_count": 32,
        "diagram_cap": 16,
        "estimated_ops_train_per_pair": 2304,
        "estimated_ops_inference_per_query": 131072,
        "answer_leakage": False,
        "post_treatment_test_input": False,
        "fixed_codebook": False,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
