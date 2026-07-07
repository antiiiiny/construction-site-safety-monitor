"""Mapping from dataset labels to internal canonical class names.

The Roboflow PPE Detection dataset uses its own label set (e.g. 'hardhat',
'safety vest'). Internally, the rule engine and alert modules use canonical
names ('helmet', 'vest'). This module is the single source of truth for
that translation — detection results are normalized here before any
downstream processing.
"""

# Dataset label -> canonical name.
# Keys are lowercase dataset labels as they appear in data/data.yaml.
# Values are the canonical names used throughout the codebase.
CLASS_MAPPING: dict[str, str] = {
    # Persons
    "person": "person",
    "worker": "person",
    "people": "person",
    # Head protection
    "hardhat": "helmet",
    "hard-hat": "helmet",
    "helmet": "helmet",
    "head": "helmet",
    # High-visibility torso wear
    "safety vest": "vest",
    "safety-vest": "vest",
    "vest": "vest",
    "reflective-vest": "vest",
    # Hand protection
    "gloves": "gloves",
    "glove": "gloves",
    "hand": "gloves",
}

# Canonical classes the system understands. Anything not mapping to one of
# these is dropped during normalization.
CANONICAL_CLASSES: frozenset[str] = frozenset(
    {"person", "helmet", "vest", "gloves"}
)


def normalize_class_name(label: str) -> str | None:
    """Normalize a dataset label to its canonical name.

    Args:
        label: Raw class label from the dataset or model output.

    Returns:
        Canonical name ('person', 'helmet', 'vest', 'gloves') or None if
        the label is not recognized and should be dropped.
    """
    if label is None:
        return None
    key = label.strip().lower()
    canonical = CLASS_MAPPING.get(key)
    if canonical is None or canonical not in CANONICAL_CLASSES:
        return None
    return canonical
