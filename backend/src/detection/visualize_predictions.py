"""Draw model predictions on images for visual inspection.

Uses the trained Predictor to run inference on sample images, then draws
colored bounding boxes with class names and confidence scores. Saves
annotated images to artifacts/stage2_predictions/.

Usage:
    python -m backend.src.detection.visualize_predictions
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from backend.src.detection.predictor import Predictor

# Sample images directory
SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample_images"

# Output directory
OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "artifacts"
    / "stage2_predictions"
)

# Color mapping for canonical classes (RGB)
CLASS_COLORS: dict[str, tuple[int, int, int]] = {
    "person": (0, 165, 255),    # orange
    "helmet": (0, 255, 0),      # green
    "vest": (255, 0, 0),        # red
    "gloves": (255, 255, 0),    # yellow
}

# Default color for unknown classes
DEFAULT_COLOR = (128, 128, 128)  # gray


def draw_predictions(
    img_path: Path,
    detections: list[dict],
    output_path: Path,
) -> None:
    """Draw bounding boxes on an image and save the result.

    Args:
        img_path: Path to the source image.
        detections: List of detection dicts from Predictor.predict().
        output_path: Where to save the annotated image.
    """
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()

    for det in detections:
        class_name = det["class_name"]
        confidence = det["confidence"]
        x1, y1, x2, y2 = det["bbox"]

        color = CLASS_COLORS.get(class_name, DEFAULT_COLOR)

        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        # Label text
        label = f"{class_name} {confidence:.2f}"

        # Label background
        bbox = draw.textbbox((x1, y1 - 18), label, font=font)
        draw.rectangle(bbox, fill=color)
        draw.text((x1, y1 - 18), label, fill=(0, 0, 0), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path))


def visualize_predictions() -> None:
    """Run inference on all sample images and save annotated results."""
    if not SAMPLE_DIR.exists():
        print(f"ERROR: {SAMPLE_DIR} not found.")
        return

    image_files = sorted(
        f for f in SAMPLE_DIR.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    )

    if not image_files:
        print("ERROR: No sample images found.")
        return

    print("Loading model from settings...")
    try:
        predictor = Predictor()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Train the model first using scripts/colab_train_yolov8.py")
        return

    print(f"Running inference on {len(image_files)} sample images...")
    print(f"Output: {OUTPUT_DIR}")
    print("-" * 50)

    total_detections = 0
    for i, img_path in enumerate(image_files):
        detections = predictor.predict(img_path)
        total_detections += len(detections)

        output_path = OUTPUT_DIR / f"pred_{img_path.name}"
        draw_predictions(img_path, detections, output_path)

        det_summary = ", ".join(
            f"{d['class_name']}({d['confidence']:.2f})" for d in detections
        )
        print(f"  [{i + 1}/{len(image_files)}] {img_path.name} — {len(detections)} dets: {det_summary}")

    print("-" * 50)
    print(f"Done. {len(image_files)} images saved to {OUTPUT_DIR}")
    print(f"Total detections: {total_detections}")


if __name__ == "__main__":
    visualize_predictions()
