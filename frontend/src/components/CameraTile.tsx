/** Camera tile component — upload, detection overlay, violations, TTS. */

import { useRef, useState } from "react";
import type { ScanResponse, Zone } from "../types";
import { useScan } from "../hooks/useApi";
import { useStore } from "../store/appStore";
import { AlertPlayer } from "./AlertPlayer";

interface CameraTileProps {
  zone: Zone;
}

export function CameraTile({ zone }: CameraTileProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const scanMutation = useScan();
  const { ttsEnabled } = useStore();

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setImageUrl(URL.createObjectURL(file));

    try {
      const result = await scanMutation.mutateAsync({
        zoneId: zone.zone_id,
        image: file,
      });
      setScanResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    }
  };

  const hasViolations = scanResult && scanResult.violation_count > 0;
  const statusText = !scanResult
    ? "No scan"
    : hasViolations
      ? "Violation"
      : "Safe";
  const statusLabel = !scanResult
    ? "badge-neutral"
    : hasViolations
      ? "badge-danger"
      : "badge-safe";

  return (
    <div className="card flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-slate-800 dark:text-white">
            Zone {zone.zone_id}: {zone.name}
          </h3>
          <p className="truncate text-xs text-slate-500 dark:text-slate-400">
            {zone.hazard_description}
          </p>
        </div>
        <span className={`ml-3 shrink-0 ${statusLabel}`}>{statusText}</span>
      </div>

      {/* Image area */}
      <div className="relative aspect-video bg-slate-100 dark:bg-surface-800">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={`Zone ${zone.zone_id}`}
            className="h-full w-full object-contain"
          />
        ) : (
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex h-full w-full flex-col items-center justify-center gap-2 text-slate-400 transition-colors hover:text-amber-500 dark:text-slate-500 dark:hover:text-amber-400"
          >
            <span className="text-4xl">🪖</span>
            <span className="text-sm font-medium">Upload image for inspection</span>
            <span className="text-xs text-slate-400 dark:text-slate-500">
              JPEG / PNG
            </span>
          </button>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={handleFileSelect}
        />
      </div>

      {/* Loading skeleton */}
      {scanMutation.isPending && (
        <div className="space-y-2 px-4 py-3">
          <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          <div className="h-4 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          <div className="flex gap-2">
            <div className="h-5 w-16 animate-pulse rounded-full bg-slate-200 dark:bg-slate-700" />
            <div className="h-5 w-20 animate-pulse rounded-full bg-slate-200 dark:bg-slate-700" />
          </div>
        </div>
      )}

      {/* Detection badges */}
      {!scanMutation.isPending && scanResult && scanResult.detections.length > 0 && (
        <div className="flex flex-wrap gap-1.5 border-t border-slate-100 px-4 py-2.5 dark:border-slate-700">
          {scanResult.detections.map((det, i) => (
            <span
              key={i}
              className="badge-neutral text-xs"
            >
              {det.class_name}{" "}
              <span className="ml-1 font-normal text-slate-400">
                {(det.confidence * 100).toFixed(0)}%
              </span>
            </span>
          ))}
        </div>
      )}

      {/* Violations */}
      {!scanMutation.isPending && hasViolations && (
        <div className="border-t border-red-200 bg-red-50/80 px-4 py-2.5 dark:border-red-900/50 dark:bg-red-950/30">
          <p className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-danger">
            <span>⚠️</span>
            {scanResult!.violation_count} violation(s) detected
          </p>
          {scanResult!.violations.map((v, i) => (
            <p key={i} className="flex items-center gap-2 pl-5 text-xs text-red-700 dark:text-red-400">
              <span>Missing:</span>
              {v.missing_ppe.map((ppe) => (
                <span key={ppe} className="severity-high text-[10px]">
                  {ppe}
                </span>
              ))}
              <span className="ml-auto text-red-500 dark:text-red-400/70">
                {v.severity}
              </span>
            </p>
          ))}
        </div>
      )}

      {/* TTS alert */}
      {!scanMutation.isPending && hasViolations && ttsEnabled && scanResult!.tts_message && (
        <AlertPlayer message={scanResult!.tts_message} />
      )}

      {/* Error */}
      {!scanMutation.isPending && error && (
        <div className="border-t border-red-200 bg-red-50 px-4 py-2.5 dark:border-red-900/50 dark:bg-red-950/30">
          <p className="text-xs text-danger">{error}</p>
        </div>
      )}

      {/* No detections (safe scan with nothing found) */}
      {!scanMutation.isPending && scanResult && scanResult.detections.length === 0 && (
        <div className="border-t border-slate-100 px-4 py-2.5 text-xs text-slate-400 dark:border-slate-700 dark:text-slate-500">
          No objects detected in this scan.
        </div>
      )}

      {/* Re-scan button */}
      {!scanMutation.isPending && scanResult && (
        <button
          onClick={() => fileInputRef.current?.click()}
          className="border-t border-slate-200 px-4 py-2.5 text-xs font-medium text-brand transition-colors hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-surface-800"
        >
          ↻ Upload new image
        </button>
      )}
    </div>
  );
}
