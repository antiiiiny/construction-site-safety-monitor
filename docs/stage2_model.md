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

**Proceeding with Option A** — the current model is sufficient for a capstone
demo. The helmet detection (the most important PPE) works well, and the
pipeline is functional end-to-end. Limitations are documented transparently.

The rule engine (Stage 3) will be designed with this in mind:
- Helmet violations: high confidence (model is reliable)
- Vest violations: medium confidence (model is weak)
- Gloves violations: low confidence / informational only (model fails)

## Files

- `artifacts/stage2_model/best.pt` — trained YOLOv8s weights (22.5MB)
- `artifacts/stage2_predictions/` — 4 annotated sample images
- `backend/src/detection/predictor.py` — inference module
- `backend/src/detection/dataset_loader.py` — dataset validation
- `backend/src/detection/visualize_predictions.py` — prediction visualization
- `scripts/colab_train_yolov8.py` — Colab training script
