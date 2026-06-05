import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Loader2, RotateCcw, Send, Trash2 } from 'lucide-react';
import { predictSentiment } from '../api.js';
import ExampleList from '../components/ExampleList.jsx';
import PredictionResult from '../components/PredictionResult.jsx';

const MIN_LENGTH = 3;

export default function DemoPage({ prefillText }) {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (prefillText) {
      setText(prefillText);
      setError('');
    }
  }, [prefillText]);

  const isValid = useMemo(() => text.trim().length >= MIN_LENGTH, [text]);

  async function submitPrediction() {
    const cleanText = text.trim();
    if (cleanText.length < MIN_LENGTH) {
      setError('Vui lòng nhập bình luận có ít nhất 3 ký tự.');
      setResult(null);
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await predictSentiment(cleanText);
      setResult(response);
      setHistory((items) => [
        {
          id: crypto.randomUUID(),
          text: cleanText,
          ...response,
          createdAt: new Date().toLocaleTimeString('vi-VN')
        },
        ...items
      ].slice(0, 6));
    } catch (err) {
      setError(err.message || 'Server lỗi, vui lòng thử lại.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function resetInput() {
    setText('');
    setResult(null);
    setError('');
  }

  function useExample(example) {
    setText(example.text);
    setError('');
  }

  return (
    <div className="page-grid demo-layout">
      <section className="panel demo-panel">
        <div className="section-title">
          <div>
            <span className="eyebrow">Live model demo</span>
            <h1>Phân tích cảm xúc bình luận Shopee</h1>
          </div>
          <span className="model-chip">PhoBERT / mock-ready API</span>
        </div>

        <label className="input-label" htmlFor="review-input">Bình luận cần phân tích</label>
        <textarea
          id="review-input"
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Ví dụ: Shop giao nhanh, sản phẩm đẹp nhưng size hơi chật."
          rows={7}
        />
        <div className="input-footer">
          <span className={isValid ? 'valid-text' : 'invalid-text'}>
            {text.trim().length} ký tự
          </span>
          <div className="button-row">
            <button className="ghost-button" onClick={resetInput} type="button" title="Xóa input">
              <RotateCcw size={17} />
              Reset
            </button>
            <button className="primary-button" onClick={submitPrediction} disabled={loading} type="button" title="Chạy dự đoán">
              {loading ? <Loader2 className="spin" size={17} /> : <Send size={17} />}
              {loading ? 'Đang chạy' : 'Predict'}
            </button>
          </div>
        </div>

        {error && (
          <div className="error-box">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <div className="quick-examples">
          <div className="mini-title">Ví dụ chạy nhanh</div>
          <ExampleList compact onSelect={useExample} />
        </div>
      </section>

      <div className="side-stack">
        <PredictionResult result={result} />

        <section className="panel history-panel">
          <div className="section-title compact-title">
            <div>
              <span className="eyebrow">Recent predictions</span>
              <h2>Lịch sử gần nhất</h2>
            </div>
            <button className="icon-button" onClick={() => setHistory([])} type="button" title="Xóa lịch sử">
              <Trash2 size={16} />
            </button>
          </div>

          {history.length === 0 ? (
            <p className="muted">Lịch sử dự đoán sẽ xuất hiện sau khi chạy model.</p>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <article className="history-item" key={item.id}>
                  <div>
                    <strong>{item.prediction}</strong>
                    <span>{Math.round(item.confidence * 100)}% · {item.processing_time_ms} ms · {item.createdAt}</span>
                  </div>
                  <p>{item.text}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
