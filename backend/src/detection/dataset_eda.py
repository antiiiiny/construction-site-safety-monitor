"""Exploratory Data Analysis (EDA) for the PPE detection dataset.

Reports:
  - Image counts per split (train/val/test)
  - Class counts and distribution
  - Image resolution range
  - Corrupt file check

Usage:
    python -m backend.src.detection.dataset_eda
"""

from __future__ import annotations

import collections
from pathlib import Path

from PIL import Image

from backend.config.class_mapping import CANONICAL_CLASSES, normalize_class_name

# Dataset root (data/ at repo root)
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Splits to analyze
SPLITS = ["train", "valid", "test"]


def parse_data_yaml(yaml_path: Path) -> dict[str, any]:
    """Parse the data.yaml file to get class names and paths.

    Args:
        yaml_path: Path to data/data.yaml.

    Returns:
        Dict with 'names' (list of class names), 'nc' (class count),
        and split paths.
    """
    import yaml

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def count_images(split: str) -> int:
    """Count image files in a split's image directory.

    Args:
        split: One of 'train', 'valid', 'test'.

    Returns:
        Number of image files (.jpg, .png).
    """
    img_dir = DATA_DIR / split / "images"
    if not img_dir.exists():
        return 0
    count = 0
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        count += len(list(img_dir.glob(ext)))
    return count


def count_labels(split: str) -> int:
    """Count label files in a split's label directory.

    Args:
        split: One of 'train', 'valid', 'test'.

    Returns:
        Number of label files (.txt).
    """
    label_dir = DATA_DIR / split / "labels"
    if not label_dir.exists():
        return 0
    return len(list(label_dir.glob("*.txt")))


