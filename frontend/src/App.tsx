import { useStore } from "./store/appStore";

/**
 * Root application component.
 *
 * Stage 0 scaffold: renders a minimal layout to verify the Vite + React +
 * TypeScript + Tailwind + Zustand stack is wired correctly. The full
 * Dashboard page with 6-camera grid is built in Stage 7.
 */
function App() {
  const { ttsEnabled, setTtsEnabled } = useStore();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-brand text-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <h1 className="text-xl font-bold">Construction Site Safety Monitor</h1>
          <p className="text-sm text-white/80">
            PPE detection · Zone compliance · Voice alerts · PDF reporting
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-2 text-lg font-semibold text-slate-800">
            Stage 0 — Setup Verified
          </h2>
          <p className="mb-4 text-sm text-slate-600">
            The frontend is running. The backend health check and full
            dashboard will be wired in later stages.
          </p>

          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={ttsEnabled}
              onChange={(e) => setTtsEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand"
            />
            <span className="text-sm text-slate-700">
              TTS enabled (Zustand store test)
            </span>
          </label>
        </div>
      </main>
    </div>
  );
}

export default App;
