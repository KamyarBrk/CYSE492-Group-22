# setup.ps1 - Automatic environment setup for CYSE492 Group 22
# Run this from the repo root directory

Write-Host "`n=== CYSE492 Environment Setup ===" -ForegroundColor Cyan

# --- Check if Python is installed ---
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = & python --version 2>$null

if (-not $pythonVersion) {
    Write-Host "❌ Python not found on this system!" -ForegroundColor Red
    Write-Host "Please install Python 3.12 from the official website before continuing:" -ForegroundColor Yellow
    Write-Host "👉 https://www.python.org/downloads/release/python-3120/" -ForegroundColor Cyan
    Write-Host "`nAfter installing, restart PowerShell and re-run this script." -ForegroundColor DarkGray
    exit 1
}

# --- Verify correct Python version (3.12.x required) ---
if ($pythonVersion -notmatch "3\.12") {
    Write-Host "❌ Detected $pythonVersion, but this project requires Python 3.12." -ForegroundColor Red
    Write-Host "Please install Python 3.12 from:" -ForegroundColor Yellow
    Write-Host "👉 https://www.python.org/downloads/release/python-3120/" -ForegroundColor Cyan
    Write-Host "`nAfter installing, make sure to check 'Add Python to PATH' during setup." -ForegroundColor DarkGray
     Write-Host "`nAlso, go to your settings > apps and uninstall any newer versions of python." -ForegroundColor DarkGray
    Write-Host "Then restart PowerShell and re-run this script." -ForegroundColor DarkGray
    exit 1
}

Write-Host "✅ Python 3.12 detected: $pythonVersion" -ForegroundColor Green

# --- Create virtual environment ---
Write-Host "`nCreating virtual environment (.venv)..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists — skipping creation." -ForegroundColor DarkGray
}

# --- Activate environment ---
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# --- Upgrade pip & tools ---
Write-Host "`nUpgrading pip, setuptools, and wheel..." -ForegroundColor Cyan
pip install --upgrade pip setuptools wheel

# --- Install requirements ---
Write-Host "`nInstalling dependencies from requirements.txt..." -ForegroundColor Cyan
pip install -r "$PSScriptRoot\requirements.txt"

# --- Handle pydantic-core separately (binary preferred) ---
Write-Host "`nEnsuring pydantic-core installs from binary if available..." -ForegroundColor Yellow
pip install pydantic-core==2.33.2 --only-binary=:all: `
    || pip install pydantic-core==2.33.2

# --- Final message ---
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Environment setup complete!" -ForegroundColor Green
    Write-Host "To activate manually later, run:" -ForegroundColor DarkGray
    Write-Host "    .\\.venv\\Scripts\\Activate.ps1" -ForegroundColor Gray
} else {
    Write-Host "`n⚠️ Setup completed with some errors. Check messages above for details." -ForegroundColor Yellow
}
