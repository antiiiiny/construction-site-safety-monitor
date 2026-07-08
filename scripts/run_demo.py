"""Demo script — loads sample images into all 6 zones via the API.

This script simulates a user uploading images to all 6 camera tiles
sequentially. It calls the /api/scan endpoint for each zone, then
prints the results and generates a PDF report.

Usage:
    # Start the backend first:
    python -m uvicorn backend.src.api.main:app --port 8000

    # Then run the demo:
    python scripts/run_demo.py

Requirements:
    - Backend running on http://localhost:8000
    - Sample images in data/sample_images/ (at least 4)
    - Model weights at artifacts/stage2_model/best.pt
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

# Configuration
BACKEND_URL = "http://localhost:8000"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_images"

# Zone IDs to scan (all 6)
ZONE_IDS = [1, 2, 3, 4, 5, 6]


def check_backend() -> bool:
    """Check if the backend is running.

    Returns:
        True if /health returns 200.
    """
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def run_demo() -> None:
    """Run the full demo: scan 6 zones, print results, generate PDF."""
    print("=" * 60)
    print("  Construction Site Safety Monitor — Demo Script")
    print("=" * 60)

    # Check backend
    if not check_backend():
        print("\nERROR: Backend is not running at http://localhost:8000")
        print("Start it with: python -m uvicorn backend.src.api.main:app --port 8000")
        sys.exit(1)

    print(f"\nBackend: {BACKEND_URL} (healthy)")
    print(f"Sample images: {SAMPLE_DIR}")

    # Get sample images
    if not SAMPLE_DIR.exists():
        print(f"ERROR: {SAMPLE_DIR} not found. Run download_dataset first.")
        sys.exit(1)

    image_files = sorted(
        f for f in SAMPLE_DIR.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    )

    if not image_files:
        print("ERROR: No sample images found.")
        sys.exit(1)

    print(f"Found {len(image_files)} sample images")
    print("-" * 60)

    # Clear any existing session
    print("Clearing session...")
    requests.post(f"{BACKEND_URL}/api/clear")
    print()

    # Scan each zone
    for i, zone_id in enumerate(ZONE_IDS):
        # Cycle through available images
        img_path = image_files[i % len(image_files)]
        print(f"[{i + 1}/{len(ZONE_IDS)}] Scanning Zone {zone_id} with {img_path.name}...")

        try:
            with open(img_path, "rb") as f:
                response = requests.post(
                    f"{BACKEND_URL}/api/scan",
                    data={"zone_id": zone_id},
                    files={"image": (img_path.name, f, "image/jpeg")},
                    timeout=60,
                )

            if response.status_code == 200:
                result = response.json()
                print(f"  → {result['detection_count']} detections, "
                      f"{result['violation_count']} violations")
                if result["violations"]:
                    for v in result["violations"]:
                        print(f"    ⚠ {v['zone_name']}: missing {', '.join(v['missing_ppe'])} "
                              f"({v['severity']})")
                if result["tts_message"]:
                    print(f"  🔊 TTS: {result['tts_message'][:80]}...")
            else:
                print(f"  ERROR: {response.status_code} — {response.text[:200]}")
        except Exception as e:
            print(f"  ERROR: {e}")

        print()

    # Print metrics
    print("-" * 60)
    print("Dashboard Metrics:")
    metrics = requests.get(f"{BACKEND_URL}/api/metrics").json()
    print(f"  Total Scans: {metrics['total_scans']}")
    print(f"  Total Violations: {metrics['total_violations']}")
    print(f"  Compliance Rate: {metrics['compliance_rate']:.1%}")
    print(f"  Most Unsafe Zone: {metrics.get('most_unsafe_zone', 'N/A')}")

    # Get KPI
    kpi = requests.get(f"{BACKEND_URL}/api/kpi").json()
    print(f"  Most Unsafe Zone Name: {kpi.get('most_unsafe_zone', 'N/A')}")

    # Get hotspots
    hotspots = requests.get(f"{BACKEND_URL}/api/hotspots").json()
    if hotspots:
        print("\nZone Hotspots:")
        for h in hotspots:
            print(f"  #{h['rank']} {h['zone_name']}: "
                  f"{h['violations']} violations ({h['violation_rate']}/scan)")

    # Generate PDF
    print("\n" + "-" * 60)
    print("Generating PDF report...")
    response = requests.get(f"{BACKEND_URL}/api/report?site_name=Demo%20Construction%20Site")
    if response.status_code == 200:
        report_path = Path(__file__).resolve().parent.parent / "artifacts" / "stage9_demo"
        report_path.mkdir(parents=True, exist_ok=True)
        pdf_path = report_path / "demo_report.pdf"
        with open(pdf_path, "wb") as f:
            f.write(response.content)
        print(f"  PDF saved: {pdf_path} ({len(response.content)} bytes)")
    else:
        print(f"  ERROR: {response.status_code}")

    # Export CSV
    print("\nExporting CSV...")
    response = requests.get(f"{BACKEND_URL}/api/export/csv")
    if response.status_code == 200:
        csv_path = report_path / "demo_events.csv"
        with open(csv_path, "wb") as f:
            f.write(response.content)
        print(f"  CSV saved: {csv_path} ({len(response.content)} bytes)")

    print("\n" + "=" * 60)
    print("  Demo complete! Check the dashboard at http://localhost:5173")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
