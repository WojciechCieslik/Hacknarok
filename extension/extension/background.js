// background.js – service worker
// ---------------------------------------------------------------------------
//  Odpowiada za:
//    - cykliczną synchronizację z serwerem Python (chrome.alarms)
//    - aktualizację reguł declarativeNetRequest dla aktywnego profilu
//    - obsługę komunikatów od popupa / content scriptu
// ---------------------------------------------------------------------------

const SERVER_URL = "http://localhost:8765";
const SYNC_ALARM = "sync-blocked";
const SYNC_INTERVAL_MIN = 0.16666667; // 10 sekund

// ---------------------------------------------------------------------------
// Cache lokalny (żeby popup miał co pokazać nawet jeśli serwer chwilowo pada)
// ---------------------------------------------------------------------------
async function cacheState(state) {
  await chrome.storage.local.set({ state, lastSync: Date.now(), serverOnline: true });
}

async function markServerOffline() {
  await chrome.storage.local.set({ serverOnline: false });
}

// ---------------------------------------------------------------------------
// Synchronizacja z serwerem Python
// ---------------------------------------------------------------------------
async function syncBlocked() {
  let state;
  try {
    const response = await fetch(`${SERVER_URL}/state`, { cache: "no-store" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    state = await response.json();
  } catch (err) {
    console.warn("[Bloker] Serwer nieosiągalny:", err.message);
    await markServerOffline();
    return;
  }

  await cacheState(state);

  const domains = (state.profile && state.profile.blockedSites) || [];
  await applyRules(domains);
  console.log(`[Bloker] Profil "${state.activeProfile}" – ${domains.length} reguł.`);
}

// ---------------------------------------------------------------------------
// Aktualizacja reguł declarativeNetRequest
// ---------------------------------------------------------------------------
async function applyRules(domains) {
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const existingIds = existing.map((r) => r.id);

  const newRules = domains.map((domain, index) => {
    const hasPath = domain.includes("/");
    // Dla domen bez ścieżki: ||domain^ (dopasowuje subdomeny i kończy na separatorze)
    // Dla wpisów ze ścieżką (np. youtube.com/shorts): dopasowanie częściowe
    const urlFilter = hasPath ? "*" + domain + "*" : "||" + domain + "^";

    return {
      id: index + 1,
      priority: 1,
      action: {
        type: "redirect",
        redirect: {
          extensionPath:
            "/blocked.html?domain=" + encodeURIComponent(domain)
        }
      },
      condition: {
        urlFilter,
        resourceTypes: ["main_frame"]
      }
    };
  });

  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: existingIds,
    addRules: newRules
  });
}

// ---------------------------------------------------------------------------
// Komunikaty z popupa / content scriptu
// ---------------------------------------------------------------------------
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    try {
      if (msg.type === "BLOCK_REDIRECT") {
        const url = chrome.runtime.getURL(
          "blocked.html?domain=" + encodeURIComponent(msg.entry) +
          "&profile=" + encodeURIComponent(msg.profile)
        );
        chrome.tabs.update(_sender.tab.id, { url });
        sendResponse({ ok: true });
      } else if (msg.type === "SYNC_NOW") {
        await syncBlocked();
        sendResponse({ ok: true });
      } else if (msg.type === "ADD_BLOCKED") {
        const res = await fetch(`${SERVER_URL}/blocked`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ site: msg.site })
        });
        const data = await res.json();
        await syncBlocked();
        sendResponse({ ok: res.ok, data });
      } else if (msg.type === "REMOVE_BLOCKED") {
        const res = await fetch(`${SERVER_URL}/blocked`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ site: msg.site })
        });
        const data = await res.json();
        await syncBlocked();
        sendResponse({ ok: res.ok, data });
      } else if (msg.type === "GET_STATE") {
        const { state, serverOnline } = await chrome.storage.local.get([
          "state", "serverOnline"
        ]);
        sendResponse({ ok: true, state, serverOnline });
      } else {
        sendResponse({ ok: false, error: "Nieznany typ komunikatu" });
      }
    } catch (err) {
      sendResponse({ ok: false, error: err.message });
    }
  })();
  return true; // sendResponse będzie wywołane asynchronicznie
});

// ---------------------------------------------------------------------------
// SPA navigation – łapiemy zmiany URL przez History API (pushState/replaceState)
// To jest jedyny niezawodny sposób w MV3 — nie zależy od page scripts ani
// od ich quirków (np. YouTube nadpisujący location.replace).
// ---------------------------------------------------------------------------
async function checkAndBlockSpa(details) {
  if (details.frameId !== 0) return; // tylko główna ramka
  const { state } = await chrome.storage.local.get(["state"]);
  const sites = state?.profile?.blockedSites || [];
  for (const entry of sites) {
    if (entry.includes("/") && details.url.includes(entry)) {
      const url = chrome.runtime.getURL(
        "blocked.html?domain=" + encodeURIComponent(entry) +
        "&profile=" + encodeURIComponent(state.activeProfile || "")
      );
      chrome.tabs.update(details.tabId, { url });
      return;
    }
  }
}

chrome.webNavigation.onHistoryStateUpdated.addListener(checkAndBlockSpa);
chrome.webNavigation.onReferenceFragmentUpdated.addListener(checkAndBlockSpa);

// ---------------------------------------------------------------------------
// Inicjalizacja harmonogramu
// ---------------------------------------------------------------------------
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create(SYNC_ALARM, { periodInMinutes: SYNC_INTERVAL_MIN });
  syncBlocked();
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create(SYNC_ALARM, { periodInMinutes: SYNC_INTERVAL_MIN });
  syncBlocked();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === SYNC_ALARM) syncBlocked();
});

// Od razu przy każdym starcie service workera
syncBlocked();
