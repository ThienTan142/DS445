from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .metrics_service import build_metrics, record_invalid_input, record_prediction
from .model_service import get_model, get_model_mode, is_real_model_loaded, normalize_text
from .schemas import ConfigResponse, HealthResponse, PredictRequest, PredictResponse


load_dotenv()

app = FastAPI(
    title="DS445 AI Model Demo API",
    description="FastAPI backend for Vietnamese Shopee sentiment analysis demo.",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "DS445 AI Model Demo API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", model_mode=get_model_mode(), model_loaded=is_real_model_loaded())


@app.get("/config", response_model=ConfigResponse)
def config() -> ConfigResponse:
    return ConfigResponse(
        power_bi_embed_url=os.getenv("POWER_BI_EMBED_URL", "").strip(),
        model_mode=get_model_mode(),
    )


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    text = normalize_text(payload.text)
    if len(text) < 3:
        record_invalid_input()
        raise HTTPException(status_code=400, detail="Input text must contain at least 3 characters.")

    result = get_model().predict(text)
    record_prediction(
        prediction=str(result["prediction"]),
        confidence=float(result["confidence"]),
        processing_time_ms=int(result["processing_time_ms"]),
    )
    return PredictResponse(
        prediction=str(result["prediction"]),
        confidence=float(result["confidence"]),
        probabilities={str(key): float(value) for key, value in dict(result["probabilities"]).items()},
        processing_time_ms=int(result["processing_time_ms"]),
        model_mode=get_model_mode(),
    )


@app.get("/metrics")
def metrics() -> dict:
    return build_metrics()
