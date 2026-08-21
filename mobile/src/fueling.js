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

/**
 * Which diet/day-type applies today.
 *
 * First choice: look up today's exact date in the ported RidePlan calendar
 * (real plan, not a guess) - accurate while that block (2026-06-15 to
 * 2026-09-20) is running. Outside that window, or if a date is somehow
 * missing, fall back to a heuristic derived from today's actual report
 * (no workout -> REST, long -> BIG, short+intense -> HARD, else ENDURANCE).
 * The fallback never resolves to TRAVEL - that one's calendar-only.
 */
export function resolveDayType(report, nutritionData) {
  const dateIso = report?.date;
  if (dateIso) {
    const entry = nutritionData.calendar.find((c) => c.date === dateIso);
    if (entry) return entry;
  }

  const pw = report?.planned_workout;
  if (!pw?.name) return { date: dateIso, type: null, diet: 'REST', hard: false, gym: null };

  const hours = (pw.duration_minutes || 0) / 60;
  if (hours >= 2.5) return { date: dateIso, type: null, diet: 'BIG', hard: false, gym: null };

  const tssPerHour = hours > 0 ? (pw.planned_tss || 0) / hours : 0;
  if (tssPerHour >= 65) return { date: dateIso, type: null, diet: 'HARD', hard: true, gym: null };

  return { date: dateIso, type: null, diet: 'ENDURANCE', hard: false, gym: null };
}

/**
 * Today-specific supplement timing, ported from the RidePlan logic.
 * Simplified vs the original: it drops the "is Sat/Sun actually a benchmark
 * test day" distinction, since that read from a separate 59-session workout
 * table we didn't port over - test weeks will just get the normal Sat/Sun
 * guidance instead of the test-day variant (caffeine + beetroot).
 */
export function supplementsToday(entry) {
  const items = [];
  let label;

  if (entry.type === 'away') {
    label = 'Viagem / fora';
    items.push('Mantém o core diário se conseguires. Poupa a cafeína extra hoje.');
  } else if (entry.diet === 'BIG') {
    label = 'Saída longa';
    items.push('Cafeína ~220 mg, 45–60 min antes — é um dia-chave.');
    items.push('Na bike: 60–90 g carbs/h + 500–1000 mg sódio/h.');
    items.push('Shake de recovery logo a seguir (ver aba de fueling).');
  } else if (entry.hard) {
    label = 'Intervalos intensos';
    items.push('Cafeína ~220 mg, 45–60 min antes.');
    items.push('Whey na janela de recovery (com o almoço).');
  } else if (entry.diet === 'ENDURANCE') {
    label = 'Endurance fácil';
    items.push('Sem cafeína extra — poupa para os dias-chave.');
    items.push('Água + eletrólitos na bike.');
  } else {
    label = 'Fácil / descanso';
    items.push('Só o core de hoje — poupa a cafeína para se manter eficaz.');
  }

  if (entry.gym) {
    items.push('Joelho: colagénio 15 g + vitamina C, ~45 min antes do ginásio.');
  }

  return { label, items };
}
