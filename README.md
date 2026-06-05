# DS445 AI Sentiment Demo

Website demo model AI cho đồ án: phân tích cảm xúc bình luận Shopee tiếng Việt bằng PhoBERT-base.

## Tính năng chính

- Demo model AI với input text, validate input, loading/error state và lịch sử dự đoán.
- Backend FastAPI có `/predict`, `/metrics`, `/health`, `/config`.
- Mock model chạy nhanh để demo portfolio.
- Có tùy chọn bật model PhoBERT thật bằng `MODEL_MODE=real`.
- Analytics dashboard bằng Recharts khi chưa có Power BI.
- Hỗ trợ nhúng Power BI report bằng `POWER_BI_EMBED_URL`.
- Trang About Model, Examples và Documentation.

## Công nghệ

- Frontend: React, Vite, Recharts, Lucide React.
- Backend: FastAPI, Uvicorn, Pydantic.
- AI/NLP: PhoBERT, Transformers, PyTorch, underthesea.
- Dataset/report hiện có: `data/`, `models/`, `reports/evaluation/`.

## Cấu trúc thư mục

```text
backend/
  app/
    main.py
    model_service.py
    metrics_service.py
    schemas.py
frontend/
  src/
    components/
    pages/
    data/
evaluation/
reports/evaluation/
models/
data/
.env.example
```

## Cài đặt

```powershell
cd F:\DS445
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
Copy-Item .env.example .env

.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd frontend
npm ci
```

Ghi chú: cấu hình mặc định dùng `MODEL_MODE=mock`, nên người clone repo có thể chạy demo ngay mà không cần tải model PhoBERT thật. Nếu muốn dùng checkpoint thật, cài thêm:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-real.txt
```

## Chạy backend

```powershell
cd F:\DS445
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Chạy frontend

```powershell
cd F:\DS445\frontend
npm run dev
```

Frontend:

```text
http://127.0.0.1:5173
```

## API documentation

### GET `/health`

Kiểm tra server và chế độ model.

### POST `/predict`

Request:

```json
{
  "text": "Shop giao nhanh, sản phẩm đẹp nhưng size hơi chật"
}
```

Response:

```json
{
  "prediction": "Neutral",
  "confidence": 0.86,
  "probabilities": {
    "Negative": 0.08,
    "Neutral": 0.86,
    "Positive": 0.06
  },
  "processing_time_ms": 124,
  "model_mode": "mock"
}
```

### GET `/metrics`

Trả dữ liệu dashboard: Accuracy, Precision, Recall, F1-score, confusion matrix, phân phối nhãn, confidence distribution, prediction history, latency và invalid input rate.

### GET `/config`

Trả cấu hình frontend cần biết, gồm `power_bi_embed_url`.

## Thay mock model bằng model thật

Mặc định backend dùng mock model để demo nhanh:

```text
MODEL_MODE=mock
```

Để bật PhoBERT thật:

```text
MODEL_MODE=real
MODEL_PATH=models/ckpt_03_shopee_absa_vietnamese
```

Code cần chỉnh nếu thay model khác nằm ở:

```text
backend/app/model_service.py
```

Class `PhoBertSentimentModel` là nơi load tokenizer/model và xử lý inference. Nếu thay bằng `.pkl`, `.pt`, `.h5` hoặc API endpoint khác, chỉ cần giữ response format giống `/predict`.

## Cấu hình Power BI

Thêm embed URL vào `.env`:

```text
POWER_BI_EMBED_URL=https://app.powerbi.com/reportEmbed?...
```

Khi có URL, trang Analytics hiển thị iframe Power BI. Khi không có URL, dashboard nội bộ bằng Recharts sẽ tự hiển thị. Nếu iframe không tải được, kiểm tra quyền truy cập report, tenant policy và loại embed URL.

## Model checkpoints

Pipeline fine-tune hiện tại:

```text
PhoBERT-base
-> ckpt_01_general_sentiment
-> ckpt_02_ecommerce_multidomain
-> ckpt_03_shopee_absa_vietnamese
```

Kết quả checkpoint cuối:

```text
Accuracy: 0.7692
Macro F1: 0.7050
Weighted F1: 0.7769
```

Chi tiết nằm trong:

```text
TRAINING_CHECKPOINTS.md
reports/evaluation/ckpt_03_shopee_absa_vietnamese/evaluation_summary.md
reports/evaluation/ckpt_03_shopee_absa_vietnamese/error_analysis.md
```

