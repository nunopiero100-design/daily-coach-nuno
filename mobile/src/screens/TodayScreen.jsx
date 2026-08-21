import { useState } from 'react';
import { sendFeedback, getApplyPreview, applyToday, ApiError } from '../api/client';
import StatusRing from '../components/StatusRing';
import StatTile from '../components/StatTile';
import { statusColor, hexToRgba } from '../statusColors';
import {
  IconMoon, IconHeart, IconActivity, IconTrendingUp, IconScale,
  IconArrowRight, IconUtensils, IconClock, IconCloudRain, IconVirus,
  IconBandage, IconBike,
} from '../components/Icons';

const FEEDBACK_OPTIONS = [
  { type: 'NO_TIME', label: 'Sem tempo', icon: <IconClock /> },
  { type: 'RAIN_INDOOR', label: 'Chuva / indoor', icon: <IconCloudRain /> },
  { type: 'SICK', label: 'Doente', icon: <IconVirus /> },
  { type: 'INJURED', label: 'Lesão', icon: <IconBandage /> },
  { type: 'NO_BIKE_WEEK', label: 'No bike week', icon: <IconBike /> },
];

// The backend only allows applying a replacement on YELLOW/RED days.
const APPLICABLE_STATUSES = ['YELLOW', 'RED'];

function fmtMin(m) {
  if (m == null) return 'n/d';
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return h > 0 ? `${h}h${mm ? mm + 'm' : ''}` : `${mm}m`;
}

function fmtNum(v, digits = 0) {
  if (v == null || Number.isNaN(v)) return 'n/d';
  return Number(v).toFixed(digits);
}

// The coach always outputs a normal plan + conditional fallbacks (60min/45min/
// indoor) + fueling, every day - even when the alternates aren't relevant.
// Group them so the normal plan reads prominently and the "se..." alternates
// are tucked away instead of forcing a wall of text every morning.
function groupActions(raw) {
  const lines = (raw || '')
    .split('\n')
    .map((l) => l.replace(/^-\s*/, '').trim())
    .filter(Boolean);
  const primary = [];
  const alternatives = [];
  const fueling = [];
  for (const line of lines) {
    const lower = line.toLowerCase();
    if (lower.startsWith('se ')) alternatives.push(line);
    else if (lower.startsWith('recupera') || lower.startsWith('fueling')) fueling.push(line);
    else primary.push(line);
  }
  return { primary, alternatives, fueling };
}

function LoadingSkeleton() {
  return (
    <div>
      <div className="skeleton" style={{ height: 96, marginBottom: 14 }} />
      <div className="stat-grid">
        {Array.from({ length: 4 }).map((_, i) => (
          <div className="skeleton" key={i} style={{ height: 60 }} />
        ))}
      </div>
      <div className="skeleton" style={{ height: 160, marginTop: 14 }} />
    </div>
  );
}

