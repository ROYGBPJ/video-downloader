$ErrorActionPreference = "Stop"
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BackendDir

Write-Host ""
Write-Host "=== Video Downloader: project-local yt-dlp + FFmpeg ==="
Write-Host "Downloading tools into this project if needed..."
try {
    & (Join-Path $BackendDir "setup-tools-windows.ps1")
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "Tool setup script failed."
    }
} catch {
    Write-Error "Tool setup failed: $_"
    exit 1
}

Write-Host ""
Write-Host "Starting the local service. Keep this PowerShell window open."
Write-Host "Chrome extension downloads will be saved under your Downloads\VideoDownloader folder."
Write-Host "Press Ctrl+C to stop the service."
Write-Host ""

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 server.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python server.py
} else {
    Write-Error "Python 3 is required. Install Python 3, then run this script again."
    exit 1
}
