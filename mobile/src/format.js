// Shared formatting helpers - previously duplicated identically in
// TodayScreen.jsx and NutritionScreen.jsx.

export function fmtMin(m) {
  if (m == null) return 'n/d';
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return h > 0 ? `${h}h${mm ? mm + 'm' : ''}` : `${mm}m`;
}

export function fmtNum(v, digits = 0) {
  if (v == null || Number.isNaN(v)) return 'n/d';
  return Number(v).toFixed(digits);
}
