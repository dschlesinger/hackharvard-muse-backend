# Filename: run.ps1
# Usage: ./run.ps1 [--skip-pip]

param(
    [switch]$skip_pip
)

# Track processes for cleanup
$global:processes = @()

# Cleanup function
function Cleanup {
    Write-Host "`nCleaning up processes..."
    foreach ($proc in $global:processes) {
        if ($proc -and !$proc.HasExited) {
            Write-Host "Stopping process: $($proc.ProcessName) (PID: $($proc.Id))"
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Cleanup complete."
}

# Register cleanup on Ctrl+C
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }
$null = Register-ObjectEvent -InputObject ([Console]) -EventName CancelKeyPress -Action {
    Cleanup
    [Environment]::Exit(0)
}

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
$streamProcess = Start-Process -NoNewWindow -FilePath "muselsl" -ArgumentList "stream" -PassThru
$global:processes += $streamProcess

# Wait for stream to start
Start-Sleep -Seconds 15

# Start muselsl view in background
Write-Host "Starting muselsl view..."
$viewProcess = Start-Process -NoNewWindow -FilePath "muselsl" -ArgumentList "view" -PassThru
$global:processes += $viewProcess

# Run blinklet (foreground process)
Write-Host "Running blinklet..."
$blinkletProcess = Start-Process -NoNewWindow -FilePath "blinklet" -PassThru -Wait
$global:processes += $blinkletProcess

# Cleanup when blinklet exits
Cleanup