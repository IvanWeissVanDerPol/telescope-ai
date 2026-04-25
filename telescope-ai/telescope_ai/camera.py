import logging
import time
from typing import Optional, Tuple
from .config import TelescopeConfig

logger = logging.getLogger(__name__)


class CameraController:
    def __init__(self, config: TelescopeConfig):
        self.config = config
        self._camera = None
        self._connected = False

    def connect(self) -> bool:
        if self._connected:
            return True

        if self.config.camera_type == "simulator":
            self._connected = True
            logger.info("Connected to simulated camera")
            return True

        try:
            if self.config.camera_type in ("asi", "zwo"):
                import ASICamera2 as asi
                num_cameras = asi.ASIGetNumOfConnectedCameras()
                if num_cameras == 0:
                    logger.error("No ZWO cameras found")
                    return False
                self._camera = asi.ASICamera(self.config.camera_index)
                self._camera.init()
                self._connected = True
                logger.info(f"Connected to ZWO camera {self.config.camera_index}")
                return True
            else:
                logger.warning(f"Unsupported camera type: {self.config.camera_type}")
                return False
        except ImportError:
            logger.error("ASICamera2 not installed. pip install zwoasi")
            return False
        except Exception as e:
            logger.error(f"Camera error: {e}")
            return False

    def capture(self, exposure_ms: int = 1000, gain: int = 100) -> Optional["np.ndarray"]:
        if self.config.camera_type == "simulator":
            return self._simulate_frame(exposure_ms)

        if not self._connected or not self._camera:
            logger.error("Camera not connected")
            return None

        try:
            import numpy as np
            self._camera.set_control("Exposure", exposure_ms * 1000)
            self._camera.set_control("Gain", gain)
            self._camera.start_video_capture()
            time.sleep(exposure_ms / 1000 + 0.1)
            frame = self._camera.get_video_data()
            return np.array(frame, dtype=np.uint16)
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            return None

    def _simulate_frame(self, exposure_ms: int):
        import numpy as np
        h, w = 480, 640
        noise = np.random.poisson(50, (h, w)).astype(np.uint16)
        num_stars = np.random.randint(20, 100)
        for _ in range(num_stars):
            x, y = np.random.randint(0, w), np.random.randint(0, h)
            brightness = np.random.randint(100, 1000)
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx * dx + dy * dy < 9:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            noise[ny, nx] = min(65535, noise[ny, nx] + brightness // (dx * dx + dy * dy + 1))
        return noise

    def disconnect(self):
        self._connected = False
        logger.info("Camera disconnected")
