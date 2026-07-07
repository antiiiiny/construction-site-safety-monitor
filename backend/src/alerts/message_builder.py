"""Build natural-language alert messages for PPE violations.

Messages vary by severity and zone, naming the zone and the missing PPE
items in a clear, professional tone suitable for a construction site.

Usage:
    from backend.src.alerts.message_builder import build_alert_message
    from backend.src.rules.models import Violation
    msg = build_alert_message(violation)
    # "Warning, Welding Zone. Safety gloves and helmet are required. This is a high-risk area."
"""

from __future__ import annotations

from backend.src.rules.models import Violation

# Human-readable PPE names for message construction.
# Canonical name -> display name in alerts.
PPE_DISPLAY_NAMES: dict[str, str] = {
    "helmet": "hard hat",
    "vest": "safety vest",
    "gloves": "safety gloves",
}


def _format_ppe_list(ppe_items: list[str]) -> str:
    """Format a list of PPE items into a natural-language phrase.

    Examples:
        ["helmet"] -> "hard hat"
        ["helmet", "vest"] -> "hard hat and safety vest"
        ["helmet", "vest", "gloves"] -> "hard hat, safety vest, and safety gloves"

    Args:
        ppe_items: List of canonical PPE names.

    Returns:
        Formatted string for use in alert messages.
    """
    display = [PPE_DISPLAY_NAMES.get(ppe, ppe) for ppe in ppe_items]

    if len(display) == 1:
        return display[0]
    if len(display) == 2:
        return f"{display[0]} and {display[1]}"
    # 3+ items: Oxford comma
    return ", ".join(display[:-1]) + f", and {display[-1]}"


def build_alert_message(violation: Violation) -> str:
    """Build a natural-language alert message for a violation.

    The message varies by severity:
      - high: "Warning, {zone}. {ppe} are required. This is a high-risk area."
      - medium: "Attention, {zone}. {ppe} required."
      - low: "Notice, {zone}. {ppe} recommended."

    Args:
        violation: The Violation object to build a message for.

    Returns:
        Alert message string.
    """
    zone_name = violation.zone_name
    ppe_phrase = _format_ppe_list(violation.missing_ppe)
    severity = violation.severity

    if severity == "high":
        verb = "is" if len(violation.missing_ppe) == 1 else "are"
        return (
            f"Warning, {zone_name}. {ppe_phrase.capitalize()} {verb} required. "
            f"This is a high-risk area."
        )
    if severity == "medium":
        verb = "is" if len(violation.missing_ppe) == 1 else "are"
        return f"Attention, {zone_name}. {ppe_phrase.capitalize()} {verb} required."
    # low
    return f"Notice, {zone_name}. {ppe_phrase.capitalize()} recommended."


def build_scan_summary_message(
    zone_name: str,
    violations: list[Violation],
) -> str:
    """Build a summary message for an entire scan (multiple violations).

    If there's only one violation, returns the single alert message.
    If multiple, returns a summary mentioning the count.

    Args:
        zone_name: Name of the zone scanned.
        violations: List of Violation objects from the scan.

    Returns:
        Summary message string. Empty string if no violations.
    """
    if not violations:
        return ""

    if len(violations) == 1:
        return build_alert_message(violations[0])

    all_missing: set[str] = set()
    for v in violations:
        all_missing.update(v.missing_ppe)

    ppe_phrase = _format_ppe_list(sorted(all_missing))
    max_severity = max(
        (v.severity for v in violations),
        key=lambda s: {"high": 3, "medium": 2, "low": 1}.get(s, 0),
    )

    if max_severity == "high":
        return (
            f"Warning, {zone_name}. {len(violations)} workers require attention. "
            f"Missing: {ppe_phrase}. This is a high-risk area."
        )
    return (
        f"Attention, {zone_name}. {len(violations)} workers require attention. "
        f"Missing: {ppe_phrase}."
    )
