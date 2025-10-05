# Filename: run.ps1
# Usage: ./run.ps1 [--skip-pip]

param(
    [switch]$skip_pip
)

# Ensure virtual environment exists
if (!(Test-Path ".venv/Scripts/Activate.ps1")) {
    Write-Host "Error: .venv not found. Please create your virtual environment first."
    exit 1
}

# Activate the virtual environment
Write-Host "Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

# Conditional pip install
if (-not $skip_pip) {
    Write-Host "Installing package..."
    pip install -e .
} else {
    Write-Host "Skipping pip install."
}

# Start muselsl stream in background
Write-Host "Starting muselsl stream..."
Start-Process -NoNewWindow -FilePath "muselsl" -ArgumentList "stream"

# Wait for stream to start
Start-Sleep -Seconds 10

# Start muselsl view in background
Write-Host "Starting muselsl view..."
Start-Process -NoNewWindow -FilePath "muselsl" -ArgumentList "view"

# Run blinklet
Write-Host "Running blinklet..."
blinklet