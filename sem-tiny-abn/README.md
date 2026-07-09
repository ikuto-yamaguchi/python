# SEM Tiny ABN

TinyCNN + lightweight Attention Branch Network for fast OK/NG judgement of aligned CD-SEM and design-pattern image pairs.

This project is designed for constrained CPU environments. It avoids saving generated difference images to disk: `pos_diff` and `neg_diff` are computed in memory inside the dataset pipeline.

## What this does

Input per sample:

- SEM grayscale image, `512x512` or `1024x1024` are fine
- Design-pattern grayscale/binary image aligned to the SEM image
- CSV annotation with `OK` / `NG`

The default model uses four channels:

1. `SEM_norm`
2. `soft_design`
3. `pos_diff = max(SEM_norm - soft_design, 0)`
4. `neg_diff = max(soft_design - SEM_norm, 0)`

`soft_design` is blurred slightly before diff calculation so that small edge shifts are not over-penalized.

The default output is two classes, `OK` and `NG`, but the class list is configurable. You can later switch to labels such as `OK,NG,EDGE_SHIFT,REVIEW` without changing the model code.

## Why this design

The goal is not just raw accuracy. For inspection, the dangerous case is false OK, meaning an NG sample is judged as OK. The training and evaluation scripts report false OK / false NG explicitly.

The lightweight ABN branch gives a low-resolution attention map for human review. It is intentionally small so it does not dominate CPU runtime.

## CSV format

Recommended:

```csv
sem,design,label
sem_0001.png,design_0001.png,OK
sem_0002.png,design_0002.png,NG
```

Accepted aliases:

- SEM column: `sem`, `sem_path`, `sem_image`, `image_sem`
- Design column: `design`, `design_path`, `pattern`, `design_image`, `image_design`
- Label column: `label`, `target`, `class`

Paths can be relative to `--data-root`.

## Quick start

```bash
cd sem-tiny-abn
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Train on CPU-friendly defaults:

```bash
python -m sem_tiny_abn.train \
  --data-root /path/to/folder \
  --csv /path/to/annotations.csv \
  --out runs/sem_tiny_abn \
  --model tiny_abn \
  --image-size 128 \
  --epochs 30 \
  --batch-size 32 \
  --device cpu
```

Evaluate:

```bash
python -m sem_tiny_abn.evaluate \
  --data-root /path/to/folder \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --device cpu
```

Predict with attention export:

```bash
python -m sem_tiny_abn.predict \
  --data-root /path/to/folder \
  --csv /path/to/annotations.csv \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --save-attention runs/sem_tiny_abn/attention \
  --device cpu
```

Export ONNX:

```bash
python -m sem_tiny_abn.export_onnx \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --out runs/sem_tiny_abn/model.onnx
```

Benchmark CPU latency:

```bash
python -m sem_tiny_abn.benchmark \
  --checkpoint runs/sem_tiny_abn/best.pt \
  --batch-size 1 \
  --iters 300 \
  --device cpu
```

## Model choices

- `tiny_cnn`: smallest, no attention. Use this as the speed baseline.
- `tiny_abn`: TinyCNN + one lightweight spatial attention map. Recommended first model.
- `tiny_freq_abn`: two attention maps over split feature channels. Useful when you want to compare coarse morphology attention and fine edge/detail attention.

## Practical advice

For your current OK/NG-only annotation setup, start with:

```bash
--model tiny_abn --classes OK,NG --task multiclass --input-mode sem_design_posneg
```

If edge shift is still confused with NG, the next minimal label expansion is not eight classes. Use:

```text
OK,NG,EDGE_SHIFT,REVIEW
```

That is usually much cheaper than full defect-type annotation.

## Accuracy note

This repository is designed to make very high accuracy possible, but no model can honestly guarantee 100% on unseen SEM data. For production-style inspection, tune the OK threshold so uncertain cases go to review instead of becoming false OK.
