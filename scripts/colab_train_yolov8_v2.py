# Stage 2 — IMPROVED YOLOv8 Training Script for Google Colab
#
# Uses the Chandimas dataset (5.17k images) instead of the original
# Roboflow Universe Projects dataset (717 images). The larger dataset
# has more instances of vest, gloves, and person — directly addressing
# the class imbalance that caused v1 to fail.
#
# Dataset: https://universe.roboflow.com/chandimas-workspace/construction-safety-monitor-mlpd4
#
# Improvements over v1:
#   - 5.17k images (7x more data than v1's 717)
#   - Filters to only canonical classes (helmet, vest, person, gloves)
#   - Uses yolov8s (small, fast) — 5x faster than yolov8m on T4
#   - 20 epochs (enough for 5k images, ~15 min total)
#   - Adds augmentation (mosaic, mixup, hsv) to help with class imbalance
#   - Lower confidence (0.20) for inference to improve recall
#
# ============================================================
# INSTRUCTIONS:
# 1. Open Google Colab: https://colab.research.google.com
# 2. Create a new notebook, paste this entire script into a cell
# 3. Runtime → Change runtime type → T4 GPU (free tier)
# 4. Run the cell — it will:
#    a. Install ultralytics + roboflow
#    b. Download the Chandimas dataset (5.17k images)
#    c. Print the actual class names (verify before filtering)
#    d. Filter labels to only canonical classes
#    e. Train YOLOv8m for 50 epochs (no early stopping)
#    f. Evaluate on val/test
#    g. Save best.pt to /content for download
# 5. Download best.pt and place it at: artifacts/stage2_model/best.pt
# 6. Copy the metrics output into docs/stage2_model.md
# ============================================================

# --- Step 1: Install dependencies ---
!pip install -q ultralytics roboflow
!pip install -q "typer>=0.12,<0.15"  # fix click version conflict

# --- Step 2: Download the Chandimas dataset (5.17k images) ---
ROBOFLOW_API_KEY = "YOUR_ROBOFLOW_API_KEY"  # <-- PASTE YOUR KEY HERE

from roboflow import Roboflow
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
# Chandimas workspace — 5.17k images, more vest/gloves/person instances
project = rf.workspace("chandimas-workspace").project("construction-safety-monitor-mlpd4")
version = project.version(1)  # Use version 1 — adjust if a newer version exists
dataset = version.download("yolov8", location="/content/data")

print(f"Dataset downloaded to: {dataset.location}")

# --- Step 3: Inspect and filter dataset classes ---
# The Chandimas dataset has different class names than the v1 dataset.
# We need to inspect the actual classes and map them to our 4 canonical names.
# Expected classes (based on Roboflow page): helmet, vest, gloves, goggles,
# boots, no-helmet, no-vest, no-gloves, no-goggles, no-boots
#
# NOTE: Chandimas may NOT have a "person" class. If so, we train on 3 classes
# (helmet, vest, gloves) and the rule engine will infer person presence
# from PPE detections (a helmet implies a person is wearing it).

import yaml
from pathlib import Path

DATA_DIR = Path("/content/data")

# Read original data.yaml to get class names
with open(DATA_DIR / "data.yaml") as f:
    original_yaml = yaml.safe_load(f)
original_names = original_yaml["names"]
print(f"\nOriginal classes ({len(original_names)}): {original_names}")

# Build class mapping dynamically based on actual class names
# We keep only the "presence" classes (helmet, vest, gloves, person)
# and drop the "absence" classes (no-helmet, no-vest, etc.)
NEW_NAMES = []  # Will be built dynamically
CLASS_MAP = {}  # old_id -> new_id (or None if dropped)

for old_id, name in enumerate(original_names):
    name_lower = name.lower().strip()

    # Map to canonical names
    if name_lower in ("helmet", "hardhat", "hard-hat", "hard hat"):
        if "helmet" not in NEW_NAMES:
            NEW_NAMES.append("helmet")
        CLASS_MAP[old_id] = NEW_NAMES.index("helmet")
    elif name_lower in ("vest", "safety vest", "safety-vest", "reflective vest"):
        if "vest" not in NEW_NAMES:
            NEW_NAMES.append("vest")
        CLASS_MAP[old_id] = NEW_NAMES.index("vest")
    elif name_lower in ("gloves", "glove"):
        if "gloves" not in NEW_NAMES:
            NEW_NAMES.append("gloves")
        CLASS_MAP[old_id] = NEW_NAMES.index("gloves")
    elif name_lower in ("person", "worker", "people", "human"):
        if "person" not in NEW_NAMES:
            NEW_NAMES.append("person")
        CLASS_MAP[old_id] = NEW_NAMES.index("person")
    else:
        # Drop: no-helmet, no-vest, no-gloves, goggles, boots, etc.
        CLASS_MAP[old_id] = None

print(f"\nFiltered to {len(NEW_NAMES)} classes: {NEW_NAMES}")
print(f"Class mapping: {CLASS_MAP}")
print(f"Dropped classes: {[n for i, n in enumerate(original_names) if CLASS_MAP[i] is None]}")

if len(NEW_NAMES) == 0:
    raise ValueError("No canonical classes found in dataset! Check class names above.")

