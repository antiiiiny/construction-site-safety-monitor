"""Convenience launcher — starts the FastAPI backend and Vite frontend together.

Usage:
    python scripts/run_dev.py

The script spawns both processes as subprocesses and streams their output
to the current terminal. Press Ctrl+C to stop both.

Requirements:
    - Backend: Python 3.11 venv with backend/requirements.txt installed
    - Frontend: Node.js 18+ with frontend/node_modules installed (npm install)

If frontend/node_modules does not exist, the script will run `npm install`
automatically on first launch.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"


def _check_venv() -> None:
    """Warn if running outside a virtual environment."""
    if sys.prefix == sys.base_prefix:
        print(
            "WARNING: Not running inside a virtual environment. "
            "Consider creating one:\n"
            "  python -m venv venv\n"
            "  venv\\Scripts\\activate  (Windows)\n"
            "  source venv/bin/activate  (macOS/Linux)\n"
        )


def _ensure_frontend_deps() -> None:
    """Run `npm install` if frontend/node_modules is missing."""
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("Frontend dependencies not found. Running `npm install`...")
        subprocess.run(
            ["npm", "install"],
            cwd=str(FRONTEND_DIR),
            check=True,
            shell=True,
        )
        print("npm install complete.\n")


def main() -> None:
    _check_venv()
    _ensure_frontend_deps()

    # Backend: uvicorn with reload for development
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.src.api.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]

    # Frontend: vite dev server
    frontend_cmd = ["npm", "run", "dev"]

    print("=" * 60)
    print("  Construction Site Safety Monitor — Dev Server")
    print("=" * 60)
    print("  Backend  : http://localhost:8000  (FastAPI)")
    print("  Frontend : http://localhost:5173  (Vite)")
    print("  API docs : http://localhost:8000/docs")
    print("=" * 60)
    print("  Press Ctrl+C to stop both servers.\n")

    procs: list[subprocess.Popen] = []

    try:
        # Start backend
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        )
        procs.append(backend_proc)

        # Start frontend
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            shell=True,
        )
        procs.append(frontend_proc)

        # Wait for either to exit
        for proc in procs:
            proc.wait()

    except KeyboardInterrupt:
        print("\nShutting down servers...")
        for proc in procs:
            if proc.poll() is None:
                if os.name == "nt":
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("Servers stopped.")


if __name__ == "__main__":
    main()
