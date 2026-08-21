import { STATUS_LABELS } from '../statusColors';

export default function StatusBadge({ status }) {
  const label = STATUS_LABELS[status] || status || 'n/d';
  const cls = STATUS_LABELS[status] ? status : 'INCOMPLETE';
  return <span className={`status-badge ${cls}`}>{label}</span>;
}
