"""Dataset loader for YOLOv8 PPE detection.

Validates the dataset is in YOLOv8 format and provides a clean interface
for the training and prediction modules to access dataset paths and
class names.

Usage:
    from backend.src.detection.dataset_loader import DatasetLoader
    loader = DatasetLoader()
    print(loader.data_yaml_path)
    print(loader.class_names)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Dataset root (data/ at repo root)
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


class DatasetLoader:
    """Loads and validates a YOLOv8-format dataset.

    Attributes:
        data_dir: Path to the dataset root (data/).
        data_yaml_path: Path to data/data.yaml.
        class_names: List of raw class names from data.yaml.
        num_classes: Number of classes.
        splits: Dict of split names to image/label directories.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize the dataset loader.

        Args:
            data_dir: Path to dataset root. Defaults to data/ at repo root.
        """
        self.data_dir = data_dir or DATA_DIR
        self.data_yaml_path = self.data_dir / "data.yaml"

        if not self.data_yaml_path.exists():
            raise FileNotFoundError(
                f"data.yaml not found at {self.data_yaml_path}. "
                "Run download_dataset first."
            )

        self._yaml_data: dict[str, Any] = self._load_yaml()
        self.class_names: list[str] = self._yaml_data.get("names", [])
        self.num_classes: int = self._yaml_data.get("nc", len(self.class_names))
        self.splits: dict[str, dict[str, Path]] = self._resolve_splits()

    def _load_yaml(self) -> dict[str, Any]:
        """Load and parse data.yaml.

        Returns:
            Parsed YAML dict.
        """
        with open(self.data_yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _resolve_splits(self) -> dict[str, dict[str, Path]]:
        """Resolve image and label directories for each split.

        Returns:
            Dict keyed by split name ('train', 'val', 'test'), each
            containing 'images' and 'labels' Path objects.
        """
        splits: dict[str, dict[str, Path]] = {}
        split_configs = {
            "train": self._yaml_data.get("train", "train/images"),
            "val": self._yaml_data.get("val", "valid/images"),
            "test": self._yaml_data.get("test", "test/images"),
        }

        for split_name, img_rel_path in split_configs.items():
            # Roboflow uses relative paths like ../train/images
            # Resolve relative to data.yaml location
            img_path = (self.data_dir / img_rel_path).resolve()
            # Try common directory name variations
            if not img_path.exists():
                # Try without the ../ prefix
                clean = img_rel_path.replace("../", "")
                img_path = (self.data_dir / clean).resolve()

            # Labels are in a parallel directory
            label_path = img_path.parent.parent / "labels" if "images" in str(img_path) else img_path

            splits[split_name] = {
                "images": img_path,
                "labels": label_path,
            }

        return splits

    def get_image_paths(self, split: str = "train") -> list[Path]:
        """Get all image file paths for a given split.

        Args:
            split: One of 'train', 'val', 'test'.

        Returns:
            List of Path objects for image files.
        """
        img_dir = self.splits.get(split, {}).get("images")
        if not img_dir or not img_dir.exists():
            return []
        return sorted(
            f for f in img_dir.iterdir()
            if f.suffix.lower() in (".jpg", ".jpeg", ".png")
        )

    def get_label_paths(self, split: str = "train") -> list[Path]:
        """Get all label file paths for a given split.

        Args:
            split: One of 'train', 'val', 'test'.

        Returns:
            List of Path objects for .txt label files.
        """
        label_dir = self.splits.get(split, {}).get("labels")
        if not label_dir or not label_dir.exists():
            return []
        return sorted(label_dir.glob("*.txt"))

    def validate(self) -> bool:
        """Validate that the dataset is complete and well-formed.

        Returns:
            True if all checks pass.
        """
        checks = []

        # data.yaml exists
        checks.append(self.data_yaml_path.exists())

        # At least one split has images
        has_images = any(
            len(self.get_image_paths(split)) > 0
            for split in self.splits
        )
        checks.append(has_images)

        # Class names are non-empty
        checks.append(len(self.class_names) > 0)

        return all(checks)

    def summary(self) -> str:
        """Return a human-readable summary of the dataset.

        Returns:
            Summary string.
        """
        lines = [
            f"Dataset root: {self.data_dir}",
            f"data.yaml: {self.data_yaml_path}",
            f"Classes ({self.num_classes}): {self.class_names}",
            "",
            "Splits:",
        ]
        for split_name in self.splits:
            img_count = len(self.get_image_paths(split_name))
            label_count = len(self.get_label_paths(split_name))
            lines.append(f"  {split_name:6s}: {img_count} images, {label_count} labels")
        return "\n".join(lines)


if __name__ == "__main__":
    loader = DatasetLoader()
    print(loader.summary())
    print(f"\nValid: {loader.validate()}")
