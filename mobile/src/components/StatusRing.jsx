import { statusColor, statusLabel, STATUS_RING_PCT } from '../statusColors';

const R = 40;
const CIRC = 2 * Math.PI * R;

/**
 * The hero moment for "how do I feel today" - a colored ring you see before
 * you read anything, instead of a small inline pill next to the title.
 * `sublabel` is for a real derived number (e.g. "form -8"), not decoration.
 */
export default function StatusRing({ status, sublabel, size = 96 }) {
  const color = statusColor(status);
  const pct = STATUS_RING_PCT[status] ?? STATUS_RING_PCT.INCOMPLETE;
  const dash = `${(CIRC * pct).toFixed(1)} ${CIRC.toFixed(1)}`;

  return (
    <div className="ring-wrap" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 96 96" style={{ transform: 'rotate(-90deg)' }}>
        <circle className="ring-bg" cx="48" cy="48" r={R} />
        <circle
          className="ring-fg"
          cx="48"
          cy="48"
          r={R}
          stroke={color}
          strokeDasharray={dash}
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
      </svg>
      <div className="ring-label">
        <div className="word" style={{ color }}>{statusLabel(status)}</div>
        {sublabel && <div className="sub">{sublabel}</div>}
      </div>
    </div>
  );
}
