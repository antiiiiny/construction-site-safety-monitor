/** Typed API endpoint functions for the backend. */

import { apiClient } from "./client";
import type {
  BarChartData,
  EventItem,
  HotspotEntry,
  KpiCards,
  MetricsSummary,
  PieChartData,
  ScanResponse,
  TimelineEntry,
  Zone,
} from "../types";

/** Get all 6 zone configurations. */
export async function getZones(): Promise<Zone[]> {
  const res = await apiClient.get<Zone[]>("/api/zones");
  return res.data;
}

/** Upload an image to a zone for scanning. Returns detections + violations. */
export async function scanZone(
  zoneId: number,
  image: File,
): Promise<ScanResponse> {
  const formData = new FormData();
  formData.append("zone_id", String(zoneId));
  formData.append("image", image);
  const res = await apiClient.post<ScanResponse>("/api/scan", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

/** Get overall summary metrics. */
export async function getMetrics(): Promise<MetricsSummary> {
  const res = await apiClient.get<MetricsSummary>("/api/metrics");
  return res.data;
}

/** Get KPI card data. */
export async function getKpi(): Promise<KpiCards> {
  const res = await apiClient.get<KpiCards>("/api/kpi");
  return res.data;
}

/** Get recent events (optionally filtered by type). */
export async function getEvents(
  limit = 50,
  eventType?: "scan" | "violation",
): Promise<EventItem[]> {
  const params: Record<string, unknown> = { limit };
  if (eventType) params.event_type = eventType;
  const res = await apiClient.get<EventItem[]>("/api/events", { params });
  return res.data;
}

/** Get bar chart data (violations per zone). */
export async function getViolationsPerZone(): Promise<BarChartData[]> {
  const res = await apiClient.get<BarChartData[]>(
    "/api/charts/violations-per-zone",
  );
  return res.data;
}

/** Get pie chart data (violations per PPE type). */
export async function getViolationsPerPpe(): Promise<PieChartData[]> {
  const res = await apiClient.get<PieChartData[]>(
    "/api/charts/violations-per-ppe",
  );
  return res.data;
}

/** Get timeline data (chronological violations). */
export async function getTimeline(): Promise<TimelineEntry[]> {
  const res = await apiClient.get<TimelineEntry[]>("/api/charts/timeline");
  return res.data;
}

/** Get hotspot ranking. */
export async function getHotspots(topN = 3): Promise<HotspotEntry[]> {
  const res = await apiClient.get<HotspotEntry[]>("/api/hotspots", {
    params: { top_n: topN },
  });
  return res.data;
}

/** Request TTS audio for a message. Returns MP3 blob URL. */
export async function getTtsAudio(message: string): Promise<string | null> {
  const res = await apiClient.post(
    "/api/tts",
    { message },
    { responseType: "blob" },
  );
  if (res.status === 200) {
    return URL.createObjectURL(res.data);
  }
  return null;
}

/** Download the PDF report. Triggers browser download. */
export async function downloadReport(siteName = "Construction Site"): Promise<void> {
  const res = await apiClient.get("/api/report", {
    params: { site_name: siteName },
    responseType: "blob",
  });
  const url = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = "safety_report.pdf";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/** Clear the session event log. */
export async function clearSession(): Promise<void> {
  await apiClient.post("/api/clear");
}
