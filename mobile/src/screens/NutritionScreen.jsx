import { useState } from 'react';
import nutritionData from '../mock/nutritionPlan.json';
import { fuelingTarget, dayTypeForReport } from '../fueling';
import { IconUtensils, IconClock } from '../components/Icons';

function fmtMin(m) {
  if (m == null) return 'n/d';
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return h > 0 ? `${h}h${mm ? mm + 'm' : ''}` : `${mm}m`;
}

function DayTypeCard({ dayType, highlighted }) {
  const hasContent = dayType.meals && dayType.meals.length > 0;
  return (
    <div className={highlighted ? 'card lead' : 'card'}>
      <div className="sub" style={{ marginBottom: 4, fontWeight: highlighted ? 700 : 400, color: highlighted ? 'var(--text)' : undefined }}>
        {dayType.label.toUpperCase()}
      </div>
      <div className="sub" style={{ marginBottom: hasContent ? 10 : 0 }}>{dayType.description}</div>

      {hasContent ? (
        dayType.meals.map((m, i) => (
          <div key={i} className="action-line" style={{ marginBottom: 6 }}>
            <IconUtensils size={14} />
            <span>{m}</span>
          </div>
        ))
      ) : (
        <div
          className="sub"
          style={{ marginTop: 8, padding: 10, border: '1px dashed var(--card-border)', borderRadius: 10, fontSize: 12.5 }}
        >
          Ainda sem plano de refeições para este tipo de dia — falta portar isto do RidePlan.
        </div>
      )}
    </div>
  );
}

export default function NutritionScreen({ report }) {
  const [showAll, setShowAll] = useState(false);
  const pw = report?.planned_workout;
  const target = fuelingTarget(pw);
  const todayKey = report ? dayTypeForReport(report) : null;
  const todayType = nutritionData.dayTypes.find((d) => d.key === todayKey);
  const otherTypes = nutritionData.dayTypes.filter((d) => d.key !== todayKey);

  return (
    <div>
      <div className="section-label" style={{ margin: '4px 2px 10px' }}>
        <IconUtensils size={13} />FUELING DE HOJE
      </div>

      <div className="card">
        {!pw?.name && (
          <div className="sub">Sem treino planeado hoje — sem necessidade de fueling específico na bike.</div>
        )}
        {pw?.name && !target && (
          <div className="sub">Duração do treino não disponível para calcular um alvo de carboidratos.</div>
        )}
        {pw?.name && target && (
          <>
            <div className="kv"><span className="k">Sessão</span><span className="v">{pw.name}</span></div>
            <div className="kv"><span className="k">Duração</span><span className="v">{fmtMin(pw.duration_minutes)}</span></div>
            <div className="kv">
              <span className="k">Carbs/hora</span>
              <span className="v mono">{target.perHourLow}–{target.perHourHigh}g</span>
            </div>
            <div className="kv" style={{ borderBottom: 'none' }}>
              <span className="k">Total estimado</span>
              <span className="v mono">{target.totalLow}–{target.totalHigh}g</span>
            </div>
            {target.note && <div className="sub" style={{ marginTop: 8 }}>{target.note}</div>}
            <div className="sub" style={{ marginTop: 8, fontSize: 11.5 }}>
              Guia geral de nutrição de endurance, não uma prescrição personalizada — ajusta ao que o teu estômago tolera.
            </div>
          </>
        )}
      </div>

      <div className="section-label" style={{ margin: '18px 2px 10px' }}>
        <IconClock size={13} />PLANO POR TIPO DE DIA
      </div>

      {todayType && <DayTypeCard dayType={todayType} highlighted />}

      {!showAll ? (
        <button className="icon-btn" style={{ width: '100%' }} onClick={() => setShowAll(true)}>
          Ver os outros tipos de dia
        </button>
      ) : (
        otherTypes.map((d) => <DayTypeCard key={d.key} dayType={d} />)
      )}
    </div>
  );
}
