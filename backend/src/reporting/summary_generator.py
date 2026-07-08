"""Rule-based natural-language summary generator for PDF reports.

Generates a professional supervisor summary from structured metrics,
without requiring an LLM. Used as the default summary method, and as
a fallback when OPENROUTER_API_KEY is not set.

Usage:
    from backend.src.reporting.summary_generator import generate_summary
    summary = generate_summary(event_log, summary_metrics)
"""

from __future__ import annotations

import contextlib
from typing import Any

from backend.src.rules.zone_config import get_zone


def generate_summary(
    event_log: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> str:
    """Generate a rule-based natural-language supervisor summary.

    Args:
        event_log: List of all events from EventLogger.get_all_events().
        metrics: Summary dict from EventLogger.get_summary().

    Returns:
        3-4 paragraph summary string.
    """
    total_scans = metrics.get("total_scans", 0)
    total_violations = metrics.get("total_violations", 0)
    compliance_rate = metrics.get("compliance_rate", 1.0)
    most_unsafe_zone_id = metrics.get("most_unsafe_zone")
    violations_per_zone = metrics.get("violations_per_zone", {})
    violations_per_ppe = metrics.get("violations_per_ppe", {})
    severity_breakdown = metrics.get("severity_breakdown", {})

    # Handle empty session
    if total_scans == 0:
        return (
            "No scans were performed during this reporting period. "
            "The safety monitoring system was not active. "
            "Ensure all camera zones are operational before the next shift."
        )

    if total_violations == 0:
        return (
            f"During this reporting period, {total_scans} scans were conducted "
            f"across all zones with zero PPE violations detected. "
            f"The compliance rate was 100%. "
            f"This indicates excellent safety adherence by all personnel. "
            f"Continue maintaining current safety standards and monitoring protocols."
        )

    # Build the summary
    paragraphs: list[str] = []

    # Paragraph 1: Overview
    most_unsafe_name = "Unknown"
    if most_unsafe_zone_id is not None:
        with contextlib.suppress(ValueError):
            most_unsafe_name = get_zone(most_unsafe_zone_id).name

    compliance_pct = compliance_rate * 100
    high_count = severity_breakdown.get("high", 0)
    medium_count = severity_breakdown.get("medium", 0)

    paragraphs.append(
        f"During this reporting period, {total_scans} scans were conducted "
        f"across 6 construction site zones, detecting {total_violations} PPE "
        f"violations. The overall compliance rate was {compliance_pct:.1f}%. "
        f"The most problematic zone was {most_unsafe_name}. "
        f"Of the violations, {high_count} were classified as high severity "
        f"and {medium_count} as medium severity."
    )

    # Paragraph 2: Zone analysis
    zone_details: list[str] = []
    for zone_id in sorted(violations_per_zone.keys()):
        count = violations_per_zone[zone_id]
        try:
            name = get_zone(zone_id).name
        except ValueError:
            name = f"Zone {zone_id}"
        zone_details.append(f"{name} ({count} violations)")

    zone_str = ", ".join(zone_details) if zone_details else "no zones had violations"
    paragraphs.append(
        f"Violations were distributed across zones as follows: {zone_str}. "
        f"The concentration of violations in specific areas suggests targeted "
        f"safety interventions may be needed in these locations."
    )

    # Paragraph 3: PPE analysis
    if violations_per_ppe:
        ppe_details = sorted(violations_per_ppe.items(), key=lambda x: -x[1])
        ppe_str = ", ".join(f"{ppe} ({count})" for ppe, count in ppe_details)
        most_common_ppe = ppe_details[0][0]
        paragraphs.append(
            f"The most common PPE violation was {most_common_ppe}, "
            f"accounting for {ppe_details[0][1]} incidents. "
            f"Full PPE breakdown: {ppe_str}. "
            f"These patterns suggest areas where compliance enforcement "
            f"or worker education may be most impactful."
        )

    # Paragraph 4: Overall assessment
    if compliance_rate < 0.7:
        assessment = (
            "The compliance rate is below 70%, indicating a significant "
            "safety concern that requires immediate attention. "
            "A site-wide safety review is recommended."
        )
    elif compliance_rate < 0.9:
        assessment = (
            "The compliance rate is moderate, indicating room for improvement. "
            "Targeted safety briefings in high-violation zones are recommended."
        )
    else:
        assessment = (
            "The compliance rate is satisfactory, indicating generally good "
            "safety practices. Continue current monitoring and address "
            "remaining violations proactively."
        )

    paragraphs.append(assessment)

    return " ".join(paragraphs)
