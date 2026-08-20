import { useState } from 'react';
import { sendFeedback, getApplyPreview, applyToday, ApiError } from '../api/client';
import StatusBadge from '../components/StatusBadge';

const FEEDBACK_OPTIONS = [
  { type: 'NO_TIME', label: 'Sem tempo' },
  { type: 'RAIN_INDOOR', label: 'Chuva / indoor' },
  { type: 'SICK', label: 'Doente' },
  { type: 'INJURED', label: 'Lesão' },
  { type: 'NO_BIKE_WEEK', label: 'No bike week' },
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

  if (loading) return <div className="center-msg">A carregar…</div>;

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

  return (
    <div>
      <div className="card lead">
        <StatusBadge status={report.status} />
        <div className="h1">{report.title || 'Sem título'}</div>
        {report.summary && <div className="sub">{report.summary}</div>}
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

      <div className="card">
        <div className="sub" style={{ marginBottom: 8 }}>READINESS</div>
        <div className="kv"><span className="k">Sono</span><span className="v">{fmtMin(Math.round((rd.sleep_hours || 0) * 60))}</span></div>
        <div className="kv"><span className="k">HRV</span><span className="v">{rd.hrv ?? 'n/d'}</span></div>
        <div className="kv"><span className="k">Resting HR</span><span className="v">{rd.resting_hr ?? 'n/d'} bpm</span></div>
        <div className="kv"><span className="k">Fitness / Fatigue</span><span className="v">{fmtNum(rd.fitness_ctl)} / {fmtNum(rd.fatigue_atl)}</span></div>
        <div className="kv"><span className="k">Form</span><span className="v">{fmtNum(rd.form)}</span></div>
      </div>

      <div className="card">
        <div className="sub" style={{ marginBottom: 8 }}>PESO</div>
        <div className="kv"><span className="k">Hoje</span><span className="v">{fmtNum(w.current_kg, 1)} kg</span></div>
        <div className="kv"><span className="k">Média 7d</span><span className="v">{fmtNum(w.avg_7d_kg, 1)} kg</span></div>
        <div className="kv"><span className="k">Objetivo</span><span className="v">{fmtNum(w.target_kg, 1)} kg</span></div>
      </div>

      <div className="card lead">
        <div className="sub" style={{ marginBottom: 8 }}>DECISÃO — {rec.action || 'n/d'}</div>
        <div className="sub" style={{ color: 'var(--text)', fontWeight: 600, marginBottom: 8 }}>{rec.headline}</div>
        {(rec.workout_modification || rec.details || '').split('\n').filter(Boolean).map((line, i) => (
          <div className="action-line" key={i} style={{ marginBottom: 6 }}>{line}</div>
        ))}
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
              <button className="primary-btn" onClick={handleConfirmApply}>Criar em Intervals.icu</button>
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

      {(rec.details || '').length > 0 && (
        <div className="card">
          <div className="sub" style={{ marginBottom: 8 }}>MOTIVOS + AÇÕES</div>
          {rec.details.split('\n').filter(Boolean).map((line, i) => (
            <div key={i} className="action-line" style={{ marginBottom: 6 }}>{line}</div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="sub" style={{ marginBottom: 4 }}>Não vai dar para seguir o plano?</div>
        <div className="feedback-row">
          {FEEDBACK_OPTIONS.map((f) => (
            <button
              key={f.type}
              className="feedback-btn"
              onClick={() => handleFeedback(f.type)}
              style={sentFeedback === f.type ? { borderColor: 'var(--lime)', color: 'var(--lime)' } : undefined}
            >
              {sentFeedback === f.type ? '✓ ' : ''}{f.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
