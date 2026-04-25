# Telescope AI Windows Installer
param(
    [switch]$SystemWide
)

Write-Host "=== Telescope AI Installer (Windows) ===" -ForegroundColor Cyan

# Check Python
$python = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $python = $cmd
                break
            }
        }
    } catch {}
}

if (-not $python) {
    Write-Host "ERROR: Python 3.10+ required." -ForegroundColor Red
    Write-Host "Download from: https://python.org"
    exit 1
}

Write-Host "Found: $(& $python --version)" -ForegroundColor Green

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    & $python -m venv venv
}

# Activate
$activate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"
. $activate

# Upgrade pip
pip install --upgrade pip -q

# Install
Write-Host "Installing telescope-ai..."
pip install -e ".[all]" -q

# Install FastMCP
pip install fastmcp -q

# Create config directory
$configDir = "$env:USERPROFILE\.config\telescope-ai"
New-Item -ItemType Directory -Force -Path $configDir | Out-Null

# Default config
$configPath = Join-Path $configDir "config.yaml"
if (-not (Test-Path $configPath)) {
    Copy-Item "config\telescope.yaml.example" $configPath -ErrorAction SilentlyContinue
    Write-Host "Default config created at $configPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Installation complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick test with simulator:"
Write-Host "  venv\Scripts\activate"
Write-Host "  telescope-ai connect --type simulator"
Write-Host "  telescope-ai position"
Write-Host "  telescope-ai plan --max 3"
Write-Host ""
Write-Host "Run MCP server (for AI access):"
Write-Host "  fastmcp run mcp_server/server.py:mcp"
Write-Host ""
Write-Host "For ASCOM/CPWI:"
Write-Host "  1. Install ASCOM Platform: https://ascom-standards.org"
Write-Host "  2. Install CPWI: https://celestron.com/pages/celestron-pwi-telescope-control-software"
Write-Host ""
Write-Host "Connect to real telescope:"
Write-Host "  telescope-ai connect --type nexstar"
