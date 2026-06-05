from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import precision_score, recall_score


LABELS = ["negative", "neutral", "positive"]
REPORT_DIR = Path("reports/evaluation/ckpt_03_shopee_absa_vietnamese")
PREDICTION_EVENTS: list[dict[str, Any]] = []
INVALID_EVENTS: list[dict[str, Any]] = []


def record_prediction(prediction: str, confidence: float, processing_time_ms: int) -> None:
    PREDICTION_EVENTS.append(
        {
            "date": date.today().isoformat(),
            "prediction": prediction.lower(),
            "confidence": confidence,
            "processing_time_ms": processing_time_ms,
        }
    )
    if len(PREDICTION_EVENTS) > 500:
        del PREDICTION_EVENTS[:-500]


def record_invalid_input() -> None:
    INVALID_EVENTS.append({"date": date.today().isoformat()})
    if len(INVALID_EVENTS) > 500:
        del INVALID_EVENTS[:-500]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_predictions() -> pd.DataFrame:
    path = REPORT_DIR / "predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def read_errors() -> pd.DataFrame:
    path = REPORT_DIR / "errors.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def sample_metrics() -> dict[str, Any]:
    return {
        "cards": {
            "accuracy": 0.7692,
            "precision": 0.68,
            "recall": 0.75,
            "f1_score": 0.705,
            "avg_processing_time_ms": 124,
            "invalid_input_rate": 0.027,
        },
        "confusion_matrix": {
            "labels": ["Negative", "Neutral", "Positive"],
            "values": [[190, 38, 3], [134, 368, 103], [27, 234, 1238]],
        },
        "label_distribution": [
            {"label": "Positive", "count": 1499},
            {"label": "Neutral", "count": 605},
            {"label": "Negative", "count": 231},
        ],
        "confidence_distribution": [
            {"bucket": "0.50-0.60", "count": 120},
            {"bucket": "0.60-0.70", "count": 260},
            {"bucket": "0.70-0.80", "count": 520},
            {"bucket": "0.80-0.90", "count": 790},
            {"bucket": "0.90-1.00", "count": 645},
        ],
        "prediction_history": [
            {"date": (date.today() - timedelta(days=6 - idx)).isoformat(), "count": value}
            for idx, value in enumerate([18, 27, 34, 29, 42, 55, 61])
        ],
        "class_performance": [
            {"label": "Negative", "precision": 0.54, "recall": 0.82, "f1": 0.65},
            {"label": "Neutral", "precision": 0.57, "recall": 0.61, "f1": 0.59},
            {"label": "Positive", "precision": 0.92, "recall": 0.83, "f1": 0.87},
        ],
        "error_analysis": {
            "summary": {
                "total_samples": 2335,
                "correct_samples": 1796,
                "error_samples": 539,
                "error_rate": 0.2308,
            },
            "confusion_pairs": [
                {"actual": "Positive", "predicted": "Neutral", "count": 234},
                {"actual": "Neutral", "predicted": "Negative", "count": 134},
                {"actual": "Neutral", "predicted": "Positive", "count": 103},
                {"actual": "Negative", "predicted": "Neutral", "count": 38},
                {"actual": "Positive", "predicted": "Negative", "count": 27},
            ],
            "aspect_errors": [
                {"aspect": "Outlook", "count": 264},
                {"aspect": "General", "count": 152},
                {"aspect": "Quality", "count": 141},
                {"aspect": "Shop_Service", "count": 119},
                {"aspect": "Size", "count": 118},
                {"aspect": "Shipping", "count": 114},
                {"aspect": "Price", "count": 64},
                {"aspect": "Others", "count": 59},
            ],
            "high_confidence_errors": [
                {
                    "review_text": "san pham gia mem, dang mua nha cac ban",
                    "actual": "Neutral",
                    "predicted": "Positive",
                    "confidence": 0.9558,
                    "aspect": "General",
                }
            ],
        },
    }


def build_confidence_distribution(df: pd.DataFrame) -> list[dict[str, Any]]:
    if "confidence" not in df.columns or df.empty:
        return sample_metrics()["confidence_distribution"]
    bins = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    labels = ["0.00-0.50", "0.50-0.60", "0.60-0.70", "0.70-0.80", "0.80-0.90", "0.90-1.00"]
    bucketed = pd.cut(df["confidence"], bins=bins, labels=labels, include_lowest=True)
    counts = bucketed.value_counts().sort_index()
    return [{"bucket": str(bucket), "count": int(count)} for bucket, count in counts.items()]


