# ============================================================
# Fraud Detection System - Installation Script (Windows)
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Fraud Detection System - Installation Wizard" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Function to display status
function Show-Status {
    param($Message, $Status)
    if ($Status -eq "OK") {
        Write-Host "[✓] $Message" -ForegroundColor Green
    }
    elseif ($Status -eq "WARN") {
        Write-Host "[!] $Message" -ForegroundColor Yellow
    }
    else {
        Write-Host "[✗] $Message" -ForegroundColor Red
    }
}

# Step 1: Check Prerequisites
Write-Host "[Step 1/6] Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check Python
if (Test-Command python) {
    $pythonVersion = python --version
    Show-Status "Python installed: $pythonVersion" "OK"
} else {
    Show-Status "Python not found! Please install Python 3.9+" "ERROR"
    exit 1
}

# Check pip
if (Test-Command pip) {
    Show-Status "pip installed" "OK"
} else {
    Show-Status "pip not found!" "ERROR"
    exit 1
}

# Check PostgreSQL
if (Test-Command psql) {
    Show-Status "PostgreSQL installed" "OK"
} else {
    Show-Status "PostgreSQL not found! Please install PostgreSQL 13+" "WARN"
}

Write-Host ""

# Step 2: Create Virtual Environment
Write-Host "[Step 2/6] Setting up virtual environment..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "venv") {
    Show-Status "Virtual environment already exists" "OK"
} else {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    if ($?) {
        Show-Status "Virtual environment created" "OK"
    } else {
        Show-Status "Failed to create virtual environment" "ERROR"
        exit 1
    }
}

Write-Host ""

# Step 3: Activate Virtual Environment
Write-Host "[Step 3/6] Activating virtual environment..." -ForegroundColor Yellow
Write-Host ""

$activateScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Show-Status "Activation script found" "OK"
    Write-Host ""
    Write-Host "Please run the following command manually:" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Then run: .\install.ps1 -Continue" -ForegroundColor Cyan
} else {
    Show-Status "Activation script not found" "ERROR"
    exit 1
}

Write-Host ""
Write-Host "Installation paused. Activate the virtual environment and continue." -ForegroundColor Yellow
Write-Host ""
