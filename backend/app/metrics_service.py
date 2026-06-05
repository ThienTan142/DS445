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
    return metrics
