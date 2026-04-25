#!/usr/bin/env bash
set -euo pipefail

echo "=== Telescope AI Installer ==="

# Check Python
PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &>/dev/null; then
        VER=$($cmd --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
        MAJOR=$(echo $VER | cut -d. -f1)
        MINOR=$(echo $VER | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON=$cmd
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.10+ required. Install it first:"
    echo "  sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
echo "Found: $($PYTHON --version)"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtualenv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
fi

source venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# Install package with all extras
echo "Installing telescope-ai..."
pip install -e ".[all]" -q

# Install FastMCP for MCP server
pip install fastmcp -q

# Create config directory
CONFIG_DIR="$HOME/.config/telescope-ai"
mkdir -p "$CONFIG_DIR"

# Copy default config if not exists
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cp config/telescope.yaml.example "$CONFIG_DIR/config.yaml" 2>/dev/null || true
    echo "Default config created at $CONFIG_DIR/config.yaml"
fi

# Add user to dialout group for serial access (Linux)
if [ "$(uname)" = "Linux" ]; then
    if ! groups "$USER" | grep -q dialout; then
        echo "Adding $USER to dialout group for serial port access..."
        sudo usermod -a -G dialout "$USER" 2>/dev/null || true
        echo "NOTE: You may need to log out and back in for group changes to take effect."
    fi
fi

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Quick test with simulator:"
echo "  source venv/bin/activate"
echo "  telescope-ai connect --type simulator"
echo "  telescope-ai position"
echo "  telescope-ai plan --max 3"
echo ""
echo "Run MCP server (for AI access):"
echo "  fastmcp run mcp_server/server.py:mcp"
echo ""
echo "Connect to real telescope:"
echo "  telescope-ai connect --type nexstar"
