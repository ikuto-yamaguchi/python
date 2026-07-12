from __future__ import annotations

from fractions import Fraction
import json
import os
import resource
import sys

from .phase12a_experiment import calibration_interactions


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def _format(value: object) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _calibration_messages() -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for interaction in calibration_interactions():
        messages.append({"role": "user", "content": interaction.prompt})
        messages.append(
            {"role": "assistant", "content": _format(interaction.trace.output)}
        )
    return messages


def main() -> None:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Phase 12b requires the optional torch and transformers packages"
        ) from exc

    request = json.load(sys.stdin)
    model_id = os.environ.get(
        "MPM_OPEN_MODEL_ID", "HuggingFaceTB/SmolLM2-135M-Instruct"
    )
    revision = os.environ.get("MPM_OPEN_MODEL_REVISION", "main")
    maximum_chars = int(request["policy"]["max_output_chars"])
    max_new_tokens = int(os.environ.get("MPM_MAX_NEW_TOKENS", "24"))
    batch_size = int(os.environ.get("MPM_OPEN_MODEL_BATCH", "8"))
    torch.set_num_threads(max(1, int(os.environ.get("MPM_TORCH_THREADS", "4"))))

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        revision=revision,
        torch_dtype=torch.float32,
    )
    model.eval()

    calibration = _calibration_messages()
    raw_examples = request["examples"]
    predictions: list[dict[str, object]] = []
    total_input_tokens = 0
    total_output_tokens = 0
    with torch.inference_mode():
        for start in range(0, len(raw_examples), batch_size):
            batch = raw_examples[start : start + batch_size]
            rendered = [
                tokenizer.apply_chat_template(
                    calibration
                    + [{"role": "user", "content": str(item["prompt"])}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
                for item in batch
            ]
            encoded = tokenizer(
                rendered,
                return_tensors="pt",
                padding=True,
                truncation=True,
            )
            output = model.generate(
                **encoded,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
            prefix_length = encoded["input_ids"].shape[1]
            input_counts = encoded["attention_mask"].sum(dim=1).tolist()
            for item, sequence, input_count in zip(batch, output, input_counts):
                generated = sequence[prefix_length:]
                generated_count = int(
                    (generated != tokenizer.pad_token_id).sum().item()
                )
                total_input_tokens += int(input_count)
                total_output_tokens += generated_count
                predictions.append(
                    {
                        "id": str(item["id"]),
                        "text": tokenizer.decode(
                            generated, skip_special_tokens=True
                        ).strip()[:maximum_chars],
                        "operations": 0,
                        "reads": int(input_count),
                        "writes": generated_count,
                    }
                )

    model_bytes = sum(
        parameter.numel() * parameter.element_size()
        for parameter in model.parameters()
    )
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    commit_hash = getattr(model.config, "_commit_hash", None)
    json.dump(
        {
            "predictions": predictions,
            "model_bytes": int(model_bytes),
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "energy_joules": None,
            "metadata": {
                "model_id": model_id,
                "requested_revision": revision,
                "resolved_revision": commit_hash,
                "max_new_tokens": max_new_tokens,
                "batch_size": batch_size,
                "torch_version": torch.__version__,
                "same_prompt_output_calibration_examples": len(
                    calibration_interactions()
                ),
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "state_transition_evidence_visible": False,
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
