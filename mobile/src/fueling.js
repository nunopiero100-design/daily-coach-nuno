// On-the-bike carb target, derived from today's own planned_workout fields
// (duration_minutes, planned_tss) instead of being a static reference page.
// Ranges follow widely-used endurance-nutrition guidance (roughly 30-90g of
// carbs/hour, scaling with duration and intensity) - general guidance, not a
// personalized prescription, and easy to retune here if it doesn't fit.

export function fuelingTarget(plannedWorkout) {
  const minutes = plannedWorkout?.duration_minutes;
  if (minutes == null || minutes <= 0) return null;

  const hours = minutes / 60;
  let range;
  if (hours < 1) range = [0, 30];
  else if (hours < 1.5) range = [30, 60];
  else if (hours < 2.5) range = [60, 75];
  else range = [75, 90];

  let note = null;
  const tss = plannedWorkout?.planned_tss;
  if (tss != null && hours > 0) {
    const tssPerHour = tss / hours;
    if (tssPerHour >= 70) {
      range = [range[0] + 10, range[1] + 15];
      note = 'Treino intenso para a duração (TSS/h alto) — tende para o topo do intervalo, ou mesmo um pouco acima se o estômago aguentar.';
    } else if (tssPerHour <= 40) {
      note = 'Ritmo mais leve — o valor mais baixo do intervalo costuma bastar.';
    }
  }

  return {
    hours,
    perHourLow: range[0],
    perHourHigh: range[1],
    totalLow: Math.round(range[0] * hours),
    totalHigh: Math.round(range[1] * hours),
    note,
  };
}

export function dayTypeForReport(report) {
  const pw = report?.planned_workout;
  if (!pw?.name) return 'REST';
  if ((pw.duration_minutes || 0) >= 120) return 'LONG';
  return 'SHORT_HARD';
}
