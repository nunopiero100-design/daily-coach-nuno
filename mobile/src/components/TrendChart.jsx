// Generic multi-series line chart, inline SVG - no charting library. Used for
// the CTL/ATL overlay and the weight trend. Values can contain nulls (a day
// with incomplete readiness data); the line breaks across a null instead of
// interpolating through it, so a data gap reads as a gap, not a lie.

function buildPath(values, xFn, yFn) {
  let d = '';
  let started = false;
  values.forEach((v, i) => {
    if (v == null || Number.isNaN(v)) {
      started = false;
      return;
    }
    d += `${started ? 'L' : 'M'} ${xFn(i).toFixed(1)} ${yFn(v).toFixed(1)} `;
    started = true;
  });
  return d.trim();
}

function lastValue(values) {
  for (let i = values.length - 1; i >= 0; i--) {
    if (values[i] != null && !Number.isNaN(values[i])) return values[i];
  }
  return null;
}

export default function TrendChart({ series, height = 90, refLine }) {
  const width = 280;
  const pad = 10;

  const allValues = series.flatMap((s) => s.values).filter((v) => v != null && !Number.isNaN(v));
  const refValues = refLine ? [refLine.value] : [];
  if (allValues.length < 2) return null;

  const min = Math.min(...allValues, ...refValues);
  const max = Math.max(...allValues, ...refValues);
  const range = max - min || 1;
  const len = Math.max(...series.map((s) => s.values.length));

  const x = (i) => pad + (i * (width - pad * 2)) / Math.max(len - 1, 1);
  const y = (v) => height - pad - ((v - min) / range) * (height - pad * 2);

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} style={{ display: 'block' }}>
        {refLine && (
          <line
            x1={pad} y1={y(refLine.value)} x2={width - pad} y2={y(refLine.value)}
            stroke={refLine.color || 'var(--card-border)'}
            strokeWidth="1"
            strokeDasharray="3,3"
          />
        )}
        {series.map((s) => (
          <path
            key={s.label}
            d={buildPath(s.values, x, y)}
            fill="none"
            stroke={s.color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}
      </svg>
      <div style={{ display: 'flex', gap: 14, marginTop: 8, flexWrap: 'wrap' }}>
        {series.map((s) => {
          const last = lastValue(s.values);
          return (
            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11.5 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: s.color, display: 'inline-block' }} />
              <span style={{ color: 'var(--text-dim)' }}>{s.label}</span>
              {last != null && <span style={{ fontFamily: 'var(--mono)', fontWeight: 700 }}>{Math.round(last)}</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
