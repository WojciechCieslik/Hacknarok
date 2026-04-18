// blocked.js – wyświetla informacje na stronie blokady
const params = new URLSearchParams(window.location.search);

document.getElementById("domain").textContent =
  params.get("domain") || "nieznana domena";

const profileEl = document.getElementById("profile");
const profileFromUrl = params.get("profile");

if (profileFromUrl) {
  profileEl.textContent = profileFromUrl;
}

// Pobierz szczegóły profilu z serwera (np. kolor) — także jako fallback gdy URL nie miał profilu
fetch("http://localhost:8765/state")
  .then((r) => r.json())
  .then((s) => {
    if (!profileFromUrl) profileEl.textContent = s.activeProfile || "—";
    if (s.profile && s.profile.color) {
      profileEl.style.background = s.profile.color;
    }
  })
  .catch(() => {
    if (!profileFromUrl) profileEl.textContent = "—";
  });
