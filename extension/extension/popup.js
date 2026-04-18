// popup.js – logika popupa rozszerzenia
// ---------------------------------------------------------------------------
//  - Pokazuje aktywny profil (z koloru ustawionego w Context Switcher Pro)
//  - Auto-wypełnia input domeną aktualnej karty
//  - Pozwala dodać i usunąć stronę z bieżącego profilu
// ---------------------------------------------------------------------------

const API = "http://localhost:8765";
const $ = (id) => document.getElementById(id);

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
    body: JSON.stringify({ site })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "HTTP " + res.status);
  return data;
}

async function removeSite(site) {
  const res = await fetch(`${API}/blocked`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ site })
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

    statusEl.textContent = "Połączono z serwerem";
    statusEl.className = "status online";

    const locked = !!(state.profile && state.profile.locked);

    badge.textContent = (locked ? "🔒 " : "") + (state.activeProfile || "—");
    if (state.profile && state.profile.color) {
      badge.style.background = state.profile.color;
    }

    $("lock-notice").hidden = !locked;
    $("site-input").disabled = locked;
    $("add-btn").disabled = locked;

    const sites = (state.profile && state.profile.blockedSites) || [];
    title.textContent = `Zablokowane (${sites.length})`;

    list.innerHTML = "";

    if (sites.length === 0) {
      list.innerHTML = '<li class="empty">Brak zablokowanych stron</li>';
      return;
    }

    sites.forEach((site) => {
      const li = document.createElement("li");

      const span = document.createElement("span");
      span.className = "domain";
      span.textContent = site;
      span.title = site;

      li.appendChild(span);

      if (!locked) {
        const btn = document.createElement("button");
        btn.className = "del-btn";
        btn.textContent = "Usuń";
        btn.title = "Usuń";
        btn.addEventListener("click", async () => {
          btn.disabled = true;
          try {
            await removeSite(site);
            showStatus(`Usunięto: ${site}`, "success");
            await render();
            chrome.runtime.sendMessage({ type: "SYNC_NOW" });
          } catch (e) {
            showStatus("Błąd: " + e.message, "error");
            btn.disabled = false;
          }
        });
        li.appendChild(btn);
      }

      list.appendChild(li);
    });
  } catch (e) {
    statusEl.textContent = "Brak połączenia z serwerem Python";
    statusEl.className = "status offline";
    list.innerHTML = '<li class="empty">Uruchom server.py</li>';
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
    const msg = data.message === "Już zablokowana"
      ? `Już zablokowana: ${data.site}`
      : `Zablokowano: ${data.site}`;
    showStatus(msg, "success");
    await render();
    chrome.runtime.sendMessage({ type: "SYNC_NOW" });
  } catch (e) {
    showStatus("Błąd: " + e.message, "error");
  }
});

$("site-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") $("add-btn").click();
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
