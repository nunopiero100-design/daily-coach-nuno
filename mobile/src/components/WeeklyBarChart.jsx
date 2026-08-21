// Weekly training-load bar chart - one bar per calendar week, height scaled
// to the heaviest week in the window. Built from completed_activity.tss
// (what you actually rode), not planned_tss, so it reflects real load.

export default function WeeklyBarChart({ weeks }) {
  if (!weeks || weeks.length < 2) return null;
  const max = Math.max(...weeks.map((w) => w.tss), 1);

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 110 }}>
      {weeks.map((w) => {
        const h = Math.max((w.tss / max) * 84, w.tss > 0 ? 4 : 2);
        return (
          <div key={w.label} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: '100%' }}>
            <div style={{ fontSize: 10.5, fontFamily: 'var(--mono)', color: 'var(--text-dim)', marginBottom: 4 }}>
              {w.tss > 0 ? Math.round(w.tss) : ''}
            </div>
            <div
              style={{
                width: '100%',
                maxWidth: 22,
                height: h,
                borderRadius: 6,
                background: w.tss > 0
                  ? 'linear-gradient(180deg, #d6ff6e, var(--lime))'
                  : 'var(--card-border)',
              }}
            />
            <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 6 }}>{w.label}</div>
          </div>
        );
      })}
    </div>
  );
}
