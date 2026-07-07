"""YOLOv8 predictor — loads trained model and runs inference on images.

The predictor normalizes raw model output to canonical class names using
backend/config/class_mapping.py. Non-canonical classes (e.g. 'NO-Hardhat',
'Excavators') are filtered out — only person, helmet, vest, gloves are
returned.

Usage:
    from backend.src.detection.predictor import Predictor
    predictor = Predictor()
    detections = predictor.predict("data/sample_images/example.jpg")
    for d in detections:
        print(f"{d['class_name']} ({d['confidence']:.2f}) at {d['bbox']}")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from backend.config.class_mapping import normalize_class_name
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Type alias for a detection result
Detection = dict[str, Any]
# {"class_name": str, "confidence": float, "bbox": list[int]}


class Predictor:
    """Loads a trained YOLOv8 model and runs inference on images.

    Attributes:
        model: The loaded YOLOv8 model.
        model_path: Path to the .pt weights file.
        confidence_threshold: Minimum confidence to include a detection.
    """

    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float | None = None,
    ) -> None:
        """Initialize the predictor and load the model.

        Args:
            model_path: Path to .pt weights. Defaults to settings.model_path.
            confidence_threshold: Min confidence. Defaults to
                settings.confidence_threshold.

        Raises:
            FileNotFoundError: If the model file does not exist.
            ImportError: If ultralytics is not installed.
        """
        self.model_path = model_path or settings.model_path
        self.confidence_threshold = confidence_threshold or settings.confidence_threshold

        # Resolve relative to repo root
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        full_path = Path(self.model_path)
        if not full_path.is_absolute():
            full_path = repo_root / full_path

        if not full_path.exists():
            raise FileNotFoundError(
                f"Model weights not found at {full_path}. "
                "Train the model first (see scripts/colab_train_yolov8.py) "
                "and place best.pt at artifacts/stage2_model/best.pt"
            )

        from ultralytics import YOLO

        self.model = YOLO(str(full_path))
        logger.info("Loaded YOLOv8 model from %s", full_path)

    def predict(
        self,
        image: str | Path | bytes,
        confidence: float | None = None,
    ) -> list[Detection]:
        """Run inference on a single image and return normalized detections.

        Args:
            image: Path to image file, or raw image bytes.
            confidence: Override confidence threshold for this call.

        Returns:
            List of detection dicts:
            {"class_name": str, "confidence": float, "bbox": [x1, y1, x2, y2]}
            Only canonical classes (person, helmet, vest, gloves) are included.
            Bbox coordinates are in pixel format [x1, y1, x2, y2].
        """
        conf = confidence or self.confidence_threshold

        results = self.model.predict(
            source=image,
            conf=conf,
            verbose=False,
        )

        if not results:
            return []

        return self._parse_results(results[0])

    def _parse_results(self, result: Any) -> list[Detection]:
        """Parse ultralytics Results object into detection dicts.

        Filters out non-canonical classes (drops NO-X, vehicles, etc.).

        Args:
            result: ultralytics.engine.results.Results object.

        Returns:
            List of normalized detection dicts.
        """
        detections: list[Detection] = []

        # Get the class names mapping from the model
        names = result.names  # dict {class_id: class_name}

        # result.boxes is a Boxes object with .cls, .conf, .xyxy
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return []

        # Extract arrays
        cls_ids = boxes.cls.cpu().numpy()  # class IDs
        confs = boxes.conf.cpu().numpy()   # confidences
        xyxy = boxes.xyxy.cpu().numpy()    # bboxes [x1, y1, x2, y2]

        for cls_id, conf, bbox in zip(cls_ids, confs, xyxy, strict=False):
            raw_name = names.get(int(cls_id), str(cls_id))
            canonical = normalize_class_name(raw_name)

            if canonical is None:
                # Non-canonical class (NO-Hardhat, Excavators, etc.) — skip
                continue

            detections.append({
                "class_name": canonical,
                "confidence": float(conf),
                "bbox": [int(v) for v in bbox],  # [x1, y1, x2, y2]
            })

        return detections

    def predict_with_raw(
        self,
        image: str | Path | bytes,
        confidence: float | None = None,
    ) -> list[Detection]:
        """Run inference and return ALL detections (including non-canonical).

        Useful for debugging — shows what the model detects before filtering.

        Args:
            image: Path to image file, or raw image bytes.
            confidence: Override confidence threshold.

        Returns:
            List of detection dicts with raw class_name (not normalized).
        """
        conf = confidence or self.confidence_threshold
        results = self.model.predict(source=image, conf=conf, verbose=False)

        if not results:
            return []

        result = results[0]
        names = result.names
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            return []

        cls_ids = boxes.cls.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        xyxy = boxes.xyxy.cpu().numpy()

        detections: list[Detection] = []
        for cls_id, conf, bbox in zip(cls_ids, confs, xyxy, strict=False):
            raw_name = names.get(int(cls_id), str(cls_id))
            detections.append({
                "class_name": raw_name,
                "confidence": float(conf),
                "bbox": [int(v) for v in bbox],
            })

        return detections
