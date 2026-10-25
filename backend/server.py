#!/usr/bin/env python3
"""Localhost bridge allowing the Chrome extension to invoke project-local yt-dlp."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import shutil
import subprocess
import sys
import uuid

HOST = "127.0.0.1"
PORT = 8765
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
TOOLS_DIR = PROJECT_DIR / "tools"
FFMPEG_BIN = TOOLS_DIR / "ffmpeg" / "bin"
OUTPUT_DIR = Path.home() / "Downloads" / "VideoDownloader"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def executable(name):
    """Prefer binaries installed inside this project, then use PATH as a fallback."""
    candidates = []
    if name == "yt-dlp":
        candidates.extend([TOOLS_DIR / "yt-dlp.exe", TOOLS_DIR / "yt-dlp"])
    elif name in ("ffmpeg", "ffprobe"):
        candidates.extend([FFMPEG_BIN / (name + ".exe"), FFMPEG_BIN / name])
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name) or shutil.which(name + ".exe")

def safe_http_url(value):
    if not isinstance(value, str) or len(value) > 8192:
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False

def extension_origin(handler):
    origin = handler.headers.get("Origin", "")
    return origin.startswith("chrome-extension://") and len(origin) < 256

class Handler(BaseHTTPRequestHandler):
    server_version = "VideoDownloaderLocal/1.2"

    def log_message(self, fmt, *args):
        sys.stderr.write("[VideoDownloader] request handled\n")

    def send_json(self, status, payload, origin=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        origin = self.headers.get("Origin", "")
        if not extension_origin(self):
            return self.send_json(403, {"ok": False, "error": "Only Chrome extension requests are allowed."})
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self):
        if not extension_origin(self):
            return self.send_json(403, {"ok": False, "error": "Only Chrome extension requests are allowed."})
        origin = self.headers.get("Origin")
        if urlparse(self.path).path != "/health":
            return self.send_json(404, {"ok": False, "error": "Not found."}, origin)
        self.send_json(200, {
            "ok": True,
            "yt_dlp": bool(executable("yt-dlp")),
            "ffmpeg": bool(executable("ffmpeg")),
            "ffprobe": bool(executable("ffprobe")),
            "tools_location": str(TOOLS_DIR),
            "output_dir": str(OUTPUT_DIR)
        }, origin)

    def do_POST(self):
        if not extension_origin(self):
            return self.send_json(403, {"ok": False, "error": "Only Chrome extension requests are allowed."}, origin=None)
        origin = self.headers.get("Origin")
        if urlparse(self.path).path != "/download":
            return self.send_json(404, {"ok": False, "error": "Not found."}, origin)
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self.send_json(411, {"ok": False, "error": "Content-Length is required."}, origin)
        if size < 1 or size > 16384:
            return self.send_json(413, {"ok": False, "error": "Request is too large."}, origin)
        try:
            payload = json.loads(self.rfile.read(size))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self.send_json(400, {"ok": False, "error": "Invalid JSON."}, origin)
        if not isinstance(payload, dict):
            return self.send_json(400, {"ok": False, "error": "Expected a JSON object."}, origin)

        url = payload.get("url")
        mode = payload.get("mode", "video")
        if not safe_http_url(url):
            return self.send_json(400, {"ok": False, "error": "Provide a valid HTTP or HTTPS URL without embedded credentials."}, origin)
        if mode not in ("video", "mp3"):
            return self.send_json(400, {"ok": False, "error": "Mode must be video or mp3."}, origin)
        ytdlp = executable("yt-dlp")
        ffmpeg = executable("ffmpeg")
        if not ytdlp:
            return self.send_json(503, {"ok": False, "error": "Project-local yt-dlp is missing. Run backend/setup-and-run-windows.ps1."}, origin)
        if mode == "mp3" and not ffmpeg:
            return self.send_json(503, {"ok": False, "error": "Project-local FFmpeg is missing. Run backend/setup-and-run-windows.ps1."}, origin)

        job_id = uuid.uuid4().hex
        log_path = OUTPUT_DIR / (job_id + ".log")
        template = str(OUTPUT_DIR / "%(title).180B [%(id)s].%(ext)s")
        args = [ytdlp, "--no-playlist", "--newline", "--no-warnings", "-o", template]
        if ffmpeg:
            args.extend(["--ffmpeg-location", str(FFMPEG_BIN if (FFMPEG_BIN / "ffmpeg.exe").is_file() else Path(ffmpeg).parent)])
        if os.name == "nt":
            args.append("--windows-filenames")
        if mode == "mp3":
            args.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
        else:
            args.extend(["-f", "bv*+ba/b", "--merge-output-format", "mp4"])
        args.extend(["--", url])
        try:
            with open(log_path, "ab") as log:
                subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                 cwd=str(OUTPUT_DIR), close_fds=(os.name != "nt"))
        except OSError as exc:
            return self.send_json(500, {"ok": False, "error": "Could not start yt-dlp: " + str(exc)}, origin)
        self.send_json(202, {"ok": True, "job_id": job_id, "output_dir": str(OUTPUT_DIR)}, origin)

def main():
    if not executable("yt-dlp"):
        print("yt-dlp is missing. Run backend/setup-and-run-windows.ps1 to place it inside this project.")
    if not executable("ffmpeg") or not executable("ffprobe"):
        print("FFmpeg is missing. Run backend/setup-and-run-windows.ps1 to place it inside this project.")
    print("Video Downloader local service listening on http://127.0.0.1:8765")
    print("Project tools folder: " + str(TOOLS_DIR))
    print("Downloads folder: " + str(OUTPUT_DIR))
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping local service.")
