export default function StatTile({ icon, label, value, unit }) {
  return (
    <div className="stat-tile">
      <div className="top-row">
        {icon}
        <span>{label}</span>
      </div>
      <div className="val">
        {value}
        {unit && <small>{unit}</small>}
      </div>
    </div>
  );
}
