/** Plotly chart factory functions for the dashboard. */

import { useMemo } from "react";
import Plot from "react-plotly.js";
import type { BarChartData, PieChartData, TimelineEntry } from "../types";
import { useStore } from "../store/appStore";

/** Shared dark-mode-aware layout overrides. */
function useLayoutOverrides() {
  const darkMode = useStore((s) => s.darkMode);
  return useMemo(
    () => ({
      paper_bgcolor: darkMode ? "#172033" : "white",
      plot_bgcolor: darkMode ? "#1e293b" : "white",
      font: { color: darkMode ? "#cbd5e1" : "#334155", family: "Inter, system-ui, sans-serif" },
      xaxis: {
        gridcolor: darkMode ? "#334155" : "#e2e8f0",
        zerolinecolor: darkMode ? "#475569" : "#cbd5e1",
        tickfont: { color: darkMode ? "#94a3b8" : "#64748b" },
      },
      yaxis: {
        gridcolor: darkMode ? "#334155" : "#e2e8f0",
        zerolinecolor: darkMode ? "#475569" : "#cbd5e1",
        tickfont: { color: darkMode ? "#94a3b8" : "#64748b" },
      },
      title: {
        font: { color: darkMode ? "#e2e8f0" : "#1e293b", size: 14 },
      },
      legend: {
        font: { color: darkMode ? "#cbd5e1" : "#334155" },
      },
    }),
    [darkMode],
  );
}

/** Bar chart: violations per zone. */
export function ViolationsPerZoneBar({ data }: { data: BarChartData[] }) {
  const layoutOverrides = useLayoutOverrides();

  return (
    <Plot
      data={[
        {
          type: "bar",
          x: data.map((d) => d.zone_name),
          y: data.map((d) => d.violations),
          marker: { color: "#f59e0b" },
        },
      ]}
      layout={{
        ...layoutOverrides,
        title: { text: "Violations per Zone", ...layoutOverrides.title },
        margin: { t: 40, b: 80, l: 40, r: 20 },
        xaxis: { ...layoutOverrides.xaxis, tickangle: -25 },
        yaxis: { ...layoutOverrides.yaxis, title: "Violations" },
        height: 300,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
    />
  );
}

/** Pie chart: violations per PPE type. */
export function PPEBreakdownPie({ data }: { data: PieChartData[] }) {
  const layoutOverrides = useLayoutOverrides();

  return (
    <Plot
      data={[
        {
          type: "pie",
          labels: data.map((d) => d.ppe),
          values: data.map((d) => d.count),
          marker: {
            colors: ["#f59e0b", "#22c55e", "#0ea5e9", "#ef4444"],
          },
          textfont: { color: layoutOverrides.font.color },
        },
      ]}
      layout={{
        ...layoutOverrides,
        title: { text: "PPE Violation Breakdown", ...layoutOverrides.title },
        margin: { t: 40, b: 20, l: 20, r: 20 },
        height: 300,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
    />
  );
}

/** Timeline scatter: violations over time. */
export function ViolationTimeline({ data }: { data: TimelineEntry[] }) {
  const layoutOverrides = useLayoutOverrides();

  return (
    <Plot
      data={[
        {
          type: "scatter",
          mode: "markers",
          x: data.map((d) => d.index),
          y: data.map((d) => d.zone_name),
          text: data.map(
            (d) =>
              `${d.severity}: ${d.missing_ppe.join(", ")}`,
          ),
          marker: {
            color: data.map((d) =>
              d.severity === "high"
                ? "#ef4444"
                : d.severity === "medium"
                  ? "#f59e0b"
                  : "#22c55e",
            ),
            size: 10,
            line: {
              color: layoutOverrides.plot_bgcolor,
              width: 1,
            },
          },
        },
      ]}
      layout={{
        ...layoutOverrides,
        title: { text: "Violation Timeline", ...layoutOverrides.title },
        margin: { t: 40, b: 60, l: 120, r: 20 },
        xaxis: { ...layoutOverrides.xaxis, title: "Violation #" },
        yaxis: { ...layoutOverrides.yaxis, title: "Zone" },
        height: 300,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
    />
  );
}
