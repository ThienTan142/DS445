from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(..., max_length=3000)


class PredictResponse(BaseModel):
    prediction: str
    confidence: float
    probabilities: dict[str, float]
    processing_time_ms: int
    model_mode: str


class HealthResponse(BaseModel):
    status: str
    model_mode: str
    model_loaded: bool


class ConfigResponse(BaseModel):
    power_bi_embed_url: str
    model_mode: str
