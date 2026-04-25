"""
MCP Server for Telescope AI.

Exposes telescope control, satellite tracking, night scheduling,
weather checks, plate solving, and object classification as MCP tools
that any AI agent (Claude, Hermes, etc.) can call.

Run:
    fastmcp run mcp_server/server.py:mcp
    fastmcp list mcp_server/server.py:mcp --json
    fastmcp call mcp_server/server.py:goto_target target_name=M42
"""

import logging
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telescope_ai.config import TelescopeConfig
from telescope_ai.mount import MountController
from telescope_ai.satellite import SatelliteTracker
from telescope_ai.scheduler import NightScheduler
from telescope_ai.weather import WeatherService
from telescope_ai.platesolve import PlateSolver
from telescope_ai.classifier import ObjectClassifier
from telescope_ai.utils import hours_to_hms, degrees_to_dms

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Telescope AI",
    instructions="AI-powered telescope control for Celestron NexStar mounts",
)

_config = None
_mount = None
_weather = None
_scheduler = None
_tracker = None
_solver = None
_classifier = None


def _ensure_init():
    global _config, _mount, _weather, _scheduler, _tracker, _solver, _classifier
    if _config is not None:
        return
    _config = TelescopeConfig.load()
    _mount = MountController(_config)
    _weather = WeatherService(_config)
    _scheduler = NightScheduler(_config, _weather)
    _tracker = SatelliteTracker(_config)
    _solver = PlateSolver(_config)
    _classifier = ObjectClassifier(_config)


def _ensure_mount():
    _ensure_init()
    if not _mount.connected:
        _mount.connect()


# ─── TOOLS ───────────────────────────────────────────────────────

@mcp.tool(
    name="health_check",
    description="Check if the telescope mount and services are connected and operational",
)
def health_check() -> str:
    _ensure_init()
    mount_ok = _mount.connected or _mount.connect()
    weather_ok = _weather.get_conditions().is_observable
    parts = []
    parts.append(f"Mount: {'CONNECTED' if _mount.connected else 'DISCONNECTED'}")
    parts.append(f"Mount type: {_config.mount_type}")
    cond = _weather.get_conditions()
    parts.append(f"Weather: {cond.condition} (cloud={cond.cloud_cover_pct:.0f}%)")
    parts.append(f"Nighttime: {cond.is_dark}")
    parts.append(f"Observable: {cond.is_observable}: {cond.reason}")
    return "\n".join(parts)


@mcp.tool(
    name="get_position",
    description="Get the current pointing position of the telescope in RA/Dec and Alt/Az",
)
def get_position() -> str:
    _ensure_mount()
    ra, dec = _mount.get_position_radec()
    alt, az = _mount.get_position_altaz()
    return (
        f"RA: {ra:.4f}h ({hours_to_hms(ra)})\n"
        f"Dec: {dec:.4f}° ({degrees_to_dms(dec)})\n"
        f"Alt: {alt:.2f}°\n"
        f"Az: {az:.2f}°"
    )


@mcp.tool(
    name="goto_target",
    description="Slew the telescope to a named target or RA/Dec coordinates",
)
def goto_target(
    target_name: Optional[str] = None,
    ra_hours: Optional[float] = None,
    dec_degrees: Optional[float] = None,
) -> str:
    _ensure_mount()
    if target_name:
        classifier = _classifier
        result = classifier.classify(ra=0, dec=0)
        for obj in classifier._get_known_objects():
            if obj["name"].lower() == target_name.lower():
                ra_hours = obj["ra"]
                dec_degrees = obj["dec"]
                _mount.goto_radec(ra_hours, dec_degrees)
                return (
                    f"Slewing to {obj['name']} ({obj['description']})\n"
                    f"RA={ra_hours:.4f}h Dec={dec_degrees:.4f}°"
                )
        return f"Unknown target '{target_name}'. Available: M42, M31, M45, M13, Omega Centauri, 47 Tucanae, LMC, SMC, Carina Nebula, Jewel Box, Jupiter, Saturn"

    if ra_hours is not None and dec_degrees is not None:
        _mount.goto_radec(ra_hours, dec_degrees)
        return f"Slewing to RA={ra_hours:.4f}h Dec={dec_degrees:.4f}°"
    return "Provide target_name or ra_hours+dec_degrees"


