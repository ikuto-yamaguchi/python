from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import torch

from .pact_commitment_compiler import Config, PACTCompiler, Pair, analyze_tokens


def load_pairs(limit: int) -> list[Pair]:
    from datasets import load_dataset

    dataset = load_dataset("llm-jp/databricks-dolly-15k-ja", split="train")
    pairs: list[Pair] = []
    for row in dataset:
        instruction = str(row.get("instruction", "")).strip()
        context = str(row.get("context", "")).strip()
        response = str(row.get("response", "")).strip()
        prompt = f"資料:\n{context}\n\n指示:\n{instruction}" if context else instruction
        if not prompt or not response:
            continue
        if len(prompt) > 1200 or len(response) > 900:
            continue
        pairs.append(Pair(prompt, response))
        if len(pairs) >= limit:
            break
    return pairs


def load_mtbench() -> list[dict]:
    from datasets import load_dataset

    return [
        dict(row)
        for row in load_dataset(
            "tokyotech-llm/swallow_japanese_mt_bench",
            split="train",
        )
    ]


def japanese_ratio(text: str) -> float:
    if not text:
        return 0.0
    count = sum(
        1
        for char in text
        if "\u3040" <= char <= "\u30ff" or "\u3400" <= char <= "\u9fff"
    )
    return count / len(text)


def content_tokens(text: str) -> list[str]:
    rows = []
    for surface, pos in analyze_tokens(text):
        if pos == "名詞" or re.fullmatch(r"[0-9０-９.,]+|[A-Za-z]+", surface):
            rows.append(surface)
    return rows


def content_f1(candidate: str, reference: str) -> float:
    a = Counter(content_tokens(candidate))
    b = Counter(content_tokens(reference))
    if not a or not b:
        return 0.0
    overlap = sum((a & b).values())
    if not overlap:
        return 0.0
    precision = overlap / sum(a.values())
    recall = overlap / sum(b.values())
    return 2 * precision * recall / (precision + recall)


def repeated(text: str) -> bool:
    return bool(re.search(r"(.)\1{7,}", text)) or (
        len(text) > 20 and len(set(text)) / len(text) < 0.08
    )


def evaluate_heldout(
    model: PACTCompiler,
    pairs: list[Pair],
    limit: int = 80,
) -> dict:
    rows = []
    for pair in pairs[:limit]:
        baseline = model.nearest_prompt_response(pair.prompt)
        pact, trace = model.respond(pair.prompt)
        rows.append(
            {
                "prompt": pair.prompt,
                "reference": pair.response,
                "nearest_output": baseline,
                "pact_output": pact,
                "nearest_content_f1": content_f1(baseline, pair.response),
                "pact_content_f1": content_f1(pact, pair.response),
                "pact_japanese_ratio": japanese_ratio(pact),
                "pact_repeated": repeated(pact),
                "trace": trace,
            }
        )
    return {
        "rows": rows,
        "summary": {
            "examples": len(rows),
            "nearest_content_f1": sum(
                row["nearest_content_f1"] for row in rows
            ) / max(1, len(rows)),
            "pact_content_f1": sum(
                row["pact_content_f1"] for row in rows
            ) / max(1, len(rows)),
            "pact_win_rate": sum(
                row["pact_content_f1"] > row["nearest_content_f1"]
                for row in rows
            ) / max(1, len(rows)),
            "pact_japanese_ratio": sum(
                row["pact_japanese_ratio"] for row in rows
            ) / max(1, len(rows)),
            "pact_nonrepetition_rate": sum(
                not row["pact_repeated"] for row in rows
            ) / max(1, len(rows)),
            "pact_unique_rate": len({row["pact_output"] for row in rows})
            / max(1, len(rows)),
        },
    }


def evaluate_dialogues(
    model: PACTCompiler,
    rows: list[dict],
    limit: int = 24,
) -> dict:
    transcripts = []
    for row in rows[:limit]:
        turn_1, turn_2 = [str(value) for value in row["turns"]]
        response_1, trace_1 = model.respond(turn_1)
        transcript = (
            f"ユーザー: {turn_1}\n"
            f"アシスタント: {response_1}\n"
            f"ユーザー: {turn_2}"
        )
        response_2, trace_2 = model.respond(transcript)
        transcripts.append(
            {
                "question_id": int(row["question_id"]),
                "category": str(row["category"]),
                "turn_1": turn_1,
                "response_1": response_1,
                "turn_2": turn_2,
                "response_2": response_2,
                "changed": response_1.strip() != response_2.strip(),
                "japanese_ratio": (
                    japanese_ratio(response_1) + japanese_ratio(response_2)
                ) / 2,
                "trace_1": trace_1,
                "trace_2": trace_2,
            }
        )
    return {
        "rows": transcripts,
        "summary": {
            "dialogues": len(transcripts),
            "followup_changed_rate": sum(
                row["changed"] for row in transcripts
            ) / max(1, len(transcripts)),
            "japanese_ratio": sum(
                row["japanese_ratio"] for row in transcripts
            ) / max(1, len(transcripts)),
            "unique_response_rate": len(
                {
                    output
                    for row in transcripts
                    for output in (row["response_1"], row["response_2"])
                }
            ) / max(1, 2 * len(transcripts)),
        },
    }


