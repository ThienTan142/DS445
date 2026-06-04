"""
Prepare Vietnamese multi-domain sentiment datasets for staged PhoBERT fine-tuning.

Outputs:
    data/general_vietnamese_sentiment.csv
    data/ecommerce_multidomain_sentiment.csv

All outputs use this shared schema:
    review_text,label,rating,target_product,category,shop_id,shop_name,item_id,
    aspect,source,split,aspect_labels
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset


LABELS = {"negative", "neutral", "positive"}
OUTPUT_COLUMNS = [
    "review_text",
    "label",
    "rating",
    "target_product",
    "category",
    "shop_id",
    "shop_name",
    "item_id",
    "aspect",
    "source",
    "split",
    "aspect_labels",
]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def normalize_label(value: object) -> str:
    label = normalize_text(value).lower()
    label_map = {
        "0": "negative",
        "1": "neutral",
        "2": "positive",
        "neg": "negative",
        "negative": "negative",
        "neu": "neutral",
        "neutral": "neutral",
        "pos": "positive",
        "positive": "positive",
    }
    return label_map.get(label, "")


def collapse_aspect_sentiments(annotations: object) -> tuple[str, dict[str, str]]:
    aspect_labels: dict[str, str] = {}
    if annotations is None:
        return "", aspect_labels

    for item in list(annotations):
        if not isinstance(item, dict):
            continue
        sentiment = normalize_label(item.get("sentiment", ""))
        if not sentiment:
            continue
        aspect = normalize_text(item.get("aspect_category", "")) or normalize_text(item.get("aspect_term", ""))
        aspect_labels[aspect or "aspect"] = sentiment

    labels = set(aspect_labels.values())
    if not labels:
        return "", aspect_labels
    if len(labels) == 1:
        return next(iter(labels)), aspect_labels
    if "negative" in labels and "positive" in labels:
        return "neutral", aspect_labels
    if "negative" in labels:
        return "negative", aspect_labels
    if "positive" in labels:
        return "positive", aspect_labels
    return "neutral", aspect_labels


def make_row(
    *,
    review_text: object,
    label: str,
    source: str,
    split: str,
    category: str,
    aspect: str = "tong_quan",
    target_product: str = "",
    aspect_labels: dict[str, str] | None = None,
) -> dict[str, str]:
    return {
        "review_text": normalize_text(review_text),
        "label": label,
        "rating": "",
        "target_product": target_product,
        "category": category,
        "shop_id": "",
        "shop_name": "",
        "item_id": "",
        "aspect": aspect,
        "source": source,
        "split": split,
        "aspect_labels": json.dumps(aspect_labels or {}, ensure_ascii=False, sort_keys=True),
    }


def load_uit_vsfc() -> pd.DataFrame:
    rows = []
    dataset = load_dataset("tridm/UIT-VSFC")
    for split, part in dataset.items():
        split_name = "val" if split == "validation" else split
        for row in part:
            label = normalize_label(row.get("Sentiment", ""))
            text = normalize_text(row.get("Sentence", ""))
            if text and label in LABELS:
                rows.append(
                    make_row(
                        review_text=text,
                        label=label,
                        source="uit_vsfc",
                        split=split_name,
                        category="general_education",
                        aspect=normalize_text(row.get("Topic", "")) or "tong_quan",
                    )
                )
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def load_vietnamese_sa() -> pd.DataFrame:
    rows = []
    dataset = load_dataset("h-i-e-u/vietnamese-SA-dataset")
    for split, part in dataset.items():
        for row in part:
            label = normalize_label(row.get("label", ""))
            text = normalize_text(row.get("text", ""))
            if text and label in LABELS:
                rows.append(
                    make_row(
                        review_text=text,
                        label=label,
                        source="vietnamese_sa",
                        split=split,
                        category="general_sentiment",
                    )
                )
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def load_viocd() -> pd.DataFrame:
    rows = []
    dataset = load_dataset("tarudesu/ViOCD")
    for split, part in dataset.items():
        split_name = "val" if split == "validation" else split
        for row in part:
            text = normalize_text(row.get("review", ""))
            if not text:
                continue
            try:
                is_complaint = int(float(row.get("label", 0))) == 1
            except (TypeError, ValueError):
                continue
            rows.append(
                make_row(
                    review_text=text,
                    label="negative" if is_complaint else "positive",
                    source="viocd_weak",
                    split=split_name,
                    category=normalize_text(row.get("domain", "")) or "ecommerce",
                    aspect="complaint",
                )
            )
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def load_causasent_tiki() -> pd.DataFrame:
    rows = []
    dataset = load_dataset("Tamir39/causasent-ate-v2")
    for split, part in dataset.items():
        split_name = "val" if split == "validation" else split
        for row in part:
            label, aspect_labels = collapse_aspect_sentiments(row.get("annotations"))
            text = normalize_text(row.get("review", ""))
            if text and label in LABELS:
                rows.append(
                    make_row(
                        review_text=text,
                        label=label,
                        source="causasent_tiki",
                        split=split_name,
                        category=normalize_text(row.get("source", "")) or "ecommerce",
                        aspect=",".join(aspect_labels.keys()) or "aspect_sentiment",
                        target_product="public_tiki",
                        aspect_labels=aspect_labels,
                    )
                )
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def save_dataset(df: pd.DataFrame, path: Path) -> None:
    df = df.drop_duplicates(subset=["review_text", "label", "source", "split"]).copy()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"Saved: {path}")
    print(f"Rows: {len(df)}")
    print("Label counts:")
    print(df["label"].value_counts().to_string())
    print("Source counts:")
    print(df["source"].value_counts().to_string())
    print("Label by split:")
    print(df.groupby("split")["label"].value_counts().to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare multi-domain Vietnamese sentiment data.")
    parser.add_argument("--out-general", default="data/general_vietnamese_sentiment.csv")
    parser.add_argument("--out-ecommerce", default="data/ecommerce_multidomain_sentiment.csv")
    args = parser.parse_args()

    print("Loading general Vietnamese sentiment datasets...")
    general = pd.concat([load_uit_vsfc(), load_vietnamese_sa()], ignore_index=True)
    save_dataset(general, Path(args.out_general))

    print("\nLoading e-commerce multi-domain sentiment datasets...")
    ecommerce = pd.concat([load_viocd(), load_causasent_tiki()], ignore_index=True)
    save_dataset(ecommerce, Path(args.out_ecommerce))


if __name__ == "__main__":
    main()
