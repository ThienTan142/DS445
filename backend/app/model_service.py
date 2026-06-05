from __future__ import annotations

import os
import time
from functools import lru_cache
from math import exp


LABELS = ["Negative", "Neutral", "Positive"]
DEFAULT_MODEL_PATH = os.getenv("MODEL_PATH", "models/ckpt_03_shopee_absa_vietnamese")
_REAL_MODEL_LOADED = False


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def softmax(values: list[float]) -> list[float]:
    max_value = max(values)
    exp_values = [exp(value - max_value) for value in values]
    total = sum(exp_values)
    return [value / total for value in exp_values]


class MockSentimentModel:
    """Fast deterministic mock model for portfolio demos and frontend testing."""

    positive_words = {
        "tốt",
        "đẹp",
        "ổn",
        "êm",
        "nhanh",
        "đáng",
        "hài lòng",
        "nên mua",
        "rẻ",
        "xịn",
        "chuẩn",
        "thích",
        "ủng hộ",
    }
    negative_words = {
        "tệ",
        "chậm",
        "lâu",
        "lỗi",
        "rè",
        "yếu",
        "đau",
        "chật",
        "bí",
        "khó chịu",
        "mắc",
        "xấu",
        "không đúng",
        "không nên",
        "thất vọng",
        "bể",
        "móp",
    }

    def predict(self, text: str) -> dict[str, object]:
        started = time.perf_counter()
        lowered = normalize_text(text).lower()
        pos_score = sum(1 for word in self.positive_words if word in lowered)
        neg_score = sum(1 for word in self.negative_words if word in lowered)

        if pos_score > 0 and neg_score > 0:
            if neg_score > pos_score:
                logits = [2.2 + neg_score * 0.35, 1.5, 1.0 + pos_score * 0.15]
            elif pos_score >= neg_score + 2:
                logits = [1.0 + neg_score * 0.15, 1.4, 2.2 + pos_score * 0.35]
            else:
                logits = [1.0 + neg_score * 0.2, 2.6, 1.0 + pos_score * 0.2]
        elif neg_score > pos_score:
            logits = [2.4 + neg_score * 0.45, 1.0, 0.8]
        elif pos_score > neg_score:
            logits = [0.8, 1.0, 2.4 + pos_score * 0.45]
        else:
            logits = [1.1, 2.0, 1.1]

        probs = softmax(logits)
        best_idx = max(range(len(probs)), key=probs.__getitem__)
        processing_time_ms = max(18, int((time.perf_counter() - started) * 1000) + 37)
        return {
            "prediction": LABELS[best_idx],
            "confidence": round(probs[best_idx], 4),
            "probabilities": {label: round(probs[index], 4) for index, label in enumerate(LABELS)},
            "processing_time_ms": processing_time_ms,
        }


class PhoBertSentimentModel:
    """Real PhoBERT inference wrapper.

    To replace the mock model, set MODEL_MODE=real and MODEL_PATH to a local
    fine-tuned checkpoint. The current project checkpoint is:
    models/ckpt_03_shopee_absa_vietnamese
    """

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from underthesea import word_tokenize

        self.torch = torch
        self.word_tokenize = word_tokenize
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def predict(self, text: str) -> dict[str, object]:
        started = time.perf_counter()
        segmented = self.word_tokenize(normalize_text(text), format="text")
        with self.torch.no_grad():
            encoded = self.tokenizer(
                [segmented],
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            )
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
            logits = self.model(**encoded).logits
            probs = self.torch.softmax(logits, dim=-1).cpu()[0].tolist()

        id2label = {int(key): value for key, value in self.model.config.id2label.items()}
        best_idx = int(self.torch.argmax(self.torch.tensor(probs)).item())
        label_map = {"negative": "Negative", "neutral": "Neutral", "positive": "Positive"}
        prediction = label_map.get(str(id2label[best_idx]).lower(), str(id2label[best_idx]))
        probabilities = {
            label_map.get(str(id2label[index]).lower(), str(id2label[index])): round(float(prob), 4)
            for index, prob in enumerate(probs)
        }
        return {
            "prediction": prediction,
            "confidence": round(float(probs[best_idx]), 4),
            "probabilities": probabilities,
            "processing_time_ms": int((time.perf_counter() - started) * 1000),
        }


@lru_cache(maxsize=1)
def get_model() -> MockSentimentModel | PhoBertSentimentModel:
    global _REAL_MODEL_LOADED
    mode = os.getenv("MODEL_MODE", "mock").strip().lower()
    if mode == "real":
        model = PhoBertSentimentModel(os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH))
        _REAL_MODEL_LOADED = True
        return model
    return MockSentimentModel()


def get_model_mode() -> str:
    return os.getenv("MODEL_MODE", "mock").strip().lower()


def is_real_model_loaded() -> bool:
    return get_model_mode() == "real" and _REAL_MODEL_LOADED
