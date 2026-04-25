import logging
import time
import math
from typing import List, Optional, Dict, Callable
from dataclasses import dataclass, field
from .config import TelescopeConfig

logger = logging.getLogger(__name__)


@dataclass
class SatellitePass:
    name: str
    norad_id: int
    start_time: float
    end_time: float
    max_altitude: float
    direction: str
    brightness: Optional[float] = None


@dataclass
class SatellitePosition:
    name: str
    norad_id: int
    alt: float
    az: float
    range_km: float
    velocity_kms: float
    is_sunlit: bool


class SatelliteTracker:
    def __init__(self, config: TelescopeConfig):
        self.config = config
        self._tle_cache: Dict[str, str] = {}
        self._skyfield_loaded = False
        self._earth = None
        self._ts = None
        self._paraguay = None

    def _ensure_skyfield(self):
        if self._skyfield_loaded:
            return True
        try:
            from skyfield.api import load, Topos, wgs84
            self._ts = load.timescale()
            self._paraguay = wgs84.latlon(self.config.latitude, self.config.longitude)
            self._skyfield_loaded = True
            return True
        except ImportError:
            logger.error("skyfield not installed. pip install skyfield")
            return False

    def fetch_tle(self, url: Optional[str] = None) -> bool:
        import urllib.request
        url = url or self.config.tle_url
        try:
            resp = urllib.request.urlopen(url, timeout=15)
            data = resp.read().decode("utf-8")
            lines = data.strip().split("\n")
            for i in range(0, len(lines) - 2, 3):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                if line1.startswith("1 ") and line2.startswith("2 "):
                    self._tle_cache[name] = f"{name}\n{line1}\n{line2}"
            logger.info(f"Fetched {len(self._tle_cache)} TLEs from {url}")
            return True
        except Exception as e:
            logger.error(f"TLE fetch failed: {e}")
            return False

    def get_available_satellites(self) -> List[str]:
        return list(self._tle_cache.keys())

    def predict_passes(
        self, satellite_name: str, min_altitude: float = 20
    ) -> List[SatellitePass]:
        if not self._ensure_skyfield():
            return []

        tle = self._tle_cache.get(satellite_name)
        if not tle:
            logger.warning(f"TLE not found for {satellite_name}")
            return []

        lines = tle.split("\n")
        from skyfield.api import EarthSatellite
        sat = EarthSatellite(lines[1], lines[2], lines[0], self._ts)

        now = self._ts.now()
        passes = []
        for hours_ahead in range(0, 72, 1):
            t = self._ts.tt + hours_ahead / 24.0
            difference = sat - self._paraguay
            topocentric = difference.at(t)
            alt, az, distance = topocentric.altaz()
            if alt.degrees >= min_altitude:
                passes.append(SatellitePass(
                    name=satellite_name,
                    norad_id=0,
                    start_time=t.utc_datetime().timestamp(),
                    end_time=t.utc_datetime().timestamp() + 600,
                    max_altitude=alt.degrees,
                    direction=self._direction_name(az.degrees),
                ))

        passes.sort(key=lambda p: p.max_altitude, reverse=True)
        return passes[:20]

    def get_current_position(self, satellite_name: str) -> Optional[SatellitePosition]:
        if not self._ensure_skyfield():
            return None

        tle = self._tle_cache.get(satellite_name)
        if not tle:
            return None

        lines = tle.split("\n")
        from skyfield.api import EarthSatellite
        sat = EarthSatellite(lines[1], lines[2], lines[0], self._ts)

        t = self._ts.now()
        difference = sat - self._paraguay
        topocentric = difference.at(t)
        alt, az, distance = topocentric.altaz()

        velocity = sat.velocity.km_per_s if hasattr(sat, 'velocity') else 0
        is_sunlit = alt.degrees > 0  # simplified
        return SatellitePosition(
            name=satellite_name,
            norad_id=0,
            alt=float(alt.degrees),
            az=float(az.degrees),
            range_km=float(distance.km),
            velocity_kms=float(velocity),
            is_sunlit=is_sunlit,
        )

    def get_iss_pass_times(self, min_altitude: float = 20) -> List[Dict]:
        if not self._ensure_skyfield():
            return []

        try:
            url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544"
            import urllib.request
            resp = urllib.request.urlopen(url, timeout=15)
            data = resp.read().decode("utf-8")

            from skyfield.api import EarthSatellite
            lines = data.strip().split("\n")
            if len(lines) >= 3:
                sat = EarthSatellite(lines[1], lines[2], lines[0], self._ts)
                passes = []
                now = self._ts.now()
                for i in range(24):
                    t = self._ts.tt + i / 24.0 + now
                    diff = sat - self._paraguay
                    topo = diff.at(t)
                    alt, az, dist = topo.altaz()
                    if alt.degrees > min_altitude:
                        passes.append({
                            "time": str(t.utc_datetime()),
                            "altitude": round(float(alt.degrees), 1),
                            "azimuth": round(float(az.degrees), 1),
                            "direction": self._direction_name(float(az.degrees)),
                        })
                return passes
        except Exception as e:
            logger.error(f"ISS lookup failed: {e}")
        return []

    @staticmethod
    def _direction_name(az: float) -> str:
            dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
            return dirs[round(az / 45) % 8]

    def track_satellite(
        self,
        name: str,
        mount_callback: Callable[[float, float], None],
        interval_s: float = 1.5,
        duration_s: float = 300,
    ):
        if not self._ensure_skyfield():
            return

        tle = self._tle_cache.get(name)
        if not tle:
            logger.error(f"No TLE for {name}")
            return

        lines = tle.split("\n")
        from skyfield.api import EarthSatellite
        sat = EarthSatellite(lines[1], lines[2], lines[0], self._ts)

        start = time.time()
        logger.info(f"Tracking {name} for {duration_s}s")
        while time.time() - start < duration_s:
            t = self._ts.now()
            diff = sat - self._paraguay
            topo = diff.at(t)
            alt, az, dist = topo.altaz()

            if alt.degrees > 0:
                mount_callback(float(alt.degrees), float(az.degrees))
                logger.debug(f"Track: Alt={alt.degrees:.1f}° Az={az.degrees:.1f}°")
            time.sleep(interval_s)

        logger.info(f"Tracking {name} finished")