export default function TodayScreen({ report, loading, error, reload }) {
  const [sentFeedback, setSentFeedback] = useState(null);

  // Apply-flow state: idle -> previewing -> confirming -> applied/failed
  const [applyState, setApplyState] = useState('idle');
  const [preview, setPreview] = useState(null);
  const [applyError, setApplyError] = useState(null);

  async function handleFeedback(type) {
    setSentFeedback(type);
    try {
      await sendFeedback(type);
    } catch (e) {
      console.warn('Feedback failed', e);
    }
  }

  async function handleStartApply() {
    setApplyError(null);
    setApplyState('previewing');
    try {
      const p = await getApplyPreview();
      setPreview(p);
      setApplyState('confirming');
    } catch (e) {
      setApplyError(e instanceof ApiError ? e.message : 'Não foi possível gerar a substituição.');
      setApplyState('idle');
    }
  }

  async function handleConfirmApply() {
    setApplyState('applying');
    try {
      await applyToday();
      setApplyState('applied');
    } catch (e) {
      setApplyError(e instanceof ApiError ? e.message : 'Falha ao aplicar em Intervals.icu.');
      setApplyState('idle');
    }
  }

  if (loading) return <LoadingSkeleton />;

  if (error) {
    return (
      <div className="center-msg">
        {error}
        <div style={{ marginTop: 14 }}>
          <button className="icon-btn" onClick={reload}>Tentar novamente</button>
        </div>
      </div>
    );
  }

  if (!report) return <div className="center-msg">Sem relatório para hoje.</div>;

  const pw = report.planned_workout;
  const rd = report.readiness || {};
  const w = report.weight || {};
  const rec = report.recommendation || {};
  const canApply = APPLICABLE_STATUSES.includes(report.status) && pw?.name;
  const grouped = groupActions(rec.workout_modification || rec.details);
  const actionLineSet = new Set(
    [...grouped.primary, ...grouped.alternatives, ...grouped.fueling]
  );
  const reasonsOnly = (rec.details || '')
    .split('\n')
    .map((l) => l.replace(/^-\s*/, '').trim())
    .filter((l) => l && !actionLineSet.has(l));

  const color = statusColor(report.status);

  return (
    <div>
      <div className="hero">
        <StatusRing status={report.status} sublabel={rd.form != null ? `form ${fmtNum(rd.form)}` : null} />
        <div className="hero-text">
          <div className="hero-eyebrow">Hoje</div>
          <div className="hero-title">{report.title || 'Sem título'}</div>
          {report.summary && <div className="hero-sub">{report.summary}</div>}
        </div>
      </div>

      {pw?.name ? (
        <div className="card">
          <div className="sub" style={{ marginBottom: 8 }}>TREINO PLANEADO HOJE</div>
          <div className="kv"><span className="k">Sessão</span><span className="v">{pw.name}</span></div>
          <div className="kv"><span className="k">TSS planeado</span><span className="v">{pw.planned_tss ?? 'n/d'}</span></div>
          <div className="kv"><span className="k">Duração</span><span className="v">{fmtMin(pw.duration_minutes)}</span></div>
        </div>
      ) : (
        <div className="card"><div className="sub">Sem treino planeado hoje.</div></div>
      )}

      <div className="section-label">Readiness &amp; peso</div>
      <div className="stat-grid">
        <StatTile icon={<IconMoon />} label="Sono" value={fmtMin(Math.round((rd.sleep_hours || 0) * 60))} />
        <StatTile icon={<IconHeart />} label="HRV" value={rd.hrv ?? 'n/d'} />
        <StatTile icon={<IconActivity />} label="Resting HR" value={rd.resting_hr ?? 'n/d'} unit={rd.resting_hr != null ? 'bpm' : null} />
        <StatTile icon={<IconTrendingUp />} label="Fitness / Fatigue" value={`${fmtNum(rd.fitness_ctl)}/${fmtNum(rd.fatigue_atl)}`} />
        <StatTile icon={<IconScale />} label="Peso hoje" value={fmtNum(w.current_kg, 1)} unit="kg" />
        <StatTile icon={<IconScale />} label="Objetivo" value={fmtNum(w.target_kg, 1)} unit="kg" />
      </div>

      <div className="decision-card" style={{ borderLeftColor: color, background: `linear-gradient(160deg, ${hexToRgba(color, 0.12)}, transparent 60%), var(--card)` }}>
        <div className="decision-tag" style={{ color }}>Decisão — {rec.action || 'n/d'}</div>
        <div className="decision-headline">{rec.headline}</div>

        {grouped.primary.map((line, i) => (
          <div className="action-line" key={`p${i}`}>
            <IconArrowRight size={15} style={{ color }} />
            <span>{line}</span>
          </div>
        ))}

        {grouped.fueling.map((line, i) => (
          <div className="action-line dim fueling" key={`f${i}`}>
            <IconUtensils size={14} />
            <span>{line}</span>
          </div>
        ))}

        {grouped.alternatives.length > 0 && (
          <details style={{ marginTop: 10 }}>
            <summary style={{ cursor: 'pointer', color: 'var(--text-dim)', fontSize: 13 }}>
              Alternativas (menos tempo / indoor) <span className="chev">›</span>
            </summary>
            <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {grouped.alternatives.map((line, i) => (
                <div className="action-line dim" key={`a${i}`} style={{ fontSize: 13 }}>
                  <IconArrowRight size={13} />
                  <span>{line}</span>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>

      {canApply && (
        <div className="card">
          <div className="sub" style={{ marginBottom: 10 }}>CRIAR ALTERNATIVA EM INTERVALS.ICU</div>

          {applyState === 'idle' && (
            <>
              {applyError && <div className="sub" style={{ color: 'var(--red)', marginBottom: 8 }}>{applyError}</div>}
              <button className="primary-btn" onClick={handleStartApply}>Ver alternativa</button>
            </>
          )}

          {applyState === 'previewing' && <div className="sub">A calcular substituição…</div>}

          {applyState === 'confirming' && preview && (
            <>
              <div className="kv"><span className="k">Original (fica)</span><span className="v" style={{ textAlign: 'right' }}>{preview.original_name}</span></div>
              <div className="kv"><span className="k">Nova alternativa</span><span className="v" style={{ textAlign: 'right' }}>{preview.new_name}</span></div>
              <div className="kv"><span className="k">Carga da alternativa</span><span className="v">{preview.new_load} TSS</span></div>
              <div className="sub" style={{ marginTop: 8 }}>Vais ficar com os dois treinos hoje - apaga o que não quiseres diretamente no Intervals.icu.</div>
              <div style={{ height: 10 }} />
              <button className="primary-btn" onClick={handleConfirmApply}>
                <IconArrowRight size={15} />
                Criar em Intervals.icu
              </button>
              <div style={{ height: 8 }} />
              <button className="icon-btn" style={{ width: '100%' }} onClick={() => setApplyState('idle')}>Cancelar</button>
            </>
          )}

          {applyState === 'applying' && <div className="sub">A aplicar em Intervals.icu…</div>}

          {applyState === 'applied' && (
            <div className="sub" style={{ color: 'var(--green)' }}>
              ✓ Treino alternativo criado em Intervals.icu.
            </div>
          )}
        </div>
      )}

      {reasonsOnly.length > 0 && (
        <div className="card">
          <div className="sub" style={{ marginBottom: 8 }}>MOTIVOS</div>
          {reasonsOnly.map((line, i) => (
            <div key={i} className="action-line" style={{ marginBottom: 6 }}>
              <IconArrowRight size={14} />
              <span>{line}</span>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="sub" style={{ marginBottom: 8 }}>Não vai dar para seguir o plano?</div>
        <div className="feedback-row">
          {FEEDBACK_OPTIONS.map((f) => (
            <button
              key={f.type}
              className={`feedback-chip ${sentFeedback === f.type ? 'active' : ''}`}
              onClick={() => handleFeedback(f.type)}
            >
              {f.icon}
              <span>{sentFeedback === f.type ? '✓ ' : ''}{f.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
