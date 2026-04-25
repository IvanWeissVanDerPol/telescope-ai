from dataclasses import dataclass, field
from typing import Optional
import yaml
import os
import json

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/telescope-ai/config.yaml")


@dataclass
class TelescopeConfig:
    mount_type: str = "nexstar"  # nexstar, simulator
    serial_port: str = "/dev/ttyUSB0"  # COM1 on Windows
    serial_baud: int = 9600
    latitude: float = -25.2637  # Asunción default
    longitude: float = -57.5759
    elevation_m: float = 100
    timezone: str = "America/Asuncion"

    camera_type: str = "simulator"  # simulator, asi, dslr, phone
    camera_index: int = 0

    weather_api_key: Optional[str] = None
    weather_provider: str = "openweathermap"

    astap_path: str = "astap"  # path to ASTAP binary
    astrometry_url: str = "http://localhost:8080"

    tle_url: str = "https://celestrak.org/NORAD/elements/stations.txt"
    satellite_update_interval_s: float = 1.5

    target_db_path: str = ""
    classifier_model_path: str = ""

    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8080

    @classmethod
    def load(cls, path: Optional[str] = None) -> "TelescopeConfig":
        path = path or DEFAULT_CONFIG_PATH
        if os.path.exists(path):
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self, path: Optional[str] = None):
        path = path or DEFAULT_CONFIG_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)

    @property
    def is_windows(self):
        return os.name == "nt"
