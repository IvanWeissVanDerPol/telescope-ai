# API Reference

## Python Library

### MountController

```python
from telescope_ai import MountController, TelescopeConfig

config = TelescopeConfig.load()
mount = MountController(config)
mount.connect()                     # Connect to mount/simulator
mount.goto_radec(5.583, -5.383)     # Slew to M42
ra, dec = mount.get_position_radec()  # Read position
alt, az = mount.get_position_altaz()
mount.set_tracking("sidereal")      # Set tracking mode
mount.abort_slew()                  # Emergency stop
mount.disconnect()
```

### SatelliteTracker

```python
from telescope_ai import SatelliteTracker

tracker = SatelliteTracker(config)
tracker.fetch_tle()                 # Download from CelesTrak
sats = tracker.get_available_satellites()  # ["ISS (ZARYA)", ...]
pos = tracker.get_current_position("ISS (ZARYA)")
# pos.alt, pos.az, pos.range_km, pos.velocity_kms, pos.is_sunlit
passes = tracker.get_iss_pass_times(min_altitude=20)
```

### NightScheduler

```python
from telescope_ai import NightScheduler

scheduler = NightScheduler(config, weather_service)
plan = scheduler.generate_plan(max_targets=5)
# plan[0].target.name, plan[0].altitude, plan[0].reason
```

### PlateSolver

```python
from telescope_ai import PlateSolver

solver = PlateSolver(config)
result = solver.solve("/path/to/image.jpg")  # (ra, dec, width, height) or None
```

### ObjectClassifier

```python
from telescope_ai import ObjectClassifier

classifier = ObjectClassifier(config)
result = classifier.classify(ra=5.583, dec=-5.383)
# result.label, result.object_type, result.confidence, result.description
```

### WeatherService

```python
from telescope_ai import WeatherService

weather = WeatherService(config)
conditions = weather.get_conditions()
# conditions.cloud_cover_pct, conditions.is_observable, conditions.temperature_c
```

## CLI

```bash
telescope-ai <command> [options]
```

### Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `connect` | `--type {nexstar,simulator}` | Connect to mount |
| `goto` | `--ra FLOAT --dec FLOAT` | Slew to RA/Dec |
| `position` | — | Current position |
| `plan` | `--max INT` | Night plan |
| `satellite` | `{list,track,predict,iss}` | Satellite ops |
| `weather` | — | Weather check |
| `platesolve` | `IMAGE_PATH` | Plate solve |
| `classify` | `--ra FLOAT --dec FLOAT --image PATH` | Classify |
| `demo` | — | Full demo |

## MCP Server

### Tools

All tools accept keyword arguments and return strings.

| Tool | Args | Returns |
|------|------|---------|
| `health_check` | — | Status string |
| `get_position` | — | Coordinates string |
| `goto_target` | `target_name?`, `ra_hours?`, `dec_degrees?` | Confirmation |
| `get_observing_plan` | `max_targets: int = 5` | Plan string |
| `track_satellite` | `satellite_name: str`, `duration_seconds: int` | Status |
| `list_satellites` | `query: str?` | List |
| `get_iss_pass` | `min_altitude: float = 20` | Pass times |
| `check_weather` | `force_refresh: bool = False` | Conditions |
| `plate_solve` | `image_path: str` | Solution |
| `classify_object` | `ra_hours?`, `dec_degrees?`, `image_path?` | Classification |
| `abort_slew` | — | Confirmation |
| `set_tracking` | `mode: str` | Confirmation |
| `configure` | `latitude?`, `longitude?`, etc. | Config |

### Resources

| URI | Name | Returns |
|-----|------|---------|
| `telescope://status` | Telescope Status | Current status |
| `telescope://tonight` | Tonight's Plan | Observing plan |
| `telescope://weather` | Weather | Conditions |

## Configuration

~/.config/telescope-ai/config.yaml:

```yaml
mount_type: simulator         # nexstar | simulator
serial_port: /dev/ttyUSB0     # COM1 on Windows
serial_baud: 9600
latitude: -25.2637            # Your latitude
longitude: -57.5759           # Your longitude
elevation_m: 100
timezone: America/Asuncion
camera_type: simulator        # simulator | asi | dslr | phone
weather_api_key: ""           # OpenWeatherMap API key
astap_path: astap             # ASTAP binary path
tle_url: https://celestrak.org/NORAD/elements/stations.txt
satellite_update_interval_s: 1.5
```
