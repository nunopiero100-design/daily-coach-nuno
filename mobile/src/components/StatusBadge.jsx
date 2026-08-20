const LABELS = {
  GREEN: 'Verde',
  YELLOW: 'Amarelo',
  RED: 'Vermelho',
  INCOMPLETE: 'Dados incompletos',
};

export default function StatusBadge({ status }) {
  const label = LABELS[status] || status || 'n/d';
  const cls = LABELS[status] ? status : 'INCOMPLETE';
  return <span className={`status-badge ${cls}`}>{label}</span>;
}
