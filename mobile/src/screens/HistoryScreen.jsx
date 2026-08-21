import { useEffect, useState } from 'react';
import { listReports, ApiError } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import TrendChart from '../components/TrendChart';
import WeeklyBarChart from '../components/WeeklyBarChart';
import { IconClock, IconTrendingUp, IconActivity, IconScale } from '../components/Icons';
import { STATUS_COLORS } from '../statusColors';

// Charts read a wider window than the itemized list below them, so trends
// (a form dip building over a week, a heavy training block) are actually
// visible - the backend supports up to 365, 42 days (~6 weeks) is enough to
// see a block without the request getting heavy.
const CHART_WINDOW_DAYS = 42;
const LIST_DAYS = 14;

function fmtDate(iso) {
  const [, m, d] = iso.split('-');
  return `${d}/${m}`;
}

function mondayOf(iso) {
  const d = new Date(`${iso}T00:00:00`);
  const day = d.getDay(); // 0 = Sunday
  const diffToMonday = (day === 0 ? -6 : 1) - day;
  d.setDate(d.getDate() + diffToMonday);
  return d.toISOString().slice(0, 10);
}

function buildWeeklyTss(oldestFirst) {
  const byWeek = new Map();
  for (const r of oldestFirst) {
    const key = mondayOf(r.date);
    const tss = r.completed_activity?.exists ? (r.completed_activity.tss || 0) : 0;
    byWeek.set(key, (byWeek.get(key) || 0) + tss);
  }
  return [...byWeek.entries()]
    .sort(([a], [b]) => (a < b ? -1 : 1))
    .map(([monday, tss]) => ({ label: fmtDate(monday), tss }));
}

function FormSparkline({ reports }) {
  const points = reports.filter((r) => r.readiness?.form != null);
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
        <circle key={i} cx={x(i)} cy={y(r.readiness.form)} r="3" fill={STATUS_COLORS[r.status] || 'var(--lime)'} />
      ))}
    </svg>
  );
}

function LoadingSkeleton() {
  return (
    <div>
      {Array.from({ length: 4 }).map((_, i) => (
        <div className="skeleton" key={i} style={{ height: 120, marginBottom: 14 }} />
      ))}
    </div>
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
        const data = await listReports(CHART_WINDOW_DAYS);
        setReports(data.reports || []);
      } catch (e) {
        setError(e instanceof ApiError ? e.message : 'Erro a carregar o histórico.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <LoadingSkeleton />;
  if (error) return <div className="center-msg">{error}</div>;
  if (!reports || reports.length === 0) return <div className="center-msg">Sem histórico ainda.</div>;

  // API returns newest-first; charts read left-to-right oldest-to-newest.
  const oldestFirst = reports.slice().reverse();
  const latestWeight = reports.find((r) => r.weight?.current_kg != null)?.weight;
  const weeklyTss = buildWeeklyTss(oldestFirst);

  return (
    <div>
      <div className="card lead">
        <div className="section-label" style={{ margin: '0 0 4px' }}><IconClock size={13} />HISTÓRICO</div>
        <div className="h1">Últimos {reports.length} dias</div>
      </div>

      <div className="card">
        <div className="section-label"><IconTrendingUp size={13} />FITNESS & FADIGA (CTL/ATL)</div>
        <TrendChart
          series={[
            { label: 'Fitness (CTL)', color: 'var(--lime)', values: oldestFirst.map((r) => r.readiness?.fitness_ctl ?? null) },
            { label: 'Fadiga (ATL)', color: 'var(--accent2)', values: oldestFirst.map((r) => r.readiness?.fatigue_atl ?? null) },
          ]}
        />
      </div>

      <div className="card">
        <div className="section-label" style={{ margin: '0 0 8px' }}>FORMA (TSB)</div>
        <FormSparkline reports={oldestFirst} />
      </div>

      <div className="card">
        <div className="section-label"><IconActivity size={13} />CARGA SEMANAL (TSS COMPLETO)</div>
        {weeklyTss.length >= 2
          ? <WeeklyBarChart weeks={weeklyTss} />
          : <div className="sub">Ainda não há semanas suficientes para o gráfico.</div>}
      </div>

      {latestWeight && (
        <div className="card">
          <div className="section-label"><IconScale size={13} />PESO (MÉDIA 7D)</div>
          <TrendChart
            series={[{ label: 'Média 7d', color: 'var(--lime)', values: oldestFirst.map((r) => r.weight?.avg_7d_kg ?? null) }]}
            refLine={latestWeight.target_kg != null ? { value: latestWeight.target_kg, color: 'var(--accent2)', label: 'Objetivo' } : undefined}
          />
        </div>
      )}

      <div className="section-label" style={{ marginTop: 6 }}>ÚLTIMOS {LIST_DAYS} DIAS</div>
      {reports.slice(0, LIST_DAYS).map((r) => (
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
