# setup.ps1
# ------------------------------
# This script ensures Python 3.12+ is installed,
# sets up a virtual environment, and installs all dependencies.
# ------------------------------

Write-Host "Checking Python version..." -ForegroundColor Cyan
$pythonVersion = & python --version 2>$null

if (-not $pythonVersion) {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.12+." -ForegroundColor Red
    exit 1
}

$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
        Write-Host "Python 3.12+ is required. You have $pythonVersion." -ForegroundColor Red
        exit 1
    }
}

# Set venv name
$venvPath = ".venv"

# Create virtual environment if it doesn't exist
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $venvPath
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
}

# Activate it
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "$venvPath/Scripts/Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install dependencies
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
    pip install -r requirements.txt
} else {
    Write-Host "requirements.txt not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Environment setup complete." -ForegroundColor Green
