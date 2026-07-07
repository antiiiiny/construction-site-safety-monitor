"""Draw bounding boxes on sample dataset images for visual inspection.

Reads YOLO-format labels and draws colored bboxes on 5 sample images
from the training set. Saves annotated images to artifacts/stage1_eda/.

Usage:
    python -m backend.src.detection.visualize_samples
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from backend.config.class_mapping import normalize_class_name

# Dataset root
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Output directory for annotated samples
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "artifacts" / "stage1_eda"

# Number of sample images to annotate
NUM_SAMPLES = 5

# Color mapping for canonical classes (RGB)
CLASS_COLORS: dict[str, tuple[int, int, int]] = {
    "person": (0, 165, 255),    # orange
    "helmet": (0, 255, 0),      # green
    "vest": (255, 0, 0),        # red
    "gloves": (255, 255, 0),    # yellow
}

# Color for non-canonical (dropped) classes
DROPPED_COLOR = (128, 128, 128)  # gray


def parse_label_file(label_path: Path, img_width: int, img_height: int) -> list[dict]:
    """Parse a YOLO-format label file and convert to pixel coordinates.

    Args:
        label_path: Path to the .txt label file.
        img_width: Image width in pixels.
        img_height: Image height in pixels.

    Returns:
        List of dicts with keys: class_name, canonical, x1, y1, x2, y2.
    """
    import yaml

    yaml_path = DATA_DIR / "data.yaml"
    with open(yaml_path, encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)
    class_names = yaml_data.get("names", [])

    boxes: list[dict] = []
    with open(label_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
            except (ValueError, IndexError):
                continue

            if not (0 <= class_id < len(class_names)):
                continue

            raw_name = class_names[class_id]
            canonical = normalize_class_name(raw_name)

            # Convert YOLO normalized coords to pixel coords
            x1 = int((x_center - width / 2) * img_width)
            y1 = int((y_center - height / 2) * img_height)
            x2 = int((x_center + width / 2) * img_width)
            y2 = int((y_center + height / 2) * img_height)

            boxes.append({
                "class_name": raw_name,
                "canonical": canonical,
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            })

    return boxes


def draw_boxes_on_image(
    img_path: Path,
    label_path: Path,
    output_path: Path,
) -> int:
    """Draw bounding boxes on an image and save the result.

    Args:
        img_path: Path to the source image.
        label_path: Path to the YOLO label file.
        output_path: Where to save the annotated image.

    Returns:
        Number of boxes drawn.
    """
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    boxes = parse_label_file(label_path, img.width, img.height)

    for box in boxes:
        canonical = box["canonical"]
        color = CLASS_COLORS.get(canonical, DROPPED_COLOR) if canonical else DROPPED_COLOR
        x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]

        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        # Draw label
        label_text = box["class_name"]
        if canonical:
            label_text += f" → {canonical}"
        else:
            label_text += " (dropped)"

        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            font = ImageFont.load_default()

        # Draw label background
        bbox = draw.textbbox((x1, y1 - 18), label_text, font=font)
        draw.rectangle(bbox, fill=color)
        draw.text((x1, y1 - 18), label_text, fill=(0, 0, 0), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path))
    return len(boxes)


def visualize_samples() -> None:
    """Select 5 random training images and draw their annotations."""
    train_img_dir = DATA_DIR / "train" / "images"
    train_label_dir = DATA_DIR / "train" / "labels"

    if not train_img_dir.exists():
        print(f"ERROR: {train_img_dir} not found. Run download_dataset first.")
        return

    # Get all image files
    image_files = sorted(
        f for f in train_img_dir.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    )

    if len(image_files) == 0:
        print("ERROR: No training images found.")
        return

    # Select random samples (seeded for reproducibility)
    random.seed(42)
    sample_size = min(NUM_SAMPLES, len(image_files))
    samples = random.sample(image_files, sample_size)

    print(f"Visualizing {sample_size} sample images...")
    print(f"Output: {OUTPUT_DIR}")
    print("-" * 50)

    total_boxes = 0
    for i, img_path in enumerate(samples):
        label_path = train_label_dir / (img_path.stem + ".txt")
        output_path = OUTPUT_DIR / f"sample_{i + 1}_{img_path.name}"

        if label_path.exists():
            num_boxes = draw_boxes_on_image(img_path, label_path, output_path)
            total_boxes += num_boxes
            print(f"  [{i + 1}/{sample_size}] {img_path.name} — {num_boxes} boxes → {output_path.name}")
        else:
            # No labels — just copy the image
            from PIL import Image as PILImage
            img = PILImage.open(img_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(output_path))
            print(f"  [{i + 1}/{sample_size}] {img_path.name} — no labels → {output_path.name}")

    print("-" * 50)
    print(f"Done. {sample_size} images saved to {OUTPUT_DIR}")
    print(f"Total boxes drawn: {total_boxes}")


if __name__ == "__main__":
    visualize_samples()
