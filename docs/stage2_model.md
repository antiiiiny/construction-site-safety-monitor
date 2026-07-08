# Stage 2 — PPE Detection Model

## Training Configuration

| Parameter | Value |
|-----------|-------|
| Model | YOLOv8s (yolov8s.pt pretrained) |
| Epochs | 50 (early stopped at epoch 28, best at epoch 18) |
| Patience | 10 (early stopping) |
| Image size | 640 |
| Batch size | 16 |
| Device | Google Colab Tesla T4 GPU (CUDA) |
| Training time | 0.058 hours (~3.5 minutes) |
| Dataset | Roboflow Construction Site Safety v1 |
| Train images | 307 |
| Val images | 57 |
| Test images | 34 |
| Total classes | 17 (filtered to 4 canonical: person, helmet, vest, gloves) |

## Evaluation Metrics (Validation Set)

### Overall

| Metric | Value |
|--------|-------|
| mAP@0.5 | 0.385 |
| mAP@0.5:0.95 | 0.271 |
| Precision | 0.800 |
| Recall | 0.353 |
| Inference speed | 15.1ms per image |

### Per-Class (Canonical Classes Only)

| Class | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|-------|-----------|--------|---------|--------------|
| helmet (Hardhat) | 0.776 | 0.392 | 0.663 | 0.321 |
| vest (Safety Vest) | 0.876 | 0.167 | 0.172 | 0.153 |
| person (Person) | 0.113 | 0.024 | 0.037 | 0.012 |
| gloves (Gloves) | 1.000 | 0.000 | 0.000 | 0.000 |

### Per-Class (All Dataset Classes)

| Class | mAP@0.5 |
|-------|---------|
| EXCAVATORS | 0.896 |
| wheel loader | 0.669 |
| NO-Hardhat | 0.458 |
| dump truck | 0.437 |
| Hardhat | 0.321 |
| Safety Vest | 0.153 |
| NO-Safety Vest | 0.024 |
| NO-Mask | 0.011 |
| Person | 0.012 |
| Gloves | 0.000 |
| Safety Shoes | 0.000 |

## Gate Criterion Assessment

**Gate requirement:** mAP@0.5 > 0.6 on key classes (person, helmet, vest)

| Class | mAP@0.5 | Gate (>0.6) | Status |
|-------|---------|-------------|--------|
| helmet | 0.663 | ✅ Pass | ✓ |
| vest | 0.172 | ❌ Fail | ✗ |
| person | 0.037 | ❌ Fail | ✗ |
| gloves | 0.000 | ❌ Fail | ✗ |

**Gate status: NOT MET.** Only helmet passes the 0.6 threshold.

## Analysis of Poor Performance

### Root Causes

1. **Severe class imbalance** — helmet has 436 instances while gloves has only 18,
   person has 69, and vest has 53. The model overfits to helmet and underfits
   the rare classes.

2. **Small dataset** — 307 training images is very small for 17 classes. The
   model doesn't have enough examples to learn rare classes.

3. **Person detection failure** — The dataset labels "Person" sparingly (only
   69 instances across all splits). Most humans in the images are annotated
   via their PPE (Hardhat, Safety Vest) rather than as Person objects. This
   is a labeling issue, not a model issue.

4. **Gloves failure** — Only 18 instances total (11 train, 5 val, 2 test).
   The model never learned to detect gloves reliably.

5. **Early stopping at epoch 28** — The model converged quickly but to a
   suboptimal solution due to the above issues.

### What Works

- **Helmet detection is strong** (mAP@0.5 = 0.663, precision = 0.776)
- **Inference is fast** (15ms per image on GPU, ~50ms on CPU)
- **The predictor pipeline works end-to-end** — model loads, runs inference,
  normalizes classes, returns structured detections
- **All 4 canonical classes are detected** on sample images (see
  `artifacts/stage2_predictions/`), even if validation metrics are low

## Sample Predictions

4 sample images with annotated predictions saved to:
`artifacts/stage2_predictions/`

- Image 1: 16 detections (helmet, person, gloves, vest all detected)
- Image 2: 6 detections (gloves, helmet, vest, person)
- Image 3: 1 detection (person)
- Image 4: 33 detections (person, helmet — crowded scene)

## Failure Cases and Observations

1. **Person class is unreliable** — The model detects persons but with very
   low precision (0.113). This is because the dataset's Person annotations
   are inconsistent. In practice, the rule engine can infer person presence
   from helmet/vest detections (a helmet implies a person is wearing it).

2. **Gloves are not detected** — 18 training instances is insufficient. The
   Welding Zone (Zone 3) requires gloves, so violations there will be
   unreliable. This should be noted as a known limitation.

3. **Vest detection is weak** — Only 53 instances and low recall (0.167).
   The model often misses vests, which will cause false violations.

## Recommendations

