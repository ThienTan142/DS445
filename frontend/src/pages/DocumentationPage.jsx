import { API_BASE_URL } from '../api.js';

export default function DocumentationPage() {
  return (
    <div className="page-stack docs-page">
      <section className="page-header">
        <span className="eyebrow">Developer notes</span>
        <h1>Documentation</h1>
        <p>Hướng dẫn chạy local, gọi API, thay mock model bằng PhoBERT thật và cấu hình Power BI.</p>
      </section>

      <DocSection title="Run backend">
        <Code>{`cd F:\\DS445
.\\.venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt
.\\.venv\\Scripts\\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000`}</Code>
      </DocSection>

      <DocSection title="Run frontend">
        <Code>{`cd F:\\DS445\\frontend
npm install
npm run dev`}</Code>
      </DocSection>

      <DocSection title="API endpoints">
        <ul className="doc-list">
          <li><strong>GET</strong> {API_BASE_URL}/health</li>
          <li><strong>POST</strong> {API_BASE_URL}/predict</li>
          <li><strong>GET</strong> {API_BASE_URL}/metrics</li>
          <li><strong>GET</strong> {API_BASE_URL}/config</li>
        </ul>
        <Code>{`POST /predict
{
  "text": "Shop giao nhanh, sản phẩm đẹp nhưng size hơi chật"
}`}</Code>
      </DocSection>

      <DocSection title="Replace mock model with real PhoBERT">
        <p>
          Backend đang mặc định dùng mock model để demo nhanh. Để dùng model thật, chỉnh `.env`:
        </p>
        <Code>{`MODEL_MODE=real
MODEL_PATH=models/ckpt_03_shopee_absa_vietnamese`}</Code>
        <p>
          Code cần thay thế nằm trong `backend/app/model_service.py`, class `PhoBertSentimentModel`.
        </p>
      </DocSection>

      <DocSection title="Power BI embed">
        <p>
          Nếu có embed URL, thêm vào `.env` backend:
        </p>
        <Code>{`POWER_BI_EMBED_URL=https://app.powerbi.com/reportEmbed?...`}</Code>
        <p>
          Khi URL tồn tại, trang Analytics tự hiển thị iframe Power BI. Nếu không có URL, dashboard nội bộ bằng Recharts sẽ được dùng.
        </p>
      </DocSection>

      <DocSection title="Project structure">
        <Code>{`backend/
  app/
frontend/
  src/components/
  src/pages/
evaluation/
reports/evaluation/
models/
data/`}</Code>
      </DocSection>
    </div>
  );
}

function DocSection({ title, children }) {
  return (
    <section className="panel doc-section">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function Code({ children }) {
  return <pre><code>{children}</code></pre>;
}