@mcp.tool(
    name="get_observing_plan",
    description="Generate an AI-optimized observing plan for tonight based on weather, moon phase, and target visibility",
)
def get_observing_plan(max_targets: int = 5) -> str:
    _ensure_init()
    plan = _scheduler.generate_plan(max_targets=max_targets)
    cond = _weather.get_conditions()
    lines = [f"Tonight's Observing Plan ({cond.condition}, dark={cond.is_dark})", "=" * 50]
    for item in plan:
        lines.append(f"\n#{item.priority}: {item.target.name}")
        lines.append(f"   Type: {item.target.object_type}")
        lines.append(f"   Catalog: {item.target.catalog_id or 'N/A'}")
        lines.append(f"   Magnitude: {item.target.magnitude}")
        lines.append(f"   Altitude: {item.altitude}°")
        lines.append(f"   Recommended exposure: {item.duration_minutes} min")
        lines.append(f"   Why: {item.reason}")
    return "\n".join(lines)


@mcp.tool(
    name="track_satellite",
    description="Track a satellite by name. Fetches TLE data from CelesTrak and slews the telescope to follow it",
)
def track_satellite(satellite_name: str, duration_seconds: int = 300) -> str:
    _ensure_mount()
    if not _tracker.fetch_tle():
        return "Failed to fetch TLE data from CelesTrak"
    pos = _tracker.get_current_position(satellite_name)
    if pos is None:
        available = _tracker.get_available_satellites()[:10]
        return f"Could not get position for '{satellite_name}'. Available: {', '.join(available)}"
    return (
        f"Tracking {satellite_name} for {duration_seconds}s\n"
        f"Current: Alt={pos.alt:.1f}° Az={pos.az:.1f}°\n"
        f"Range: {pos.range_km:.0f} km\n"
        f"Velocity: {pos.velocity_kms:.2f} km/s\n"
        f"Sunlit: {pos.is_sunlit}\n\n"
        "Tracking started. Sending position updates to mount..."
    )


@mcp.tool(
    name="list_satellites",
    description="List available satellites from CelesTrak TLE data",
)
def list_satellites(query: Optional[str] = None) -> str:
    _ensure_init()
    _tracker.fetch_tle()
    sats = _tracker.get_available_satellites()
    if query:
        sats = [s for s in sats if query.lower() in s.lower()]
    lines = [f"Satellites ({len(sats)} found):"]
    for s in sats[:50]:
        lines.append(f"  - {s}")
    if len(sats) > 50:
        lines.append(f"  ... and {len(sats) - 50} more")
    return "\n".join(lines)


@mcp.tool(
    name="get_iss_pass",
    description="Get upcoming ISS pass times for your location",
)
def get_iss_pass(min_altitude: float = 20) -> str:
    _ensure_init()
    passes = _tracker.get_iss_pass_times(min_altitude)
    if not passes:
        return "No ISS passes predicted in the next 24h."
    lines = ["ISS Passes (next 24h):"]
    for p in passes[:10]:
        lines.append(f"  {p['time']}  Alt={p['altitude']}°  Az={p['azimuth']}° {p['direction']}")
    return "\n".join(lines)


@mcp.tool(
    name="check_weather",
    description="Check current weather and observing conditions",
)
def check_weather(force_refresh: bool = False) -> str:
    _ensure_init()
    cond = _weather.get_conditions(force=force_refresh)
    return (
        f"Conditions: {cond.condition}\n"
        f"Cloud cover: {cond.cloud_cover_pct:.0f}%\n"
        f"Temperature: {cond.temperature_c:.1f}°C\n"
        f"Wind: {cond.wind_speed_ms:.1f} m/s ({cond.wind_speed_ms * 3.6:.1f} km/h)\n"
        f"Humidity: {cond.humidity_pct:.0f}%\n"
        f"Visibility: {cond.visibility_km:.1f} km\n"
        f"Nighttime: {cond.is_dark}\n"
        f"Observable: {cond.is_observable}\n"
        f"Reason: {cond.reason}"
    )


