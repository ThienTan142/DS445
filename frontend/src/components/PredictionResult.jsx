import { CheckCircle2, Clock, Gauge } from 'lucide-react';

function labelClass(label) {
  const normalized = String(label || '').toLowerCase();
  if (normalized.includes('positive')) return 'positive';
  if (normalized.includes('negative')) return 'negative';
  return 'neutral';
}

export default function PredictionResult({ result }) {
  if (!result) {
    return (
      <section className="panel empty-state">
        <Gauge size={30} />
        <h2>Chưa có kết quả dự đoán</h2>
        <p>Nhập bình luận hoặc chọn ví dụ mẫu để chạy model.</p>
      </section>
    );
  }

  const probabilities = Object.entries(result.probabilities || {});

  return (
    <section className="panel result-panel">
      <div className="section-title">
        <div>
          <span className="eyebrow">Prediction result</span>
          <h2>Kết quả model</h2>
        </div>
        <span className={`label-badge ${labelClass(result.prediction)}`}>{result.prediction}</span>
      </div>

      <div className="result-grid">
        <div className="result-stat">
          <CheckCircle2 size={18} />
          <span>Confidence</span>
          <strong>{Math.round(result.confidence * 100)}%</strong>
        </div>
        <div className="result-stat">
          <Clock size={18} />
          <span>Processing time</span>
          <strong>{result.processing_time_ms} ms</strong>
        </div>
      </div>

      <div className="probability-list">
        {probabilities.map(([label, value]) => (
          <div className="probability-row" key={label}>
            <div>
              <span>{label}</span>
              <strong>{Math.round(value * 100)}%</strong>
            </div>
            <div className="bar-track">
              <span className={`bar-fill ${labelClass(label)}`} style={{ width: `${Math.round(value * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
