// content.js – wstrzykiwany w każdą stronę przy document_start
// ---------------------------------------------------------------------------
// Cel: blokować wpisy SPA ze ścieżką (np. "youtube.com/shorts").
// Wpisy bez ścieżki (np. "facebook.com") obsługuje declarativeNetRequest.
//
// Problem z YouTube (i innymi SPA):
//   YouTube NIE używa standardowego history.pushState przy nawigacji do Shorts.
//   Korzysta z własnych zdarzeń yt-navigate-start / yt-navigate-finish.
//   Dodatkowo ich framework może nadpisać nasz hook na pushState po załadowaniu.
//
// Rozwiązanie – trzy warstwy detekcji (od najszybszej do fallbacku):
//   1. Override history.pushState / replaceState    → natychmiastowe dla większości SPA
//   2. Zdarzenia YouTube yt-navigate-*              → natychmiastowe dla YouTube
//   3. Polling co 500 ms                            → łapie WSZYSTKO czego 1 i 2 nie złapią
//
// Polling sprawdza TYLKO czy URL się zmienił (lastUrl !== currentUrl),
// więc przy nieruchomym URL nie robi żadnej pracy.
// ---------------------------------------------------------------------------

let blockedList  = [];
let activeProfile = null;
let lastUrl      = location.href;

// ---------------------------------------------------------------------------
// Wczytywanie listy z serwera
// ---------------------------------------------------------------------------
async function loadState() {
  try {
    const res = await fetch("http://localhost:8765/state", { cache: "no-store" });
    if (!res.ok) return;
    const state = await res.json();
    activeProfile = state.activeProfile;
    blockedList   = (state.profile && state.profile.blockedSites) || [];
  } catch (_) {
    // serwer nie działa — zachowaj poprzednią listę
  }
}

// ---------------------------------------------------------------------------
// Sprawdzanie i blokowanie bieżącego URL
// ---------------------------------------------------------------------------
function getMatchingEntry(url) {
  for (const entry of blockedList) {
    // Interesują nas tylko wpisy ze ścieżką — reszta idzie przez declarativeNetRequest
    if (entry.includes("/") && url.includes(entry)) return entry;
  }
  return null;
}

function redirectIfBlocked() {
  const entry = getMatchingEntry(window.location.href);
  if (!entry) return;

  chrome.runtime.sendMessage({
    type: "BLOCK_REDIRECT",
    entry,
    profile: activeProfile || ""
  });
}

// Wywoływane przy każdej potencjalnej zmianie URL
function onUrlMaybeChanged() {
  const currentUrl = window.location.href;
  if (currentUrl === lastUrl) return; // URL nie zmieniony — nic nie rób
  lastUrl = currentUrl;
  redirectIfBlocked();
}

// ---------------------------------------------------------------------------
// Warstwa 1 – Override pushState / replaceState
// Działa dla większości SPA (React Router, Vue Router, Next.js, …)
// ---------------------------------------------------------------------------
(function patchHistory() {
  const originalPush    = history.pushState;
  const originalReplace = history.replaceState;

  history.pushState = function (...args) {
    originalPush.apply(this, args);
    onUrlMaybeChanged();
  };

  history.replaceState = function (...args) {
    originalReplace.apply(this, args);
    onUrlMaybeChanged();
  };
})();

window.addEventListener("popstate", onUrlMaybeChanged);

// ---------------------------------------------------------------------------
// Warstwa 2 – Zdarzenia własne YouTube
// yt-navigate-start odpala się ZANIM YouTube zmieni window.location.href,
// więc nie możemy polegać na porównaniu URL-i — musimy wyciągnąć URL docelowy
// z event.detail i sprawdzić blokadę z wyprzedzeniem.
// ---------------------------------------------------------------------------
document.addEventListener("yt-navigate-start", () => {
  // event.detail jest null w izolowanym świecie MV3 — zamiast tego
  // czekamy aż YouTube zaktualizuje location.href i sprawdzamy po chwili
  setTimeout(onUrlMaybeChanged, 50);
  setTimeout(onUrlMaybeChanged, 250);
});

for (const evName of ["yt-navigate-finish", "yt-page-data-updated"]) {
  document.addEventListener(evName, onUrlMaybeChanged);
}

// ---------------------------------------------------------------------------
// Warstwa 3 – Polling co 500 ms (fallback absolutny)
// Łapie SPA frameworki, które w ogóle nie emitują zdarzeń historii,
// oraz edge-case'y gdzie YouTube zmienia URL poza swoim systemem zdarzeń.
// Przy statycznym URL == zero kosztu (jeden string compare co 500 ms).
// ---------------------------------------------------------------------------
setInterval(onUrlMaybeChanged, 500);

// ---------------------------------------------------------------------------
// Cykliczne odświeżanie listy co 30 s
// (żeby zmiana profilu w Context Switcher Pro była widoczna bez reloadu strony)
// ---------------------------------------------------------------------------
setInterval(loadState, 30000);

// ---------------------------------------------------------------------------
// Start – wczytaj listę i sprawdź bieżący URL
// ---------------------------------------------------------------------------
loadState().then(() => {
  lastUrl = location.href; // ustaw baseline po wczytaniu listy
  redirectIfBlocked();     // sprawdź od razu (np. bezpośredni URL do /shorts)
});