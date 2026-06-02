"""
Train a reproducible baseline sentiment model from crawled Shopee reviews.

The training label is initially derived from rating:
    1-2 stars -> negative
    3 stars   -> neutral
    4-5 stars -> positive
"""

from __future__ import annotations

import argparse
import joblib
import sys
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train TF-IDF Logistic Regression sentiment model.")
    parser.add_argument("--data", default="data/shopee_reviews_all.csv")
    parser.add_argument("--model-out", default="models/sentiment_tfidf_lr.joblib")
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    df = df.dropna(subset=["review_text", "label"]).copy()
    df["review_text"] = df["review_text"].astype(str)
    df["label"] = df["label"].astype(str).str.lower()

    label_counts = df["label"].value_counts()
    print("Label counts:")
    print(label_counts.to_string())

    if len(label_counts) < 2:
        raise SystemExit("Cần ít nhất 2 nhãn để train model. Hãy crawl thêm review neutral/negative.")

    stratify = df["label"] if label_counts.min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        df["review_text"],
        df["label"],
        test_size=args.test_size,
        random_state=42,
        stratify=stratify,
    )

    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=30000)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, zero_division=0))

    model_path = Path(args.model_out)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"Saved model: {model_path}")


if __name__ == "__main__":
    main()
