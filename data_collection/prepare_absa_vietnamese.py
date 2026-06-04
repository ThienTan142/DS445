"""
Prepare Kaggle ABSA Vietnamese Shopee reviews for review-level sentiment.

Input files:
    data/raw/absa_vietnamese/train_data.csv
    data/raw/absa_vietnamese/val_data.csv
    data/raw/absa_vietnamese/test_data.csv

Output schema:
    review_text,label,rating,target_product,category,shop_id,shop_name,item_id,
    aspect,source,split,aspect_labels
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


ASPECT_COLUMNS = [
    "Price",
    "Shipping",
    "Outlook",
    "Quality",
    "Size",
    "Shop_Service",
    "General",
    "Others",
]
VALUE_TO_LABEL = {0: "negative", 1: "positive", 2: "neutral"}
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


def extract_aspect_labels(row: pd.Series) -> dict[str, str]:
    labels = {}
    for aspect in ASPECT_COLUMNS:
        try:
            value = int(row[aspect])
        except (KeyError, TypeError, ValueError):
            continue
        label = VALUE_TO_LABEL.get(value)
        if label:
            labels[aspect] = label
    return labels


def collapse_review_label(aspect_labels: dict[str, str]) -> str:
    """Collapse aspect sentiments into one review sentiment label."""
    labels = set(aspect_labels.values())
    if not labels:
        return ""
    if len(labels) == 1:
        return next(iter(labels))
    if "negative" in labels and "positive" in labels:
        return "neutral"
    if "negative" in labels:
        return "negative"
    if "positive" in labels:
        return "positive"
    return "neutral"


def load_split(raw_dir: Path, file_name: str, split: str) -> pd.DataFrame:
    path = raw_dir / file_name
    raw = pd.read_csv(path, encoding="utf-8-sig")
    rows = []
    for _, row in raw.iterrows():
        text = normalize_text(row.get("Review", ""))
        aspect_labels = extract_aspect_labels(row)
        label = collapse_review_label(aspect_labels)
        if not text or not label:
            continue
        rows.append(
            {
                "review_text": text,
                "label": label,
                "rating": "",
                "target_product": "giay_shopee",
                "category": "fashion_shoes",
                "shop_id": "",
                "shop_name": "",
                "item_id": "",
                "aspect": ",".join(aspect_labels.keys()) or "tong_quan",
                "source": "kaggle_absa_vietnamese_shopee",
                "split": split,
                "aspect_labels": json.dumps(aspect_labels, ensure_ascii=False, sort_keys=True),
            }
        )
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare ABSA Vietnamese Shopee reviews.")
    parser.add_argument("--raw-dir", default="data/raw/absa_vietnamese")
    parser.add_argument("--out", default="data/shopee_vietnamese_absa_sentiment.csv")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    frames = [
        load_split(raw_dir, "train_data.csv", "train"),
        load_split(raw_dir, "val_data.csv", "val"),
        load_split(raw_dir, "test_data.csv", "test"),
    ]
    output = pd.concat(frames, ignore_index=True)
    output = output.drop_duplicates(subset=["review_text", "label", "split"])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Saved: {out_path}")
    print(f"Rows: {len(output)}")
    print("Label counts:")
    print(output["label"].value_counts().to_string())
    print("Split counts:")
    print(output["split"].value_counts().to_string())
    print("Label by split:")
    print(output.groupby("split")["label"].value_counts().to_string())


if __name__ == "__main__":
    main()