### Option A: Proceed with current model (recommended for capstone demo)

- **Helmet detection works well** — this is the primary PPE item
- **Document the limitations honestly** — evaluators appreciate transparency
- **Adjust the rule engine** to be more lenient: only trigger violations for
  missing helmet (the reliable class), and log vest/gloves as "informational"
  rather than "violation"
- **Lower the confidence threshold** to 0.25 for vest/gloves to improve recall
  at the cost of precision

### Option B: Retrain with improvements

- **Augment with Chandimas dataset** (5.17k images) — has more person/vest/gloves
- **Use class-weighted loss** or oversample rare classes
- **Train for more epochs** (disable early stopping: patience=0)
- **Use a larger model** (yolov8m.pt) if GPU allows
- **Filter the dataset** to only canonical classes before training (removes
  confusion from 17 classes when we only need 4)

### Option C: Use a pretrained checkpoint from Roboflow

- The dataset page lists 7 pretrained models. One may perform better than
  our fine-tune. Download and evaluate.

## Decision

**Proceeding with Option B (retrain with improvements)** — the first
training run (v1) only passed the gate for helmet. An improved script
(`scripts/colab_train_yolov8_v2.py`) addresses the root causes:

### v2 Improvements

| Issue (v1) | Fix (v2) |
|------------|----------|
| 717 images (too small) | **5.17k images** (Chandimas dataset — 7x more data) |
| 17 classes (model confused) | Filter to canonical classes only (helmet, vest, person, gloves) |
| imgsz=640, batch=16 | **imgsz=512, batch=32** — faster training |
| 50 epochs (stopped at 28) | **20 epochs** (enough for 5k images, ~15 min) |
| No augmentation tuning | mosaic, mixup, HSV, rotation, flip |
| Confidence 0.25 | Lower to 0.20 for better recall |

### v2 Dataset

**Chandimas Construction Safety Monitor** — 5.17k images
- URL: https://universe.roboflow.com/chandimas-workspace/construction-safety-monitor-mlpd4
- Classes: helmet, vest, gloves, goggles, boots + no-X counterparts
- **Note**: May not have a `person` class. The script handles this
  dynamically — if person is missing, trains on 3 classes and the rule
  engine infers person presence from PPE detections.

### v2 Training Configuration

| Parameter | v1 (original) | v2 (improved) |
|-----------|---------------|---------------|
| Dataset | Roboflow Universe (717 images) | **Chandimas (5.17k images)** |
| Model | yolov8s | **yolov8s** (same, but 7x more data) |
| Epochs | 50 (stopped at 28) | **20 (patience=5)** |
| Image size | 640 | **512** (faster) |
| Batch size | 16 | **32** (better GPU utilization) |
| Classes | 17 (all) | **Filtered to canonical only** |
| Augmentation | Default | **mosaic, mixup, HSV, rotation, flip** |
| Inference conf | 0.25 | **0.20** |

### To Retrain

1. Open `scripts/colab_train_yolov8_v2.py`
2. Paste into a Colab notebook with T4 GPU
3. Replace `YOUR_ROBOFLOW_API_KEY` with your key
4. Run — takes ~15-20 minutes (5.17k images, yolov8s, 20 epochs)
5. The script will print the actual class names from Chandimas — verify
   the mapping is correct before training starts
6. Download `best.pt` → `artifacts/stage2_model/best.pt`
7. Run `python -m backend.src.detection.visualize_predictions` to verify
8. Update this file with the new metrics

### If Chandimas Doesn't Have Person Labels

The Chandimas dataset may not include a `person` class (only PPE items).
If so, the v2 script trains on 3 classes (helmet, vest, gloves). The rule
engine can be adapted:
- **Option A**: Infer person from helmet/vest bbox (a helmet implies a
  person is wearing it — create a synthetic person bbox around the PPE)
- **Option B**: Merge Chandimas + v1 dataset (v1 has Person labels)
- **Option C**: Use a general person detection model (COCO pretrained)
  alongside the PPE model

## Rule Engine Adaptation

Regardless of which model version is used, the rule engine (Stage 3) is
designed to weight violations by model reliability:
- Helmet violations: high confidence (model is reliable)
- Vest violations: medium confidence (model is weak)
- Gloves violations: low confidence / informational only (model fails)

## Files

- `artifacts/stage2_model/best.pt` — trained YOLOv8s weights (22.5MB, v1)
- `artifacts/stage2_predictions/` — 4 annotated sample images
- `backend/src/detection/predictor.py` — inference module
- `backend/src/detection/dataset_loader.py` — dataset validation
- `backend/src/detection/visualize_predictions.py` — prediction visualization
- `scripts/colab_train_yolov8.py` — Colab training script (v1, 17 classes)
- `scripts/colab_train_yolov8_v2.py` — **Improved** Colab training script (v2, 4 classes, yolov8m)
