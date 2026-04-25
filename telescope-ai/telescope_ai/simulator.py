import math
import time
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SimulatedMount:
    def __init__(self):
        self.ra = 0.0
        self.dec = 0.0
        self.alt = 45.0
        self.az = 180.0
        self.tracking = True
        self.target_ra = 0.0
        self.target_dec = 0.0
        self.slewing = False
        self._slew_start = 0
        self._slew_duration = 2.0
        logger.info("Simulated mount initialized")

    def is_connected(self):
        return True

    def is_slewing(self):
        if not self.slewing:
            return False
        if time.time() - self._slew_start > self._slew_duration:
            self.slewing = False
            self.ra, self.dec = self.target_ra, self.target_dec
            logger.info(f"Slew complete: RA={self.ra:.2f}h Dec={self.dec:.2f}°")
            return False
        return True

    def goto_ra_dec(self, ra_hours: float, dec_degrees: float):
        self.target_ra = ra_hours
        self.target_dec = dec_degrees
        self.slewing = True
        self._slew_start = time.time()
        logger.info(f"Simulating goto RA={ra_hours:.2f}h Dec={dec_degrees:.2f}°")

    def goto_alt_az(self, alt_degrees: float, az_degrees: float):
        self.target_az = az_degrees
        self.alt = alt_degrees
        self.az = az_degrees
        self.slewing = True
        self._slew_start = time.time()
        logger.info(f"Simulating goto Alt={alt_degrees:.2f}° Az={az_degrees:.2f}°")

    def get_position_ra_dec(self) -> Tuple[float, float]:
        return (self.ra, self.dec)

    def get_position_alt_az(self) -> Tuple[float, float]:
        return (self.alt, self.az)

    def slew_fixed(self, az_rate: int, alt_rate: int):
        if az_rate == 0 and alt_rate == 0 and self.slewing:
            self.slewing = False

    def slew_variable(self, az_rate: int, alt_rate: int):
        pass

    def set_tracking_mode(self, mode):
        self.tracking = mode != 0

    def set_location(self, lat, lng):
        logger.info(f"Simulated location: {lat}, {lng}")

    def set_time(self, dt):
        logger.info(f"Simulated time: {dt}")

    def get_version(self) -> str:
        return "SIM-0.1"

    def close(self):
        logger.info("Simulated mount disconnected")
