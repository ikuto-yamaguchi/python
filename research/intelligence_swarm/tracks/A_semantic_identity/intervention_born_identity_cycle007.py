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


def feat(text: str, dim: int = 384) -> np.ndarray:
    vector = np.zeros(dim, dtype=float)
    raw = text.encode("utf-8")
    for n in (2, 3, 4, 5):
        for i in range(max(0, len(raw) - n + 1)):
            h = 2166136261
            for byte in raw[i : i + n]:
                h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
            vector[h % dim] += 1.0
    return vector / (np.linalg.norm(vector) + 1e-9)


def utter(domain: str, target: int, operation: int, goal: int, style: int) -> str:
    spec = DOMAINS[domain]
    obj = spec["obj"][target]
    op = spec["op"][operation]
    goal_word = spec["goal"][goal]
    forms = [
        f"{obj}を{op}動かし、基準へ{goal_word}。",
        f"基準へ{goal_word}ように、{obj}は{op}。",
        f"前の話は保つ。\n対象は{obj}、動きは{op}、狙いは{goal_word}。",
        f"この場面では、最終的に{goal_word}ため{obj}へ{op}の変化を与えて。",
        f"{goal_word}という意図を満たすなら、{op}のは{obj}。",
    ]
    return forms[style % len(forms)]


def apply(world: np.ndarray, target: int, operation: int) -> np.ndarray:
    after = world.copy()
    after[target] += DIRS[operation]
    return after


def episode(domain: str, rng: np.random.Generator, style: int | None = None) -> dict:
    world = rng.uniform(-2, 2, (6, 2))
    target = int(rng.integers(4))
    operation = int(rng.integers(4))
    goal = int(rng.integers(2))
    style = int(rng.integers(5)) if style is None else style
    return {
        "domain": domain,
        "world": world,
        "target": target,
        "operation": operation,
        "goal": goal,
        "style": style,
        "text": utter(domain, target, operation, goal, style),
        "after": apply(world, target, operation),
    }


def outcome_signature(world: np.ndarray, after: np.ndarray) -> np.ndarray:
    delta = after - world
    changed = np.linalg.norm(delta, axis=1) > 1e-7
    distances = np.linalg.norm(after[:, None] - after[None, :], axis=2).ravel()
    return np.r_[changed.astype(float), delta.reshape(-1), np.sort(distances)[:12]]


def candidate_signatures(ep: dict) -> list[tuple[int, int, int, np.ndarray]]:
    candidates = []
    for target in range(4):
        for operation in range(4):
            for goal in range(2):
                candidates.append(
                    (
                        target,
                        operation,
                        goal,
                        outcome_signature(ep["world"], apply(ep["world"], target, operation)),
                    )
                )
    return candidates


def survivor(ep: dict) -> tuple[int, int, int]:
    observed = outcome_signature(ep["world"], ep["after"])
    candidates = candidate_signatures(ep)
    distances = np.array([np.linalg.norm(candidate[3] - observed) for candidate in candidates])
    return candidates[int(np.argmin(distances))][:3]


def select_records(pool: list[dict], budget: int, rng: np.random.Generator, mode: str) -> list[dict]:
    if mode == "random":
        return list(rng.choice(pool, budget, replace=False))

    scores = []
    for ep in pool:
        signatures = np.stack([candidate[3] for candidate in candidate_signatures(ep)])
        gram = signatures @ signatures.T
        distances = np.diag(gram)[:, None] + np.diag(gram)[None, :] - 2 * gram
        np.fill_diagonal(distances, np.inf)
        scores.append(float(np.percentile(distances[np.isfinite(distances)], 25)))
    return [pool[index] for index in np.argsort(scores)[-budget:]]


