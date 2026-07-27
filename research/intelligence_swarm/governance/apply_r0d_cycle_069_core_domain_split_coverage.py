#!/usr/bin/env python3
"""Apply R0-D Cycle 069 domain-local train/eval coverage hardening."""
from pathlib import Path

TARGET = Path("research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py")


def replace_once(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one patch anchor, found {count}: {old!r}")
    return text.replace(old, new, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    topology, per_seed_splits = defaultdict(set), defaultdict(set)\n",
        "    topology, per_seed_splits = defaultdict(set), defaultdict(set)\n"
        "    per_domain_seed_splits = defaultdict(set)\n",
    )
    text = replace_once(
        text,
        "            seeds.add(seed); topology[(domain, split, condition)].add(seed); per_seed_splits[seed].add(split)\n",
        "            seeds.add(seed); topology[(domain, split, condition)].add(seed); per_seed_splits[seed].add(split); per_domain_seed_splits[(domain, seed)].add(split)\n",
    )
    text = replace_once(
        text,
        "    for seed in sorted(CANONICAL_SEEDS):\n"
        "        if \"train\" not in per_seed_splits.get(seed, set()): errors.append(f\"seed {seed}: train split is missing\")\n"
        "        if not (EVAL_SPLITS & per_seed_splits.get(seed, set())): errors.append(f\"seed {seed}: evaluation split is missing\")\n"
        "    if not domains: errors.append(\"need >=1 domain\")\n",
        "    for seed in sorted(CANONICAL_SEEDS):\n"
        "        if \"train\" not in per_seed_splits.get(seed, set()): errors.append(f\"seed {seed}: train split is missing\")\n"
        "        if not (EVAL_SPLITS & per_seed_splits.get(seed, set())): errors.append(f\"seed {seed}: evaluation split is missing\")\n"
        "    for domain in sorted(domains):\n"
        "        for seed in sorted(CANONICAL_SEEDS):\n"
        "            domain_seed_splits = per_domain_seed_splits.get((domain, seed), set())\n"
        "            if \"train\" not in domain_seed_splits:\n"
        "                errors.append(f\"domain {domain!r} seed {seed}: train split is missing\")\n"
        "            if not (EVAL_SPLITS & domain_seed_splits):\n"
        "                errors.append(f\"domain {domain!r} seed {seed}: evaluation split is missing\")\n"
        "    if not domains: errors.append(\"need >=1 domain\")\n",
    )
    text = replace_once(
        text,
        '"canonical_seed_topology_required": True, "adapted_schema": True,',
        '"canonical_seed_topology_required": True, "domain_local_train_eval_coverage_required": True, "domain_seed_split_coverage": {str(k): sorted(v) for k, v in sorted(per_domain_seed_splits.items())}, "adapted_schema": True,',
    )
    TARGET.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
