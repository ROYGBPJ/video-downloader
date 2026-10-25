# Video Downloader — Chrome Extension

This project is a Chrome Manifest V3 browser extension, not a Python desktop app.

## Features
- Scans the active webpage for directly exposed video/audio URLs and media-file links.
- Supports common direct media formats including MP4, WebM, MOV, MKV, MP3, M4A, WAV, OGG, and FLAC.
- Downloads one item or all discovered items using Chrome's built-in download manager.
- Does not add an artificial queue-count or file-size limit. Actual limits are determined by Chrome, the operating system, the server, and the website.
- Works on sites that expose downloadable media URLs to the page.

## Install in Chrome
1. Download or clone this repository.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Select **Load unpacked**.
5. Choose the repository folder containing `manifest.json`.
6. Open a webpage with a directly accessible media file, click the extension icon, then select **Scan** or **Download all**.

## Site compatibility
Many websites expose ordinary media file URLs. Other sites use segmented streaming, short-lived signed URLs, authentication, or protected playback. A browser extension that only scans page URLs cannot automatically turn every such stream into a downloadable file. YouTube is detected and explained in the popup, but its adaptive streams are not treated as ordinary direct file URLs by this version. Do not use this extension to bypass DRM, access controls, or website restrictions.

Only download content you own, have permission to save, or are otherwise authorized to download. Respect applicable law and each site's terms.

## Project files
- `manifest.json` — extension configuration
- `popup.html`, `popup.css`, `popup.js` — popup interface and scan/download controls
- `background.js` — page scanning and Chrome Downloads API
