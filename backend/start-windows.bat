@echo off
setlocal
cd /d "%~dp0"

echo.
echo === Video Downloader: project-local yt-dlp and FFmpeg ===
echo This downloads the tools into the repository's tools folder.
echo Internet access is required for the first setup.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-tools-windows.ps1"
if errorlevel 1 (
  echo.
  echo Tool setup failed. Check your internet connection and try again.
  pause
  exit /b 1
)

echo.
echo Starting the local service...
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py
) else (
  python server.py
)
if errorlevel 1 (
  echo.
  echo Could not start the local service. Install Python 3 and make sure it is on PATH.
  pause
)
