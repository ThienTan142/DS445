"""
Evaluate a fine-tuned PhoBERT sentiment checkpoint.

Outputs:
    metrics.json
    classification_report.txt
    confusion_matrix.csv
    confusion_matrix.png
    predictions.csv
    errors.csv
    evaluation_summary.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from underthesea import word_tokenize


LABELS = ["negative", "neutral", "positive"]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def parse_sources(value: str) -> set[str]:
    return {part.strip().lower() for part in value.split(",") if part.strip()}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def segment_text(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    return word_tokenize(text, format="text")


def load_eval_data(args: argparse.Namespace) -> pd.DataFrame:
    df = pd.read_csv(args.data, encoding="utf-8-sig")
    text_col = args.text_col if args.text_col in df.columns else "review_text"
    if text_col not in df.columns:
        raise SystemExit(f"Khong tim thay cot text: {args.text_col} hoac review_text")
    if "label" not in df.columns:
        raise SystemExit("Khong tim thay cot label de danh gia.")

    df = df.copy()
    df["label"] = df["label"].astype(str).str.lower().str.strip()
    df = df[df["label"].isin(LABELS)].copy()

    if "source" not in df.columns:
        df["source"] = "unknown"
    df["source"] = df["source"].astype(str).str.lower().str.strip()

    include_sources = parse_sources(args.include_sources)
    if include_sources:
        df = df[df["source"].isin(include_sources)].copy()

    if args.split_col and args.split_col in df.columns and args.eval_split:
        split_values = df[args.split_col].astype(str).str.lower().str.strip()
        df = df[split_values.eq(args.eval_split.lower().strip())].copy()

    if args.max_samples > 0 and len(df) > args.max_samples:
        df = df.sample(n=args.max_samples, random_state=args.seed).copy()

    df["eval_text"] = df[text_col].map(segment_text)
    df = df[df["eval_text"].str.len() > 0].copy()
    if df.empty:
        raise SystemExit("Khong con du lieu sau khi loc split/source/text.")

    df["row_id"] = range(len(df))
    return df


def predict(df: pd.DataFrame, model_dir: str, batch_size: int, max_length: int) -> pd.DataFrame:
    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    texts = df["eval_text"].astype(str).tolist()
    rows: list[dict[str, float | str]] = []
    id2label = {int(k): v for k, v in model.config.id2label.items()}

    with torch.no_grad():
        for start in tqdm(range(0, len(texts), batch_size), desc="Predicting"):
            batch_texts = texts[start : start + batch_size]
            encoded = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(device) for key, value in encoded.items()}
            logits = model(**encoded).logits
            probs = torch.softmax(logits, dim=-1).cpu()
            pred_ids = torch.argmax(probs, dim=-1).tolist()
            for offset, pred_id in enumerate(pred_ids):
                prob_values = probs[offset].tolist()
                rows.append(
                    {
                        "predicted_label": id2label[pred_id],
                        "confidence": max(prob_values),
                        "prob_negative": prob_values[0],
                        "prob_neutral": prob_values[1],
                        "prob_positive": prob_values[2],
                    }
                )

    return pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def save_confusion_matrix(cm: pd.DataFrame, out_path: Path, title: str) -> None:
    plt.figure(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.xlabel("Predicted label")
    plt.ylabel("True label")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def write_summary(
    out_dir: Path,
    args: argparse.Namespace,
    metrics: dict[str, object],
    report_text: str,
    label_counts: pd.Series,
    pred_counts: pd.Series,
) -> None:
    summary = f"""# Evaluation Summary

Model:

```text
{args.model}
```

Data:

```text
{args.data}
split_col={args.split_col}
eval_split={args.eval_split}
include_sources={args.include_sources or "all"}
```

Metrics:

```text
Accuracy: {metrics["accuracy"]:.4f}
Macro F1: {metrics["f1_macro"]:.4f}
Weighted F1: {metrics["f1_weighted"]:.4f}
Samples: {metrics["num_samples"]}
Errors: {metrics["num_errors"]}
```

True label counts:

```text
{label_counts.to_string()}
```

Predicted label counts:

```text
{pred_counts.to_string()}
```

Classification report:

```text
{report_text}
```
"""
    (out_dir / "evaluation_summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a PhoBERT sentiment checkpoint.")
    parser.add_argument("--data", default="data/shopee_vietnamese_absa_sentiment.csv")
    parser.add_argument("--model", default="models/ckpt_03_shopee_absa_vietnamese")
    parser.add_argument("--out-dir", default="reports/evaluation/ckpt_03_shopee_absa_vietnamese")
    parser.add_argument("--text-col", default="review_text")
    parser.add_argument("--split-col", default="split")
    parser.add_argument("--eval-split", default="test")
    parser.add_argument("--include-sources", default="")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_eval_data(args)
    scored = predict(df, args.model, batch_size=args.batch_size, max_length=args.max_length)
    scored["is_correct"] = scored["label"].eq(scored["predicted_label"])

    y_true = scored["label"]
    y_pred = scored["predicted_label"]
    metrics = {
        "model": args.model,
        "data": args.data,
        "num_samples": int(len(scored)),
        "num_errors": int((~scored["is_correct"]).sum()),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, labels=LABELS, average="weighted", zero_division=0)),
    }

    report_text = classification_report(y_true, y_pred, labels=LABELS, zero_division=0)
    cm_values = confusion_matrix(y_true, y_pred, labels=LABELS)
    cm = pd.DataFrame(cm_values, index=LABELS, columns=LABELS)

    scored.to_csv(out_dir / "predictions.csv", index=False, encoding="utf-8-sig")
    scored[~scored["is_correct"]].sort_values("confidence", ascending=False).to_csv(
        out_dir / "errors.csv", index=False, encoding="utf-8-sig"
    )
    cm.to_csv(out_dir / "confusion_matrix.csv", encoding="utf-8-sig")
    save_confusion_matrix(cm, out_dir / "confusion_matrix.png", title=Path(args.model).name)
    (out_dir / "classification_report.txt").write_text(report_text, encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(
        out_dir,
        args,
        metrics,
        report_text,
        label_counts=y_true.value_counts(),
        pred_counts=y_pred.value_counts(),
    )

    print(f"Saved evaluation report: {out_dir}")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(report_text)


if __name__ == "__main__":
    main()
