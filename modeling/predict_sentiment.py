"""
Predict sentiment for crawled Shopee reviews and fill predicted_label.
"""

from __future__ import annotations

import argparse
import joblib
import sys
from pathlib import Path

import pandas as pd


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict Shopee review sentiment.")
    parser.add_argument("--data", default="data/shopee_reviews_all.csv")
    parser.add_argument("--model", default="models/sentiment_tfidf_lr.joblib")
    parser.add_argument("--out", default="data/shopee_reviews_scored.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    model = joblib.load(args.model)

    df["review_text"] = df["review_text"].fillna("").astype(str)
    df["predicted_label"] = model.predict(df["review_text"])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Saved scored reviews: {out_path}")
    print(df["predicted_label"].value_counts().to_string())


if __name__ == "__main__":
    main()
