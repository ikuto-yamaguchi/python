from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict
from pathlib import Path

import torch

from .pact_commitment_compiler import Config
from .pact_communication_experiment import (
    evaluate_dialogues,
    evaluate_heldout,
    evaluate_probes,
    load_mtbench,
    load_pairs,
    render_markdown,
)
from .pact_fast_runtime import FastPACTCompiler


def run(
    output_dir: Path,
    cfg: Config,
    train_examples: int,
    valid_examples: int,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    pairs = load_pairs(train_examples + valid_examples)
    random.Random(cfg.seed).shuffle(pairs)
    train = pairs[:train_examples]
    valid = pairs[train_examples:train_examples + valid_examples]
    model = FastPACTCompiler(cfg)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    training = model.train(train, device=device)
    heldout = evaluate_heldout(model, valid)
    dialogues = evaluate_dialogues(model, load_mtbench())
    probes = evaluate_probes(model)
    held_summary = heldout["summary"]
    dialogue_summary = dialogues["summary"]
    probe_summary = probes["summary"]
    supported = (
        held_summary["pact_content_f1"]
        >= held_summary["nearest_content_f1"] + 0.01
        and held_summary["pact_nonrepetition_rate"] >= 0.98
        and held_summary["pact_unique_rate"] >= 0.65
        and dialogue_summary["japanese_ratio"] >= 0.45
        and probe_summary["turn_pass_rate"] >= 0.40
    )
    checkpoint = output_dir / "pact-commitment-transactions-001.pt"
    torch.save(model.state_dict(), checkpoint)
    report = {
        "experiment": "pact-commitment-transactions-001",
        "principle": "Predictive Agreement through Commitment Transactions",
        "architecture": "sparse utterance encoders + commitment atoms + bindable response programs + sparse compatibility verifier",
        "config": asdict(cfg),
        "training": training,
        "heldout": heldout,
        "dialogues": dialogues,
        "probes": probes,
        "checkpoint": checkpoint.name,
        "candidate_supported": supported,
        "highschool_level_passed": False,
        "claim_boundary": "Actual Japanese transcripts are primary. Automatic diagnostics cannot establish intelligence.",
    }
    (output_dir / "pact-commitment-transactions-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "pact-commitment-transactions-001.md").write_text(
        render_markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "supported": supported,
                "training": training,
                "heldout": held_summary,
                "dialogues": dialogue_summary,
                "probes": probe_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--train-examples", type=int, default=4000)
    parser.add_argument("--valid-examples", type=int, default=400)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--hash-buckets", type=int, default=8192)
    parser.add_argument("--embedding-dim", type=int, default=64)
    args = parser.parse_args()
    cfg = Config(
        hash_buckets=args.hash_buckets,
        embedding_dim=args.embedding_dim,
        commitment_atoms=48,
        top_atoms=4,
        max_templates=args.train_examples,
        epochs=args.epochs,
        batch_size=256,
        retrieval_candidates=48,
    )
    run(args.output_dir, cfg, args.train_examples, args.valid_examples)


if __name__ == "__main__":
    main()