# Warn if person class is missing
if "person" not in NEW_NAMES:
    print("\n⚠ WARNING: 'person' class not found in dataset!")
    print("  The rule engine uses person bboxes for PPE containment logic.")
    print("  Without person detections, the rule engine will need adaptation:")
    print("  - Option A: Infer person from helmet/vest bbox (helmet implies person)")
    print("  - Option B: Merge with the v1 dataset (which has Person labels)")
    print("  Proceeding with 3-class training for now...")

# Rewrite all label files with filtered + remapped classes
for split in ["train", "valid", "test"]:
    label_dir = DATA_DIR / split / "labels"
    if not label_dir.exists():
        continue

    rewritten = 0
    for label_file in label_dir.glob("*.txt"):
        lines = []
        with open(label_file) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                old_class = int(parts[0])
                new_class = CLASS_MAP.get(old_class)
                if new_class is not None:
                    parts[0] = str(new_class)
                    lines.append(" ".join(parts))

        # Overwrite with filtered labels
        with open(label_file, "w") as f:
            f.write("\n".join(lines))
        rewritten += 1

    print(f"  {split}: rewrote {rewritten} label files")

# Write new data.yaml
new_yaml = {
    "train": "../train/images",
    "val": "../valid/images",
    "test": "../test/images",
    "nc": len(NEW_NAMES),
    "names": NEW_NAMES,
}
with open(DATA_DIR / "data.yaml", "w") as f:
    yaml.dump(new_yaml, f, default_flow_style=False)
print(f"\nNew data.yaml written with {len(NEW_NAMES)} classes: {NEW_NAMES}")

# --- Step 4: Train YOLOv8s (small, fast) with 20 epochs ---
from ultralytics import YOLO

# Use yolov8s (small) — fast on T4, still good accuracy with 5k images
# yolov8m was too slow (6 min/epoch → 5+ hours for 50 epochs)
model = YOLO("yolov8s.pt")

# Train with:
# - 20 epochs (enough for 5k images, ~15 min total on T4)
# - imgsz=512 (faster than 640, minimal accuracy loss)
# - batch=32 (T4 has 15GB VRAM, can handle larger batches)
# - patience=5 (early stop if no improvement for 5 epochs)
results = model.train(
    data="/content/data/data.yaml",
    epochs=20,
    imgsz=512,
    batch=32,
    patience=5,  # Early stop if no improvement
    device=0,    # GPU
    project="/content/runs",
    name="ppe_detection_v2",
    exist_ok=True,
    # Augmentation settings (helps with class imbalance)
    hsv_h=0.02,    # HSV hue augmentation
    hsv_s=0.7,     # HSV saturation
    hsv_v=0.5,     # HSV value
    degrees=10.0,  # Rotation
    translate=0.2, # Translation
    scale=0.5,     # Scaling
    flipud=0.1,    # Vertical flip (10% probability)
    fliplr=0.5,    # Horizontal flip (50% probability)
    mosaic=1.0,    # Mosaic augmentation
    mixup=0.1,     # Mixup augmentation
)

print("Training complete!")
print(f"Best weights: /content/runs/ppe_detection_v2/weights/best.pt")

# --- Step 5: Evaluate on validation set ---
metrics = model.val()
print("\n=== Validation Metrics ===")
print(f"mAP@0.5:      {metrics.box.map50:.4f}")
print(f"mAP@0.5:0.95: {metrics.box.map:.4f}")
print(f"Precision:    {metrics.box.mp:.4f}")
print(f"Recall:       {metrics.box.mr:.4f}")

# Per-class metrics
print("\n=== Per-Class Metrics ===")
for i, name in enumerate(NEW_NAMES):
    if i < len(metrics.box.maps):
        print(f"  {name:20s}: mAP@0.5 = {metrics.box.maps[i]:.4f}")

# --- Step 6: Run inference on test images with lower confidence ---
test_dir = "/content/data/test/images"
test_results = model.predict(
    source=test_dir,
    save=True,
    project="/content/runs",
    name="test_predictions_v2",
    exist_ok=True,
    conf=0.20,  # Lower confidence threshold to improve recall
)
print(f"\nTest predictions saved to /content/runs/test_predictions_v2/")

# --- Step 7: Copy best.pt to /content for easy download ---
import shutil
shutil.copy(
    "/content/runs/ppe_detection_v2/weights/best.pt",
    "/content/best.pt"
)
print("\n" + "=" * 60)
print("  TRAINING COMPLETE (v2 — improved)")
print("=" * 60)
print(f"  best.pt is at: /content/best.pt")
print(f"  Download it and place at: artifacts/stage2_model/best.pt")
print(f"  Training curves: /content/runs/ppe_detection_v2/")
print(f"  Test predictions: /content/runs/test_predictions_v2/")
print("=" * 60)

# --- Step 8: Print training summary for docs ---
print("\n=== Training Configuration (for docs/stage2_model.md) ===")
print(f"  Model: YOLOv8s (yolov8s.pt pretrained)")
print(f"  Epochs: 20 (patience=5 early stopping)")
print(f"  Image size: 512")
print(f"  Batch size: 32")
print(f"  Device: Google Colab T4 GPU")
print(f"  Dataset: Chandimas Construction Safety Monitor (5.17k images)")
print(f"  Source: https://universe.roboflow.com/chandimas-workspace/construction-safety-monitor-mlpd4")
print(f"  Classes: {len(NEW_NAMES)} ({', '.join(NEW_NAMES)})")
print(f"  Augmentation: mosaic, mixup, HSV, rotation, flip")
print(f"  Inference confidence: 0.20")
