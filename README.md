# Video Downloader — Chrome Extension + project-local yt-dlp/FFmpeg

A Google Chrome Manifest V3 extension with two download paths:
- **Direct media:** find ordinary video/audio URLs exposed by the current page and download them with Chrome.
- **yt-dlp downloader:** use yt-dlp for YouTube and many other supported sites.
- **MP3 extraction:** use FFmpeg through yt-dlp's audio-extraction options.
- **No artificial extension queue-count or file-size cap.** Actual limits still depend on the website, storage, Chrome, and the tools involved.

## Windows quick start (no .bat file)

1. Download or extract this repository to a normal writable folder.
2. Install Python 3 if it is not already installed.
3. Open the project folder in File Explorer, then open the `backend` folder.
4. Right-click in the folder and choose **Open in Terminal**.
5. Run this command in PowerShell:
   `powershell -NoProfile -ExecutionPolicy Bypass -File .\setup-and-run-windows.ps1`
6. On the first run, the script downloads yt-dlp and FFmpeg into the project:
   - `tools/yt-dlp.exe`
   - `tools/ffmpeg/bin/ffmpeg.exe`
   - `tools/ffmpeg/bin/ffprobe.exe`
7. For more reliable YouTube extraction, install Node.js (20.18.1 or newer) and make sure `node.exe` is available on PATH. The backend detects Node.js automatically and passes it to yt-dlp as a JavaScript runtime; Node.js is optional for other supported sites.
8. Keep the PowerShell window open while using the extension.
9. Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select the project folder that directly contains `manifest.json`.
10. Open a video page, click the extension icon, paste the page URL into **Video or supported site URL**, choose video or MP3, and click **Download with yt-dlp**.

Files and diagnostic logs are saved in your user profile's `Downloads/VideoDownloader` folder. Internet access is needed for the first tool download. The executables are stored locally in the project folder after setup; they are not embedded into Chrome's extension sandbox.

## Other operating systems

The automatic setup script targets Windows. On other operating systems, install Python 3, yt-dlp, and FFmpeg using their official instructions, then run `python3 backend/server.py` from the project root or `python3 server.py` from the backend directory. The service checks project-local tool paths first and then falls back to PATH.

## Chrome localization manifest fix

The manifest includes `"default_locale": "en"`, which addresses Chrome's error:
`Localization used, but default_locale wasn't specified in the manifest.`

If Chrome still shows the old error, make sure you load the repository folder that directly contains the updated `manifest.json`, not an older nested copy.

## Security notes

- The companion service binds only to `127.0.0.1` and accepts requests from Chrome extension origins, not ordinary websites.
- It invokes yt-dlp with a fixed set of arguments; it does not accept arbitrary command-line arguments.
- Use it only with content you own, have permission to download, or are otherwise authorized to save. Respect site terms and applicable law. It does not implement DRM circumvention.
- Do not expose the local service port to your network.

## Direct-link mode

Direct-link mode scans the active page for common media files such as MP4, WebM, MOV, MKV, MP3, M4A, WAV, OGG, and FLAC, and uses Chrome's built-in download manager. Some sites do not expose direct media URLs, so use yt-dlp mode when the site is supported.

## Limitations and test status

Site support is controlled by yt-dlp and the target site's current behavior. MP3 conversion depends on FFmpeg and the source's audio availability. The repository changes have not yet been runtime-tested in Chrome on a Windows computer.

## Project files

- `manifest.json` — Chrome Manifest V3 metadata, including the default locale.
- `popup.html`, `popup.css`, `popup.js` — user interface and controls.
- `background.js` — direct media scanning and downloads.
- `backend/server.py` — local HTTP bridge to yt-dlp.
- `backend/setup-and-run-windows.ps1` — PowerShell-only setup and launcher.
- `backend/setup-tools-windows.ps1` — downloads tool binaries into the project-local `tools/` folder.
- `backend/requirements.txt` — Python dependency notes.
