import type { KPISpec } from "./types";

const TREND_COLORS = {
  up: "#10b981",
  down: "#ef4444",
  neutral: "#6b7280",
} as const;

export function KpiRenderer({ spec }: { spec: KPISpec }) {
  const { label, value, delta, trend, description } = spec;
  const color = trend ? TREND_COLORS[trend] : TREND_COLORS.neutral;

  return (
    <div className="a2ui-card" style={{ minWidth: 180, display: "inline-block", marginRight: 8 }}>
      <div className="a2ui-kpi-label">{label}</div>
      <div className="a2ui-kpi-value">{value}</div>
      {delta && (
        <div className="a2ui-kpi-delta" style={{ color }}>
          {delta}
        </div>
      )}
      {description && <p className="desc" style={{ marginTop: 8 }}>{description}</p>}
    </div>
  );
}
