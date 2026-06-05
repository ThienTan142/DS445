import { useEffect, useState } from 'react';
import { Activity, BarChart3, BookOpen, FileText, FlaskConical } from 'lucide-react';
import DemoPage from './pages/DemoPage.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';
import AboutModelPage from './pages/AboutModelPage.jsx';
import ExamplesPage from './pages/ExamplesPage.jsx';
import DocumentationPage from './pages/DocumentationPage.jsx';
import { getHealth } from './api.js';

const navItems = [
  { key: 'demo', label: 'Demo', icon: FlaskConical },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
  { key: 'about', label: 'About Model', icon: Activity },
  { key: 'examples', label: 'Examples', icon: BookOpen },
  { key: 'docs', label: 'Documentation', icon: FileText }
];

export default function App() {
  const [activePage, setActivePage] = useState('demo');
  const [prefillText, setPrefillText] = useState('');
  const [health, setHealth] = useState({ status: 'checking', model_mode: 'mock' });

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: 'offline', model_mode: 'unknown' }));
  }, []);

  function runExample(text) {
    setPrefillText(text);
    setActivePage('demo');
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">AI</div>
          <div>
            <strong>DS445 Demo</strong>
            <span>PhoBERT sentiment</span>
          </div>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={`nav-item ${activePage === item.key ? 'active' : ''}`}
                onClick={() => setActivePage(item.key)}
                title={item.label}
                type="button"
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className={`status-pill ${health.status === 'ok' ? 'online' : 'offline'}`}>
          <span className="status-dot" />
          <div>
            <strong>{health.status === 'ok' ? 'API online' : 'API offline'}</strong>
            <span>{health.model_mode || 'unknown'} mode</span>
          </div>
        </div>
      </aside>

      <main className="content">
        {activePage === 'demo' && <DemoPage prefillText={prefillText} />}
        {activePage === 'analytics' && <AnalyticsPage />}
        {activePage === 'about' && <AboutModelPage />}
        {activePage === 'examples' && <ExamplesPage onRunExample={runExample} />}
        {activePage === 'docs' && <DocumentationPage />}
      </main>
    </div>
  );
}
