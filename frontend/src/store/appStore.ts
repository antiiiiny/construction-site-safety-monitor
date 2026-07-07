import { create } from "zustand";

/**
 * Global UI state for the frontend.
 *
 * Server-cached data (metrics, events, scan results) is handled by React
 * Query. This Zustand store holds only UI-level state: the currently
 * selected zone, TTS settings, and the confidence threshold.
 */

interface AppState {
  /** Currently selected zone in the camera grid (1-6). */
  selectedZone: number;
  /** Master toggle for TTS audio playback. */
  ttsEnabled: boolean;
  /** TTS backend selection: "edge" (default) or "gtts". */
  ttsBackend: "edge" | "gtts";
  /** YOLOv8 confidence threshold (0.0 - 1.0). */
  confidenceThreshold: number;

  // Actions
  setSelectedZone: (zone: number) => void;
  setTtsEnabled: (enabled: boolean) => void;
  setTtsBackend: (backend: "edge" | "gtts") => void;
  setConfidenceThreshold: (value: number) => void;
}

export const useStore = create<AppState>((set) => ({
  selectedZone: 1,
  ttsEnabled: true,
  ttsBackend: "edge",
  confidenceThreshold: 0.5,

  setSelectedZone: (zone) => set({ selectedZone: zone }),
  setTtsEnabled: (enabled) => set({ ttsEnabled: enabled }),
  setTtsBackend: (backend) => set({ ttsBackend: backend }),
  setConfidenceThreshold: (value) => set({ confidenceThreshold: value }),
}));
