"""
Predict Shopee review sentiment with a fine-tuned PhoBERT model.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from underthesea import word_tokenize


ASPECT_KEYWORDS = {
    "giao_hang": ["giao", "ship", "van chuyen", "vận chuyển", "nhanh", "cham", "chậm", "lau", "lâu"],
    "dong_goi": ["dong goi", "đóng gói", "hop", "hộp", "bao bi", "bao bì", "mop", "móp"],
    "chat_luong": ["chat luong", "chất lượng", "dung", "dùng", "tham", "thấm", "mui", "mùi", "vai", "vải", "am thanh", "âm thanh", "size"],
    "gia_ca": ["gia", "giá", "re", "rẻ", "dat", "đắt", "tien", "tiền"],
    "dich_vu_shop": ["shop", "tu van", "tư vấn", "phan hoi", "phản hồi"],
}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return re.sub(r"\s+", " ", text).strip()


def segment_text(value: object) -> str:
    text = normalize_text(value)
    return word_tokenize(text, format="text") if text else ""


def infer_aspect(text: str) -> str:
    lowered = text.lower()
    for aspect, keywords in ASPECT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return aspect
    return "tong_quan"


def load_catalog(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    catalog = pd.read_csv(path, encoding="utf-8-sig")
    if "target_product" not in catalog.columns or "category" not in catalog.columns:
        return {}
    return {
        normalize_text(row["target_product"]).lower(): normalize_text(row["category"])
        for _, row in catalog.iterrows()
        if normalize_text(row["target_product"])
    }


def add_model_input(df: pd.DataFrame, catalog: dict[str, str]) -> pd.DataFrame:
    df = df.copy()
    for column in ["review_text", "target_product", "category", "aspect"]:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].map(normalize_text)

    target_key = df["target_product"].str.lower()
    df.loc[df["category"].eq(""), "category"] = target_key.map(catalog).fillna("")
    df.loc[df["category"].eq(""), "category"] = "unknown"
    df.loc[df["aspect"].eq(""), "aspect"] = df.loc[df["aspect"].eq(""), "review_text"].map(infer_aspect)

    df["model_input_text"] = (
        "san_pham: "
        + df["target_product"]
        + " | danh_muc: "
        + df["category"]
        + " | khia_canh: "
        + df["aspect"]
        + " | binh_luan: "
        + df["review_text"]
    )
    df["phobert_input_text"] = df["model_input_text"].map(segment_text)
    return df


def predict_labels(df: pd.DataFrame, model_dir: str, batch_size: int, max_length: int) -> list[str]:
    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    labels: list[str] = []
    texts = df["phobert_input_text"].fillna("").astype(str).tolist()
    id2label = model.config.id2label

    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch_texts = texts[start : start + batch_size]
            encoded = tokenizer(batch_texts, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
            encoded = {key: value.to(device) for key, value in encoded.items()}
            logits = model(**encoded).logits
            pred_ids = torch.argmax(logits, dim=-1).cpu().tolist()
            labels.extend(str(id2label[pred_id]) for pred_id in pred_ids)
    return labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict Shopee review sentiment with PhoBERT.")
    parser.add_argument("--data", default="data/shopee_vietnamese_absa_sentiment.csv")
    parser.add_argument("--model", default="models/phobert_absa_shopee_vietnamese")
    parser.add_argument("--catalog", default="data/product_catalog.csv")
    parser.add_argument("--out", default="data/shopee_vietnamese_absa_scored.csv")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=256)
    args = parser.parse_args()

    df = pd.read_csv(args.data, encoding="utf-8-sig")
    catalog = load_catalog(Path(args.catalog))
    df = add_model_input(df, catalog)
    df["predicted_label"] = predict_labels(df, args.model, args.batch_size, args.max_length)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Saved scored reviews: {out_path}")
    print(df["predicted_label"].value_counts().to_string())


if __name__ == "__main__":
    main()
