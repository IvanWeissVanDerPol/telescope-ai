import logging
import time
from typing import Optional, Dict
from dataclasses import dataclass, field
from .config import TelescopeConfig

logger = logging.getLogger(__name__)


@dataclass
class WeatherConditions:
    cloud_cover_pct: float = 0.0
    temperature_c: float = 20.0
    wind_speed_ms: float = 0.0
    humidity_pct: float = 0.0
    visibility_km: float = 10.0
    condition: str = "clear"
    is_dark: bool = False
    is_observable: bool = False
    reason: str = ""


class WeatherService:
    def __init__(self, config: TelescopeConfig):
        self.config = config
        self._cache: Optional[WeatherConditions] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 300

    def get_conditions(self, force: bool = False) -> WeatherConditions:
        if not force and self._cache and time.time() - self._cache_time < self._cache_ttl:
            return self._cache

        if self.config.weather_api_key:
            conditions = self._fetch_openweathermap()
        else:
            conditions = self._estimate_clear()

        if conditions is not None:
            if conditions.cloud_cover_pct <= 50 and conditions.wind_speed_ms < 10 and conditions.is_dark:
                conditions.is_observable = True
                conditions.reason = "Good conditions"
            else:
                reasons = []
                if conditions.cloud_cover_pct > 50:
                    reasons.append(f"Cloudy ({conditions.cloud_cover_pct:.0f}%)")
                if conditions.wind_speed_ms >= 10:
                    reasons.append(f"Windy ({conditions.wind_speed_ms:.1f} m/s)")
                if not conditions.is_dark:
                    reasons.append("Not dark")
                conditions.reason = ", ".join(reasons)
                conditions.is_observable = False

            self._cache = conditions
            self._cache_time = time.time()

        return conditions or WeatherConditions()

    def _fetch_openweathermap(self) -> Optional[WeatherConditions]:
        try:
            import requests
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": self.config.latitude,
                    "lon": self.config.longitude,
                    "appid": self.config.weather_api_key,
                    "units": "metric",
                },
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning(f"Weather API error: {resp.status_code}")
                return None

            data = resp.json()
            clouds = data.get("clouds", {}).get("all", 0)
            main = data.get("main", {})
            wind = data.get("wind", {})

            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            sunrise = data.get("sys", {}).get("sunrise", 0)
            sunset = data.get("sys", {}).get("sunset", 0)
            is_dark = not (sunrise < now.timestamp() < sunset)

            return WeatherConditions(
                cloud_cover_pct=float(clouds),
                temperature_c=float(main.get("temp", 20)),
                wind_speed_ms=float(wind.get("speed", 0)),
                humidity_pct=float(main.get("humidity", 50)),
                visibility_km=float(data.get("visibility", 10000)) / 1000,
                condition=data.get("weather", [{}])[0].get("description", "unknown"),
                is_dark=is_dark,
            )
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return None

    def _estimate_clear(self) -> WeatherConditions:
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        hour = now.hour + now.minute / 60
        is_dark = hour < 5 or hour > 19
        return WeatherConditions(
            cloud_cover_pct=0,
            is_dark=is_dark,
            is_observable=is_dark,
            reason="No weather API configured, assuming clear" if is_dark else "Daytime",
        )