def communication_probes() -> list[dict]:
    return [
        {
            "name": "numeric_repair",
            "turns": [
                "17ではなく23に訂正してください。",
                "さらに23ではなく31へ訂正してください。",
            ],
            "required": [["23"], ["31"]],
            "forbidden": [["17"], ["17"]],
        },
        {
            "name": "color_repair",
            "turns": [
                "青ではなく赤に訂正してください。",
                "やはり赤ではなく緑に直してください。",
            ],
            "required": [["赤"], ["緑"]],
            "forbidden": [[], []],
        },
        {
            "name": "entity_binding",
            "turns": [
                "京都の人口について簡潔に説明してください。",
                "同じ形式で札幌について説明してください。",
            ],
            "required": [["京都"], ["札幌"]],
            "forbidden": [[], ["京都"]],
        },
        {
            "name": "feature_binding",
            "turns": [
                "鳥の特徴を二つ挙げてください。",
                "では魚の特徴に変更してください。",
            ],
            "required": [["鳥"], ["魚"]],
            "forbidden": [[], ["鳥"]],
        },
        {
            "name": "format_constraint",
            "turns": [
                "安全なパスワードの条件を箇条書きで三つ説明してください。",
                "二つ目だけを一文で言い換えてください。",
            ],
            "required": [[], []],
            "forbidden": [[], []],
        },
        {
            "name": "reading",
            "turns": [
                "資料: ミナは午前に図書館へ行き、午後に公園で友人と会った。質問: ミナが友人と会った場所はどこですか。",
                "その前に行った場所も答えてください。",
            ],
            "required": [["公園"], ["図書館"]],
            "forbidden": [[], []],
        },
    ]


def evaluate_probes(model: PACTCompiler) -> dict:
    rows = []
    for probe in communication_probes():
        history = ""
        outputs = []
        checks = []
        for index, turn in enumerate(probe["turns"]):
            prompt = (
                f"{history}\nユーザー: {turn}".strip()
                if history
                else turn
            )
            output, _ = model.respond(prompt)
            outputs.append(output)
            required = probe["required"][index]
            forbidden = probe["forbidden"][index]
            passed = all(token in output for token in required) and all(
                token not in output for token in forbidden
            )
            checks.append(passed)
            history = f"{prompt}\nアシスタント: {output}"
        rows.append(
            {
                "name": probe["name"],
                "turns": probe["turns"],
                "outputs": outputs,
                "checks": checks,
                "passed": all(checks),
            }
        )
    return {
        "rows": rows,
        "summary": {
            "probe_count": len(rows),
            "turn_pass_rate": sum(sum(row["checks"]) for row in rows)
            / max(1, sum(len(row["checks"]) for row in rows)),
            "dialogue_pass_rate": sum(row["passed"] for row in rows)
            / max(1, len(rows)),
        },
    }


def render_markdown(report: dict) -> str:
    held = report["heldout"]["summary"]
    dialogue = report["dialogues"]["summary"]
    probes = report["probes"]["summary"]
    lines = [
        "# PACT commitment-transactions 001",
        "",
        "Primary evidence is the actual Japanese transcript. PACT does not predict the next token. It learns a cross-utterance commitment space, induces bindable response programs from ordinary prompt-response pairs, compiles a candidate, and verifies the completed utterance before emission.",
        "",
        f"- candidate supported by automatic diagnostics: **{report['candidate_supported']}**",
        "- high-school intelligence: **False**",
        f"- trained records: {report['training']['records']:,}",
        f"- package bytes: {report['training']['total_bytes']:,}",
        f"- nearest-response content F1: {held['nearest_content_f1']:.4f}",
        f"- PACT content F1: {held['pact_content_f1']:.4f}",
        f"- PACT win rate: {held['pact_win_rate']:.4f}",
        f"- communication probe turn pass: {probes['turn_pass_rate']:.4f}",
        f"- follow-up changed: {dialogue['followup_changed_rate']:.4f}",
        "",
        "## Objective communication probes",
        "",
    ]
    for row in report["probes"]["rows"]:
        lines.append(f"### {row['name']}")
        for turn, output, passed in zip(
            row["turns"], row["outputs"], row["checks"]
        ):
            lines.extend(
                [
                    f"- User: {turn}",
                    f"- PACT: {output}",
                    f"- Check: {passed}",
                ]
            )
        lines.append("")
    lines.extend(["## Actual Japanese MT-Bench two-turn transcripts", ""])
    for row in report["dialogues"]["rows"][:12]:
        lines.extend(
            [
                f"### {row['question_id']} / {row['category']}",
                f"**User 1:** {row['turn_1']}",
                "",
                f"**PACT 1:** {row['response_1']}",
                "",
                f"**User 2:** {row['turn_2']}",
                "",
                f"**PACT 2:** {row['response_2']}",
                "",
            ]
        )
    lines.extend(["## Held-out examples", ""])
    for row in report["heldout"]["rows"][:20]:
        lines.extend(
            [
                f"**Prompt:** {row['prompt']}",
                "",
                f"**Reference:** {row['reference']}",
                "",
                f"**Nearest baseline:** {row['nearest_output']}",
                "",
                f"**PACT:** {row['pact_output']}",
                "",
            ]
        )
    return "\n".join(lines)


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
    model = PACTCompiler(cfg)
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
        "architecture": "hashed sparse utterance encoders + learned commitment atoms + automatically induced bindable response programs + compatibility verifier",
        "config": asdict(cfg),
        "training": training,
        "heldout": heldout,
        "dialogues": dialogues,
        "probes": probes,
        "checkpoint": checkpoint.name,
        "candidate_supported": supported,
        "highschool_level_passed": False,
        "claim_boundary": "PACT is supported only if its actual Japanese outputs are relevant and coherent. It is not high-school-level intelligence and cannot be promoted on automatic scores alone.",
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
    parser.add_argument("--train-examples", type=int, default=8000)
    parser.add_argument("--valid-examples", type=int, default=600)
    parser.add_argument("--epochs", type=int, default=4)
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
    )
    run(args.output_dir, cfg, args.train_examples, args.valid_examples)


if __name__ == "__main__":
    main()
