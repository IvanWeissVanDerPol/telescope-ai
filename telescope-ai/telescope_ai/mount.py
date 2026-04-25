import logging
import time
from typing import Optional, Tuple
from .config import TelescopeConfig
from .simulator import SimulatedMount

logger = logging.getLogger(__name__)


class MountController:
    def __init__(self, config: TelescopeConfig):
        self.config = config
        self._mount = None
        self._connected = False

    def connect(self) -> bool:
        if self._connected:
            return True

        if self.config.mount_type == "simulator":
            self._mount = SimulatedMount()
            self._connected = True
            logger.info("Connected to simulated mount")
            return True

        try:
            from nexstar_control.device import NexStarHandControl, LatitudeDMS, LongitudeDMS

            port = self.config.serial_port
            self._mount = NexStarHandControl(port)
            if not self._mount.is_connected():
                logger.error(f"Failed to connect on {port}")
                return False

            lat = self.config.latitude
            lon = self.config.longitude
            self._mount.set_location(
                lat=LatitudeDMS.from_decimal(lat),
                lng=LongitudeDMS.from_decimal(lon),
            )
            import datetime
            from zoneinfo import ZoneInfo
            self._mount.set_time(datetime.datetime.now(tz=ZoneInfo(self.config.timezone)))

            self._connected = True
            logger.info(f"Connected to NexStar on {port}")
            return True

        except ImportError:
            logger.error("nexstar-control not installed. pip install nexstar-control")
            logger.info("Falling back to simulator mode")
            self.config.mount_type = "simulator"
            return self.connect()
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        if self._mount and hasattr(self._mount, "close"):
            self._mount.close()
        self._connected = False
        logger.info("Disconnected")

    @property
    def connected(self) -> bool:
        return self._connected

    def goto_radec(self, ra_hours: float, dec_degrees: float) -> bool:
        if not self._connected:
            raise RuntimeError("Mount not connected")
        logger.info(f"Goto RA={ra_hours:.4f}h Dec={dec_degrees:.4f}°")
        self._mount.goto_ra_dec(ra_hours, dec_degrees)
        return True

    def goto_altaz(self, alt_degrees: float, az_degrees: float) -> bool:
        if not self._connected:
            raise RuntimeError("Mount not connected")
        logger.info(f"Goto Alt={alt_degrees:.2f}° Az={az_degrees:.2f}°")
        self._mount.goto_alt_az(alt_degrees, az_degrees)
        return True

    def get_position_radec(self) -> Tuple[float, float]:
        if not self._connected:
            raise RuntimeError("Mount not connected")
        return self._mount.get_position_ra_dec()

    def get_position_altaz(self) -> Tuple[float, float]:
        if not self._connected:
            raise RuntimeError("Mount not connected")
        return self._mount.get_position_alt_az()

    def slew_fixed(self, az_rate: int, alt_rate: int):
        if not self._connected:
            raise RuntimeError("Mount not connected")
        self._mount.slew_fixed(az_rate, alt_rate)

    def slew_variable(self, az_rate: int, alt_rate: int):
        if not self._connected:
            raise RuntimeError("Mount not connected")
        self._mount.slew_variable(az_rate, alt_rate)

    def set_tracking(self, mode: str):
        if not self._connected:
            raise RuntimeError("Mount not connected")
        from nexstar_control.device import TrackingMode
        mode_map = {
            "off": TrackingMode.OFF,
            "sidereal": TrackingMode.SIDEREAL,
            "solar": TrackingMode.SOLAR,
            "lunar": TrackingMode.LUNAR,
        }
        self._mount.set_tracking_mode(mode_map.get(mode.lower(), TrackingMode.SIDEREAL))

    def set_location(self, lat: float, lon: float):
        if not self._connected:
            raise RuntimeError("Mount not connected")
        from nexstar_control.device import LatitudeDMS, LongitudeDMS
        self._mount.set_location(
            lat=LatitudeDMS.from_decimal(lat),
            lng=LongitudeDMS.from_decimal(lon),
        )

    def abort_slew(self):
        if not self._connected:
            return
        self.slew_fixed(0, 0)

    def get_firmware_version(self) -> str:
        if not self._connected:
            return ""
        return self._mount.get_version()

    @property
    def is_slewing(self) -> bool:
        if not self._connected:
            return False
        return self._mount.is_slewing()
