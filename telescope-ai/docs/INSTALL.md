# Installation Guide

## Prerequisites

| Item | Required | Notes |
|------|----------|-------|
| Python 3.10+ | Yes | Check with `python3 --version` |
| USB-serial cable | For real mount | Celestron #93920 or generic FTDI |
| Celestron NexStar 130SLT | For real mount | Works with mount connected or simulator |

## Step 1: Install the Package

### Option A: From Source (recommended)

```bash
git clone https://github.com/your-org/telescope-ai.git
cd telescope-ai
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Option B: Quick pip install

```bash
pip install telescope-ai
```

### Option C: Dev install (includes testing tools)

```bash
pip install -e ".[dev]"
```

## Step 2: Configure

### Generate initial config:

```bash
telescope-ai connect --type simulator
```

This creates `~/.config/telescope-ai/config.yaml`. Edit it:

```yaml
mount_type: nexstar        # nexstar or simulator
serial_port: /dev/ttyUSB0  # Linux; use COM1 on Windows
serial_baud: 9600
latitude: -25.2637         # Your latitude
longitude: -57.5759        # Your longitude
timezone: America/Asuncion
weather_api_key: ""        # Optional: openweathermap.org API key
astap_path: astap          # Path to ASTAP binary (if installed)
```

### Windows users:

Change `serial_port` to `COM1` (or whatever COM port the USB-serial adapter appears as).

## Step 3: Verify Connection

### Test with simulator (no telescope needed):

```bash
telescope-ai connect --type simulator
telescope-ai position
telescope-ai plan --max 3
telescope-ai weather
```

Expected output:
```
Connected to simulator mount
RA=0.0000h  Dec=0.0000°
Alt=45.00°  Az=180.00°
```

### Test with real telescope:

1. Connect USB-serial cable to hand controller and laptop
2. Turn on telescope
3. Run:

```bash
telescope-ai connect --type nexstar
telescope-ai position
telescope-ai goto --ra 5.583 --dec -5.383
```

## Step 4: Install the MCP Server

The MCP server is what lets AI agents (Claude, Hermes, any LLM) control the telescope.

### Install FastMCP:

```bash
pip install fastmcp
```

### Test the MCP server:

```bash
# List available tools
fastmcp list mcp_server/server.py:mcp --json

# Call health check
fastmcp call mcp_server/server.py:mcp health_check --json

# Generate a night plan
fastmcp call mcp_server/server.py:mcp get_observing_plan max_targets=3 --json
```

### Install into Claude Code:

```bash
fastmcp install claude-code mcp_server/server.py
```

### Install into Claude Desktop:

```bash
fastmcp install claude-desktop mcp_server/server.py
```

### Run as HTTP server:

```bash
fastmcp run mcp_server/server.py:mcp --transport http --host 127.0.0.1 --port 8080
```

Then any AI agent can call `http://127.0.0.1:8080/mcp` with standard MCP requests.

## Step 5: Install Optional Dependencies

### For satellite tracking:

```bash
pip install skyfield
```

### For direct mount serial control:

```bash
pip install nexstar-control
```

### For weather API:

1. Sign up at https://openweathermap.org/api
2. Get a free API key
3. Add it to config: `weather_api_key: your_key_here`

### For plate solving:

1. Download ASTAP from https://hnsky.org/astap.htm
2. Install it and note the binary path
3. Set `astap_path` in config
4. Download the GAIA star catalog (ASTAP will prompt)

### For camera control (ZWO):

```bash
pip install zwoasi
```

## Step 6: Windows-Specific Setup

### Install ASCOM Platform:

1. Download from https://ascom-standards.org
2. Install ASCOM Platform 6.6+
3. Install Celestron Telescope Driver (comes with CPWI)
4. Download CPWI from https://celestron.com/pages/celestron-pwi-telescope-control-software

### Install N.I.N.A. (optional, for automated imaging):

1. Download from https://nighttime-imaging.eu
2. Install .NET 8.0 if not present
3. Launch N.I.N.A., configure mount via ASCOM

### Install SharpCap (optional, for live viewing):

1. Download from https://sharpcap.co.uk
2. Basic version is free, Pro is £15/year

### Driver installation:

```powershell
# Install USB-serial driver (if needed)
# Prolific PL2303 or FTDI - Windows usually auto-detects
```

## Step 7: Linux/Raspberry Pi Setup

### Install INDI/KStars (alternative to ASCOM):

```bash
sudo apt update
sudo apt install indi-full kstars-bleeding
```

### Install as a service (auto-start on boot):

```bash
# Create systemd service
sudo cp scripts/telescope-ai.service /etc/systemd/system/
sudo systemctl enable telescope-ai
sudo systemctl start telescope-ai
```

## Step 8: Verify Everything Works

Run the full test suite:

```bash
# Unit tests
python -m pytest tests/ -v

# Integration test (simulator)
telescope-ai demo

# MCP server smoke test
fastmcp call mcp_server/server.py:mcp health_check --json
```

## Troubleshooting

### Cannot connect to mount

```
Error: Failed to connect on /dev/ttyUSB0
```

- Check cable: `ls /dev/ttyUSB*` or `ls /dev/tty.usb*` (macOS)
- On Windows, check Device Manager for COM port number
- Ensure telescope is powered on
- Try: `pip install pyserial` and test with:
  ```python
  import serial
  s = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
  print(s.write(b"K#\n"))  # should return 3
  ```

### No such file or directory: 'astap'

- Install ASTAP from https://hnsky.org/astap.htm
- Or set `mount_type: simulator` to test without plate solving

### fastmcp: command not found

- Run: `pip install fastmcp`
- Or use: `python -m fastmcp` instead

### ModuleNotFoundError: No module named 'skyfield'

- Satellite tracking requires skyfield: `pip install skyfield`

### Permission denied on /dev/ttyUSB0 (Linux)

```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```
