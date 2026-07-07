"""Zone configuration loader for the rule engine.

Provides a clean interface for the violation engine to access zone
definitions without importing config directly.

Usage:
    from backend.src.rules.zone_config import get_zone, get_all_zones
    zone = get_zone(3)  # Welding Zone
    print(zone.required_ppe)  # ['helmet', 'gloves', 'vest']
"""

from __future__ import annotations

from backend.config.zones import ZONES, Zone


def get_zone(zone_id: int) -> Zone:
    """Get the zone configuration for a given zone ID.

    Args:
        zone_id: Integer zone identifier (1-6).

    Returns:
        Zone dataclass with name, required_ppe, and hazard_description.

    Raises:
        ValueError: If zone_id is not in the valid range.
    """
    for zone in ZONES:
        if zone.zone_id == zone_id:
            return zone
    raise ValueError(
        f"Unknown zone_id: {zone_id}. Valid range is 1-{len(ZONES)}."
    )


def get_all_zones() -> list[Zone]:
    """Get all zone configurations.

    Returns:
        List of all Zone dataclasses.
    """
    return list(ZONES)


def get_required_ppe(zone_id: int) -> list[str]:
    """Get the list of required PPE items for a zone.

    Args:
        zone_id: Integer zone identifier (1-6).

    Returns:
        List of canonical PPE names required in this zone.
    """
    return get_zone(zone_id).required_ppe