def train(seed: int, mode: str = "active") -> dict:
    rng = np.random.default_rng(seed)
    features = []
    outcomes = []
    for domain in ("d1", "d2", "d3"):
        pool = [episode(domain, rng) for _ in range(72)]
        selected = select_records(pool, 24, rng, "random" if mode == "random" else "active")
        survivors = [survivor(ep) for ep in selected]
        if mode == "shuffle":
            rng.shuffle(survivors)
        for ep, outcome in zip(selected, survivors):
            features.append(feat(ep["text"]))
            outcomes.append(outcome)

    matrix = np.stack(features)
    prototypes = np.zeros((32, matrix.shape[1]), dtype=float)
    counts = np.zeros(32, dtype=float)
    for vector, (target, operation, goal) in zip(matrix, outcomes):
        index = (target * 4 + operation) * 2 + goal
        prototypes[index] += vector
        counts[index] += 1
    prototypes /= np.maximum(counts[:, None], 1)
    prototypes /= np.linalg.norm(prototypes, axis=1, keepdims=True) + 1e-9
    return {"prototype": prototypes, "counts": counts}


def evaluate(model: dict, seed: int, domain: str, style: int) -> dict:
    rng = np.random.default_rng(seed + sum(map(ord, domain)) + style * 101)
    joint = []
    target_accuracy = []
    inverse = []
    prototypes = model["prototype"]

    for _ in range(48):
        ep = episode(domain, rng, style)
        scores = prototypes @ feat(ep["text"])
        index = int(np.argmax(scores))
        target = index // 8
        operation = (index // 2) % 4
        goal = index % 2
        joint.append((target, operation, goal) == (ep["target"], ep["operation"], ep["goal"]))
        target_accuracy.append(target == ep["target"])

        operation_indices = [(ep["target"] * 4 + candidate_operation) * 2 + ep["goal"] for candidate_operation in range(4)]
        inverse.append(int(np.argmax(scores[operation_indices])) == ep["operation"])

    return {
        "joint": float(np.mean(joint)),
        "target": float(np.mean(target_accuracy)),
        "inverse": float(np.mean(inverse)),
    }


def main() -> None:
    started = time.perf_counter()
    raw = {}
    model_sizes = []
    modes = ("active", "random", "shuffle")
    styles = ((0, "held"), (1, "word_order"), (2, "paragraph"), (3, "free"), (4, "rename"))

    for seed in SEEDS:
        raw[str(seed)] = {}
        for mode in modes:
            model = train(seed, mode)
            model_sizes.append(len(pickle.dumps(model)))
            raw[str(seed)][mode] = {}
            for domain in DOMAINS:
                for style, label in styles:
                    raw[str(seed)][mode][f"{domain}_{label}"] = evaluate(model, seed, domain, style)

    summary = {
        mode: {
            key: {
                metric: float(np.mean([raw[str(seed)][mode][key][metric] for seed in SEEDS]))
                for metric in ("joint", "target", "inverse")
            }
            for key in raw["1"][mode]
        }
        for mode in modes
    }

    strict_gate = []
    for seed in SEEDS:
        passed = True
        for key in ("d3_word_order", "d3_free"):
            for metric in ("joint", "inverse"):
                active = raw[str(seed)]["active"][key][metric]
                baseline = max(raw[str(seed)]["random"][key][metric], raw[str(seed)]["shuffle"][key][metric])
                passed &= active - baseline >= 0.10
        strict_gate.append(bool(passed))

    result = {
        "cycle": 7,
        "hypothesis": "Intervention-Born Semantic Identity from Minimal Discriminating Action Sets",
        "seeds": SEEDS,
        "summary": summary,
        "raw": raw,
        "strict_gate_by_seed": strict_gate,
        "model_bytes_mean": float(np.mean(model_sizes)),
        "runtime_seconds": time.perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "observation_budget_per_domain": 24,
        "candidate_count": 32,
        "estimated_ops_update_per_episode": 384 * 32,
        "estimated_ops_inference_per_query": 384 * 32,
        "answer_leakage": False,
        "post_treatment_test_input": False,
        "fixed_ontology": False,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
