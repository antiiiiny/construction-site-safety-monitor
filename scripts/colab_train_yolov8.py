# Stage 2 — YOLOv8 Training Script for Google Colab

# ============================================================
# INSTRUCTIONS:
# 1. Open Google Colab: https://colab.research.google.com
# 2. Create a new notebook, paste this entire script into a cell
# 3. Runtime → Change runtime type → T4 GPU (free tier)
# 4. Run the cell — it will:
#    a. Install ultralytics
#    b. Download the Roboflow dataset
#    c. Train YOLOv8s for 50 epochs
#    d. Evaluate on val/test
#    e. Save best.pt to /content for you to download
# 5. Download best.pt and place it at:
#    artifacts/stage2_model/best.pt
# ============================================================

# --- Step 1: Install dependencies ---
!pip install -q ultralytics roboflow
!pip install -q "typer>=0.12,<0.15"  # fix click version conflict

# --- Step 2: Download dataset from Roboflow ---
# Replace YOUR_ROBOFLOW_API_KEY with your actual key from .env
# (Settings → API Key at https://app.roboflow.com)
ROBOFLOW_API_KEY = "YOUR_ROBOFLOW_API_KEY"  # <-- PASTE YOUR KEY HERE

from roboflow import Roboflow
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace("roboflow-universe-projects").project("construction-site-safety")
version = project.version(1)
dataset = version.download("yolov8", location="/content/data")

print(f"Dataset downloaded to: {dataset.location}")
print(f"data.yaml path: /content/data/data.yaml")

# --- Step 3: Train YOLOv8s ---
from ultralytics import YOLO

# Load pretrained YOLOv8s (small model — good balance of speed/accuracy)
model = YOLO("yolov8s.pt")

# Train with fine-tuning
# - 50 epochs (dataset is small, needs enough iterations)
# - imgsz=640 (standard YOLO size)
# - batch=16 (Colab T4 has enough VRAM)
# - patience=10 (early stopping if no improvement)
results = model.train(
    data="/content/data/data.yaml",
    epochs=50,
    imgsz=640,
    batch=16,
    patience=10,
    device=0,  # GPU
    project="/content/runs",
    name="ppe_detection",
    exist_ok=True,
)

print("Training complete!")
print(f"Best weights: /content/runs/ppe_detection/weights/best.pt")

# --- Step 4: Evaluate on validation set ---
metrics = model.val()
print("\n=== Validation Metrics ===")
print(f"mAP@0.5:      {metrics.box.map50:.4f}")
print(f"mAP@0.5:0.95: {metrics.box.map:.4f}")
print(f"Precision:    {metrics.box.mp:.4f}")
print(f"Recall:       {metrics.box.mr:.4f}")

# Per-class metrics
print("\n=== Per-Class Metrics ===")
import yaml
with open("/content/data/data.yaml") as f:
    data_yaml = yaml.safe_load(f)
class_names = data_yaml["names"]

for i, name in enumerate(class_names):
    if i < len(metrics.box.maps):
        print(f"  {name:20s}: mAP@0.5 = {metrics.box.maps[i]:.4f}")

# --- Step 5: Run inference on test images ---
test_dir = "/content/data/test/images"
test_results = model.predict(
    source=test_dir,
    save=True,
    project="/content/runs",
    name="test_predictions",
    exist_ok=True,
    conf=0.25,
)
print(f"\nTest predictions saved to /content/runs/test_predictions/")

# --- Step 6: Copy best.pt to /content for easy download ---
import shutil
shutil.copy(
    "/content/runs/ppe_detection/weights/best.pt",
    "/content/best.pt"
)
print("\n" + "=" * 60)
print("  TRAINING COMPLETE")
print("=" * 60)
print(f"  best.pt is at: /content/best.pt")
print(f"  Download it and place at: artifacts/stage2_model/best.pt")
print(f"  Training curves: /content/runs/ppe_detection/")
print(f"  Test predictions: /content/runs/test_predictions/")
print("=" * 60)

# --- Step 7: Print training summary for docs ---
print("\n=== Training Configuration (for docs/stage2_model.md) ===")
print(f"  Model: YOLOv8s (yolov8s.pt pretrained)")
print(f"  Epochs: 50 (with patience=10 early stopping)")
print(f"  Image size: 640")
print(f"  Batch size: 16")
print(f"  Device: Google Colab T4 GPU")
print(f"  Dataset: Roboflow Construction Site Safety v1")
print(f"  Train images: 307")
print(f"  Val images: 57")
print(f"  Test images: 34")
print(f"  Classes: 17 (filtered to 4 canonical: person, helmet, vest, gloves)")