def build_prediction_history() -> list[dict[str, Any]]:
    today = date.today()
    base = {str(today - timedelta(days=6 - idx)): 0 for idx in range(7)}
    if PREDICTION_EVENTS:
        for event in PREDICTION_EVENTS:
            if event["date"] in base:
                base[event["date"]] += 1
        return [{"date": day, "count": count} for day, count in base.items()]
    return sample_metrics()["prediction_history"]


def title_label(value: Any) -> str:
    return str(value or "").strip().title()


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def split_aspects(value: Any) -> list[str]:
    if pd.isna(value) or not str(value).strip():
        return ["Unknown"]
    return [part.strip() for part in str(value).split(",") if part.strip()] or ["Unknown"]


def build_error_analysis(predictions_df: pd.DataFrame, errors_df: pd.DataFrame) -> dict[str, Any]:
    if predictions_df.empty:
        return sample_metrics()["error_analysis"]

    if errors_df.empty:
        errors_df = predictions_df[predictions_df["label"].astype(str) != predictions_df["predicted_label"].astype(str)]

    total_samples = len(predictions_df)
    error_samples = len(errors_df)
    correct_samples = total_samples - error_samples
    error_rate = error_samples / total_samples if total_samples else 0.0

    confusion_pairs = []
    if not errors_df.empty:
        pair_counts = (
            errors_df.groupby(["label", "predicted_label"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        confusion_pairs = [
            {
                "actual": title_label(row["label"]),
                "predicted": title_label(row["predicted_label"]),
                "count": int(row["count"]),
            }
            for _, row in pair_counts.head(8).iterrows()
        ]

    aspect_counter: dict[str, int] = {}
    if "aspect" in errors_df.columns:
        for value in errors_df["aspect"]:
            for aspect in split_aspects(value):
                aspect_counter[aspect] = aspect_counter.get(aspect, 0) + 1
    aspect_errors = [
        {"aspect": aspect, "count": count}
        for aspect, count in sorted(aspect_counter.items(), key=lambda item: item[1], reverse=True)[:10]
    ]

    high_confidence_errors = []
    needed_cols = {"review_text", "label", "predicted_label", "confidence"}
    if needed_cols.issubset(errors_df.columns):
        top_errors = errors_df.sort_values("confidence", ascending=False).head(8)
        high_confidence_errors = [
            {
                "review_text": clean_text(row["review_text"]),
                "actual": title_label(row["label"]),
                "predicted": title_label(row["predicted_label"]),
                "confidence": round(float(row["confidence"]), 4),
                "aspect": clean_text(row.get("aspect", "")),
            }
            for _, row in top_errors.iterrows()
        ]

    return {
        "summary": {
            "total_samples": int(total_samples),
            "correct_samples": int(correct_samples),
            "error_samples": int(error_samples),
            "error_rate": round(float(error_rate), 4),
        },
        "confusion_pairs": confusion_pairs,
        "aspect_errors": aspect_errors,
        "high_confidence_errors": high_confidence_errors,
    }


def build_metrics() -> dict[str, Any]:
    metrics = sample_metrics()
    raw_metrics = read_json(REPORT_DIR / "metrics.json")
    df = read_predictions()
    if df.empty:
        return metrics

    y_true = df["label"].astype(str).str.lower()
    y_pred = df["predicted_label"].astype(str).str.lower()
    precision = precision_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)
    recall = recall_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)

    processing_values = [event["processing_time_ms"] for event in PREDICTION_EVENTS]
    avg_processing = sum(processing_values) / len(processing_values) if processing_values else 124
    total_events = len(PREDICTION_EVENTS) + len(INVALID_EVENTS)
    invalid_rate = len(INVALID_EVENTS) / total_events if total_events else 0.027

    cm_path = REPORT_DIR / "confusion_matrix.csv"
    cm_df = pd.read_csv(cm_path, index_col=0, encoding="utf-8-sig") if cm_path.exists() else pd.DataFrame()
    label_counts = df["label"].value_counts()

    metrics["cards"] = {
        "accuracy": round(float(raw_metrics.get("accuracy", 0.0)), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(raw_metrics.get("f1_macro", 0.0)), 4),
        "avg_processing_time_ms": round(float(avg_processing), 1),
        "invalid_input_rate": round(float(invalid_rate), 4),
    }
    if not cm_df.empty:
        metrics["confusion_matrix"] = {
            "labels": [label.title() for label in cm_df.columns.tolist()],
            "values": cm_df.astype(int).values.tolist(),
        }
    metrics["label_distribution"] = [
        {"label": label.title(), "count": int(label_counts.get(label, 0))} for label in ["positive", "neutral", "negative"]
    ]
    metrics["confidence_distribution"] = build_confidence_distribution(df)
    metrics["prediction_history"] = build_prediction_history()
    metrics["error_analysis"] = build_error_analysis(df, read_errors())
    return metrics
