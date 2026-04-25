import logging
import subprocess
import json
import os
import tempfile
from typing import Optional, Tuple
from .config import TelescopeConfig

logger = logging.getLogger(__name__)


class PlateSolver:
    def __init__(self, config: TelescopeConfig):
        self.config = config

    def solve(self, image_path: str) -> Optional[Tuple[float, float, float, float]]:
        if self.config.astap_path:
            return self._solve_astap(image_path)
        return self._solve_astrometry(image_path)

    def _solve_astap(self, image_path: str) -> Optional[Tuple[float, float, float, float]]:
        try:
            result = subprocess.run(
                [self.config.astap_path, "-f", image_path, "-s", "-r", "5"],
                capture_output=True, text=True, timeout=30,
            )
            for line in result.stdout.split("\n"):
                if line.startswith("RA=") and line.startswith("DEC="):
                    parts = line.split()
                    ra = float(parts[0].split("=")[1])
                    dec = float(parts[1].split("=")[1])
                    width = float(parts[2].split("=")[1]) if len(parts) > 2 else 0
                    height = float(parts[3].split("=")[1]) if len(parts) > 3 else 0
                    logger.info(f"ASTAP solved: RA={ra:.4f} Dec={dec:.4f}")
                    return (ra, dec, width, height)
            logger.warning("ASTAP did not return a solution")
            return None
        except FileNotFoundError:
            logger.error(f"ASTAP not found at {self.config.astap_path}")
            return None
        except subprocess.TimeoutExpired:
            logger.error("ASTAP timed out")
            return None
        except Exception as e:
            logger.error(f"ASTAP error: {e}")
            return None

    def _solve_astrometry(self, image_path: str) -> Optional[Tuple[float, float, float, float]]:
        try:
            import requests
            with open(image_path, "rb") as f:
                resp = requests.post(
                    f"{self.config.astrometry_url}/solve",
                    files={"file": f},
                    params={"scale_est": 1.0, "scale_err": 50},
                    timeout=60,
                )
            if resp.status_code == 200:
                data = resp.json()
                ra = data.get("ra", 0)
                dec = data.get("dec", 0)
                width = data.get("width", 0)
                height = data.get("height", 0)
                logger.info(f"Astrometry.net solved: RA={ra:.4f} Dec={dec:.4f}")
                return (ra, dec, width, height)
            logger.warning(f"Astrometry.net failed: {resp.status_code}")
            return None
        except ImportError:
            logger.error("requests required for astrometry.net. pip install requests")
            return None
        except Exception as e:
            logger.error(f"Astrometry.net error: {e}")
            return None

    def estimate_initial(self, image_path: str) -> Optional[Tuple[float, float]]:
        try:
            import numpy as np
            from PIL import Image
            img = Image.open(image_path).convert("L")
            arr = np.array(img, dtype=np.float32)
            arr -= arr.mean()
            arr /= arr.std() + 1e-8
            bright = np.percentile(arr, 99.9)
            num_bright = np.sum(arr > bright)
            if num_bright > 100:
                logger.info(f"Estimated: dense star field ({num_bright} bright pixels)")
            elif num_bright > 10:
                logger.info(f"Estimated: sparse star field ({num_bright} bright pixels)")
            else:
                logger.warning("No bright stars detected")
            return None
        except Exception as e:
            logger.error(f"Estimation failed: {e}")
            return None