def get_class_distribution(yaml_data: dict[str, any]) -> dict[str, dict[str, int]]:
    """Count label instances per class across all splits.

    Args:
        yaml_data: Parsed data.yaml dict with 'names' list.

    Returns:
        Dict keyed by split name, each containing a dict of
        {class_name: instance_count}.
    """
    class_names = yaml_data.get("names", [])
    distribution: dict[str, dict[str, int]] = {}

    for split in SPLITS:
        label_dir = DATA_DIR / split / "labels"
        split_counts: dict[str, int] = collections.defaultdict(int)

        if not label_dir.exists():
            distribution[split] = dict(split_counts)
            continue

        for label_file in label_dir.glob("*.txt"):
            with open(label_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # YOLO format: class_id x_center y_center width height
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    try:
                        class_id = int(parts[0])
                    except ValueError:
                        continue
                    if 0 <= class_id < len(class_names):
                        raw_name = class_names[class_id]
                        split_counts[raw_name] += 1

        distribution[split] = dict(split_counts)

    return distribution


def get_canonical_distribution(
    yaml_data: dict[str, any],
) -> dict[str, dict[str, int]]:
    """Count label instances per canonical class (after mapping).

    Args:
        yaml_data: Parsed data.yaml dict with 'names' list.

    Returns:
        Dict keyed by split, each containing {canonical_name: count}.
    """
    class_names = yaml_data.get("names", [])
    distribution: dict[str, dict[str, int]] = {}

    for split in SPLITS:
        label_dir = DATA_DIR / split / "labels"
        split_counts: dict[str, int] = collections.defaultdict(int)

        if not label_dir.exists():
            distribution[split] = dict(split_counts)
            continue

        for label_file in label_dir.glob("*.txt"):
            with open(label_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    try:
                        class_id = int(parts[0])
                    except ValueError:
                        continue
                    if 0 <= class_id < len(class_names):
                        raw_name = class_names[class_id]
                        canonical = normalize_class_name(raw_name)
                        if canonical is not None:
                            split_counts[canonical] += 1

        distribution[split] = dict(split_counts)

    return distribution


def get_resolution_range() -> dict[str, tuple[int, int]]:
    """Get min/max width and height across all images.

    Returns:
        Dict with 'width_range' and 'height_range' tuples.
    """
    widths: list[int] = []
    heights: list[int] = []

    for split in SPLITS:
        img_dir = DATA_DIR / split / "images"
        if not img_dir.exists():
            continue
        for img_file in img_dir.iterdir():
            if img_file.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            try:
                with Image.open(img_file) as img:
                    widths.append(img.width)
                    heights.append(img.height)
            except Exception:
                continue

    if not widths:
        return {"width_range": (0, 0), "height_range": (0, 0)}

    return {
        "width_range": (min(widths), max(widths)),
        "height_range": (min(heights), max(heights)),
    }


def check_corrupt_files() -> list[str]:
    """Check for corrupt/unreadable image files.

    Returns:
        List of file paths that failed to open.
    """
    corrupt: list[str] = []

    for split in SPLITS:
        img_dir = DATA_DIR / split / "images"
        if not img_dir.exists():
            continue
        for img_file in img_dir.iterdir():
            if img_file.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            try:
                with Image.open(img_file) as img:
                    img.verify()
            except Exception:
                corrupt.append(str(img_file))

    return corrupt


def run_eda() -> None:
    """Run the full EDA and print a summary report."""
    yaml_path = DATA_DIR / "data.yaml"
    if not yaml_path.exists():
        print(f"ERROR: {yaml_path} not found. Run download_dataset first.")
        return

    print("=" * 60)
    print("  Construction Site Safety — Dataset EDA")
    print("=" * 60)

    # Parse data.yaml
    yaml_data = parse_data_yaml(yaml_path)
    class_names = yaml_data.get("names", [])
    print(f"\nDataset: {yaml_data.get('roboflow', {}).get('project', 'unknown')}")
    print(f"Version: {yaml_data.get('roboflow', {}).get('version', '?')}")
    print(f"License: {yaml_data.get('roboflow', {}).get('license', '?')}")
    print(f"Total classes in dataset: {len(class_names)}")
    print(f"Class names: {class_names}")

    # Image and label counts
    print("\n--- Image & Label Counts ---")
    total_images = 0
    for split in SPLITS:
        img_count = count_images(split)
        label_count = count_labels(split)
        total_images += img_count
        print(f"  {split:6s}: {img_count:4d} images, {label_count:4d} labels")
    print(f"  {'total':6s}: {total_images:4d} images")

    # Raw class distribution
    print("\n--- Raw Class Distribution (all dataset labels) ---")
    raw_dist = get_class_distribution(yaml_data)
    all_classes: set[str] = set()
    for split_counts in raw_dist.values():
        all_classes.update(split_counts.keys())
    for cls in sorted(all_classes):
        counts = [raw_dist.get(s, {}).get(cls, 0) for s in SPLITS]
        total = sum(counts)
        print(f"  {cls:20s}: {counts[0]:4d} / {counts[1]:4d} / {counts[2]:4d}  (total: {total})")

    # Canonical class distribution (after mapping)
    print("\n--- Canonical Class Distribution (after mapping) ---")
    print(f"  Canonical classes: {sorted(CANONICAL_CLASSES)}")
    canon_dist = get_canonical_distribution(yaml_data)
    for cls in sorted(CANONICAL_CLASSES):
        counts = [canon_dist.get(s, {}).get(cls, 0) for s in SPLITS]
        total = sum(counts)
        print(f"  {cls:20s}: {counts[0]:4d} / {counts[1]:4d} / {counts[2]:4d}  (total: {total})")

    # Resolution range
    print("\n--- Image Resolution Range ---")
    res = get_resolution_range()
    print(f"  Width:  {res['width_range'][0]} - {res['width_range'][1]} px")
    print(f"  Height: {res['height_range'][0]} - {res['height_range'][1]} px")

    # Corrupt files
    print("\n--- Corrupt File Check ---")
    corrupt = check_corrupt_files()
    if corrupt:
        print(f"  WARNING: {len(corrupt)} corrupt files found:")
        for f in corrupt[:10]:
            print(f"    {f}")
    else:
        print("  No corrupt files found. All images open correctly.")

    # Balance assessment
    print("\n--- Balance Assessment ---")
    canon_totals = {
        cls: sum(canon_dist.get(s, {}).get(cls, 0) for s in SPLITS)
        for cls in CANONICAL_CLASSES
    }
    if canon_totals:
        max_count = max(canon_totals.values())
        min_count = min(canon_totals.values())
        if min_count == 0:
            print("  WARNING: One or more canonical classes have 0 instances!")
        elif max_count / min_count > 3:
            print(f"  IMBALANCED: max/min ratio = {max_count / min_count:.1f}")
            print("  (ratio > 3 indicates significant class imbalance)")
        else:
            print(f"  Reasonably balanced: max/min ratio = {max_count / min_count:.1f}")
        for cls, count in sorted(canon_totals.items(), key=lambda x: -x[1]):
            print(f"    {cls}: {count}")

    print("\n" + "=" * 60)
    print("  EDA complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_eda()
