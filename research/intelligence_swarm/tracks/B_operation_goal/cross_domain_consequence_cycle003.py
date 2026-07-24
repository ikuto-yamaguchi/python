from __future__ import annotations

import hashlib
import json
import pickle
import random
import resource
import statistics
import time

import numpy as np

DIM_X = 256
DIM_Y = 48
SEEDS = (1, 7, 19)
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
SELECTORS = ("nearest", "farthest", "leftmost", "rightmost")
MOVES = ("right", "left", "up", "down")
PAIRS = np.array([(i, j) for i in range(8) for j in range(i + 1, 8)])
PROJECTION = np.random.default_rng(123).normal(size=(19, DIM_Y)).astype(np.float32)

PHRASES = {
    "nearest": ["基準にいちばん近いもの", "目印のそばにある対象", "基準点への距離が最小のもの"],
    "farthest": ["基準からいちばん遠いもの", "目印から最も離れた対象", "基準点への距離が最大のもの"],
    "leftmost": ["いちばん左にあるもの", "左端の対象", "横位置が最小のもの"],
    "rightmost": ["いちばん右にあるもの", "右端の対象", "横位置が最大のもの"],
    "right": ["右へ動かして", "右側へ移してください", "横の正方向へずらす"],
    "left": ["左へ動かして", "左側へ移してください", "横の負方向へずらす"],
    "up": ["上へ動かして", "上側へ移してください", "縦の正方向へずらす"],
    "down": ["下へ動かして", "下側へ移してください", "縦の負方向へずらす"],
}


def stable_hash(text: str) -> int:
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "little")


def language_feature(text: str) -> np.ndarray:
    vector = np.zeros(DIM_X, dtype=np.float32)
    source = "^" + text + "$"
    for width in (2, 3):
        for start in range(len(source) - width + 1):
            value = stable_hash(source[start : start + width])
            vector[value % DIM_X] += 1.0 if ((value >> 8) & 1) == 0 else -1.0
    return vector / (np.linalg.norm(vector) + 1e-8)


def generate_world(rng: random.Random, domain: str = "A") -> np.ndarray:
    points = []
    used = set()
    while len(points) < 8:
        point = (rng.randint(-5, 5), rng.randint(-5, 5))
        if point != (0, 0) and point not in used:
            used.add(point)
            points.append(point)
    scale = {"A": 1, "B": 2, "C": 3}[domain]
    return np.array(points, dtype=np.int16) * scale


def select_target(points: np.ndarray, selector: str) -> int:
    radial = (points.astype(float) ** 2).sum(axis=1)
    if selector == "nearest":
        return int(np.argmin(radial))
    if selector == "farthest":
        return int(np.argmax(radial))
    if selector == "leftmost":
        return int(np.argmin(points[:, 0]))
    return int(np.argmax(points[:, 0]))


def apply_move(points: np.ndarray, target: int, move: str) -> np.ndarray:
    result = points.copy()
    result[target] += np.array(DIRS[MOVES.index(move)])
    return result


