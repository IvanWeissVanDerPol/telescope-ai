# Features

## 1. Mount Control

### Capabilities
- **Connect/Disconnect**: Serial connection to NexStar hand controller
- **Goto RA/Dec**: Point telescope at any right ascension and declination
- **Goto Alt/Az**: Point using altitude and azimuth
- **Position Read**: Get current RA/Dec and Alt/Az
- **Slew Control**: Fixed-rate and variable-rate manual slewing
- **Tracking**: Sidereal, solar, lunar, or off
- **Abort**: Emergency stop

### Protocol
Uses the Celestron NexStar serial protocol (9600 baud, 8N1) documented at nexstarsite.com. Commands are sent as ASCII strings terminated with `#`.

### Simulator
Built-in mount simulator for development and testing without hardware. Simulates 2-second slew times and random star fields.

## 2. Satellite Tracking

### Capabilities
- **TLE Fetch**: Downloads orbital elements from CelesTrak
- **Satellite Database**: Maintains searchable cache of tracked objects
- **Pass Prediction**: Calculates upcoming visible passes for any satellite
- **Real-Time Position**: Current Alt/Az/range/velocity for any satellite
- **ISS Integration**: Dedicated ISS pass calculation
- **Auto-Tracking**: Continuously slews mount to follow satellite
- **Direction**: Cardinal direction labels (N, NE, E, etc.)

### Libraries
- `skyfield` for orbital mechanics and coordinate transforms
- CelesTrak REST API for TLE data
- Supports any satellite with two-line element data

### Satellite Sources
- Space stations (ISS, Tiangong)
- Starlink constellations
- Weather satellites (NOAA, GOES)
- Amateur radio satellites (AMSAT)
- Any satellite in the CelesTrak catalog

## 3. AI Night Scheduler

### Target Database
Pre-loaded with 15+ targets optimized for Southern Hemisphere (-25° latitude):
- Messier objects (M42, M31, M45, M13)
- NGC objects (Omega Centauri, 47 Tucanae, Carina Nebula, Tarantula Nebula)
- Magellanic Clouds (LMC, SMC)
- Planets (Jupiter, Saturn, Mars)
- Southern exclusives (Jewel Box, Eta Carinae)

### Scoring Algorithm
Each target is scored on:
- **Altitude**: Higher = better (less atmosphere)
- **Object type**: Planets and clusters score higher
- **Brightness**: Brighter = easier to see
- **Moon phase**: Galaxies/nebulae penalized when moon is up
- **Latitude bonus**: Southern hemisphere gems get extra points
- **Weather**: Integrates with weather service

### Output
Returns a ranked list with: target name, type, altitude, recommended duration, and explanation of why it was chosen.

## 4. Object Classification

### Coordinate-Based
Looks up known objects within 5° of given RA/Dec. Returns:
- Object name and catalog ID
- Type (nebula, galaxy, cluster, planet)
- Confidence score (based on angular distance)
- Description and fun facts

### ML-Ready Architecture
- Interface for loading PyTorch/torchscript models
- Image preprocessing pipeline (resize to 224x224, normalize)
- Extensible: swap in any image classification model

### Known Object Database
15+ deep-sky objects with catalog IDs, descriptions, and approximate magnitudes.

## 5. Plate Solving

### ASTAP Integration
- Calls ASTAP binary for local plate solving
- Sub-arcsecond accuracy in <3 seconds
- Returns RA, Dec, field of view

### Astrometry.net Integration
- HTTP client for local or remote astrometry.net instances
- Works with ansvr (local astrometry.net server)

### Image Quality Estimation
- Pre-solve analysis: star count estimation, brightness distribution
- Validates image quality before attempting solve

## 6. Weather Service

### OpenWeatherMap Integration
- Current conditions: temperature, humidity, wind, clouds
- Sunrise/sunset times for darkness calculation
- Observability score based on cloud cover, wind, and darkness

### Caching
- 5-minute cache to avoid API rate limits
- Force-refresh option for up-to-date checks

### Offline Fallback
- Works without API key (assumes clear skies, checks hour for darkness)
- Graceful degradation when API is unreachable

## 7. Camera Control

### Simulator
Generates synthetic star field images with:
- Poisson noise distribution
- Random star positions and brightnesses
- Configurable exposure time

### ZWO ASI Camera Support
- Connect/disconnect ZWO cameras
- Set exposure time and gain
- Capture frames to NumPy arrays

### Extensible
- Architecture supports adding DSLR (gPhoto), webcam (OpenCV), or phone camera

## 8. MCP Server (AI Interface)

### Tools Exposed
13 MCP tools for AI agent access:

| Tool | Type | Description |
|------|------|-------------|
| `health_check` | Query | Connection + weather status |
| `get_position` | Query | Current RA/Dec/Alt/Az |
| `goto_target` | Action | Slew by name or coordinates |
| `get_observing_plan` | Query | AI-generated night plan |
| `track_satellite` | Action | Follow satellite |
| `list_satellites` | Query | Search satellite database |
| `get_iss_pass` | Query | ISS pass prediction |
| `check_weather` | Query | Observing conditions |
| `plate_solve` | Action | Image plate solving |
| `classify_object` | Query | Object identification |
| `abort_slew` | Action | Emergency stop |
| `set_tracking` | Action | Change tracking mode |
| `configure` | Config | View/update settings |

### Resources Exposed
3 MCP resources (read-only data):

| Resource | URI | Description |
|----------|-----|-------------|
| Telescope Status | `telescope://status` | Current position + weather |
| Tonight's Plan | `telescope://tonight` | AI observing plan |
| Weather | `telescope://weather` | Current conditions |

### Transports
- **stdio**: For Claude Code, Cursor, Claude Desktop
- **HTTP**: For network access (runs on port 8080)

## 9. CLI Interface

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `connect` | Connect to mount | `telescope-ai connect --type nexstar` |
| `goto` | Slew to coordinates | `telescope-ai goto --ra 5.58 --dec -5.38` |
| `position` | Current position | `telescope-ai position` |
| `plan` | Night observing plan | `telescope-ai plan --max 5` |
| `satellite` | Satellite operations | `telescope-ai satellite track --name ISS` |
| `weather` | Weather check | `telescope-ai weather` |
| `platesolve` | Solve an image | `telescope-ai platesolve /tmp/frame.jpg` |
| `classify` | Identify object | `telescope-ai classify --ra 5.58 --dec -5.38` |
| `demo` | Full demo run | `telescope-ai demo` |

## 10. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Agent (Claude/Hermes)                 │
│  "What should I look at tonight? Point at the best target."  │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol
┌────────────────────────┴────────────────────────────────────┐
│                     MCP Server (server.py)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐ │
│  │ Tools    │ │Resources │ │Prompts   │ │ Config          │ │
│  └────┬─────┘ └──────────┘ └──────────┘ └─────────────────┘ │
└───────┼─────────────────────────────────────────────────────┘
        │
┌───────┴─────────────────────────────────────────────────────┐
│               Telescope AI Library (telescope_ai/)            │
│  ┌──────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐  │
│  │Mount │ │Satellite │ │Sched   │ │Classify│ │PlateSolve│  │
│  └──┬───┘ └──────────┘ └────────┘ └────────┘ └──────────┘  │
└─────┼───────────────────────────────────────────────────────┘
      │ Serial (9600 baud)
┌─────┴───────────────────────────────────────────────────────┐
│              Celestron NexStar 130SLT                        │
│           (or SimulatedMount for testing)                    │
└─────────────────────────────────────────────────────────────┘
```
