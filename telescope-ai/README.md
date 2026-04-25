# Telescope AI

AI-powered telescope control for **Celestron NexStar 130SLT** (and any ASCOM/INDI-compatible mount).

```
               AI Agent
                  │
          ┌───────┴────────┐
          │   MCP Server   │  ← AI talks to telescope via standard protocol
          └───────┬────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
  Mount Ctrl   Plate Solve   Satellite
     │            │            │
     └────────────┼────────────┘
                  │
          ┌───────┴────────┐
          │   NexStar 130  │
          │   (or Sim)     │
          └────────────────┘
```

## Quick Start

```bash
# 1. Install
git clone https://github.com/your-org/telescope-ai.git
cd telescope-ai
pip install -e .
telescope-ai connect --type simulator
telescope-ai position

# 2. Generate observing plan
telescope-ai plan --max 5

# 3. Run the MCP server (for AI access)
fastmcp run mcp_server/server.py:mcp
```

## What It Does

| Feature | CLI | MCP Tool | Description |
|---------|-----|----------|-------------|
| Mount control | `telescope-ai goto --ra --dec` | `goto_target` | Point the telescope anywhere |
| Position read | `telescope-ai position` | `get_position` | Where is the scope pointing? |
| Satellite tracking | `telescope-ai satellite track` | `track_satellite` | Follow ISS/Starlink across the sky |
| Night planning | `telescope-ai plan` | `get_observing_plan` | AI-picks best targets for tonight |
| Weather | `telescope-ai weather` | `check_weather` | Can we observe? |
| Plate solving | `telescope-ai platesolve` | `plate_solve` | Know exactly where you're pointing |
| Object ID | `telescope-ai classify` | `classify_object` | What am I looking at? |
| Health | — | `health_check` | Everything connected? |
| Config | — | `configure` | Set lat/lon, port, API keys |

## Repository Structure

```
telescope-ai/
├── telescope_ai/          # Core Python library
│   ├── mount.py           # Mount control (NexStar serial / simulator)
│   ├── satellite.py       # Satellite tracking (SkyField + CelesTrak)
│   ├── scheduler.py       # AI night scheduler
│   ├── classifier.py      # Object classification from image/coordinates
│   ├── platesolve.py      # Plate solving (ASTAP / astrometry.net)
│   ├── weather.py         # Weather service (OpenWeatherMap)
│   ├── camera.py          # Camera interface (ZWO/DSLR/simulator)
│   ├── config.py          # Configuration management
│   ├── simulator.py       # Mount simulator (no hardware needed)
│   ├── cli.py             # Command-line interface
│   └── utils.py           # Coordinate conversion utilities
├── mcp_server/
│   ├── server.py          # FastMCP server exposing 13 AI tools
│   └── tools.py           # Tool definitions (imported by server)
├── docs/
│   ├── INSTALL.md         # Full installation guide
│   ├── FEATURES.md        # Detailed feature documentation
│   ├── API.md             # API reference for developers
│   ├── HARDWARE.md        # Hardware setup guide
│   └── AI_INTEGRATION.md  # AI integration patterns
├── scripts/               # Demo scripts
├── config/                # Configuration templates
└── tests/                 # Unit tests
```

## AI Integration (MCP)

The MCP server lets any AI agent (Claude Code, Hermes, Cursor, etc.) control the telescope through standard tools.

### Available MCP Tools

| Tool | What it does | When to use |
|------|-------------|-------------|
| `health_check` | Returns connection status + weather | Before any operation |
| `goto_target` | Slew to target by name or RA/Dec | "Point at M42" |
| `get_position` | Read current coordinates | "Where are we?" |
| `get_observing_plan` | AI-generated night plan | "What should I look at tonight?" |
| `track_satellite` | Follow a satellite across the sky | "Track the ISS" |
| `list_satellites` | Query CelesTrak for available sats | "Find Starlink" |
| `get_iss_pass` | Next ISS pass times | "When's the ISS?" |
| `check_weather` | Observing conditions | "Can we observe?" |
| `plate_solve` | Determine pointing from image | "Where am I aimed?" |
| `classify_object` | Identify what we're seeing | "What's this object?" |
| `abort_slew` | Emergency stop | "Stop!" |
| `set_tracking` | Change tracking mode | "Set lunar tracking" |
| `configure` | View/update settings | "Set my latitude" |

### Running the MCP Server

```bash
# Install FastMCP
pip install fastmcp

# Run the server (stdio mode - for Claude Code, etc.)
fastmcp run mcp_server/server.py:mcp

# Run as HTTP endpoint (for network access)
fastmcp run mcp_server/server.py:mcp --transport http --host 0.0.0.0 --port 8080

# List available tools
fastmcp list mcp_server/server.py:mcp --json

# Call a tool directly from CLI
fastmcp call mcp_server/server.py:mcp health_check --json

# Install into Claude Code
fastmcp install claude-code mcp_server/server.py
```

### Registering with Hermes Agent

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  telescope-ai:
    transport: stdio
    command: python
    args: ["-m", "fastmcp", "run", "/path/to/telescope-ai/mcp_server/server.py:mcp"]
```

## CLI Usage

```bash
# Connect (simulator mode for testing)
telescope-ai connect --type simulator

# Connect to real telescope
telescope-ai connect --type nexstar

# Goto coordinates
telescope-ai goto --ra 5.583 --dec -5.383

# Current position
telescope-ai position

# Observing plan
telescope-ai plan --max 5

# Satellite tracking
telescope-ai satellite track --name "ISS (ZARYA)" --duration 120

# Weather
telescope-ai weather

# Plate solve
telescope-ai platesolve /path/to/image.jpg

# Classify what you're looking at
telescope-ai classify --ra 5.583 --dec -5.383

# Full demo
telescope-ai demo
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format
ruff format telescope_ai/ mcp_server/
```

## Requirements

- Python 3.10+
- USB-serial connection to Celestron NexStar hand controller
- Windows (for ASCOM/N.I.N.A./SharpCap) or Linux (for INDI/KStars)
- Optional: weather API key (openweathermap.org)
- Optional: camera (phone adapter, webcam, ZWO, DSLR)
- Optional: `skyfield` for satellite tracking
- Optional: `nexstar-control` for direct mount access

## License

MIT