def consequence_base(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    before_f = before.astype(np.float32)
    after_f = after.astype(np.float32)
    displacement = after_f - before_f
    changed = np.abs(displacement).sum(axis=1) > 0
    radial_before = np.sqrt((before_f * before_f).sum(axis=1))
    radial_after = np.sqrt((after_f * after_f).sum(axis=1))
    pair_before = np.sqrt(((before_f[PAIRS[:, 0]] - before_f[PAIRS[:, 1]]) ** 2).sum(axis=1))
    pair_after = np.sqrt(((after_f[PAIRS[:, 0]] - after_f[PAIRS[:, 1]]) ** 2).sum(axis=1))
    radial_change = np.sort(radial_after - radial_before)
    pair_change = np.sort(pair_after - pair_before)
    changed_origin = before_f[changed].mean(axis=0) if changed.any() else np.zeros(2)
    features = [
        float(changed.sum()),
        float(displacement[:, 0].sum()),
        float(displacement[:, 1].sum()),
        float(np.linalg.norm(displacement.sum(axis=0))),
        float(changed_origin[0]),
        float(changed_origin[1]),
        float(np.linalg.norm(changed_origin)),
    ]
    features.extend(float(x) for x in np.quantile(radial_change, [0, 0.25, 0.5, 0.75, 1]))
    features.extend(float(x) for x in np.quantile(pair_change, [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]))
    return np.array(features, dtype=np.float32)


def consequence_feature(before: np.ndarray, after: np.ndarray, center: np.ndarray, scale: np.ndarray) -> np.ndarray:
    normalized = (consequence_base(before, after) - center) / (scale + 1e-6)
    projected = np.tanh(normalized @ PROJECTION)
    return projected / (np.linalg.norm(projected) + 1e-8)


def render_command(rng: random.Random, selector: str, move: str, mode: str, domain: str = "A") -> str:
    selector_phrase = rng.choice(PHRASES[selector])
    move_phrase = rng.choice(PHRASES[move])
    wrapper = {"A": "", "B": "航路盤では、", "C": "細胞配置の記録上、"}[domain]
    if mode == "word_order":
        return wrapper + f"{move_phrase}。対象は{selector_phrase}です。"
    if mode == "nested":
        return wrapper + f"依頼は「{selector_phrase}を{move_phrase}」という内容です。"
    if mode == "paragraph":
        return wrapper + f"前の記録は維持します。\n{selector_phrase}を{move_phrase}。\n他は変えません。"
    if mode == "free":
        return wrapper + f"周囲はそのままで、{selector_phrase}だけ{move_phrase}ようにしてください。"
    if mode == "repair":
        return wrapper + f"先ほどの案は誤りです。代わりに{selector_phrase}を{move_phrase}。"
    if mode == "goal_change":
        return wrapper + f"目標を変更します。今度は{selector_phrase}を{move_phrase}。"
    return wrapper + f"{selector_phrase}を{move_phrase}。"


def make_dataset(seed: int, count: int, modes: tuple[str, ...], domain: str = "A") -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for _ in range(count):
        before = generate_world(rng, domain)
        selector = rng.choice(SELECTORS)
        move = rng.choice(MOVES)
        target = select_target(before, selector)
        after = apply_move(before, target, move)
        mode = rng.choice(modes)
        rows.append({
            "text": render_command(rng, selector, move, mode, domain),
            "before": before,
            "after": after,
            "selector": selector,
            "move": move,
            "target": target,
            "mode": mode,
            "domain": domain,
        })
    return rows


def train(rows: list[dict], invariant: bool, shuffled: bool) -> tuple:
    started = time.perf_counter()
    bases = np.stack([consequence_base(row["before"], row["after"]) for row in rows])
    center = bases.mean(axis=0) if invariant else np.zeros(bases.shape[1], dtype=np.float32)
    scale = bases.std(axis=0) + 1e-3 if invariant else np.ones(bases.shape[1], dtype=np.float32)
    inputs = np.stack([language_feature(row["text"]) for row in rows])
    input_center = inputs.mean(axis=0) if invariant else np.zeros(inputs.shape[1], dtype=np.float32)
    outputs = np.stack([consequence_feature(row["before"], row["after"], center, scale) for row in rows])
    if shuffled:
        outputs = outputs[np.random.default_rng(991).permutation(len(outputs))]
    matrix = (inputs - input_center).T @ outputs / len(rows)
    return matrix, input_center, center, scale, time.perf_counter() - started


def evaluate(rows: list[dict], model: tuple) -> dict[str, float]:
    matrix, input_center, center, scale, _ = model
    joint, target_hits, move_hits, inverse_hits = [], [], [], []
    started = time.perf_counter()
    for row in rows:
        query = (language_feature(row["text"]) - input_center) @ matrix
        query /= np.linalg.norm(query) + 1e-8
        candidates = []
        for target in range(8):
            for move in MOVES:
                candidate_after = apply_move(row["before"], target, move)
                effect = consequence_feature(row["before"], candidate_after, center, scale)
                candidates.append((float(query @ effect), target, move))
        _, predicted_target, predicted_move = max(candidates)
        target_hits.append(float(predicted_target == row["target"]))
        move_hits.append(float(predicted_move == row["move"]))
        joint.append(float(predicted_target == row["target"] and predicted_move == row["move"]))
        choices = [(row["selector"], row["move"])]
        choice_rng = random.Random(stable_hash(row["text"]))
        while len(choices) < 8:
            candidate = (choice_rng.choice(SELECTORS), choice_rng.choice(MOVES))
            if candidate not in choices:
                choices.append(candidate)
        observed_effect = consequence_feature(row["before"], row["after"], center, scale)
        scores = []
        for selector, move in choices:
            text = render_command(choice_rng, selector, move, "seen", row["domain"])
            inverse_query = (language_feature(text) - input_center) @ matrix
            inverse_query /= np.linalg.norm(inverse_query) + 1e-8
            scores.append(float(inverse_query @ observed_effect))
        inverse_hits.append(float(int(np.argmax(scores)) == 0))
    return {
        "joint_accuracy": statistics.mean(joint),
        "target_accuracy": statistics.mean(target_hits),
        "move_accuracy": statistics.mean(move_hits),
        "inverse_accuracy": statistics.mean(inverse_hits),
        "inference_ms_per_query": (time.perf_counter() - started) * 1000 / len(rows),
    }


def run_seed(seed: int) -> tuple[dict, dict]:
    training_rows = make_dataset(seed, 360, ("seen", "word_order", "nested", "paragraph", "free"))
    models = {
        "consequence_invariant": train(training_rows, invariant=True, shuffled=False),
        "raw_effect": train(training_rows, invariant=False, shuffled=False),
        "shuffled_effect": train(training_rows, invariant=True, shuffled=True),
    }
    tests = {
        "held": make_dataset(seed + 100, 72, ("seen",)),
        "word_order": make_dataset(seed + 101, 72, ("word_order",)),
        "nested": make_dataset(seed + 102, 72, ("nested",)),
        "paragraph": make_dataset(seed + 103, 72, ("paragraph",)),
        "free_japanese": make_dataset(seed + 104, 72, ("free",)),
        "goal_change": make_dataset(seed + 105, 72, ("goal_change",)),
        "failure_repair": make_dataset(seed + 106, 72, ("repair",)),
        "cross_domain_B": make_dataset(seed + 200, 72, ("seen", "word_order", "free"), "B"),
        "cross_domain_C": make_dataset(seed + 201, 72, ("seen", "nested", "paragraph"), "C"),
    }
    results = {name: {condition: evaluate(rows, model) for condition, rows in tests.items()} for name, model in models.items()}
    metadata = {name: {"training_seconds": model[4], "model_bytes": len(pickle.dumps(model[:4]))} for name, model in models.items()}
    return results, metadata


def main() -> dict:
    raw, metadata_raw = {}, {}
    for seed in SEEDS:
        raw[str(seed)], metadata_raw[str(seed)] = run_seed(seed)
    summary = {}
    for method in ("consequence_invariant", "raw_effect", "shuffled_effect"):
        summary[method] = {}
        for condition in raw[str(SEEDS[0])][method]:
            summary[method][condition] = {
                metric: statistics.mean(raw[str(seed)][method][condition][metric] for seed in SEEDS)
                for metric in raw[str(SEEDS[0])][method][condition]
            }
        summary[method]["model_bytes"] = statistics.mean(metadata_raw[str(seed)][method]["model_bytes"] for seed in SEEDS)
        summary[method]["training_seconds"] = statistics.mean(metadata_raw[str(seed)][method]["training_seconds"] for seed in SEEDS)
    return {
        "track": "B_operation_goal",
        "cycle": 3,
        "hypothesis": "Cross-Domain Consequence-Invariant Operation Grounding",
        "seeds": list(SEEDS),
        "chance": {"joint": 1 / 32, "target": 1 / 8, "move": 1 / 4, "inverse": 1 / 8},
        "summary": summary,
        "raw": raw,
        "peak_rss_kib_runtime_included": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "estimated_update_ops_per_episode": DIM_X * DIM_Y,
        "estimated_inference_ops_per_query": 32 * DIM_Y * 19 + DIM_X * DIM_Y,
        "candidate_count": 32,
        "post_treatment_information_used_at_test": False,
        "domain_dictionary_or_shared_object_id_used": False,
        "fixed_ontology_or_handwritten_slot_used_by_model": False,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
