import logging
import json
import math
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from .config import TelescopeConfig

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    object_type: str
    confidence: float
    label: str
    description: str = ""
    catalog_ids: List[str] = field(default_factory=list)


class ObjectClassifier:
    def __init__(self, config: TelescopeConfig):
        self.config = config
        self._model = None
        self._rule_based = True  # fallback when no ML model

    def classify(self, image_path: Optional[str] = None, ra: float = 0, dec: float = 0) -> ClassificationResult:
        if self._model is not None:
            return self._classify_ml(image_path)

        if ra != 0 or dec != 0:
            return self._classify_by_coordinates(ra, dec)

        return ClassificationResult(
            object_type="unknown",
            confidence=0.0,
            label="No data provided",
            description="Provide an image or coordinates",
        )

    def _classify_ml(self, image_path: str) -> ClassificationResult:
        try:
            import numpy as np
            from PIL import Image

            img = Image.open(image_path).convert("RGB")
            img = img.resize((224, 224))
            arr = np.array(img, dtype=np.float32) / 255.0

            logger.info(f"ML classification of {image_path} ({arr.shape})")
            return ClassificationResult(
                object_type="unknown",
                confidence=0.0,
                label="ML model not loaded",
                description="Model loading not yet implemented",
            )
        except Exception as e:
            logger.error(f"ML classify failed: {e}")
            return ClassificationResult(
                object_type="error",
                confidence=0.0,
                label=str(e),
            )

    def _classify_by_coordinates(self, ra: float, dec: float) -> ClassificationResult:
        known = self._get_known_objects()
        best_match = None
        best_dist = float("inf")

        for obj in known:
            dist = ((ra - obj["ra"]) * 15 * math.cos(math.radians(dec))) ** 2 + (dec - obj["dec"]) ** 2
            dist = math.sqrt(dist)
            if dist < best_dist and dist < 5:
                best_dist = dist
                best_match = obj

        if best_match:
            confidence = max(0.5, 1.0 - best_dist / 5.0)
            return ClassificationResult(
                object_type=best_match["type"],
                confidence=round(confidence, 3),
                label=best_match["name"],
                description=best_match.get("description", ""),
                catalog_ids=best_match.get("catalog_ids", []),
            )

        return ClassificationResult(
            object_type="star_field",
            confidence=0.3,
            label=f"Unidentified at RA={ra:.2f}h Dec={dec:.2f}°",
            description="No known DSO near this position",
        )

    @staticmethod
    def _get_known_objects() -> List[Dict]:
        return [
            {"name": "M42", "ra": 5.583, "dec": -5.383, "type": "nebula", "description": "Orion Nebula, stellar nursery 1344 ly away"},
            {"name": "M31", "ra": 0.708, "dec": 41.267, "type": "galaxy", "description": "Andromeda Galaxy, 2.5M ly away"},
            {"name": "M45", "ra": 3.783, "dec": 24.117, "type": "cluster", "description": "Pleiades, open cluster 444 ly away"},
            {"name": "M13", "ra": 16.0, "dec": 36.5, "type": "cluster", "description": "Hercules Globular Cluster"},
            {"name": "NGC 5139", "ra": 13.467, "dec": -47.283, "type": "cluster", "description": "Omega Centauri, largest globular in sky"},
            {"name": "NGC 104", "ra": 0.367, "dec": -72.083, "type": "cluster", "description": "47 Tucanae, bright globular cluster"},
            {"name": "LMC", "ra": 5.333, "dec": -69.75, "type": "galaxy", "description": "Large Magellanic Cloud, satellite galaxy"},
            {"name": "SMC", "ra": 0.917, "dec": -72.8, "type": "galaxy", "description": "Small Magellanic Cloud, satellite galaxy"},
            {"name": "NGC 3372", "ra": 10.75, "dec": -59.867, "type": "nebula", "description": "Carina Nebula, huge star-forming region"},
            {"name": "NGC 2070", "ra": 5.633, "dec": -69.1, "type": "nebula", "description": "Tarantula Nebula in LMC"},
            {"name": "NGC 4755", "ra": 12.9, "dec": -60.35, "type": "cluster", "description": "Jewel Box, colorful open cluster"},
        ]

    def load_model(self, model_path: str):
        try:
            import torch
            self._model = torch.load(model_path, map_location="cpu")
            self._model.eval()
            self._rule_based = False
            logger.info(f"Loaded ML model from {model_path}")
        except Exception as e:
            logger.error(f"Model load failed: {e}")
