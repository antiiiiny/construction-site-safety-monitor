/** Site floor-plan heatmap — replaces the per-zone bar chart.

Renders a simple construction-site layout where each zone is a colored
region. Color intensity (green -> amber -> red) reflects the number of
PPE violations detected in that zone, giving an at-a-glance "heatmap" of
where safety compliance is worst across the site.
*/

import { useMemo } from "react";
import type { BarChartData } from "../types";
import { useStore } from "../store/appStore";
import { FLOOR_PLAN_VIEWBOX, FLOOR_ZONE_LAYOUT } from "../config/floorPlan";

/** Interpolate a heat color for intensity in [0,1]: green->amber->red. */
function heatColor(intensity: number): string {
  const t = Math.max(0, Math.min(1, intensity));
  const stops: Array<{ t: number; c: [number, number, number] }> = [
    { t: 0, c: [34, 197, 94] }, // #22c55e green (safe)
    { t: 0.5, c: [245, 158, 11] }, // #f59e0b amber (warning)
    { t: 1, c: [239, 68, 68] }, // #ef4444 red (high risk)
  ];
  let lo = stops[0];
  let hi = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {
    if (t >= stops[i].t && t <= stops[i + 1].t) {
      lo = stops[i];
      hi = stops[i + 1];
      break;
    }
  }
  const span = hi.t - lo.t || 1;
  const f = (t - lo.t) / span;
  const r = Math.round(lo.c[0] + (hi.c[0] - lo.c[0]) * f);
  const g = Math.round(lo.c[1] + (hi.c[1] - lo.c[1]) * f);
  const b = Math.round(lo.c[2] + (hi.c[2] - lo.c[2]) * f);
  return `rgb(${r}, ${g}, ${b})`;
}

export function FloorPlanHeatmap({ data }: { data: BarChartData[] }) {
  const darkMode = useStore((s) => s.darkMode);

  const { zones, maxViolations } = useMemo(() => {
    const byId = new Map(data.map((d) => [d.zone_id, d]));
    const max = Math.max(0, ...data.map((d) => d.violations));
    const zones = FLOOR_ZONE_LAYOUT.map((layout) => {
      const d = byId.get(layout.zone_id);
      const violations = d?.violations ?? 0;
      const name = d?.zone_name ?? `Zone ${layout.zone_id}`;
      const intensity = max > 0 ? violations / max : 0;
      return { ...layout, name, violations, intensity };
    });
    return { zones, maxViolations: max };
  }, [data]);

  const stroke = darkMode ? "#334155" : "#cbd5e1";
  const boundaryFill = darkMode ? "#0f172a" : "#f8fafc";
  // Dark text with a white outline stays readable on any heat color.
  const labelFill = "#0f172a";
  const labelStroke = "#ffffff";

  return (
    <div className="space-y-3">
      <svg
        viewBox={`0 0 ${FLOOR_PLAN_VIEWBOX.width} ${FLOOR_PLAN_VIEWBOX.height}`}
        className="w-full"
        role="img"
        aria-label="Site floor plan violation heatmap"
      >
        {/* Site boundary */}
        <rect
          x={8}
          y={8}
          width={FLOOR_PLAN_VIEWBOX.width - 16}
          height={FLOOR_PLAN_VIEWBOX.height - 16}
          rx={16}
          fill={boundaryFill}
          stroke={stroke}
          strokeWidth={2}
        />

        {zones.map((z) => (
          <g key={z.zone_id}>
            <rect
              x={z.x}
              y={z.y}
              width={z.w}
              height={z.h}
              rx={10}
              fill={heatColor(z.intensity)}
              stroke={stroke}
              strokeWidth={1.5}
            />
            {/* Zone id badge */}
            <text
              x={z.x + 14}
              y={z.y + 30}
              fontSize={20}
              fontWeight={700}
              fill={labelFill}
              stroke={labelStroke}
              strokeWidth={0.75}
              paintOrder="stroke"
            >
              {z.zone_id}
            </text>
            {/* Zone name */}
            <text
              x={z.x + z.w / 2}
              y={z.y + z.h / 2 - 6}
              fontSize={16}
              fontWeight={600}
              fill={labelFill}
              stroke={labelStroke}
              strokeWidth={0.75}
              paintOrder="stroke"
              textAnchor="middle"
            >
              {z.name}
            </text>
            {/* Violation count */}
            <text
              x={z.x + z.w / 2}
              y={z.y + z.h / 2 + 24}
              fontSize={22}
              fontWeight={700}
              fill={labelFill}
              stroke={labelStroke}
              strokeWidth={0.75}
              paintOrder="stroke"
              textAnchor="middle"
            >
              {z.violations} {z.violations === 1 ? "violation" : "violations"}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
        <span>Low</span>
        <div
          className="h-3 flex-1 rounded"
          style={{
            background:
              "linear-gradient(to right, rgb(34,197,94), rgb(245,158,11), rgb(239,68,68))",
          }}
        />
        <span>High</span>
        <span className="ml-2 font-medium text-slate-600 dark:text-slate-300">
          Max: {maxViolations}
        </span>
      </div>
    </div>
  );
}
