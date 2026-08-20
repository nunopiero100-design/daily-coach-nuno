import { useEffect, useState } from 'react';
import { listReports, ApiError } from '../api/client';
import StatusBadge from '../components/StatusBadge';

const STATUS_COLOR = { GREEN: '#4fd67a', YELLOW: '#f0c14b', RED: '#f0574b', INCOMPLETE: '#8b96a3' };

function fmtDate(iso) {
  const [, m, d] = iso.split('-');
  return `${d}/${m}`;
}

function FormSparkline({ reports }) {
  const points = reports
    .filter((r) => r.readiness?.form != null)
    .slice()
    .reverse(); // oldest -> newest, left to right
  if (points.length < 2) return null;

  const values = points.map((r) => r.readiness.form);
  const min = Math.min(...values, -10);
  const max = Math.max(...values, 10);
  const w = 280;
  const h = 70;
  const pad = 8;

  const x = (i) => pad + (i * (w - pad * 2)) / (points.length - 1);
  const y = (v) => h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2);
  const zeroY = y(0);

  const path = points.map((r, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(r.readiness.form).toFixed(1)}`).join(' ');

  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" height={h} style={{ display: 'block' }}>
      <line x1={pad} y1={zeroY} x2={w - pad} y2={zeroY} stroke="var(--card-border)" strokeWidth="1" strokeDasharray="3,3" />
      <path d={path} fill="none" stroke="var(--lime)" strokeWidth="2" />
      {points.map((r, i) => (
        <circle key={i} cx={x(i)} cy={y(r.readiness.form)} r="3" fill={STATUS_COLOR[r.status] || 'var(--lime)'} />
      ))}
    </svg>
  );
}

export default function HistoryScreen() {
  const [reports, setReports] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await listReports(14);
        setReports(data.reports || []);
      } catch (e) {
        setError(e instanceof ApiError ? e.message : 'Erro a carregar o histórico.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="center-msg">A carregar…</div>;
  if (error) return <div className="center-msg">{error}</div>;
  if (!reports || reports.length === 0) return <div className="center-msg">Sem histórico ainda.</div>;

  return (
    <div>
      <div className="card lead">
        <div className="sub">HISTÓRICO</div>
        <div className="h1">Últimos {reports.length} dias</div>
        <div className="sub" style={{ marginBottom: 8 }}>Form ao longo do tempo</div>
        <FormSparkline reports={reports} />
      </div>

      {reports.map((r) => (
        <div className="card" key={r.date}>
          <div className="kv" style={{ borderBottom: 'none', paddingBottom: 0 }}>
            <span className="k">{fmtDate(r.date)}</span>
            <StatusBadge status={r.status} />
          </div>
          <div style={{ fontSize: 13, marginTop: 6, color: 'var(--text-dim)' }}>{r.title}</div>
          {r.readiness?.form != null && (
            <div style={{ fontSize: 12, marginTop: 4, color: 'var(--text-dim)' }}>Form: {r.readiness.form.toFixed(0)}</div>
          )}
        </div>
      ))}
    </div>
  );
}
