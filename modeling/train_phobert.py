"""
Fine-tune PhoBERT for Vietnamese sentiment classification.

Recommended two-stage flow:
    1. Public/general training:
       python modeling/train_phobert.py --include-sources public,amazon_vi,uit_vsfc,manual --output-dir models/phobert_public

    2. Shopee domain fine-tuning:
       python modeling/train_phobert.py --base-model models/phobert_public --include-sources shopee,manual --output-dir models/phobert_shopee
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)
from underthesea import word_tokenize


LABELS = ["negative", "neutral", "positive"]
LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}
ID_TO_LABEL = {index: label for label, index in LABEL_TO_ID.items()}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def parse_sources(value: str) -> set[str]:
    return {part.strip() for part in value.split(",") if part.strip()}


def sample_max_per_label(df: pd.DataFrame, max_per_label: int, seed: int) -> pd.DataFrame:
    if max_per_label <= 0:
        return df
    parts = []
    for _, group in df.groupby("label"):
        n = min(len(group), max_per_label)
        parts.append(group.sample(n=n, random_state=seed))
    return pd.concat(parts, ignore_index=True) if parts else df


def segment_text(text: object) -> str:
    value = "" if pd.isna(text) else str(text)
    value = " ".join(value.split())
    if not value:
        return ""
    return word_tokenize(value, format="text")


def load_training_data(args: argparse.Namespace) -> pd.DataFrame:
    df = pd.read_csv(args.data, encoding="utf-8-sig")
    text_col = args.text_col if args.text_col in df.columns else "review_text"
    if text_col not in df.columns:
        raise SystemExit(f"Khong tim thay cot text: {args.text_col} hoac review_text")
    if "source" not in df.columns:
        df["source"] = "unknown"

    df = df.dropna(subset=[text_col, "label"]).copy()
    df["label"] = df["label"].astype(str).str.lower().str.strip()
    df["source"] = df["source"].astype(str).str.lower().str.strip()
    df = df[df["label"].isin(LABELS)].copy()

    include_sources = parse_sources(args.include_sources)
    exclude_sources = parse_sources(args.exclude_sources)
    if include_sources:
        df = df[df["source"].isin(include_sources)].copy()
    if exclude_sources:
        df = df[~df["source"].isin(exclude_sources)].copy()

    df = sample_max_per_label(df, max_per_label=args.max_per_label, seed=args.seed)

    df["text"] = df[text_col].map(segment_text)
    df["label_id"] = df["label"].map(LABEL_TO_ID)
    df = df[df["text"].str.len() > 0].copy()

    if df.empty:
        raise SystemExit("Khong con du lieu sau khi loc source/label/text.")

    print("Rows:", len(df))
    print("Label counts:")
    print(df["label"].value_counts().to_string())
    print("Source counts:")
    print(df["source"].value_counts().to_string())
    columns = ["text", "label_id", "label", "source"]
    if args.split_col and args.split_col in df.columns:
        columns.append(args.split_col)
    return df[columns]


def build_datasets(args: argparse.Namespace, df: pd.DataFrame) -> tuple[Dataset, Dataset]:
    if args.split_col and args.split_col in df.columns and args.eval_split:
        split_values = df[args.split_col].astype(str).str.lower().str.strip()
        train_splits = parse_sources(args.train_splits.lower())
        eval_split = args.eval_split.lower().strip()
        train_df = df[split_values.isin(train_splits)].copy()
        eval_df = df[split_values.eq(eval_split)].copy()
        train_df = sample_max_per_label(train_df, max_per_label=args.train_max_per_label, seed=args.seed)
        if train_df.empty or eval_df.empty:
            raise SystemExit("Khong tao duoc train/eval tu split_col, train_splits va eval_split.")
        print("Train rows:", len(train_df))
        print(train_df["label"].value_counts().to_string())
        print("Eval rows:", len(eval_df))
        print(eval_df["label"].value_counts().to_string())
        return Dataset.from_pandas(train_df.reset_index(drop=True)), Dataset.from_pandas(eval_df.reset_index(drop=True))

    label_counts = df["label"].value_counts()
    stratify = df["label"] if label_counts.min() >= 2 else None
    train_df, eval_df = train_test_split(
        df,
        test_size=args.test_size,
        random_state=args.seed,
        stratify=stratify,
    )
    train_df = sample_max_per_label(train_df, max_per_label=args.train_max_per_label, seed=args.seed)
    return Dataset.from_pandas(train_df.reset_index(drop=True)), Dataset.from_pandas(eval_df.reset_index(drop=True))


def tokenize_dataset(dataset: Dataset, tokenizer: AutoTokenizer, max_length: int) -> Dataset:
    def tokenize(batch: dict) -> dict:
        encoded = tokenizer(batch["text"], truncation=True, max_length=max_length)
        encoded["labels"] = batch["label_id"]
        return encoded

    return dataset.map(tokenize, batched=True, remove_columns=dataset.column_names)


def compute_metrics(eval_pred) -> dict:
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro", zero_division=0),
    }


def print_final_report(trainer: Trainer, eval_dataset: Dataset) -> None:
    output = trainer.predict(eval_dataset)
    preds = np.argmax(output.predictions, axis=-1)
    labels = output.label_ids
    print(classification_report(labels, preds, target_names=LABELS, zero_division=0))
    print("Confusion matrix labels:", LABELS)
    print(confusion_matrix(labels, preds))


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune PhoBERT for Vietnamese sentiment.")
    parser.add_argument("--data", default="data/sentiment_train.csv")
    parser.add_argument("--model-name", default="vinai/phobert-base")
    parser.add_argument("--base-model", default="", help="Use this checkpoint for continued fine-tuning.")
    parser.add_argument("--output-dir", default="models/phobert_shopee")
    parser.add_argument("--text-col", default="model_input_text")
    parser.add_argument("--include-sources", default="", help="Comma list, e.g. shopee,manual")
    parser.add_argument("--exclude-sources", default="", help="Comma list, e.g. shopee")
    parser.add_argument("--max-per-label", type=int, default=0)
    parser.add_argument("--train-max-per-label", type=int, default=0)
    parser.add_argument("--split-col", default="")
    parser.add_argument("--train-splits", default="train")
    parser.add_argument("--eval-split", default="")
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = load_training_data(args)
    train_ds, eval_ds = build_datasets(args, df)

    checkpoint = args.base_model.strip() or args.model_name
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        checkpoint,
        num_labels=len(LABELS),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID,
    )

    tokenized_train = tokenize_dataset(train_ds, tokenizer, args.max_length)
    tokenized_eval = tokenize_dataset(eval_ds, tokenizer, args.max_length)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        seed=args.seed,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        processing_class=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )
    trainer.train()
    print_final_report(trainer, tokenized_eval)

    out_path = Path(args.output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    trainer.save_model(out_path)
    tokenizer.save_pretrained(out_path)
    (out_path / "label_mapping.json").write_text(
        json.dumps({"label2id": LABEL_TO_ID, "id2label": ID_TO_LABEL}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved PhoBERT model: {out_path}")


if __name__ == "__main__":
    main()
