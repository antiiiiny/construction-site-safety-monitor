/** React Query hooks for data fetching and mutations. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  clearSession,
  downloadReport,
  getEvents,
  getHotspots,
  getKpi,
  getMetrics,
  getTimeline,
  getViolationsPerPpe,
  getViolationsPerZone,
  getZones,
  scanZone,
} from "../api/endpoints";

/** Query keys for cache invalidation. */
export const queryKeys = {
  zones: ["zones"] as const,
  metrics: ["metrics"] as const,
  kpi: ["kpi"] as const,
  events: ["events"] as const,
  violationsPerZone: ["charts", "violations-per-zone"] as const,
  violationsPerPpe: ["charts", "violations-per-ppe"] as const,
  timeline: ["charts", "timeline"] as const,
  hotspots: ["hotspots"] as const,
};

/** Fetch all zones. */
export function useZones() {
  return useQuery({
    queryKey: queryKeys.zones,
    queryFn: getZones,
    staleTime: Infinity, // Zones don't change
  });
}

/** Fetch summary metrics (refetches when scans happen). */
export function useMetrics() {
  return useQuery({
    queryKey: queryKeys.metrics,
    queryFn: getMetrics,
    refetchInterval: 5000, // Poll every 5s
  });
}

/** Fetch KPI card data. */
export function useKpi() {
  return useQuery({
    queryKey: queryKeys.kpi,
    queryFn: getKpi,
    refetchInterval: 5000,
  });
}

/** Fetch recent events. */
export function useEvents(limit = 50, eventType?: "scan" | "violation") {
  return useQuery({
    queryKey: [queryKeys.events, limit, eventType],
    queryFn: () => getEvents(limit, eventType),
    refetchInterval: 5000,
  });
}

/** Fetch bar chart data. */
export function useViolationsPerZone() {
  return useQuery({
    queryKey: queryKeys.violationsPerZone,
    queryFn: getViolationsPerZone,
    refetchInterval: 5000,
  });
}

/** Fetch pie chart data. */
export function useViolationsPerPpe() {
  return useQuery({
    queryKey: queryKeys.violationsPerPpe,
    queryFn: getViolationsPerPpe,
    refetchInterval: 5000,
  });
}

/** Fetch timeline data. */
export function useTimeline() {
  return useQuery({
    queryKey: queryKeys.timeline,
    queryFn: getTimeline,
    refetchInterval: 5000,
  });
}

/** Fetch hotspot ranking. */
export function useHotspots(topN = 3) {
  return useQuery({
    queryKey: [queryKeys.hotspots, topN],
    queryFn: () => getHotspots(topN),
    refetchInterval: 5000,
  });
}

/** Scan a zone with an uploaded image. Invalidates metrics on success. */
export function useScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ zoneId, image }: { zoneId: number; image: File }) =>
      scanZone(zoneId, image),
    onSuccess: () => {
      // Invalidate all data that depends on the event log
      queryClient.invalidateQueries({ queryKey: queryKeys.metrics });
      queryClient.invalidateQueries({ queryKey: queryKeys.kpi });
      queryClient.invalidateQueries({ queryKey: queryKeys.events });
      queryClient.invalidateQueries({ queryKey: queryKeys.violationsPerZone });
      queryClient.invalidateQueries({ queryKey: queryKeys.violationsPerPpe });
      queryClient.invalidateQueries({ queryKey: queryKeys.timeline });
      queryClient.invalidateQueries({ queryKey: queryKeys.hotspots });
    },
  });
}

/** Clear the session. Invalidates all data on success. */
export function useClearSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: clearSession,
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });
}

/** Download the PDF report. */
export function useDownloadReport() {
  return useMutation({
    mutationFn: (siteName?: string) => downloadReport(siteName),
  });
}
