// Single source of truth for status -> color/label, shared by StatusBadge,
// StatusRing and HistoryScreen's sparkline so the three don't drift out of
// sync with three separate hardcoded maps.

export const STATUS_COLORS = {
  GREEN: '#4fd67a',
  YELLOW: '#f0c14b',
  RED: '#f0574b',
  INCOMPLETE: '#8b96a3',
};

export const STATUS_LABELS = {
  GREEN: 'Verde',
  YELLOW: 'Amarelo',
  RED: 'Vermelho',
  INCOMPLETE: 'Dados incompletos',
};

// Roughly how "full" the hero ring should read per status - not a real
// computed score, just a visual proxy so GREEN reads fuller than RED.
export const STATUS_RING_PCT = {
  GREEN: 0.88,
  YELLOW: 0.6,
  RED: 0.32,
  INCOMPLETE: 0.15,
};

export function statusColor(status) {
  return STATUS_COLORS[status] || STATUS_COLORS.INCOMPLETE;
}

export function statusLabel(status) {
  return STATUS_LABELS[status] || status || 'n/d';
}

export function hexToRgba(hex, alpha = 1) {
  const h = hex.replace('#', '');
  const bigint = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
