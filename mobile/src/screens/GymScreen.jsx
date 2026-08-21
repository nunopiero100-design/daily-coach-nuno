import { useState } from 'react';
import gymData from '../mock/gymPlan.json';
import { IconDumbbell, IconArrowRight } from '../components/Icons';

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DAY_LABELS_PT = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];

export default function GymScreen({ report }) {
  const todayIdx = new Date().getDay();
  const todayName = DAY_NAMES[todayIdx];
  const dayIndexForToday = gymData.gymmap[todayName];
  const hasSessionToday = dayIndexForToday !== undefined;

  const [selectedDay, setSelectedDay] = useState(
    hasSessionToday ? dayIndexForToday : 0
  );

  const day = gymData.strength.days[selectedDay];
  const status = report?.status;
  const isViewingToday = selectedDay === dayIndexForToday;

  return (
    <div>
      <div className="card lead">
        <div className="section-label" style={{ margin: '0 0 4px' }}><IconDumbbell size={13} />GYM</div>
        <div className="h1">{hasSessionToday ? 'Hoje tens ginásio' : DAY_LABELS_PT[todayIdx]}</div>
        {!hasSessionToday && <div className="sub">Sem sessão de ginásio programada hoje.</div>}
      </div>

      {isViewingToday && hasSessionToday && status === 'RED' && (
        <div className="card" style={{ borderLeft: '4px solid var(--red)' }}>
          <div className="sub" style={{ color: 'var(--red)', fontWeight: 700, marginBottom: 4 }}>DIA DE RECUPERAÇÃO NA BIKE</div>
          <div className="sub">O treino de hoje na bike está em recovery - considera aliviar bastante o ginásio também (menos carga, sem chegar ao falhanço) ou saltar esta sessão.</div>
        </div>
      )}
      {isViewingToday && hasSessionToday && status === 'YELLOW' && (
        <div className="card" style={{ borderLeft: '4px solid var(--yellow)' }}>
          <div className="sub" style={{ color: 'var(--yellow)', fontWeight: 700, marginBottom: 4 }}>TREINO DE BIKE REDUZIDO HOJE</div>
          <div className="sub">Mantém o ginásio moderado - carga normal está bem, mas evita forçar até ao limite hoje.</div>
        </div>
      )}

      <div className="feedback-row" style={{ gridTemplateColumns: `repeat(${gymData.strength.days.length}, 1fr)`, marginBottom: 14 }}>
        {gymData.strength.days.map((d, i) => (
          <button
            key={i}
            className="feedback-btn"
            onClick={() => setSelectedDay(i)}
            style={i === selectedDay ? { borderColor: 'var(--lime)', color: 'var(--lime)' } : undefined}
          >
            {d.title.split(' - ')[1] || d.title.split(' ')[0]}
          </button>
        ))}
      </div>

      <div className="card">
        <div className="sub" style={{ marginBottom: 10 }}>{day.title.toUpperCase()}</div>
        {day.ex.map((e, i) => (
          <div key={i} style={{ marginBottom: 14, paddingBottom: 12, borderBottom: i < day.ex.length - 1 ? '1px solid var(--card-border)' : 'none' }}>
            <div style={{ fontWeight: 700, fontSize: 15 }}>{e.n}</div>
            <div className="sub" style={{ margin: '4px 0 2px' }}>{e.sr} · {e.load}</div>
            {e.note && <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>{e.note}</div>}
          </div>
        ))}
      </div>

      <div className="card">
        <div className="sub" style={{ marginBottom: 8 }}>PROGRESSÃO</div>
        <div style={{ fontSize: 13, lineHeight: 1.5 }}>{gymData.strength.progression}</div>
      </div>

      <div className="card">
        <div className="sub" style={{ marginBottom: 8 }}>EVITAR (JOELHO)</div>
        {gymData.strength.avoid.map((a, i) => (
          <div key={i} className="action-line" style={{ marginBottom: 6 }}>
            <IconArrowRight size={14} />
            <span>{a}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
