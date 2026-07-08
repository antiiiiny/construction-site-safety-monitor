/** Sidebar controls — confidence, TTS toggle, clear session, PDF. */

import { useStore } from "../store/appStore";
import { useClearSession, useDownloadReport, useSimulateSession } from "../hooks/useApi";

export function Sidebar() {
  const {
    ttsEnabled,
    setTtsEnabled,
    ttsBackend,
    setTtsBackend,
    confidenceThreshold,
    setConfidenceThreshold,
    darkMode,
    toggleDarkMode,
  } = useStore();

  const clearMutation = useClearSession();
  const reportMutation = useDownloadReport();
  const simulateMutation = useSimulateSession();

  return (
    <aside className="w-full space-y-4 lg:w-64">
      {/* ⚙ Controls */}
      <div className="card divide-y divide-slate-200 dark:divide-slate-700">
        <div className="px-4 py-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-white">
            <span>⚙️</span> Controls
          </h2>
        </div>

        {/* Confidence threshold */}
        <div className="px-4 py-3">
          <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
            Confidence Threshold
          </label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
              className="w-full accent-amber-500"
            />
            <span className="shrink-0 text-xs font-semibold text-slate-700 dark:text-slate-300">
              {(confidenceThreshold * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* TTS toggle */}
        <div className="px-4 py-3">
          <label className="flex items-center gap-2.5">
            <input
              type="checkbox"
              checked={ttsEnabled}
              onChange={(e) => setTtsEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-amber-500 focus:ring-amber-500 dark:border-slate-600"
            />
            <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
              🔊 TTS Voice Alerts
            </span>
          </label>
        </div>

        {/* TTS backend */}
        {ttsEnabled && (
          <div className="px-4 py-3">
            <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
              TTS Backend
            </label>
            <select
              value={ttsBackend}
              onChange={(e) =>
                setTtsBackend(e.target.value as "edge" | "gtts")
              }
              className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-700 focus:border-amber-500 focus:outline-none dark:border-slate-600 dark:bg-surface-800 dark:text-slate-300"
            >
              <option value="edge">edge-tts (neural)</option>
              <option value="gtts">gTTS (fallback)</option>
            </select>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-2 px-4 py-3">
          <button
            onClick={() => simulateMutation.mutate(24)}
            disabled={simulateMutation.isPending}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-sky-500 px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-sky-600 disabled:opacity-50"
          >
            <span>▶️</span>
            {simulateMutation.isPending ? "Simulating..." : "Start Simulation"}
          </button>

          <button
            onClick={() => clearMutation.mutate()}
            disabled={clearMutation.isPending}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:bg-surface-800 dark:text-slate-300 dark:hover:bg-surface-700"
          >
            <span>🗑️</span>
            {clearMutation.isPending ? "Clearing..." : "Clear Session"}
          </button>

          <button
            onClick={() => reportMutation.mutate(undefined)}
            disabled={reportMutation.isPending}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-amber-500 px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
          >
            <span>📄</span>
            {reportMutation.isPending ? "Generating..." : "Download PDF Report"}
          </button>

          <button
            onClick={toggleDarkMode}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-surface-800 dark:text-slate-300 dark:hover:bg-surface-700"
          >
            {darkMode ? <span>☀️</span> : <span>🌙</span>}
            {darkMode ? "Light Mode" : "Dark Mode"}
          </button>
        </div>
      </div>
    </aside>
  );
}
