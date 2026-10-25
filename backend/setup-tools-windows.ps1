$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ToolsRoot = Join-Path $ProjectRoot "tools"
$FfmpegBin = Join-Path $ToolsRoot "ffmpeg\bin"
$TempRoot = Join-Path $env:TEMP ("VideoDownloaderTools-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $ToolsRoot, $FfmpegBin, $TempRoot | Out-Null

try {
    Write-Host "Downloading yt-dlp into the project tools folder..."
    $YtDlpPath = Join-Path $ToolsRoot "yt-dlp.exe"
    Invoke-WebRequest -Uri "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" -OutFile $YtDlpPath

    Write-Host "Downloading the FFmpeg Windows essentials build..."
    $ZipPath = Join-Path $TempRoot "ffmpeg.zip"
    $ExtractPath = Join-Path $TempRoot "ffmpeg"
    Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $ZipPath
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExtractPath -Force

    $FfmpegExe = Get-ChildItem -LiteralPath $ExtractPath -Filter "ffmpeg.exe" -File -Recurse | Select-Object -First 1
    $FfprobeExe = Get-ChildItem -LiteralPath $ExtractPath -Filter "ffprobe.exe" -File -Recurse | Select-Object -First 1
    if (-not $FfmpegExe -or -not $FfprobeExe) {
        throw "The FFmpeg archive did not contain ffmpeg.exe and ffprobe.exe."
    }
    Copy-Item -LiteralPath $FfmpegExe.FullName -Destination (Join-Path $FfmpegBin "ffmpeg.exe") -Force
    Copy-Item -LiteralPath $FfprobeExe.FullName -Destination (Join-Path $FfmpegBin "ffprobe.exe") -Force

    Write-Host ""
    Write-Host "Tools are now stored inside your Video Downloader project:"
    Write-Host "  $YtDlpPath"
    Write-Host "  $(Join-Path $FfmpegBin 'ffmpeg.exe')"
    Write-Host "  $(Join-Path $FfmpegBin 'ffprobe.exe')"
    Write-Host "The downloaded executables are local project files; they are not embedded into Chrome itself."
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
