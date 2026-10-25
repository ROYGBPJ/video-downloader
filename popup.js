const pageUrl = document.getElementById("pageUrl");
const notice = document.getElementById("notice");
const results = document.getElementById("results");
const count = document.getElementById("count");
const scanButton = document.getElementById("scan");
const downloadAllButton = document.getElementById("downloadAll");
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

function renderItems() {
  count.textContent = mediaItems.length + (mediaItems.length === 1 ? " media file" : " media files");
  downloadAllButton.disabled = mediaItems.length === 0;
  results.replaceChildren();
  if (!mediaItems.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No directly downloadable media was found. This page may use a player that hides its actual media URLs.";
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
    const response = await chrome.runtime.sendMessage({type:"SCAN_TAB", tabId:tab.id});
    if (!response?.ok) throw new Error(response?.error || "Scan failed");
    mediaItems = response.items;
    renderItems();
    const host = new URL(tab.url).hostname;
    if (/(^|\.)youtube\.com$|(^|\.)youtu\.be$/.test(host)) {
      setNotice("Actual YouTube video extraction is not implemented yet. YouTube uses adaptive streaming, so its video and audio are not normally available as ordinary direct file links. Successful YouTube downloads have not been verified, and this extension has not been tested in Chrome.", true);
    } else {
      setNotice(mediaItems.length ? "Found media URLs exposed directly by this page." : "No direct media files found. Try opening the media itself in a tab.");
    }
  } catch (error) {
    mediaItems = []; renderItems();
    setNotice(error.message || "Could not scan this page.", true);
  } finally {
    scanButton.disabled = false;
  }
}

async function downloadOne(item) {
  try {
    const response = await chrome.runtime.sendMessage({type:"DOWNLOAD_MEDIA", item});
    if (!response?.ok) throw new Error(response?.error || "Download could not be started");
    setNotice("Download started: " + (item.name || "media file"));
  } catch (error) { setNotice(error.message || "Download failed to start.", true); }
}

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
  setNotice("Started " + started + " of " + mediaItems.length + " downloads.");
  downloadAllButton.disabled = mediaItems.length === 0;
});
scanPage();
