# Stage 1 — Dataset Acquisition & EDA

## Dataset Source

- **Name**: Construction Site Safety
- **Provider**: Roboflow Universe Projects
- **URL**: https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety
- **Version**: 1
- **License**: CC BY 4.0
- **Download method**: `roboflow` Python SDK via `backend/src/detection/download_dataset.py`

## Dataset Stats

### Image Counts

| Split   | Images | Labels |
|---------|--------|--------|
| Train   | 307    | 307    |
| Valid   | 57     | 57     |
| Test    | 34     | 34     |
| **Total** | **398** | **398** |

### Raw Class Distribution (17 classes in dataset)

| Class            | Train | Valid | Test | Total |
|------------------|-------|-------|------|-------|
| Hardhat          | 289   | 115   | 32   | 436   |
| NO-Hardhat       | 92    | 9     | 7    | 108   |
| EXCAVATORS       | 107   | 3     | 0    | 110   |
| dump truck       | 77    | 8     | 12   | 97    |
| wheel loader     | 62    | 11    | 9    | 82    |
| Person           | 42    | 23    | 4    | 69    |
| NO-Mask          | 36    | 14    | 2    | 52    |
| Safety Vest      | 45    | 6     | 2    | 53    |
| NO-Safety Vest   | 21    | 14    | 3    | 38    |
| Safety Shoes     | 9     | 13    | 0    | 22    |
| Gloves           | 11    | 5     | 2    | 18    |
| Safety Net       | 3     | 0     | 0    | 3     |
| Barricade        | 1     | 0     | 0    | 1     |
| Dumpster         | 1     | 0     | 0    | 1     |
| Mask             | 1     | 0     | 0    | 1     |
| mini-van         | 1     | 0     | 0    | 1     |
| truck            | 1     | 0     | 0    | 1     |

### Canonical Class Distribution (after mapping)

The system maps dataset labels to 4 canonical classes. Labels not in the
mapping (e.g. `NO-Hardhat`, `EXCAVATORS`, `dump truck`) are dropped during
inference — violations are inferred by the rule engine via containment logic.

| Canonical | Train | Valid | Test | Total |
|-----------|-------|-------|------|-------|
| helmet    | 289   | 115   | 32   | 436   |
| person    | 42    | 23    | 4    | 69    |
| vest      | 45    | 6     | 2    | 53    |
| gloves    | 11    | 5     | 2    | 18    |

### Balance Assessment

- **Max/min ratio**: 24.2 (helmet: 436 vs gloves: 18)
- **Status**: **IMBALANCED** — significant class imbalance
- **Impact**: The model will be good at detecting helmets but may struggle
  with gloves (only 18 instances). This is acceptable for a capstone demo
  but should be noted as a limitation.
- **Mitigation**: If gloves mAP is too low after Stage 2 training, consider
  augmenting with the Chandimas dataset (5.17k images, includes gloves).

### Image Resolution Range

- **Width**: 194 – 2046 px
- **Height**: 196 – 1920 px
- **Note**: Wide range — YOLOv8 will resize to 640x640 during training.

### Corrupt Files

- **None found** — all 398 images open correctly with PIL.

## Class Mapping Strategy

The dataset has 17 classes including presence/absence pairs (e.g.
`Hardhat` / `NO-Hardhat`). We keep only the presence classes and drop
the absence ones — violations are inferred by the rule engine via
containment logic (a person with no helmet bbox inside their bbox =
helmet violation).

See `backend/config/class_mapping.py` for the full mapping.

## Files

- `data/data.yaml` — YOLOv8 dataset config
- `data/train/images/`, `data/train/labels/` — training split
- `data/valid/images/`, `data/valid/labels/` — validation split
- `data/test/images/`, `data/test/labels/` — test split
- `data/sample_images/` — 4 sample images for pipeline testing
- `artifacts/stage1_eda/` — 5 annotated sample images with bboxes
