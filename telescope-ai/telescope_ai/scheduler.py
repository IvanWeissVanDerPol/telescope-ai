import logging
import math
import json
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from .config import TelescopeConfig
from .weather import WeatherService, WeatherConditions

logger = logging.getLogger(__name__)


@dataclass
class Target:
    name: str
    ra: float
    dec: float
    magnitude: float
    object_type: str
    constellation: str = ""
    catalog_id: str = ""
    description: str = ""


@dataclass
class ScheduledTarget:
    target: Target
    altitude: float
    best_time: str
    duration_minutes: int
    priority: int
    reason: str


class NightScheduler:
    def __init__(self, config: TelescopeConfig, weather: Optional[WeatherService] = None):
        self.config = config
        self.weather = weather
        self._targets: List[Target] = []
        self._load_default_targets()

    def _load_default_targets(self):
        self._targets = [
            Target("Orion Nebula", 5.583, -5.383, 4.0, "nebula", "Orion", "M42", "Star-forming region, best Nov-Feb"),
            Target("Andromeda Galaxy", 0.708, 41.267, 3.4, "galaxy", "Andromeda", "M31", "Nearest major galaxy"),
            Target("Pleiades", 3.783, 24.117, 1.6, "cluster", "Taurus", "M45", "Open star cluster"),
            Target("Hercules Cluster", 16.0, 36.5, 5.8, "cluster", "Hercules", "M13", "Great globular cluster"),
            Target("Omega Centauri", 13.467, -47.283, 3.7, "cluster", "Centaurus", "NGC 5139", "Largest globular in the sky"),
            Target("47 Tucanae", 0.367, -72.083, 4.1, "cluster", "Tucana", "NGC 104", "Bright globular cluster"),
            Target("Large Magellanic Cloud", 5.333, -69.75, 0.9, "galaxy", "Dorado", "LMC", "Satellite galaxy of Milky Way"),
            Target("Small Magellanic Cloud", 0.917, -72.8, 2.7, "galaxy", "Tucana", "SMC", "Satellite galaxy"),
            Target("Carina Nebula", 10.75, -59.867, 1.0, "nebula", "Carina", "NGC 3372", "Huge star-forming region"),
            Target("Jupiter", 0, 0, -2.5, "planet", "", "", "Best Apr-Jun 2026, late evening"),
            Target("Saturn", 0, 0, 0.7, "planet", "", "", "Rings visible, best Jun-Aug 2026"),
            Target("Mars", 0, 0, -1.5, "planet", "", "", "Opposition Jan 2025, dimmer now"),
            Target("Jewel Box Cluster", 12.9, -60.35, 4.2, "cluster", "Crux", "NGC 4755", "Colorful open cluster near Southern Cross"),
            Target("Tarantula Nebula", 5.633, -69.1, 8.0, "nebula", "Dorado", "NGC 2070", "In LMC, largest known nebula"),
            Target("Eta Carinae Nebula", 10.742, -59.675, 6.2, "nebula", "Carina", "NGC 3372", "Homunculus Nebula"),
        ]

    def _get_target_altitude(self, target: Target, now: Optional[datetime] = None) -> float:
        try:
            from skyfield.api import load, wgs84
            ts = load.timescale()
            now = now or datetime.now(timezone.utc)
            t = ts.from_datetime(now)
            loc = wgs84.latlon(self.config.latitude, self.config.longitude)
            from skyfield.positionlib import position_from_radec
            pos = position_from_radec(
                target.ra * 15, target.dec,
                center=loc, epoch=t,
            )
            alt, az, dist = pos.altaz()
            return float(alt.degrees)
        except ImportError:
            import random
            return random.uniform(10, 80)
        except Exception as e:
            logger.warning(f"Altitude calc failed for {target.name}: {e}")
            return 30.0

    def _get_moon_phase(self) -> float:
        try:
            from skyfield.api import load, wgs84
            ts = load.timescale()
            eph = load("de421.bsp")
            t = ts.now()
            sun, moon, earth = eph["sun"], eph["moon"], eph["earth"]
            phase = (moon - earth).at(t).observe(sun).apparent().separation_from(
                (sun - earth).at(t).apparent()
            ).degrees
            return phase / 180.0
        except Exception:
            return 0.5

    def generate_plan(
        self,
        max_targets: int = 5,
        weather_override: Optional[WeatherConditions] = None,
    ) -> List[ScheduledTarget]:
        weather = weather_override
        if weather is None and self.weather:
            weather = self.weather.get_conditions()

        moon_phase = self._get_moon_phase()
        now = datetime.now(timezone.utc)
        is_moon_up = moon_phase < 0.5

        scored: List[tuple] = []
        for target in self._targets:
            alt = self._get_target_altitude(target, now)
            if alt < 15:
                continue

            score = alt
            if target.object_type == "planet":
                score += 10
            if target.object_type == "cluster":
                score += 5
            if target.magnitude < 5:
                score += 10
            if is_moon_up and target.object_type in ("galaxy", "nebula"):
                score -= 15
            if is_moon_up and target.object_type == "planet":
                score += 5
            if self.config.latitude < 0 and "Centauri" in target.name:
                score += 20
            if self.config.latitude < 0 and "Magellanic" in target.name:
                score += 15
            if self.config.latitude < 0 and "Tucanae" in target.name:
                score += 15

            scored.append((score, target, alt))

        scored.sort(key=lambda x: x[0], reverse=True)

        plan = []
        for score, target, alt in scored[:max_targets]:
            duration = 15 if target.object_type == "planet" else 30
            if target.object_type == "nebula":
                duration = 45
            if alt > 60:
                duration = int(duration * 1.5)

            reason_parts = []
            if alt > 60:
                reason_parts.append(f"High altitude ({alt:.0f}°)")
            elif alt > 40:
                reason_parts.append(f"Good altitude ({alt:.0f}°)")
            if target.magnitude < 3:
                reason_parts.append("Bright")
            if "Centauri" in target.name or "Tucanae" in target.name:
                reason_parts.append("Southern hemisphere gem")
            if "Magellanic" in target.name:
                reason_parts.append("Southern exclusive")
            if target.object_type == "planet":
                reason_parts.append("Planet season")

            plan.append(ScheduledTarget(
                target=target,
                altitude=round(alt, 1),
                best_time=now.strftime("%H:%M"),
                duration_minutes=duration,
                priority=len(plan) + 1,
                reason=", ".join(reason_parts) or "Visible now",
            ))

        return plan

    def add_target(self, target: Target):
        self._targets.append(target)

    def save_targets(self, path: str):
        with open(path, "w") as f:
            json.dump([t.__dict__ for t in self._targets], f, indent=2)

    def load_targets(self, path: str):
        with open(path) as f:
            data = json.load(f)
            self._targets = [Target(**t) for t in data]
