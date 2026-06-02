"""
Build shop profiles from sentiment-scored Shopee reviews.

Input:
    data/shopee_reviews_scored.csv

Output:
    data/shop_profiles.csv

Each row is a shop profile for one target product.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


LABEL_SCORE = {
    "positive": 1.0,
    "neutral": 0.5,
    "negative": 0.0,
}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def choose_sentiment_column(df: pd.DataFrame) -> str:
    if "predicted_label" in df.columns and df["predicted_label"].fillna("").astype(str).str.len().sum() > 0:
        return "predicted_label"
    return "label"


def classify_shop(row: pd.Series, min_reviews: int) -> str:
    if row["total_reviews"] < min_reviews:
        return "chua_du_du_lieu"
    if row["avg_rating"] >= 4.5 and row["positive_rate"] >= 0.75 and row["negative_rate"] <= 0.10:
        return "rat_tot"
    if row["avg_rating"] >= 4.0 and row["positive_rate"] >= 0.60 and row["negative_rate"] <= 0.20:
        return "tot_on_dinh"
    if row["negative_rate"] >= 0.35 or row["avg_rating"] < 3.5:
        return "rui_ro_cao"
    if row["neutral_rate"] >= 0.40:
        return "trung_tinh_can_can_nhac"
    return "can_can_nhac"


def build_profiles(df: pd.DataFrame, min_reviews: int) -> pd.DataFrame:
    sentiment_col = choose_sentiment_column(df)
    df = df.copy()

    for col in ["target_product", "shop_name", "item_id", "product_url"]:
        if col not in df.columns:
            df[col] = ""

    df["sentiment_label"] = df[sentiment_col].fillna("").astype(str).str.lower()
    df["sentiment_value"] = df["sentiment_label"].map(LABEL_SCORE).fillna(0.5)
    df["review_length"] = df["review_text"].fillna("").astype(str).str.len()

    group_cols = ["target_product", "shop_id"]
    profiles = (
        df.groupby(group_cols)
        .agg(
            shop_name=("shop_name", lambda x: next((v for v in x if str(v).strip()), "")),
            total_reviews=("review_text", "count"),
            avg_rating=("rating", "mean"),
            sentiment_score=("sentiment_value", "mean"),
            positive_count=("sentiment_label", lambda x: (x == "positive").sum()),
            neutral_count=("sentiment_label", lambda x: (x == "neutral").sum()),
            negative_count=("sentiment_label", lambda x: (x == "negative").sum()),
            avg_review_length=("review_length", "mean"),
            product_count=("item_id", "nunique"),
        )
        .reset_index()
    )

    profiles["positive_rate"] = profiles["positive_count"] / profiles["total_reviews"]
    profiles["neutral_rate"] = profiles["neutral_count"] / profiles["total_reviews"]
    profiles["negative_rate"] = profiles["negative_count"] / profiles["total_reviews"]

    global_sentiment = df["sentiment_value"].mean()
    smoothing = 20
    profiles["smoothed_sentiment"] = (
        profiles["sentiment_score"] * profiles["total_reviews"] + global_sentiment * smoothing
    ) / (profiles["total_reviews"] + smoothing)

    profiles["recommendation_score"] = (
        0.55 * profiles["smoothed_sentiment"]
        + 0.30 * (profiles["avg_rating"] / 5.0)
        + 0.15 * (1.0 - profiles["negative_rate"])
    )
    profiles["shop_type"] = profiles.apply(lambda row: classify_shop(row, min_reviews=min_reviews), axis=1)

    return profiles.sort_values(
        ["target_product", "recommendation_score", "total_reviews"],
        ascending=[True, False, False],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build shop profiles from sentiment-scored reviews.")
    parser.add_argument("--reviews", default="data/shopee_reviews_scored.csv")
    parser.add_argument("--out", default="data/shop_profiles.csv")
    parser.add_argument("--min-reviews", type=int, default=10)
    args = parser.parse_args()

    reviews_path = Path(args.reviews)
    if not reviews_path.exists() and args.reviews == "data/shopee_reviews_scored.csv":
        fallback_path = Path("data/shopee_reviews_all.csv")
        if fallback_path.exists():
            print(f"Chua co {reviews_path}, dung tam {fallback_path}.")
            reviews_path = fallback_path

    df = pd.read_csv(reviews_path)
    required = {"review_text", "rating", "label", "shop_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df = df.dropna(subset=["review_text", "rating", "label", "shop_id"]).copy()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["rating"])

    profiles = build_profiles(df, min_reviews=args.min_reviews)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Saved shop profiles: {out_path}")
    print(profiles.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
