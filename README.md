# Video Downloader

A Windows-friendly desktop video downloader built with Python, Tkinter, and yt-dlp. It supports YouTube and the many additional websites supported by yt-dlp. Support varies by site and may change when a site updates its service.

## Features
- Desktop interface for pasting a video or playlist URL
- Best available quality, or a 1080p, 720p, or 480p cap
- Audio-only MP3 extraction (requires FFmpeg)
- Progress, transfer speed, and estimated time remaining
- Choose a save folder and open it from the app
- Retries for transient download failures

## Requirements
- Python 3.11 or newer
- FFmpeg recommended; required for merging separate video/audio streams and MP3 conversion

## Run on Windows
1. Install Python 3.11+ and enable the Python launcher (`py`).
2. Double-click `run-windows.bat`. It installs the Python dependency and starts the app.

Or run manually in PowerShell:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Update yt-dlp when site support breaks:

```powershell
python -m pip install --upgrade yt-dlp
```

## Notes
- Not every site or video is available; login requirements, regional restrictions, and site changes can affect downloads.
- This project does not bypass DRM, paywalls, or access controls. Only download media you own, have permission to download, or are permitted to download under applicable site terms and law.
