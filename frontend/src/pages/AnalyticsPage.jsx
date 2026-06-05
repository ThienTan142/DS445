import { useEffect, useState } from 'react';
import { AlertCircle, BarChart3, Loader2 } from 'lucide-react';
import { getConfig, getMetrics } from '../api.js';
import MetricsDashboard from '../components/MetricsDashboard.jsx';
import PowerBIEmbed from '../components/PowerBIEmbed.jsx';

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState(null);
  const [powerBiUrl, setPowerBiUrl] = useState(import.meta.env.VITE_POWER_BI_EMBED_URL || '');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError('');
      try {
        const [config, metricPayload] = await Promise.all([getConfig(), getMetrics()]);
        setPowerBiUrl(config.power_bi_embed_url || import.meta.env.VITE_POWER_BI_EMBED_URL || '');
        setMetrics(metricPayload);
      } catch (err) {
        setError(err.message || 'Không tải được dữ liệu dashboard.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="page-stack">
      <section className="page-header">
        <span className="eyebrow">Model monitoring</span>
        <h1>Analytics dashboard</h1>
        <p>Dashboard hiển thị metric đánh giá, phân phối nhãn, confidence, lịch sử request và fallback Power BI.</p>
      </section>

      {loading && (
        <section className="panel empty-state">
          <Loader2 className="spin" size={30} />
          <h2>Đang tải dashboard</h2>
          <p>Backend đang đọc dữ liệu từ report evaluation.</p>
        </section>
      )}

      {!loading && error && (
        <section className="panel error-box large">
          <AlertCircle size={20} />
          <span>{error}</span>
        </section>
      )}

      {!loading && !error && powerBiUrl && <PowerBIEmbed embedUrl={powerBiUrl} />}
      {!loading && !error && !powerBiUrl && metrics && <MetricsDashboard metrics={metrics} />}

      {!loading && !error && !powerBiUrl && !metrics && (
        <section className="panel empty-state">
          <BarChart3 size={30} />
          <h2>Chưa có dữ liệu metric</h2>
          <p>Backend sẽ trả dashboard mẫu nếu chưa có report thật.</p>
        </section>
      )}
    </div>
  );
}