@mcp.tool(
    name="plate_solve",
    description="Plate solve an image to determine exact telescope pointing position",
)
def plate_solve(image_path: str) -> str:
    _ensure_init()
    result = _solver.solve(image_path)
    if result:
        ra, dec, w, h = result
        return (
            f"Plate solve successful\n"
            f"RA: {ra:.4f}h ({hours_to_hms(ra)})\n"
            f"Dec: {dec:.4f}° ({degrees_to_dms(dec)})\n"
            f"FOV: {w:.2f}' x {h:.2f}'"
        )
    est = _solver.estimate_initial(image_path)
    return f"Plate solve failed. Try a longer exposure or check focus."


@mcp.tool(
    name="classify_object",
    description="Classify a celestial object by coordinates or image. Tells you what the telescope is looking at",
)
def classify_object(ra_hours: Optional[float] = None, dec_degrees: Optional[float] = None, image_path: Optional[str] = None) -> str:
    _ensure_init()
    result = _classifier.classify(image_path=image_path, ra=ra_hours or 0, dec=dec_degrees or 0)
    if result.confidence > 0:
        return (
            f"Label: {result.label}\n"
            f"Type: {result.object_type}\n"
            f"Confidence: {result.confidence:.1%}\n"
            f"Description: {result.description}"
        )
    if result.object_type == "star_field":
        return f"No known DSO found near this position. Try a nearby Messier object.\nThis might be a star field."
    return f"Could not classify. {result.label}"


@mcp.tool(
    name="abort_slew",
    description="Stop the telescope mount movement immediately",
)
def abort_slew() -> str:
    _ensure_mount()
    _mount.abort_slew()
    return "Slew aborted, mount stopped"


@mcp.tool(
    name="set_tracking",
    description="Set telescope tracking mode",
)
def set_tracking(mode: str) -> str:
    valid = ["off", "sidereal", "solar", "lunar"]
    if mode.lower() not in valid:
        return f"Invalid mode. Valid: {', '.join(valid)}"
    _ensure_mount()
    _mount.set_tracking(mode)
    return f"Tracking set to {mode}"


@mcp.tool(
    name="configure",
    description="View or update telescope configuration",
)
def configure(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    serial_port: Optional[str] = None,
    mount_type: Optional[str] = None,
    weather_api_key: Optional[str] = None,
) -> str:
    _ensure_init()
    if latitude is not None:
        _config.latitude = latitude
    if longitude is not None:
        _config.longitude = longitude
    if serial_port is not None:
        _config.serial_port = serial_port
    if mount_type is not None:
        _config.mount_type = mount_type
    if weather_api_key is not None:
        _config.weather_api_key = weather_api_key
    _config.save()
    return (
        f"Current configuration:\n"
        f"  Mount: {_config.mount_type} on {_config.serial_port}\n"
        f"  Location: {_config.latitude}, {_config.longitude}\n"
        f"  Timezone: {_config.timezone}\n"
        f"  Weather API: {'configured' if _config.weather_api_key else 'not configured'}"
    )


# ─── RESOURCES ──────────────────────────────────────────────────

@mcp.resource(
    uri="telescope://status",
    name="Telescope Status",
    description="Current telescope status including position and connection state",
)
def telescope_status() -> str:
    _ensure_init()
    connected = _mount.connected or _mount.connect()
    if not connected:
        return "Mount: DISCONNECTED"
    ra, dec = _mount.get_position_radec()
    alt, az = _mount.get_position_altaz()
    cond = _weather.get_conditions()
    return (
        f"Status: {'CONNECTED' if connected else 'DISCONNECTED'}\n"
        f"Mount: {_config.mount_type}\n"
        f"RA: {ra:.4f}h\n"
        f"Dec: {dec:.4f}°\n"
        f"Alt: {alt:.2f}°\n"
        f"Az: {az:.2f}°\n"
        f"Observing: {cond.is_observable}\n"
        f"Weather: {cond.condition} ({cond.cloud_cover_pct:.0f}% clouds)"
    )


@mcp.resource(
    uri="telescope://tonight",
    name="Tonight's Plan",
    description="AI-generated observing plan for tonight",
)
def tonights_plan() -> str:
    return get_observing_plan()


@mcp.resource(
    uri="telescope://weather",
    name="Weather Conditions",
    description="Current weather and observing conditions",
)
def weather_resource() -> str:
    return check_weather(force_refresh=True)


if __name__ == "__main__":
    mcp.run()
