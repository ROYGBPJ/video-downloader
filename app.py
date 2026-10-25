from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


APP_NAME = "Video Downloader"
DEFAULT_OUTPUT = str(Path.home() / "Downloads" / "Video Downloader")


class DownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("760x590")
        self.minsize(650, 520)
        self.configure(bg="#101522")
        self.events: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.cancel_event = threading.Event()
        self.output_var = tk.StringVar(value=DEFAULT_OUTPUT)
        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar(value="Best quality")
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self._setup_style()
        self._build_ui()
        self.after(100, self._poll_events)

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#101522")
        style.configure("Panel.TFrame", background="#171f30")
        style.configure("TLabel", background="#101522", foreground="#e8eefc", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background="#101522", foreground="#9ba9c5", font=("Segoe UI", 9))
        style.configure("Panel.TLabel", background="#171f30", foreground="#e8eefc", font=("Segoe UI", 10))
        style.configure("TEntry", fieldbackground="#202b40", foreground="#ffffff", insertcolor="#ffffff")
        style.configure("TCombobox", fieldbackground="#202b40", foreground="#ffffff")
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure("Accent.TButton", background="#6c7cff", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#8793ff"), ("disabled", "#39415d")])
        style.configure("Horizontal.TProgressbar", troughcolor="#202b40", background="#7b8cff", thickness=10)

    def _build_ui(self):
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="VIDEO DOWNLOADER", font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="YouTube and many more sites supported by yt-dlp",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 20))

        panel = ttk.Frame(outer, style="Panel.TFrame", padding=18)
        panel.pack(fill="x")
        ttk.Label(panel, text="Video URL", style="Panel.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.url_entry = ttk.Entry(panel, textvariable=self.url_var)
        self.url_entry.pack(fill="x", pady=(8, 16))
        self.url_entry.bind("<Return>", lambda _event: self.start_download())

        row = ttk.Frame(panel, style="Panel.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Quality", style="Panel.TLabel").pack(side="left")
        quality = ttk.Combobox(
            row,
            textvariable=self.quality_var,
            values=("Best quality", "1080p or lower", "720p or lower", "480p or lower", "Audio only (MP3)"),
            state="readonly",
            width=22,
        )
        quality.pack(side="left", padx=(10, 0))

        ttk.Label(outer, text="Save folder").pack(anchor="w", pady=(18, 7))
        folder_row = ttk.Frame(outer)
        folder_row.pack(fill="x")
        ttk.Entry(folder_row, textvariable=self.output_var).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="Browse…", command=self.choose_folder).pack(side="left", padx=(8, 0))

        self.progress = ttk.Progressbar(outer, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress.pack(fill="x", pady=(22, 8))
        ttk.Label(outer, textvariable=self.status_var, style="Muted.TLabel").pack(anchor="w")

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(18, 0))
        self.download_button = ttk.Button(actions, text="Download", style="Accent.TButton", command=self.start_download)
        self.download_button.pack(side="left")
        ttk.Button(actions, text="Open save folder", command=self.open_folder).pack(side="left", padx=(8, 0))

        ttk.Label(
            outer,
            text="Use only for content you’re allowed to download. DRM, paywalls, and access controls are not bypassed.",
            style="Muted.TLabel",
            wraplength=700,
        ).pack(anchor="w", side="bottom", pady=(18, 0))

    def choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.home()))
        if chosen:
            self.output_var.set(chosen)

    def open_folder(self):
        folder = Path(self.output_var.get()).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        import os
        import subprocess
        import sys
        try:
            if sys.platform == "win32":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            messagebox.showerror("Could not open folder", str(exc))

    def start_download(self):
        if yt_dlp is None:
            messagebox.showerror(
                "Missing dependency",
                "yt-dlp is not installed. Run: python -m pip install -r requirements.txt",
            )
            return
        url = self.url_var.get().strip()
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            messagebox.showwarning("Check URL", "Enter a complete http:// or https:// video URL.")
            return
        if self.worker and self.worker.is_alive():
            return
        output = Path(self.output_var.get()).expanduser()
        try:
            output.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Save folder error", str(exc))
            return

        self.progress_var.set(0)
        self.status_var.set("Starting download…")
        self.download_button.configure(state="disabled")
        self.cancel_event.clear()
        self.worker = threading.Thread(target=self._download_worker, args=(url, output), daemon=True)
        self.worker.start()

    def _download_worker(self, url: str, output: Path):
        quality = self.quality_var.get()
        if quality == "Audio only (MP3)":
            fmt = "bestaudio/best"
            postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
        else:
            height = {
                "1080p or lower": 1080,
                "720p or lower": 720,
                "480p or lower": 480,
            }.get(quality)
            fmt = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]" if height else "bestvideo*+bestaudio/best"
            postprocessors = []

        def hook(data):
            if self.cancel_event.is_set():
                raise InterruptedError("Download cancelled")
            state = data.get("status")
            if state == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded = data.get("downloaded_bytes", 0)
                percent = (downloaded / total * 100) if total else 0
                speed = data.get("speed")
                eta = data.get("eta")
                self.events.put(("progress", percent, f"Downloading… {percent:.1f}% · {self._rate(speed)} · ETA {self._duration(eta)}"))
            elif state == "finished":
                self.events.put(("progress", 100, "Download finished; processing file…"))

        options = {
            "format": fmt,
            "outtmpl": str(output / "%(title).180B [%(id)s].%(ext)s"),
            "noplaylist": False,
            "ignoreerrors": False,
            "retries": 3,
            "fragment_retries": 3,
            "progress_hooks": [hook],
            "postprocessors": postprocessors,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": False,
        }
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(url, download=True)
            if info:
                self.events.put(("done", "Download complete."))
            else:
                self.events.put(("error", "No downloadable media was returned by the site."))
        except InterruptedError:
            self.events.put(("error", "Download cancelled."))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    @staticmethod
    def _rate(value):
        if not value:
            return "speed unknown"
        units = ("B/s", "KB/s", "MB/s", "GB/s")
        value = float(value)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}"
            value /= 1024
        return ""

    @staticmethod
    def _duration(value):
        if value is None:
            return "calculating"
        seconds = max(0, int(value))
        return f"{seconds // 60}:{seconds % 60:02d}"

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "progress":
                    self.progress_var.set(event[1])
                    self.status_var.set(event[2])
                elif kind == "done":
                    self.progress_var.set(100)
                    self.status_var.set(event[1])
                    self.download_button.configure(state="normal")
                    messagebox.showinfo("Complete", event[1])
                elif kind == "error":
                    self.status_var.set(event[1][:220])
                    self.download_button.configure(state="normal")
                    messagebox.showerror("Download issue", event[1])
        except queue.Empty:
            pass
        self.after(100, self._poll_events)


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
