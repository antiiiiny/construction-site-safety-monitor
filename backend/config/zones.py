"""Zone definitions for the construction site safety monitor.

Each zone represents a fixed camera location on a construction site with
specific PPE requirements. Zone rules are config-driven — detection and
alert modules read from this file, never hardcode zone data.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
    """A single camera zone on the construction site."""

    zone_id: int
    name: str
    required_ppe: list[str]
    hazard_description: str


# Canonical PPE classes detectable by the model.
# NOTE: harness and boots are intentionally omitted — most public PPE
# datasets (including the pinned Roboflow set) do not label them, so
# requiring them would produce false violations on every person.
ZONES: list[Zone] = [
    Zone(
        zone_id=1,
        name="Entry Gate",
        required_ppe=["helmet", "vest"],
        hazard_description="General entry point — high foot traffic, vehicle movement.",
    ),
    Zone(
        zone_id=2,
        name="Scaffold Zone",
        required_ppe=["helmet", "vest"],
        hazard_description="Elevated work area — fall risk, falling objects.",
    ),
    Zone(
        zone_id=3,
        name="Welding Zone",
        required_ppe=["helmet", "gloves", "vest"],
        hazard_description="Hot work — UV/IR radiation, sparks, burn risk.",
    ),
    Zone(
        zone_id=4,
        name="Concrete Zone",
        required_ppe=["helmet", "vest"],
        hazard_description="Pouring and curing — chemical burns, heavy loads.",
    ),
    Zone(
        zone_id=5,
        name="Loading Zone",
        required_ppe=["helmet", "vest"],
        hazard_description="Vehicle and crane activity — crush risk, swinging loads.",
    ),
    Zone(
        zone_id=6,
        name="Material Yard",
        required_ppe=["helmet", "vest"],
        hazard_description="Storage and handling — stacking hazards, manual handling.",
    ),
]


def get_zone(zone_id: int) -> Zone:
    """Return the zone config for a given zone_id.

    Args:
        zone_id: Integer zone identifier (1-6).

    Returns:
        Zone dataclass for the requested zone.

    Raises:
        ValueError: If zone_id is not in 1..6.
    """
    for zone in ZONES:
        if zone.zone_id == zone_id:
            return zone
    raise ValueError(f"Unknown zone_id: {zone_id}. Valid range is 1-{len(ZONES)}.")
