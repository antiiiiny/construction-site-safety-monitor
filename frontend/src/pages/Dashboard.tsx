/** Main dashboard page — camera grid + metrics + charts + events table. */

import { CameraTile } from "../components/CameraTile";
import { FloorPlanHeatmap } from "../components/FloorPlanHeatmap";
import { MetricCard } from "../components/MetricCard";
import { Sidebar } from "../components/Sidebar";
import {
  PPEBreakdownPie,
  ViolationTimeline,
} from "../components/ChartBuilder";
import {
  useEvents,
  useHotspots,
  useKpi,
  useTimeline,
  useViolationsPerPpe,
  useViolationsPerZone,
  useZones,
} from "../hooks/useApi";

/** Skeleton grid for loading camera tiles. */
function CameraGridSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="card overflow-hidden">
          <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
            <div className="mb-1 h-4 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-3 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          </div>
          <div className="aspect-video animate-pulse bg-slate-200 dark:bg-surface-800" />
          <div className="space-y-2 px-4 py-3">
            <div className="h-3 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            <div className="flex gap-2">
              <div className="h-5 w-16 animate-pulse rounded-full bg-slate-200 dark:bg-slate-700" />
              <div className="h-5 w-20 animate-pulse rounded-full bg-slate-200 dark:bg-slate-700" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/** Skeleton row for KPI cards. */
function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="card flex items-center gap-4 p-4">
          <div className="h-12 w-12 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-6 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function Dashboard() {
  const zonesQuery = useZones();
  const kpiQuery = useKpi();
  const eventsQuery = useEvents(20);
  const barQuery = useViolationsPerZone();
  const pieQuery = useViolationsPerPpe();
  const timelineQuery = useTimeline();
  const hotspotsQuery = useHotspots(3);

  const kpi = kpiQuery.data;
  const compliancePct = kpi
    ? `${(kpi.compliance_rate * 100).toFixed(1)}%`
    : "—";

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 space-y-6">
        {/* KPI cards */}
        {kpiQuery.isLoading ? (
          <KpiSkeleton />
        ) : (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard
              label="Total Scans"
              value={kpi?.total_scans ?? 0}
              icon="📸"
              color="brand"
            />
            <MetricCard
              label="Total Violations"
              value={kpi?.total_violations ?? 0}
              icon="⚠️"
              color="danger"
            />
            <MetricCard
              label="Compliance Rate"
              value={compliancePct}
              icon="✅"
              color="safe"
            />
            <MetricCard
              label="Most Unsafe Zone"
              value={kpi?.most_unsafe_zone ?? "—"}
              icon="🚨"
              color="warning"
            />
          </div>
        )}

        {/* Camera grid (3x2) */}
        <div>
          <h2 className="section-heading mb-3">
            <span>📹</span> Camera Grid
          </h2>
          {zonesQuery.isLoading ? (
            <CameraGridSkeleton />
          ) : zonesQuery.data ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {zonesQuery.data.map((zone) => (
                <CameraTile key={zone.zone_id} zone={zone} />
              ))}
            </div>
          ) : (
            <div className="card flex items-center gap-3 p-6 text-sm text-danger">
              <span>⚠️</span> Failed to load zones.
            </div>
          )}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="card p-4">
            <h3 className="section-heading mb-3">
              <span>🗺️</span> Site Floor Plan — Violation Heatmap
            </h3>
            {barQuery.isLoading ? (
              <div className="space-y-3">
                <div className="h-5 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                <div className="h-[260px] animate-pulse rounded bg-slate-100 dark:bg-surface-800" />
              </div>
            ) : barQuery.data ? (
              <FloorPlanHeatmap data={barQuery.data} />
            ) : (
              <p className="py-8 text-center text-xs text-slate-400">No zone data available.</p>
            )}
          </div>
          <div className="card p-4">
            {pieQuery.isLoading ? (
              <div className="space-y-3">
                <div className="h-5 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                <div className="h-[260px] animate-pulse rounded bg-slate-100 dark:bg-surface-800" />
              </div>
            ) : pieQuery.data ? (
              <PPEBreakdownPie data={pieQuery.data} />
            ) : (
              <p className="py-8 text-center text-xs text-slate-400">No PPE data available.</p>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="card p-4">
          {timelineQuery.isLoading ? (
            <div className="space-y-3">
              <div className="h-5 w-1/3 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              <div className="h-[260px] animate-pulse rounded bg-slate-100 dark:bg-surface-800" />
            </div>
          ) : timelineQuery.data ? (
            <ViolationTimeline data={timelineQuery.data} />
          ) : (
            <p className="py-8 text-center text-xs text-slate-400">No violation timeline data.</p>
          )}
        </div>

        {/* Hotspots */}
        {hotspotsQuery.isLoading ? (
          <div className="card space-y-3 p-4">
            <div className="h-5 w-1/3 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-4 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            ))}
          </div>
        ) : hotspotsQuery.data && hotspotsQuery.data.length > 0 ? (
          <div className="card p-4">
            <h3 className="section-heading mb-3">
              <span>🚨</span> Zone Hotspot Ranking
            </h3>
            <div className="space-y-2">
              {hotspotsQuery.data.map((h) => (
                <div
                  key={h.zone_id}
                  className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-xs dark:bg-surface-800"
                >
                  <span className="flex items-center gap-2 font-medium text-slate-700 dark:text-slate-300">
                    {h.rank === 1 && <span className="text-base">🥇</span>}
                    {h.rank === 2 && <span className="text-base">🥈</span>}
                    {h.rank === 3 && <span className="text-base">🥉</span>}
                    {h.rank > 3 && <span className="text-slate-400">#{h.rank}</span>}
                    {h.zone_name}
                  </span>
                  <span className="badge-danger text-[10px]">
                    {h.violations} violations ({h.violation_rate.toFixed(1)}/scan)
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* Recent events table */}
        <div className="card p-4">
          <h3 className="section-heading mb-3">
            <span>🔔</span> Recent Alerts
          </h3>
          {eventsQuery.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-8 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              ))}
            </div>
          ) : eventsQuery.data && eventsQuery.data.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500 dark:border-slate-700 dark:text-slate-400">
                    <th className="py-2 pr-4 font-medium">Time</th>
                    <th className="py-2 pr-4 font-medium">Zone</th>
                    <th className="py-2 pr-4 font-medium">Missing PPE</th>
                    <th className="py-2 font-medium">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {eventsQuery.data
                    .filter((e) => e.type === "violation")
                    .slice(0, 10)
                    .map((e, i) => (
                      <tr key={i} className="border-b border-slate-100 dark:border-slate-800">
                        <td className="py-2 pr-4 text-slate-500 dark:text-slate-400">
                          {new Date(e.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="py-2 pr-4 font-medium text-slate-700 dark:text-slate-300">
                          {e.zone_name}
                        </td>
                        <td className="py-2 pr-4">
                          <div className="flex flex-wrap gap-1">
                            {e.missing_ppe?.map((ppe) => (
                              <span key={ppe} className="badge-danger text-[10px]">
                                {ppe}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-2">
                          <span
                            className={
                              e.severity === "high"
                                ? "severity-high"
                                : e.severity === "medium"
                                  ? "severity-medium"
                                  : "severity-low"
                            }
                          >
                            {e.severity}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-md bg-green-50 px-4 py-6 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
              <span>✅</span>
              <span>All clear — no violations detected.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
