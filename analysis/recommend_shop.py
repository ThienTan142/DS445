"""
Recommend the best Shopee shop for a product keyword.

Flow:
    crawled reviews -> sentiment label per review -> product query -> best shop

Usage:
    python analysis/recommend_shop.py --query "kem chong nang"
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

import pandas as pd


LABEL_SCORE = {
    "positive": 1.0,
    "neutral": 0.5,
    "negative": 0.0,
}


SHOP_TYPE_PRIORITY = {
    "rat_tot": 5,
    "tot_on_dinh": 4,
    "trung_tinh_can_can_nhac": 3,
    "can_can_nhac": 2,
    "rui_ro_cao": 1,
    "chua_du_du_lieu": 0,
}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def normalize_text(text: str) -> str:
    """Lowercase and remove Vietnamese accents for robust keyword matching."""
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.replace("_", " ").split())


def choose_sentiment_column(df: pd.DataFrame) -> str:
    if "predicted_label" in df.columns and df["predicted_label"].fillna("").astype(str).str.len().sum() > 0:
        return "predicted_label"
    return "label"


def load_reviews(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"review_text", "rating", "label", "shop_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    for col in ["target_product", "shop_name", "item_id", "product_url"]:
        if col not in df.columns:
            df[col] = ""

    df = df.dropna(subset=["review_text", "rating", "label", "shop_id"]).copy()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["rating"])
    return df


def apply_shop_map(df: pd.DataFrame, shop_map_path: Path | None) -> pd.DataFrame:
    """Attach shop names from a shop_id -> shop_name mapping file."""
    if shop_map_path is None or not shop_map_path.exists():
        return df

    shop_map = pd.read_csv(shop_map_path)
    required = {"shop_id", "shop_name"}
    missing = required - set(shop_map.columns)
    if missing:
        raise ValueError(f"shop map missing columns: {sorted(missing)}")

    mapped = df.merge(
        shop_map[["shop_id", "shop_name"]].drop_duplicates("shop_id"),
        on="shop_id",
        how="left",
        suffixes=("", "_mapped"),
    )
    mapped["shop_name"] = mapped["shop_name"].fillna("")
    mapped["shop_name_mapped"] = mapped["shop_name_mapped"].fillna("")
    mapped["shop_name"] = mapped["shop_name"].where(
        mapped["shop_name"].astype(str).str.strip().ne(""),
        mapped["shop_name_mapped"],
    )
    return mapped.drop(columns=["shop_name_mapped"])


def filter_by_query(df: pd.DataFrame, query: str) -> pd.DataFrame:
    query_norm = normalize_text(query)
    searchable = (
        df["target_product"].fillna("").map(normalize_text)
        + " "
        + df["product_url"].fillna("").map(normalize_text)
    )
    return df[searchable.str.contains(query_norm, regex=False)].copy()


def rank_shops(df: pd.DataFrame, min_reviews: int) -> pd.DataFrame:
    sentiment_col = choose_sentiment_column(df)
    df = df.copy()
    df["sentiment_label"] = df[sentiment_col].fillna("").astype(str).str.lower()
    df["sentiment_value"] = df["sentiment_label"].map(LABEL_SCORE).fillna(0.5)

    grouped = (
        df.groupby("shop_id")
        .agg(
            shop_name=("shop_name", lambda x: next((v for v in x if str(v).strip()), "")),
            total_reviews=("review_text", "count"),
            avg_rating=("rating", "mean"),
            sentiment_score=("sentiment_value", "mean"),
            positive_count=("sentiment_label", lambda x: (x == "positive").sum()),
            neutral_count=("sentiment_label", lambda x: (x == "neutral").sum()),
            negative_count=("sentiment_label", lambda x: (x == "negative").sum()),
            product_count=("item_id", "nunique"),
        )
        .reset_index()
    )

    grouped["positive_rate"] = grouped["positive_count"] / grouped["total_reviews"]
    grouped["negative_rate"] = grouped["negative_count"] / grouped["total_reviews"]

    global_sentiment = df["sentiment_value"].mean()
    smoothing = 20
    grouped["smoothed_sentiment"] = (
        grouped["sentiment_score"] * grouped["total_reviews"] + global_sentiment * smoothing
    ) / (grouped["total_reviews"] + smoothing)

    grouped["recommendation_score"] = (
        0.55 * grouped["smoothed_sentiment"]
        + 0.30 * (grouped["avg_rating"] / 5.0)
        + 0.15 * (1.0 - grouped["negative_rate"])
    )

    grouped = grouped[grouped["total_reviews"] >= min_reviews].copy()
    grouped["neutral_rate"] = grouped["neutral_count"] / grouped["total_reviews"]
    grouped["shop_type"] = grouped.apply(lambda row: classify_shop(row, min_reviews=min_reviews), axis=1)
    grouped["recommended_shop"] = grouped.apply(
        lambda row: row["shop_name"] if str(row["shop_name"]).strip() else f"shop_id={row['shop_id']}",
        axis=1,
    )


def classify_shop(row: pd.Series, min_reviews: int) -> str:
    if row["total_reviews"] < min_reviews:
        return "chua_du_du_lieu"
    if row["avg_rating"] >= 4.5 and row["positive_rate"] >= 0.75 and row["negative_rate"] <= 0.10:
        return "rat_tot"
    if row["avg_rating"] >= 4.0 and row["positive_rate"] >= 0.60 and row["negative_rate"] <= 0.20:
        return "tot_on_dinh"
    if row["negative_rate"] >= 0.35 or row["avg_rating"] < 3.5:
        return "rui_ro_cao"
    if row.get("neutral_rate", 0.0) >= 0.40:
        return "trung_tinh_can_can_nhac"
    return "can_can_nhac"


def load_profiles(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    profiles = pd.read_csv(path)
    required = {"target_product", "shop_id", "total_reviews", "recommendation_score", "shop_type"}
    missing = required - set(profiles.columns)
    if missing:
        raise ValueError(f"profile file missing columns: {sorted(missing)}")
    return profiles


def filter_profiles_by_query(profiles: pd.DataFrame, query: str, min_reviews: int) -> pd.DataFrame:
    query_norm = normalize_text(query)
    filtered = profiles[
        profiles["target_product"].fillna("").map(normalize_text).str.contains(query_norm, regex=False)
    ].copy()
    filtered = filtered[filtered["total_reviews"] >= min_reviews].copy()
    if "recommended_shop" not in filtered.columns:
        filtered["shop_name"] = filtered.get("shop_name", "").fillna("")
        filtered["recommended_shop"] = filtered.apply(
            lambda row: row["shop_name"] if str(row["shop_name"]).strip() else f"shop_id={row['shop_id']}",
            axis=1,
        )
    filtered["shop_type_priority"] = filtered["shop_type"].map(SHOP_TYPE_PRIORITY).fillna(0)
    return filtered.sort_values(
        ["shop_type_priority", "recommendation_score", "total_reviews", "avg_rating"],
        ascending=[False, False, False, False],
    )
    return grouped.sort_values(
        ["recommendation_score", "total_reviews", "avg_rating"],
        ascending=[False, False, False],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Recommend best Shopee shop by product keyword.")
    parser.add_argument("--query", help="Tên vật phẩm cần mua, ví dụ: kem chong nang")
    parser.add_argument("--reviews", default="data/shopee_reviews_scored.csv")
    parser.add_argument("--profiles", default="data/shop_profiles.csv")
    parser.add_argument("--shop-map", default="data/shop_map.csv")
    parser.add_argument("--out", default="data/recommended_shops.csv")
    parser.add_argument("--min-reviews", type=int, default=5)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    query = args.query or input("Nhập tên vật phẩm cần mua: ").strip()
    profiles = load_profiles(Path(args.profiles))
    if profiles is not None:
        ranking = filter_profiles_by_query(profiles, query, min_reviews=args.min_reviews)
        if ranking.empty:
            print(f"Khong tim thay shop profile du dieu kien cho vat pham: {query}")
        else:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            ranking.to_csv(out_path, index=False, encoding="utf-8-sig")

            best = ranking.iloc[0]
            print(f"Vat pham: {query}")
            print(f"Shop goi y tot nhat: {best['recommended_shop']}")
            print(f"Loai shop: {best['shop_type']}")
            print(f"Diem goi y: {best['recommendation_score']:.4f}")
            print(f"So review: {int(best['total_reviews'])}")
            print(f"Rating trung binh: {best.get('avg_rating', 0):.2f}")
            print()
            columns = [
                "recommended_shop",
                "shop_id",
                "shop_type",
                "total_reviews",
                "avg_rating",
                "positive_rate",
                "negative_rate",
                "recommendation_score",
            ]
            existing_columns = [col for col in columns if col in ranking.columns]
            print(ranking.head(args.top_k)[existing_columns].to_string(index=False))
            print(f"\nDa luu bang goi y: {out_path}")
            return

    reviews_path = Path(args.reviews)
    if not reviews_path.exists() and args.reviews == "data/shopee_reviews_scored.csv":
        fallback_path = Path("data/shopee_reviews_all.csv")
        if fallback_path.exists():
            print(f"Chưa có {reviews_path}, dùng tạm {fallback_path}.")
            reviews_path = fallback_path

    reviews = load_reviews(reviews_path)
    reviews = apply_shop_map(reviews, Path(args.shop_map))
    filtered = filter_by_query(reviews, query)

    if filtered.empty:
        available = sorted(set(reviews["target_product"].dropna().astype(str)))
        print(f"Không tìm thấy review cho vật phẩm: {query}")
        if available:
            print("Các target_product hiện có:")
            for value in available[:30]:
                if value.strip():
                    print(f"- {value}")
        return

    ranking = rank_shops(filtered, min_reviews=args.min_reviews)
    if ranking.empty:
        print(f"Có {len(filtered)} review cho '{query}', nhưng chưa shop nào đạt min_reviews={args.min_reviews}.")
        print("Thử giảm --min-reviews hoặc crawl thêm dữ liệu.")
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ranking.to_csv(out_path, index=False, encoding="utf-8-sig")

    best = ranking.iloc[0]
    print(f"Vật phẩm: {query}")
    print(f"Shop gợi ý tốt nhất: {best['recommended_shop']}")
    print(f"Điểm gợi ý: {best['recommendation_score']:.4f}")
    print(f"Số review: {int(best['total_reviews'])}")
    print(f"Rating trung bình: {best['avg_rating']:.2f}")
    print(f"Tỷ lệ tích cực: {best['positive_rate']:.2%}")
    print(f"Tỷ lệ tiêu cực: {best['negative_rate']:.2%}")
    print()
    print(ranking.head(args.top_k)[
        [
            "recommended_shop",
            "shop_id",
            "total_reviews",
            "avg_rating",
            "shop_type",
            "positive_rate",
            "negative_rate",
            "recommendation_score",
        ]
    ].to_string(index=False))
    print(f"\nĐã lưu bảng xếp hạng: {out_path}")


if __name__ == "__main__":
    main()
