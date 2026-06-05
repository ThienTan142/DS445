import { Fragment } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

const palette = ['#0f766e', '#d97706', '#be123c', '#2563eb', '#7c3aed'];

function formatPercent(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

export default function MetricsDashboard({ metrics }) {
  const cards = metrics?.cards || {};
  const matrix = metrics?.confusion_matrix || { labels: [], values: [] };
  const errorAnalysis = metrics?.error_analysis || {};
  const errorSummary = errorAnalysis.summary || {};
  const shortDate = (value) => String(value || '').slice(5);

  return (
    <div className="dashboard-stack">
      <div className="metric-grid">
        <MetricCard label="Accuracy" value={formatPercent(cards.accuracy)} />
        <MetricCard label="Precision" value={formatPercent(cards.precision)} />
        <MetricCard label="Recall" value={formatPercent(cards.recall)} />
        <MetricCard label="F1-score" value={formatPercent(cards.f1_score)} />
        <MetricCard label="Avg latency" value={`${cards.avg_processing_time_ms || 0} ms`} />
        <MetricCard label="Invalid input" value={formatPercent(cards.invalid_input_rate)} />
      </div>

      <div className="chart-grid">
        <section className="panel chart-panel">
          <h2>Confusion matrix</h2>
          <div className="matrix-scroll">
            <div className="matrix" style={{ '--size': matrix.labels.length || 3 }}>
              <span className="matrix-corner">Actual / Pred</span>
              {matrix.labels.map((label) => <strong className="matrix-header" key={label}>{label}</strong>)}
              {matrix.values.map((row, rowIndex) => (
                <Fragment key={matrix.labels[rowIndex] || rowIndex}>
                  <b className="matrix-row-label">{matrix.labels[rowIndex]}</b>
                  {row.map((value, colIndex) => (
                    <div className={`matrix-cell ${rowIndex === colIndex ? 'diagonal' : ''}`} key={`${rowIndex}-${colIndex}`}>
                      <span>{value}</span>
                    </div>
                  ))}
                </Fragment>
              ))}
            </div>
          </div>
        </section>

        <section className="panel chart-panel">
          <h2>Số lượng mẫu theo nhãn</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={metrics.label_distribution} dataKey="count" nameKey="label" outerRadius={88} label>
                {(metrics.label_distribution || []).map((entry, index) => (
                  <Cell key={entry.label} fill={palette[index % palette.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </section>

        <section className="panel chart-panel">
          <h2>Phân bố confidence score</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={metrics.confidence_distribution} margin={{ top: 12, right: 16, bottom: 28, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" angle={-20} textAnchor="end" interval={0} tick={{ fontSize: 12 }} height={54} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#0f766e" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="panel chart-panel">
          <h2>Lượt dự đoán theo ngày</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={metrics.prediction_history} margin={{ top: 12, right: 18, bottom: 12, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={shortDate} tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line dataKey="count" stroke="#be123c" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </section>

        <section className="panel chart-panel wide">
          <h2>Precision, Recall, F1 theo lớp</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={metrics.class_performance} margin={{ top: 12, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis tickFormatter={formatPercent} />
              <Tooltip formatter={(value) => formatPercent(value)} />
              <Legend />
              <Bar dataKey="precision" fill="#2563eb" radius={[6, 6, 0, 0]} />
              <Bar dataKey="recall" fill="#d97706" radius={[6, 6, 0, 0]} />
              <Bar dataKey="f1" fill="#0f766e" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="panel chart-panel wide error-analysis-panel">
          <div className="section-title compact-title">
            <div>
              <span className="eyebrow">Error analysis</span>
              <h2>Bảng phân tích lỗi dự đoán</h2>
            </div>
            <span className="label-badge negative">{formatPercent(errorSummary.error_rate)} error rate</span>
          </div>

          <div className="error-summary-row">
            <SummaryItem label="Total samples" value={errorSummary.total_samples || 0} />
            <SummaryItem label="Correct" value={errorSummary.correct_samples || 0} />
            <SummaryItem label="Errors" value={errorSummary.error_samples || 0} />
            <SummaryItem label="Error rate" value={formatPercent(errorSummary.error_rate)} />
          </div>

          <div className="error-tables-grid">
            <div className="table-block">
              <h3>Cặp nhãn hay bị nhầm</h3>
              <div className="table-wrap">
                <table className="compact-table">
                  <thead>
                    <tr>
                      <th>Actual</th>
                      <th>Predicted</th>
                      <th>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(errorAnalysis.confusion_pairs || []).map((row) => (
                      <tr key={`${row.actual}-${row.predicted}`}>
                        <td>{row.actual}</td>
                        <td>{row.predicted}</td>
                        <td>{row.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="table-block">
              <h3>Lỗi theo aspect</h3>
              <div className="table-wrap">
                <table className="compact-table">
                  <thead>
                    <tr>
                      <th>Aspect</th>
                      <th>Error count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(errorAnalysis.aspect_errors || []).map((row) => (
                      <tr key={row.aspect}>
                        <td>{row.aspect}</td>
                        <td>{row.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="table-block">
            <h3>Lỗi confidence cao</h3>
            <div className="table-wrap">
              <table className="error-table">
                <thead>
                  <tr>
                    <th>Review</th>
                    <th>Actual</th>
                    <th>Predicted</th>
                    <th>Confidence</th>
                    <th>Aspect</th>
                  </tr>
                </thead>
                <tbody>
                  {(errorAnalysis.high_confidence_errors || []).map((row, index) => (
                    <tr key={`${row.review_text}-${index}`}>
                      <td className="review-cell">{row.review_text}</td>
                      <td>{row.actual}</td>
                      <td>{row.predicted}</td>
                      <td>{formatPercent(row.confidence)}</td>
                      <td>{row.aspect}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function SummaryItem({ label, value }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <section className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </section>
  );
}
