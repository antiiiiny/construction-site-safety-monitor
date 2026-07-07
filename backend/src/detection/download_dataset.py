"""Download the Construction Site Safety dataset from Roboflow.

Pinned dataset:
  https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety

Downloads in YOLOv8 format into data/ with the standard split structure:
  data/images/{train,val,test}/
  data/labels/{train,val,test}/
  data/data.yaml

Usage:
    python -m backend.src.detection.download_dataset

The Roboflow API key is read from .env via settings — never hardcoded.
"""

from __future__ import annotations

import sys
from pathlib import Path

from backend.config.settings import settings

# Roboflow dataset identifiers (from the universe URL)
WORKSPACE = "roboflow-universe-projects"
PROJECT = "construction-site-safety"

# We'll try version 1 first; the user can override if needed.
# The Roboflow API will tell us the latest version if this fails.
VERSION = 1

# Output directory (relative to repo root)
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def download_dataset() -> None:
    """Download the pinned Roboflow dataset in YOLOv8 format.

    Raises:
        RuntimeError: If the API key is missing or the download fails.
    """
    if not settings.roboflow_configured:
        print(
            "ERROR: ROBOFLOW_API_KEY is not set in .env.\n"
            "Get one at https://app.roboflow.com/settings → API Key\n"
            "Then add it to your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Import here so the module loads even without roboflow installed
    # (e.g. in CI that doesn't need dataset download)
    from roboflow import Roboflow

    print(f"Downloading dataset: {WORKSPACE}/{PROJECT} v{VERSION}")
    print(f"Output directory: {DATA_DIR}")
    print("Format: yolov8")
    print("-" * 50)

    # Ensure the data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    rf = Roboflow(api_key=settings.roboflow_api_key)
    workspace = rf.workspace(WORKSPACE)
    project = workspace.project(PROJECT)
    version = project.version(VERSION)

    # Download to a temporary location first, then we know where it is
    import shutil
    import tempfile
    import zipfile

    with tempfile.TemporaryDirectory() as tmpdir:
        version.download(
            model_format="yolov8",
            location=tmpdir,
        )

        # Find the downloaded zip file
        zip_files = list(Path(tmpdir).rglob("*.zip"))
        if zip_files:
            print(f"Found zip: {zip_files[0]}")
            with zipfile.ZipFile(zip_files[0], "r") as zf:
                zf.extractall(str(DATA_DIR))
        else:
            # If no zip, the SDK may have extracted directly
            # Copy everything from tmpdir to DATA_DIR
            for item in Path(tmpdir).rglob("*"):
                if item.is_file():
                    rel = item.relative_to(tmpdir)
                    dest = DATA_DIR / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)

    print("-" * 50)
    print(f"Dataset downloaded to {DATA_DIR}")

    # Verify data.yaml exists
    yaml_path = DATA_DIR / "data.yaml"
    if yaml_path.exists():
        print(f"data.yaml found at {yaml_path}")
    else:
        print("WARNING: data.yaml not found. Check the data/ directory.")

    # Count files
    image_count = len(list(DATA_DIR.rglob("*.jpg"))) + len(list(DATA_DIR.rglob("*.png")))
    label_count = len(list(DATA_DIR.rglob("*.txt")))
    print(f"Images found: {image_count}")
    print(f"Labels found: {label_count}")
    print("Verify with: python -m backend.src.detection.dataset_eda")


if __name__ == "__main__":
    download_dataset()
