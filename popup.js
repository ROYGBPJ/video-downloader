const pageUrl = document.getElementById("pageUrl");
const notice = document.getElementById("notice");
const results = document.getElementById("results");
const count = document.getElementById("count");
const scanButton = document.getElementById("scan");
const downloadAllButton = document.getElementById("downloadAll");
const backendUrl = document.getElementById("backendUrl");
const downloadMode = document.getElementById("downloadMode");
const backendStatus = document.getElementById("backendStatus");
const backendDownload = document.getElementById("backendDownload");
const BACKEND = "http://127.0.0.1:8765";
let mediaItems = [];

function setNotice(message, warning = false) {
  notice.textContent = message;
  notice.classList.toggle("warn", warning);
}
function readableSize(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "Size unknown";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes, unit = 0;
  while (value >= 1024 && unit < units.length - 1) { value /= 1024; unit++; }
  return value.toFixed(unit === 0 ? 0 : 1) + " " + units[unit];
}
function safeName(url, fallback) {
  try {
    const name = decodeURIComponent(new URL(url).pathname.split("/").pop() || "");
    return name && name.includes(".") ? name : fallback;
  } catch { return fallback; }
}
async function checkBackend() {
  try {
    const response = await fetch(BACKEND + "/health", {signal: AbortSignal.timeout(1800)});
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "Backend unavailable");
    backendStatus.textContent = data.yt_dlp ? (data.ffmpeg ? "Ready" : "FFmpeg missing") : "yt-dlp missing";
    backendStatus.classList.toggle("ready", Boolean(data.yt_dlp && data.ffmpeg));
    backendDownload.disabled = !(data.yt_dlp && data.ffmpeg);
    if (!data.yt_dlp || !data.ffmpeg) setNotice("Local service is running, but yt-dlp or FFmpeg was not found on PATH.", true);
  } catch {
    backendStatus.textContent = "Offline";
    backendStatus.classList.remove("ready");
    backendDownload.disabled = true;
  }
}
function renderItems() {
  count.textContent = mediaItems.length + (mediaItems.length === 1 ? " direct media file" : " direct media files");
  downloadAllButton.disabled = mediaItems.length === 0;
  results.replaceChildren();
  if (!mediaItems.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No directly downloadable media was found. Try the yt-dlp section above for supported sites.";
    results.append(empty);
    return;
  }
  mediaItems.forEach((item, index) => {
    const row = document.createElement("div"); row.className = "item";
    const kind = document.createElement("div"); kind.className = "kind"; kind.textContent = item.kind === "audio" ? "♫" : "▶";
    const details = document.createElement("div"); details.className = "details";
    const name = document.createElement("div"); name.className = "name"; name.textContent = item.name || safeName(item.url, "media-" + (index + 1));
    const meta = document.createElement("div"); meta.className = "meta"; meta.textContent = item.kind.toUpperCase() + " · " + readableSize(item.size);
    details.append(name, meta);
    const button = document.createElement("button"); button.textContent = "Download";
    button.addEventListener("click", () => downloadOne(item));
    row.append(kind, details, button); results.append(row);
  });
}
async function getActiveTab() {
  const tabs = await chrome.tabs.query({active:true,currentWindow:true});
  return tabs[0];
}
async function scanPage() {
  scanButton.disabled = true;
  setNotice("Scanning page for media…");
  try {
    const tab = await getActiveTab();
    if (!tab?.id || !tab.url || !/^https?:/.test(tab.url)) {
      pageUrl.value = tab?.url || "";
      mediaItems = []; renderItems();
      setNotice("This browser page cannot be scanned. Open a normal website tab and try again.", true);
      return;
    }
    pageUrl.value = tab.url;
    if (!backendUrl.value) backendUrl.value = tab.url;
    const response = await chrome.runtime.sendMessage({type:"SCAN_TAB", tabId:tab.id});
    if (!response?.ok) throw new Error(response?.error || "Scan failed");
    mediaItems = response.items;
    renderItems();
    setNotice(mediaItems.length ? "Found media URLs exposed directly by this page." : "No direct media files found. If the site is supported, try Download with yt-dlp.");
  } catch (error) {
    mediaItems = []; renderItems();
    setNotice(error.message || "Could not scan this page.", true);
  } finally { scanButton.disabled = false; }
}
async function downloadOne(item) {
  try {
    const response = await chrome.runtime.sendMessage({type:"DOWNLOAD_MEDIA", item});
    if (!response?.ok) throw new Error(response?.error || "Download could not be started");
    setNotice("Direct download started: " + (item.name || "media file"));
  } catch (error) { setNotice(error.message || "Download failed to start.", true); }
}
backendDownload.addEventListener("click", async () => {
  const url = backendUrl.value.trim();
  if (!url) { setNotice("Enter a video or supported-site URL first.", true); return; }
  let parsed;
  try { parsed = new URL(url); } catch { setNotice("Enter a valid URL.", true); return; }
  if (!["http:", "https:"].includes(parsed.protocol)) { setNotice("Only HTTP and HTTPS URLs are supported.", true); return; }
  backendDownload.disabled = true;
  setNotice("Sending download job to local yt-dlp service…");
  try {
    const response = await fetch(BACKEND + "/download", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({url: parsed.href, mode: downloadMode.value}),
      signal: AbortSignal.timeout(10000)
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "The local service rejected the request.");
    setNotice("Download queued on this computer. Check the VideoDownloader folder in your Downloads directory.");
  } catch (error) {
    setNotice(error.name === "TimeoutError" ? "The local service did not respond in time. Check that it is running." : (error.message || "Could not reach the local service."), true);
  } finally { await checkBackend(); }
});
scanButton.addEventListener("click", scanPage);
downloadAllButton.addEventListener("click", async () => {
  downloadAllButton.disabled = true;
  let started = 0;
  for (const item of mediaItems) {
    try {
      const response = await chrome.runtime.sendMessage({type:"DOWNLOAD_MEDIA", item});
      if (response?.ok) started++;
    } catch {}
  }
  setNotice("Started " + started + " of " + mediaItems.length + " direct-link downloads.");
  downloadAllButton.disabled = mediaItems.length === 0;
});
scanPage();
checkBackend();