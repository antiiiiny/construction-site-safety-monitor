import { create } from "zustand";

/**
 * Global UI state for the frontend.
 *
 * Server-cached data (metrics, events, scan results) is handled by React
 * Query. This Zustand store holds only UI-level state: the currently
 * selected zone, TTS settings, the confidence threshold, and dark mode.
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
  /** Dark mode toggle. */
  darkMode: boolean;

  // Actions
  setSelectedZone: (zone: number) => void;
  setTtsEnabled: (enabled: boolean) => void;
  setTtsBackend: (backend: "edge" | "gtts") => void;
  setConfidenceThreshold: (value: number) => void;
  toggleDarkMode: () => void;
}

/** Detect system preference for dark mode. */
const prefersDark = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-color-scheme: dark)").matches;

export const useStore = create<AppState>((set) => ({
  selectedZone: 1,
  ttsEnabled: true,
  ttsBackend: "edge",
  confidenceThreshold: 0.5,
  darkMode: prefersDark(),

  setSelectedZone: (zone) => set({ selectedZone: zone }),
  setTtsEnabled: (enabled) => set({ ttsEnabled: enabled }),
  setTtsBackend: (backend) => set({ ttsBackend: backend }),
  setConfidenceThreshold: (value) => set({ confidenceThreshold: value }),
  toggleDarkMode: () =>
    set((state) => ({ darkMode: !state.darkMode })),
}));
