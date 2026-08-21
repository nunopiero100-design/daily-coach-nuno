import { useState } from 'react';
import nutritionData from '../mock/nutritionPlan.json';
import { fuelingTarget, resolveDayType, supplementsToday } from '../fueling';
import { IconUtensils, IconClock } from '../components/Icons';

// Ported from Nuno_RidePlan_App_3.html - real meal options, macros and
// supplement timing, not placeholder content.
const DIET_ORDER = ['REST', 'ENDURANCE', 'HARD', 'BIG', 'TRAVEL'];

function fmtMin(m) {
  if (m == null) return 'n/d';
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return h > 0 ? `${h}h${mm ? mm + 'm' : ''}` : `${mm}m`;
}

function MealSlot({ meal }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div className="sub" style={{ fontWeight: 700, textTransform: 'uppercase', fontSize: 11, marginBottom: 4 }}>
        {meal.meal}
      </div>
      {meal.opts.map((o, i) => (
        <div key={i} className="sub" style={{ marginBottom: 2 }}>
          {i + 1}. {o.desc} <span style={{ color: 'var(--text-dim)' }}>({o.macro})</span>
        </div>
      ))}
    </div>
  );
}

function DietTypeCard({ dietType, highlighted }) {
  return (
    <div className="card" style={{ borderLeft: `4px solid ${dietType.hdr}` }}>
      <div className="sub" style={{ fontWeight: highlighted ? 700 : 400, color: highlighted ? 'var(--text)' : undefined, marginBottom: 4 }}>
        {dietType.label.toUpperCase()}
      </div>
      {dietType.target && <div className="sub" style={{ marginBottom: 2 }}>{dietType.target}</div>}
      {dietType.when && <div className="sub" style={{ marginBottom: 8 }}>{dietType.when}</div>}

      {dietType.travel && <div className="sub">{dietType.travel}</div>}

      {dietType.onbike && (
        <div className="action-line dim" style={{ marginBottom: 10 }}>
          <IconUtensils size={14} />
          <span>{dietType.onbike}</span>
        </div>
      )}

      {dietType.meals?.map((m, i) => <MealSlot key={i} meal={m} />)}
    </div>
  );
}

export default function NutritionScreen({ report }) {
  const [showAll, setShowAll] = useState(false);
  const pw = report?.planned_workout;
  const target = fuelingTarget(pw);

  const todayEntry = report ? resolveDayType(report, nutritionData) : null;
  const todayKey = todayEntry?.diet;
  const todayType = todayKey ? nutritionData.dietTypes[todayKey] : null;
  const otherKeys = DIET_ORDER.filter((k) => k !== todayKey);
  const supp = todayEntry ? supplementsToday(todayEntry) : null;

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

      {supp && (
        <div className="card">
          <div className="section-label" style={{ margin: '0 0 8px' }}>SUPLEMENTOS — {supp.label.toUpperCase()}</div>
          {supp.items.map((it, i) => (
            <div key={i} className="action-line" style={{ marginBottom: 6 }}>
              <IconUtensils size={14} />
              <span>{it}</span>
            </div>
          ))}
          <div className="sub" style={{ marginTop: 6 }}>Core diário: {nutritionData.supplements.core.join(' · ')}</div>
          <div className="sub" style={{ marginTop: 6, fontSize: 11.5 }}>{nutritionData.supplements.notes}</div>
        </div>
      )}

      <div className="section-label" style={{ margin: '18px 2px 10px' }}>
        <IconClock size={13} />PLANO POR TIPO DE DIA
      </div>

      {todayType && <DietTypeCard dietType={todayType} highlighted />}

      {!showAll ? (
        <button className="icon-btn" style={{ width: '100%' }} onClick={() => setShowAll(true)}>
          Ver os outros tipos de dia
        </button>
      ) : (
        otherKeys.map((k) => <DietTypeCard key={k} dietType={nutritionData.dietTypes[k]} />)
      )}

      <details style={{ marginTop: 16 }}>
        <summary style={{ cursor: 'pointer', color: 'var(--text-dim)', fontSize: 13 }}>
          Princípios gerais <span className="chev">›</span>
        </summary>
        <div className="card" style={{ marginTop: 8 }}>
          {nutritionData.principles.map((p, i) => (
            <div key={`p${i}`} className="action-line" style={{ marginBottom: 8 }}>
              <IconUtensils size={13} />
              <span style={{ fontSize: 13 }}>{p}</span>
            </div>
          ))}
          {nutritionData.dietnotes.map((p, i) => (
            <div key={`n${i}`} className="action-line dim" style={{ marginBottom: 8, fontSize: 12.5 }}>
              <IconUtensils size={12} />
              <span>{p}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
