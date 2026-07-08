import { useEffect } from "react";
import { Dashboard } from "./pages/Dashboard";
import { useStore } from "./store/appStore";

/**
 * Root application component.
 * Renders the header and the Dashboard page with the 6-camera grid,
 * live metrics, charts, and TTS playback.
 */
function App() {
  const darkMode = useStore((s) => s.darkMode);
  const toggleDarkMode = useStore((s) => s.toggleDarkMode);

  // Sync dark class on <html>
  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-surface-50 text-slate-800 dark:bg-surface-950 dark:text-slate-100">
      {/* ── Header ── */}
      <header className="border-b border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-surface-900">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          {/* Left: logo + title */}
          <div className="flex items-center gap-3">
            {/* Hard-hat logo */}
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500 text-lg font-bold text-white shadow-sm">
              🪖
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800 dark:text-white">
                Site Safety Monitor
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                PPE detection · Zone compliance · Voice alerts · PDF reporting
              </p>
            </div>
          </div>

          {/* Right: dark mode toggle */}
          <button
            onClick={toggleDarkMode}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-surface-50 px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-surface-800 dark:text-slate-300 dark:hover:bg-surface-700"
            aria-label="Toggle dark mode"
          >
            {darkMode ? (
              <>
                <span className="text-lg">☀️</span>
                <span className="hidden sm:inline">Light</span>
              </>
            ) : (
              <>
                <span className="text-lg">🌙</span>
                <span className="hidden sm:inline">Dark</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* ── Status bar ── */}
      <div className="border-b border-slate-200 bg-surface-100/50 dark:border-slate-800 dark:bg-surface-900/50">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-1.5 text-xs text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            System Online
          </span>
          <span className="hidden sm:inline">·</span>
          <span className="hidden sm:inline">YOLOv8 · FastAPI · React</span>
        </div>
      </div>

      {/* ── Main ── */}
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
