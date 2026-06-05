import { ExternalLink } from 'lucide-react';

export default function PowerBIEmbed({ embedUrl }) {
  return (
    <section className="panel powerbi-panel">
      <div className="section-title">
        <div>
          <span className="eyebrow">Power BI mode</span>
          <h2>Power BI report</h2>
        </div>
        <a className="ghost-link" href={embedUrl} target="_blank" rel="noreferrer">
          <ExternalLink size={16} />
          Open
        </a>
      </div>
      <div className="iframe-wrap">
        <iframe
          title="Power BI report"
          src={embedUrl}
          allowFullScreen
          loading="lazy"
        />
      </div>
      <p className="muted">
        Nếu report không hiển thị, hãy kiểm tra quyền truy cập, allow-list domain và loại embed URL trong Power BI.
      </p>
    </section>
  );
}
