function looksLikeMedia(url, type = "") {
  try {
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol)) return false;
    if (/^(video|audio)\//i.test(type)) return true;
    return /\.(mp4|m4v|webm|mov|mkv|avi|mp3|m4a|aac|wav|ogg|opus|flac)(?:$|[?#])/i.test(url);
  } catch { return false; }
}

function mediaKind(url, type = "") {
  return /^audio\//i.test(type) || /\.(mp3|m4a|aac|wav|ogg|opus|flac)(?:$|[?#])/i.test(url) ? "audio" : "video";
}

async function scanTab(tabId) {
  const injection = await chrome.scripting.executeScript({
    target: {tabId},
    func: () => {
      const found = new Map();
      const add = (url, type = "", name = "", size = 0) => {
        try {
          const absolute = new URL(url, location.href).href;
          if (!/^https?:/.test(absolute)) return;
          const mediaExt = /\.(mp4|m4v|webm|mov|mkv|avi|mp3|m4a|aac|wav|ogg|opus|flac)(?:$|[?#])/i.test(absolute);
          if (!mediaExt && !/^(video|audio)\//i.test(type)) return;
          if (!found.has(absolute)) found.set(absolute, {url:absolute, type, name:name || "", size:Number(size)||0});
        } catch {}
      };
      document.querySelectorAll("video, audio").forEach(el => {
        add(el.currentSrc || el.src, el.tagName === "AUDIO" ? "audio/unknown" : "video/unknown", el.getAttribute("title") || "");
        el.querySelectorAll("source").forEach(s => add(s.src, s.type, s.getAttribute("title") || ""));
      });
      document.querySelectorAll("a[href]").forEach(a => {
        const href = a.href;
        if (/\.(mp4|m4v|webm|mov|mkv|avi|mp3|m4a|aac|wav|ogg|opus|flac)(?:$|[?#])/i.test(href)) add(href, "", a.download || a.textContent.trim());
      });
      try {
        performance.getEntriesByType("resource").forEach(r => {
          if (/\.(mp4|m4v|webm|mov|mkv|avi|mp3|m4a|aac|wav|ogg|opus|flac)(?:$|[?#])/i.test(r.name)) add(r.name);
        });
      } catch {}
      return Array.from(found.values());
    }
  });
  const raw = injection?.[0]?.result || [];
  return raw.map((item, index) => ({
    url: item.url,
    kind: mediaKind(item.url, item.type),
    name: item.name || (() => { try { return decodeURIComponent(new URL(item.url).pathname.split("/").pop()) || "media-" + (index + 1); } catch { return "media-" + (index + 1); } })(),
    size: item.size || 0
  }));
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "SCAN_TAB") {
    scanTab(message.tabId).then(items => sendResponse({ok:true, items})).catch(error => sendResponse({ok:false, error:error.message}));
    return true;
  }
  if (message?.type === "DOWNLOAD_MEDIA") {
    const item = message.item;
    try {
      const url = new URL(item?.url);
      if (!["http:", "https:"].includes(url.protocol)) throw new Error("Only HTTP and HTTPS media URLs are supported.");
      chrome.downloads.download({url:url.href, saveAs:true}, downloadId => {
        const error = chrome.runtime.lastError;
        if (error) sendResponse({ok:false, error:error.message});
        else sendResponse({ok:true, downloadId});
      });
    } catch (error) { sendResponse({ok:false, error:error.message}); }
    return true;
  }
});
