"""Pattern-based recommendations generator for PDF reports.

Generates actionable safety recommendations based on violation patterns
in the event log.

Usage:
    from backend.src.reporting.recommendations import generate_recommendations
    recs = generate_recommendations(metrics)
"""

from __future__ import annotations

from typing import Any

from backend.src.rules.zone_config import get_zone


def generate_recommendations(metrics: dict[str, Any]) -> list[str]:
    """Generate actionable safety recommendations from metrics.

    Args:
        metrics: Summary dict from EventLogger.get_summary().

    Returns:
        List of recommendation strings.
    """
    recommendations: list[str] = []

    total_scans = metrics.get("total_scans", 0)
    total_violations = metrics.get("total_violations", 0)
    compliance_rate = metrics.get("compliance_rate", 1.0)
    most_unsafe_zone_id = metrics.get("most_unsafe_zone")
    violations_per_zone = metrics.get("violations_per_zone", {})
    violations_per_ppe = metrics.get("violations_per_ppe", {})

    # No data
    if total_scans == 0:
        return [
            "Activate the safety monitoring system before the next shift.",
            "Ensure all 6 camera zones are operational and positioned correctly.",
        ]

    # No violations
    if total_violations == 0:
        return [
            "Maintain current safety standards — zero violations detected.",
            "Continue regular monitoring and safety briefings.",
        ]

    # Compliance rate recommendations
    if compliance_rate < 0.7:
        recommendations.append(
            "URGENT: Compliance rate is below 70%. Conduct an immediate "
            "site-wide safety review and halt non-essential work in "
            "high-violation zones until compliance improves."
        )
    elif compliance_rate < 0.9:
        recommendations.append(
            "Conduct targeted safety briefings in zones with the highest "
            "violation rates to improve overall compliance."
        )

    # Most unsafe zone
    if most_unsafe_zone_id is not None:
        try:
            zone_name = get_zone(most_unsafe_zone_id).name
            count = violations_per_zone.get(most_unsafe_zone_id, 0)
            recommendations.append(
                f"Increase monitoring frequency in {zone_name} — "
                f"it has the most violations ({count} detected). "
                f"Consider assigning additional safety personnel to this area."
            )
        except ValueError:
            pass

    # Most common missing PPE
    if violations_per_ppe:
        most_common_ppe = max(violations_per_ppe, key=violations_per_ppe.get)
        most_common_count = violations_per_ppe[most_common_ppe]
        ppe_display = {
            "helmet": "hard hats",
            "vest": "safety vests",
            "gloves": "safety gloves",
        }.get(most_common_ppe, most_common_ppe)

        recommendations.append(
            f"Conduct a {ppe_display} compliance briefing — "
            f"{most_common_ppe} violations are the most common "
            f"({most_common_count} incidents). "
            f"Ensure adequate PPE supply at all site entry points."
        )

    # High severity violations
    severity_breakdown = metrics.get("severity_breakdown", {})
    high_count = severity_breakdown.get("high", 0)
    if high_count > 0:
        recommendations.append(
            f"Address {high_count} high-severity violations immediately. "
            f"These occurred in high-risk zones and require urgent corrective action."
        )

    # Multiple zones with violations
    zones_with_violations = len(violations_per_zone)
    if zones_with_violations >= 4:
        recommendations.append(
            f"Violations are spread across {zones_with_violations} zones, "
            f"indicating a systemic compliance issue. Consider a site-wide "
            f"safety stand-down meeting to reinforce PPE requirements."
        )

    # General recommendation
    recommendations.append(
        "Continue regular safety monitoring and update this report daily "
        "to track compliance trends over time."
    )

    return recommendations
