# Video Downloader — Chrome Extension + yt-dlp

A Chrome Manifest V3 extension with two download paths:
- **Direct media:** find ordinary video/audio URLs exposed by the current page and download them with Chrome.
- **yt-dlp companion service:** use the installed yt-dlp command-line downloader for YouTube and many other supported sites.
- **MP3 extraction:** use FFmpeg through yt-dlp's audio-extraction options.
- **No artificial extension queue-count or file-size cap.** Actual limits still depend on the website, storage, Chrome, and the tools involved.

## Requirements for yt-dlp downloads
- Python 3.9+ for the local bridge.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp), installed and available on your PATH.
- [FFmpeg](https://ffmpeg.org/download.html), with ffmpeg available on your PATH. FFmpeg is required for MP3 extraction and often helps merge separate video/audio streams.
- Google Chrome.

Update yt-dlp regularly because supported sites can change.

## Windows setup
1. Install Python 3 and make sure the Python launcher (py) or python command works.
2. Install yt-dlp using its official instructions. For example, if Python's pip is available, run **py -m pip install -U yt-dlp**.
3. Install FFmpeg and add its bin directory to your Windows PATH. Open a new terminal and verify **yt-dlp --version** and **ffmpeg -version**.
4. In this repository, double-click **backend/start-windows.bat**. Keep its terminal window open while using the extension.
5. Open chrome://extensions, enable **Developer mode**, choose **Load unpacked**, and select the repository folder containing manifest.json.
6. Open a video page, click the extension icon, paste the page URL into **Video or supported site URL**, choose video or MP3, and click **Download with yt-dlp**.
7. Files are saved under the Downloads folder named VideoDownloader in your user profile. Diagnostic .log files are also written there.

## Other operating systems
Install Python 3, yt-dlp, and FFmpeg using their official instructions, then run **python3 backend/server.py** from the repository root (or run **python3 server.py** from the backend directory). Keep the service running while using the extension.

## Security notes
- The companion service binds only to 127.0.0.1 and accepts requests from Chrome extension origins, not ordinary websites.
- It invokes yt-dlp with a fixed set of arguments; it does not accept arbitrary command-line arguments.
- The service accepts HTTP/HTTPS URLs. Use it only with content you own, have permission to download, or are otherwise authorized to save. Respect site terms and applicable law. It does not implement DRM circumvention.
- Downloads happen on the computer where the companion service is running; the extension cannot bundle or silently install yt-dlp or FFmpeg.
- Do not expose the local service port to your network.

## Direct-link mode
Direct-link mode scans the active page for common media files such as MP4, WebM, MOV, MKV, MP3, M4A, WAV, OGG, and FLAC, and uses Chrome's built-in download manager. Some sites do not expose direct media URLs, so use the yt-dlp companion mode when the site is supported.

## Limitations and test status
Site support is controlled by yt-dlp and the target site's current behavior; no claim is made that every site works. MP3 conversion depends on FFmpeg and the source's audio availability. This repository update has not yet been runtime-tested in Chrome or end-to-end with installed yt-dlp/FFmpeg.

## Project files
- manifest.json — extension permissions and popup.
- popup.html, popup.css, popup.js — user interface and controls.
- background.js — direct media scanning and downloads.
- backend/server.py — local HTTP bridge to yt-dlp.
- backend/start-windows.bat — Windows launcher.
- backend/requirements.txt — notes about Python dependencies.