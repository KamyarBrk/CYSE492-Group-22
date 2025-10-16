<#
.SYNOPSIS
  Create a Python virtual environment and install dependencies from requirements.txt,
  and (optionally) activate it automatically.

.USAGE
  Dot-source to create AND keep the venv activated in your current session:
    . .\setup.ps1

  Run normally and open a new PowerShell window WITH the activated venv:
    .\setup.ps1 -AutoOpenTerminal

PARAMS
  -VenvDir (default ".venv")
  -AutoOpenTerminal : open a new PowerShell window with the venv activated (useful if you didn't dot-source)
  -MinPythonVersion / -MaxPythonVersion for version enforcement
#>

param(
    [string]$VenvDir = ".venv",
    [string]$PythonExe = "python",
    [string]$RequirementsFile = "requirements.txt",
    [Version]$MinPythonVersion = "3.10.0",
    [Version]$MaxPythonVersion = "3.12.8",
    [switch]$AutoOpenTerminal
)

function Write-ErrorAndExit($msg, [int]$code = 1) {
    Write-Host ""
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit $code
}

# Detect if script was dot-sourced (then activation can change the caller's session)
$dotSourced = $false
if ($MyInvocation.InvocationName -eq '.') { $dotSourced = $true }

Write-Host "== Setup script starting =="

# Resolve python executable (try python then python3)
$pythonCandidates = @($PythonExe, "python3") | Select-Object -Unique
$foundPython = $null
$foundVersion = $null

foreach ($cand in $pythonCandidates) {
    try {
        $verOut = & $cand -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>&1
        if ($LASTEXITCODE -eq 0 -or ($verOut -and $verOut -match '^\d+\.\d+(\.\d+)?$')) {
            try {
                $foundVersion = [Version]$verOut.Trim()
                $foundPython = $cand
                break
            } catch {
                # parse failed - continue
            }
        }
    } catch {
        # ignore and try next
    }
}

if (-not $foundPython) {
    Write-ErrorAndExit "No usable Python executable found. Make sure 'python' or 'python3' is on PATH."
}

Write-Host "Found Python executable: $foundPython (version $foundVersion)"

# Enforce minimum and maximum Python versions
if ($foundVersion -lt $MinPythonVersion) {
    Write-ErrorAndExit "Python version $foundVersion found but minimum required is $MinPythonVersion. Please install a newer Python."
}

if ($foundVersion -gt $MaxPythonVersion) {
    Write-ErrorAndExit "Python version $foundVersion is newer than the maximum supported version $MaxPythonVersion. Please use Python $MaxPythonVersion or earlier."
}

# Check requirements.txt exists
if (-not (Test-Path $RequirementsFile)) {
    Write-ErrorAndExit "Requirements file '$RequirementsFile' not found in $(Get-Location)."
}

# Create venv (if not present)
$venvPath = (Resolve-Path -LiteralPath $VenvDir -ErrorAction SilentlyContinue)
if ($venvPath) {
    Write-Host "Virtual environment directory '$VenvDir' already exists. Skipping creation."
} else {
    Write-Host "Creating virtual environment in '$VenvDir'..."
    $createResult = & $foundPython -m venv $VenvDir 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host $createResult
        Write-ErrorAndExit "Failed to create virtual environment."
    }
    Write-Host "Virtual environment created."
}

# Determine python executable inside venv
$venvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = Join-Path $VenvDir "bin/python"
}

if (-not (Test-Path $venvPython)) {
    Write-ErrorAndExit "Unable to locate python inside the virtual environment at '$VenvDir'."
}

# Upgrade pip and install requirements
Write-Host "Upgrading pip inside venv..."
& $venvPython -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-ErrorAndExit "Failed to upgrade pip inside virtual environment."
}

Write-Host "Installing requirements from '$RequirementsFile'..."
& $venvPython -m pip install -r $RequirementsFile
if ($LASTEXITCODE -ne 0) {
    Write-ErrorAndExit "pip install failed. See output above for errors."
}

Write-Host ""
Write-Host "== Success! Dependencies installed. ==" -ForegroundColor Green
Write-Host ""

# Activation handling
$activatePs1 = Join-Path $VenvDir "Scripts\Activate.ps1"
$activatePs1Unix = Join-Path $VenvDir "bin/activate"

if (Test-Path $activatePs1) {
    if ($dotSourced) {
        Write-Host "Dot-sourced run detected — activating venv in current session..."
        . $activatePs1
        Write-Host "Activated. (Run 'deactivate' to exit the venv.)" -ForegroundColor Green
    } elseif ($AutoOpenTerminal) {
        Write-Host "Opening a new PowerShell window with the venv activated..."
        # Start a new PowerShell window that sources the Activate.ps1 and stays open
        $actPathFull = (Resolve-Path $activatePs1).Path
        Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", ". `"$actPathFull`""
        Write-Host "New PowerShell window started and activated." -ForegroundColor Green
    } else {
        Write-Host "To activate the virtual environment in this session, run (one line):" -ForegroundColor Cyan
        Write-Host "  . $PWD\$activatePs1" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Or run this script by dot-sourcing to auto-activate:" -ForegroundColor Yellow
        Write-Host "  . .\\setup.ps1" -ForegroundColor Yellow
    }
} elseif (Test-Path $activatePs1Unix) {
    Write-Host "For Unix shells, activate with:" -ForegroundColor Cyan
    Write-Host "  source $PWD/$activatePs1Unix" -ForegroundColor Cyan
} else {
    Write-Host "Activation script not found — you can still use $venvPython directly." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Notes:"
Write-Host "- This repository requires Python versions between $MinPythonVersion and $MaxPythonVersion (inclusive)." -ForegroundColor Yellow
Write-Host "- If you see 'running scripts is disabled on this system', run (one-time for current user):" -ForegroundColor Yellow
Write-Host "    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
Write-Host "  Or run the setup non-persistently with:"
Write-Host "    powershell -ExecutionPolicy Bypass -File .\\setup.ps1"
Write-Host ""
Write-Host "Done. Click the '+' icon in the top right of the terminal to open a new terminal in the venv." -ForegroundColor Yellow
Write-Host "You should then see '(.venv)' in green." -ForegroundColor Yellow
Write-Host ""