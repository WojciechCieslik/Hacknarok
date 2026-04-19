// popup.js – extension popup logic
// ---------------------------------------------------------------------------
//  - Shows the active profile (using the color set in Time Guard)
//  - Auto-fills the input with the current tab's domain
//  - Allows adding and removing sites from the current profile
// ---------------------------------------------------------------------------

const API = "http://localhost:8765";
const $ = (id) => document.getElementById(id);

// Unlock password (in-memory only, cleared when popup closes)
let unlockPassword = "";
let currentProfileName = "";
// ---------- Komunikacja z serwerem ----------------------------------------
async function fetchState() {
  const res = await fetch(`${API}/state`, { cache: "no-store" });
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.json();
}

async function addSite(site) {
  const res = await fetch(`${API}/blocked`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ site, password: unlockPassword })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "HTTP " + res.status);
  return data;
}

async function removeSite(site) {
  const res = await fetch(`${API}/blocked`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ site, password: unlockPassword })
  });
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.json();
}

// ---------- Narzędzia ------------------------------------------------------
function extractDomain(url) {
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}

async function getCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url) return null;
  if (tab.url.startsWith("chrome://") ||
      tab.url.startsWith("chrome-extension://") ||
      tab.url.startsWith("about:")) {
    return null;
  }
  return tab;
}

async function prefillFromCurrentTab() {
  const tab = await getCurrentTab();
  if (!tab) return;
  const domain = extractDomain(tab.url);
  if (!domain) return;
  $("site-input").value = domain;
}

function showStatus(msg, type = "info") {
  const f = $("status-footer");
  f.textContent = msg;
  f.className = type === "error" ? "error" : type === "success" ? "success" : "";
  if (msg) {
    setTimeout(() => {
      if (f.textContent === msg) { f.textContent = ""; f.className = ""; }
    }, 3500);
  }
}

// ---------- Renderowanie ---------------------------------------------------
async function render() {
  const statusEl = $("server-status");
  const list = $("list");
  const badge = $("profile-badge");
  const title = $("list-title");

  try {
    const state = await fetchState();

    statusEl.textContent = "Connected to server";
    statusEl.className = "status online";

    const locked = !!(state.profile && state.profile.locked);

    // Clear saved password when the active profile changes
    if (state.activeProfile !== currentProfileName) {
      currentProfileName = state.activeProfile;
      unlockPassword = "";
    }
    const unlocked = !locked || unlockPassword !== "";

    badge.textContent = (locked ? "🔒 " : "") + (state.activeProfile || "—");
    if (state.profile && state.profile.color) {
      badge.style.background = state.profile.color;
    }

    $("lock-notice").hidden = !locked || unlocked;
    $("unlock-box").hidden = !locked || unlocked;
    $("site-input").disabled = !unlocked;
    $("add-btn").disabled = !unlocked;

    const sites = (state.profile && state.profile.blockedSites) || [];
    title.textContent = `Blocked (${sites.length})`;

    list.innerHTML = "";

    if (sites.length === 0) {
      list.innerHTML = '<li class="empty">No blocked sites</li>';
      return;
    }

    sites.forEach((site) => {
      const li = document.createElement("li");

      const span = document.createElement("span");
      span.className = "domain";
      span.textContent = site;
      span.title = site;

      li.appendChild(span);

      if (unlocked) {
        const btn = document.createElement("button");
        btn.className = "del-btn";
        btn.textContent = "Remove";
        btn.title = "Remove";
        btn.addEventListener("click", async () => {
          btn.disabled = true;
          try {
            await removeSite(site);
            showStatus(`Removed: ${site}`, "success");
            await render();
            chrome.runtime.sendMessage({ type: "SYNC_NOW" });
          } catch (e) {
            showStatus("Error: " + e.message, "error");
            btn.disabled = false;
          }
        });
        li.appendChild(btn);
      }

      list.appendChild(li);
    });
  } catch (e) {
    statusEl.textContent = "No connection to Python server";
    statusEl.className = "status offline";
    list.innerHTML = '<li class="empty">Start server.py</li>';
    badge.textContent = "?";
    badge.style.background = "#555";
  }
}

// ---------- Event listenery ------------------------------------------------
$("add-btn").addEventListener("click", async () => {
  const input = $("site-input");
  const site = input.value.trim();
  if (!site) { input.focus(); return; }

  try {
    const data = await addSite(site);
    input.value = "";
    const msg = data.message === "Already blocked"
      ? `Already blocked: ${data.site}`
      : `Blocked: ${data.site}`;
    showStatus(msg, "success");
    await render();
    chrome.runtime.sendMessage({ type: "SYNC_NOW" });
  } catch (e) {
    showStatus("Error: " + e.message, "error");
  }
});

$("site-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") $("add-btn").click();
});

// Unlock via password – verify by attempting to remove a non-existent site
$("unlock-btn").addEventListener("click", async () => {
  const pw = $("password-input").value;
  if (!pw) return;
  try {
    const res = await fetch(`${API}/blocked`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        site: "__verify__.time-guard.invalid",
        password: pw,
      }),
    });
    if (res.status === 403) {
      showStatus("Invalid password", "error");
      return;
    }
    if (!res.ok) {
      showStatus("Password verification error", "error");
      return;
    }
    unlockPassword = pw;
    $("password-input").value = "";
    showStatus("Unlocked", "success");
    await render();
  } catch (e) {
    showStatus("Error: " + e.message, "error");
  }
});

$("password-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") $("unlock-btn").click();
});

$("list-toggle").addEventListener("click", () => {
  const list = $("list");
  const arrow = $("list-arrow");
  const toggle = $("list-toggle");
  const expanded = !list.hidden;
  list.hidden = expanded;
  arrow.textContent = expanded ? "▸" : "▾";
  toggle.setAttribute("aria-expanded", String(!expanded));
});

// ---------- Start ----------------------------------------------------------
prefillFromCurrentTab();
render();
