"""Tests for the dataset loader and predictor modules.

The predictor tests use mock detection results (no model weights required)
so they pass even before training is complete. Once best.pt is available,
an integration test can be added to verify real inference.
"""

from unittest.mock import MagicMock

from backend.src.detection.dataset_loader import DatasetLoader

# ---- DatasetLoader Tests ----


class TestDatasetLoader:
    """Tests for the DatasetLoader class."""

    def test_loader_initializes(self) -> None:
        """DatasetLoader should initialize without error if data.yaml exists."""
        loader = DatasetLoader()
        assert loader.data_yaml_path.exists()
        assert loader.num_classes > 0
        assert len(loader.class_names) > 0

    def test_class_names_include_canonical(self) -> None:
        """Dataset should contain labels that map to our canonical classes."""
        loader = DatasetLoader()
        # The raw dataset should have Hardhat, Safety Vest, Gloves, Person
        raw_names_lower = [n.lower() for n in loader.class_names]
        assert "hardhat" in raw_names_lower
        assert "safety vest" in raw_names_lower
        assert "gloves" in raw_names_lower
        assert "person" in raw_names_lower

    def test_splits_have_images(self) -> None:
        """At least the train split should have images."""
        loader = DatasetLoader()
        train_images = loader.get_image_paths("train")
        assert len(train_images) > 0

    def test_validate_passes(self) -> None:
        """Dataset validation should pass."""
        loader = DatasetLoader()
        assert loader.validate() is True

    def test_summary_returns_string(self) -> None:
        """Summary should return a non-empty string."""
        loader = DatasetLoader()
        summary = loader.summary()
        assert isinstance(summary, str)
        assert "Dataset root" in summary
        assert "Classes" in summary


# ---- Predictor Tests (mocked — no model weights needed) ----


class TestPredictorParsing:
    """Tests for the Predictor._parse_results method using mocks.

    These tests verify that raw YOLOv8 output is correctly normalized
    to canonical class names and non-canonical classes are filtered.
    """

    def _make_mock_result(
        self,
        detections: list[tuple[int, float, list[int]]],
        names: dict[int, str],
    ) -> MagicMock:
        """Create a mock ultralytics Results object.

        Args:
            detections: List of (class_id, confidence, bbox) tuples.
            names: Dict mapping class_id to class name.

        Returns:
            MagicMock simulating ultralytics Results.
        """
        result = MagicMock()
        result.names = names

        if not detections:
            result.boxes = MagicMock()
            result.boxes.__len__ = MagicMock(return_value=0)
            result.boxes.cls = MagicMock()
            result.boxes.cls.cpu = MagicMock(return_value=MagicMock(return_value=[]))
            result.boxes.conf = MagicMock()
            result.boxes.conf.cpu = MagicMock(return_value=MagicMock(return_value=[]))
            result.boxes.xyxy = MagicMock()
            result.boxes.xyxy.cpu = MagicMock(return_value=MagicMock(return_value=[]))
            return result

        import numpy as np

        cls_ids = np.array([d[0] for d in detections])
        confs = np.array([d[1] for d in detections])
        bboxes = np.array([d[2] for d in detections])

        boxes = MagicMock()
        boxes.__len__ = MagicMock(return_value=len(detections))

        cls_mock = MagicMock()
        cls_mock.cpu.return_value = MagicMock()
        cls_mock.cpu.return_value.numpy.return_value = cls_ids

        conf_mock = MagicMock()
        conf_mock.cpu.return_value = MagicMock()
        conf_mock.cpu.return_value.numpy.return_value = confs

        xyxy_mock = MagicMock()
        xyxy_mock.cpu.return_value = MagicMock()
        xyxy_mock.cpu.return_value.numpy.return_value = bboxes

        boxes.cls = cls_mock
        boxes.conf = conf_mock
        boxes.xyxy = xyxy_mock

        result.boxes = boxes
        return result

    def test_parse_filters_non_canonical(self) -> None:
        """Non-canonical classes (NO-Hardhat, Excavators) should be filtered."""
        from backend.src.detection.predictor import Predictor

        # Mock the model loading — we only test _parse_results
        predictor = object.__new__(Predictor)

        names = {
            0: "Hardhat",
            1: "NO-Hardhat",
            2: "Excavators",
            3: "Person",
            4: "Safety Vest",
        }
        mock_result = self._make_mock_result(
            detections=[
                (0, 0.95, [100, 50, 200, 150]),   # Hardhat → helmet
                (1, 0.80, [110, 60, 210, 160]),   # NO-Hardhat → dropped
                (2, 0.70, [50, 200, 300, 400]),   # Excavators → dropped
                (3, 0.90, [50, 100, 300, 500]),   # Person → person
                (4, 0.85, [60, 110, 310, 510]),   # Safety Vest → vest
            ],
            names=names,
        )

        result = predictor._parse_results(mock_result)

        assert len(result) == 3  # only helmet, person, vest
        class_names = [d["class_name"] for d in result]
        assert "helmet" in class_names
        assert "person" in class_names
        assert "vest" in class_names
        assert "no-hardhat" not in [d["class_name"] for d in result]

    def test_parse_returns_correct_format(self) -> None:
        """Each detection should have class_name, confidence, and bbox."""
        from backend.src.detection.predictor import Predictor

        predictor = object.__new__(Predictor)
        names = {0: "Hardhat", 1: "Person"}
        mock_result = self._make_mock_result(
            detections=[
                (0, 0.92, [100, 50, 200, 150]),
                (1, 0.88, [50, 100, 300, 500]),
            ],
            names=names,
        )

        result = predictor._parse_results(mock_result)

        assert len(result) == 2
        for det in result:
            assert "class_name" in det
            assert "confidence" in det
            assert "bbox" in det
            assert isinstance(det["class_name"], str)
            assert isinstance(det["confidence"], float)
            assert isinstance(det["bbox"], list)
            assert len(det["bbox"]) == 4

    def test_parse_empty_results(self) -> None:
        """Empty results should return an empty list."""
        from backend.src.detection.predictor import Predictor

        predictor = object.__new__(Predictor)
        names = {0: "Hardhat"}
        mock_result = self._make_mock_result(
            detections=[],
            names=names,
        )

        result = predictor._parse_results(mock_result)
        assert result == []

    def test_parse_gloves_normalized(self) -> None:
        """Gloves class should be normalized correctly."""
        from backend.src.detection.predictor import Predictor

        predictor = object.__new__(Predictor)
        names = {0: "Gloves", 1: "Hardhat"}
        mock_result = self._make_mock_result(
            detections=[
                (0, 0.75, [100, 200, 150, 250]),
                (1, 0.90, [100, 50, 200, 150]),
            ],
            names=names,
        )

        result = predictor._parse_results(mock_result)
        assert len(result) == 2
        class_names = [d["class_name"] for d in result]
        assert "gloves" in class_names
        assert "helmet" in class_names
