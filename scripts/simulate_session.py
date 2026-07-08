"""Simulate a full safety monitoring session with mock data.

This script populates the EventLogger with realistic mock events across
all 6 zones, then generates a PDF report — no image upload or model
inference required. Useful for demos, testing the dashboard, and
generating sample reports.

Usage:
    # Start the backend first:
    python -m uvicorn backend.src.api.main:app --port 8000

    # Then run the simulation:
    python scripts/simulate_session.py

    # Or generate just a PDF without the backend:
    python scripts/simulate_session.py --pdf-only
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.src.analytics.event_logger import EventLogger  # noqa: E402
from backend.src.reporting.pdf_generator import generate_daily_report  # noqa: E402
from backend.src.rules.models import Violation  # noqa: E402
from backend.src.rules.zone_config import get_zone  # noqa: E402


def generate_mock_session(num_scans: int = 24) -> EventLogger:
    """Generate a realistic mock session with violations across all 6 zones.

    Args:
        num_scans: Number of scans to simulate (default 24 = ~4 per zone).

    Returns:
        EventLogger populated with mock events.
    """
    logger = EventLogger(session_id="simulated-session")
    random.seed(42)  # Reproducible

    zone_names = {z.zone_id: z.name for z in [get_zone(i) for i in range(1, 7)]}
    zone_required_ppe = {z.zone_id: z.required_ppe for z in [get_zone(i) for i in range(1, 7)]}

    # Simulate scans over the past 8 hours
    base_time = datetime.now(UTC) - timedelta(hours=8)

    for i in range(num_scans):
        zone_id = (i % 6) + 1  # Cycle through zones
        scan_time = base_time + timedelta(minutes=i * 20)
        required = zone_required_ppe[zone_id]

        # 60% chance of having a violation
        has_violation = random.random() < 0.6

        if has_violation:
            # Pick 1-2 missing PPE items
            num_missing = random.randint(1, min(2, len(required)))
            missing = random.sample(required, num_missing)

            # Determine severity
            severity = "high" if zone_id == 3 or num_missing >= 2 else "medium"

            # Create violation
            v = Violation(
                zone_id=zone_id,
                zone_name=zone_names[zone_id],
                person_bbox=(
                    random.randint(50, 200),
                    random.randint(50, 200),
                    random.randint(300, 500),
                    random.randint(400, 700),
                ),
                missing_ppe=missing,
                severity=severity,
                timestamp=scan_time.isoformat(),
            )

            # Generate mock detections (person + some PPE)
            detections = [
                {"class_name": "person", "confidence": 0.92,
                 "bbox": [100, 100, 300, 600]},
            ]
            # Add detected PPE (everything except missing)
            for ppe in required:
                if ppe not in missing:
                    detections.append({
                        "class_name": ppe,
                        "confidence": random.uniform(0.75, 0.95),
                        "bbox": [
                            random.randint(120, 250),
                            random.randint(80, 300),
                            random.randint(200, 350),
                            random.randint(200, 500),
                        ],
                    })

            logger.log_scan(zone_id, detections, [v])
        else:
            # Compliant scan — all PPE detected
            detections = [
                {"class_name": "person", "confidence": 0.95,
                 "bbox": [100, 100, 300, 600]},
            ]
            for ppe in required:
                detections.append({
                    "class_name": ppe,
                    "confidence": random.uniform(0.80, 0.98),
                    "bbox": [
                        random.randint(120, 250),
                        random.randint(80, 300),
                        random.randint(200, 350),
                        random.randint(200, 500),
                    ],
                })

            logger.log_scan(zone_id, detections, [])

    return logger


def run_via_api(logger: EventLogger) -> None:
    """Send the mock data to the running backend via API.

    Args:
        logger: The populated EventLogger (used for reference).
    """
    import requests

    backend_url = "http://localhost:8000"

    # Check backend
    try:
        r = requests.get(f"{backend_url}/health", timeout=5)
        if r.status_code != 200:
            print("Backend not healthy. Start it first.")
            return
    except requests.exceptions.ConnectionError:
        print("Backend not running. Start it first:")
        print("  python -m uvicorn backend.src.api.main:app --port 8000")
        return

    # Clear existing session
    print("Clearing existing session...")
    requests.post(f"{backend_url}/api/clear")

    # We can't directly inject events via API — the API only accepts scans.
    # Instead, we'll use the backend's internal event logger by importing it.
    # This requires the backend to be running in the same process.
    # For a running server, we simulate by calling the scan endpoint with
    # sample images.

    print("\nNote: API simulation requires sample images.")
    print("Use --pdf-only to generate a PDF without the backend.")
    print("Or use the demo script: python scripts/run_demo.py")

    # Generate PDF via API
    print("\nGenerating PDF report via API...")
    r = requests.get(f"{backend_url}/api/report?site_name=Simulated%20Construction%20Site")
    if r.status_code == 200:
        report_dir = REPO_ROOT / "artifacts" / "simulated_session"
        report_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = report_dir / "simulated_report.pdf"
        with open(pdf_path, "wb") as f:
            f.write(r.content)
        print(f"  PDF saved: {pdf_path} ({len(r.content)} bytes)")
    else:
        print(f"  ERROR: {r.status_code}")


def generate_pdf_only(logger: EventLogger) -> None:
    """Generate a PDF report directly from the mock session (no backend needed).

    Args:
        logger: The populated EventLogger.
    """
    print("\nGenerating PDF report directly...")
    events = logger.get_all_events()
    summary = logger.get_summary()

    print("\nSession Summary:")
    print(f"  Total Scans: {summary['total_scans']}")
    print(f"  Total Violations: {summary['total_violations']}")
    print(f"  Compliance Rate: {summary['compliance_rate']:.1%}")
    print(f"  Most Unsafe Zone: {summary.get('most_unsafe_zone', 'N/A')}")

    # Per-zone breakdown
    print("\n  Per-Zone:")
    zone_stats = logger.get_zone_stats()
    for zone_id in range(1, 7):
        stats = zone_stats.get(zone_id, {})
        zone = get_zone(zone_id)
        scans = stats.get("scans", 0)
        violations = stats.get("violations", 0)
        print(f"    Zone {zone_id} ({zone.name}): {scans} scans, {violations} violations")

    # Generate PDF
    pdf_bytes = generate_daily_report(
        event_log=events,
        site_name="Simulated Construction Site",
        date=datetime.now(UTC).strftime("%Y-%m-%d"),
    )

    # Save
    report_dir = REPO_ROOT / "artifacts" / "simulated_session"
    report_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = report_dir / "simulated_report.pdf"
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"\n  PDF saved: {pdf_path} ({len(pdf_bytes)} bytes)")

    # Also export CSV
    from backend.src.analytics.export_csv import export_events_csv

    csv_bytes = export_events_csv(logger)
    csv_path = report_dir / "simulated_events.csv"
    with open(csv_path, "wb") as f:
        f.write(csv_bytes)
    print(f"  CSV saved: {csv_path} ({len(csv_bytes)} bytes)")

    print("\n  Open the PDF to view the full report.")


def main() -> None:
    """Run the simulation."""
    parser = argparse.ArgumentParser(
        description="Simulate a safety monitoring session with mock data."
    )
    parser.add_argument(
        "--pdf-only",
        action="store_true",
        help="Generate PDF directly without the backend (no API calls).",
    )
    parser.add_argument(
        "--scans",
        type=int,
        default=24,
        help="Number of scans to simulate (default: 24).",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Construction Site Safety Monitor — Session Simulator")
    print("=" * 60)

    # Generate mock session
    print(f"\nGenerating {args.scans} mock scans across 6 zones...")
    logger = generate_mock_session(num_scans=args.scans)

    summary = logger.get_summary()
    print(f"  Generated {summary['total_scans']} scans, "
          f"{summary['total_violations']} violations")
    print(f"  Compliance rate: {summary['compliance_rate']:.1%}")

    if args.pdf_only:
        generate_pdf_only(logger)
    else:
        run_via_api(logger)

    print("\n" + "=" * 60)
    print("  Simulation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
