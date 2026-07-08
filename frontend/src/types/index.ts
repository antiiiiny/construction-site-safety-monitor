/** Shared TypeScript types matching the backend Pydantic schemas. */

export interface Detection {
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
}

export interface Violation {
  zone_id: number;
  zone_name: string;
  person_bbox: [number, number, number, number];
  missing_ppe: string[];
  severity: "high" | "medium" | "low";
  timestamp: string;
}

export interface Zone {
  zone_id: number;
  name: string;
  required_ppe: string[];
  hazard_description: string;
}

export interface ScanResponse {
  zone_id: number;
  zone_name: string;
  detections: Detection[];
  violations: Violation[];
  tts_message: string;
  tts_audio_available: boolean;
  detection_count: number;
  violation_count: number;
}

export interface MetricsSummary {
  total_scans: number;
  total_violations: number;
  scans_with_violations: number;
  compliance_rate: number;
  violations_per_zone: Record<number, number>;
  violations_per_ppe: Record<string, number>;
  severity_breakdown: Record<string, number>;
  most_unsafe_zone: number | null;
  session_id: string;
}

export interface KpiCards {
  total_scans: number;
  total_violations: number;
  compliance_rate: number;
  most_unsafe_zone: string | null;
}

export interface BarChartData {
  zone_id: number;
  zone_name: string;
  violations: number;
}

export interface PieChartData {
  ppe: string;
  count: number;
}

export interface TimelineEntry {
  index: number;
  timestamp: string;
  zone_id: number;
  zone_name: string;
  severity: string;
  missing_ppe: string[];
}

export interface HotspotEntry {
  zone_id: number;
  zone_name: string;
  violations: number;
  scans: number;
  violation_rate: number;
  rank: number;
}

export interface EventItem {
  type: "scan" | "violation";
  timestamp: string;
  zone_id?: number;
  zone_name?: string;
  severity?: string;
  missing_ppe?: string[];
  detection_count?: number;
  violation_count?: number;
}
