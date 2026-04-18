# Bloker Stron – Rozszerzenie dla Context Switcher Pro

Rozszerzenie do Chrome, które blokuje strony wg aktywnego profilu z Context Switcher Pro.

## Co nowego w wersji 2.0

- **Struktura profilowa** w `blocked.json` — każdy profil (Praca/Nauka/Rozrywka) ma własną listę stron
- **Dodawanie z poziomu przeglądarki** — ręcznie albo jednym klikiem "🔒 Zablokuj tę kartę"
- **Usuwanie z listy w popupie** — przycisk ✕ przy każdym wpisie
- **Widoczny aktywny profil** w popupie i na stronie blokady (z kolorem profilu)
- **Chrome Alarms** zamiast `setInterval` (niezawodne w MV3)
- **Atomowy zapis** pliku + lock w serwerze (bez uszkodzonego JSON-a)
- **Normalizacja wpisów** — `https://www.YouTube.com/` i `youtube.com` to to samo
- **Migracja** ze starego formatu listy → nowy format profilowy jest automatyczna

## Struktura pliku `blocked.json`

```json
{
  "activeProfile": "Praca",
  "profiles": {
    "Praca":    { "name": "Praca",    "color": "#4A90E2", "blockedSites": ["facebook.com", ...] },
    "Nauka":    { "name": "Nauka",    "color": "#50C878", "blockedSites": [...] },
    "Rozrywka": { "name": "Rozrywka", "color": "#E74C3C", "blockedSites": [] }
  }
}
```

## Uruchomienie

```bash
pip install flask flask-cors
python server.py
```

Potem w Chrome: `chrome://extensions` → Tryb dewelopera → Załaduj rozpakowane → wskaż folder.

## API serwera

| Metoda | Endpoint | Opis |
|---|---|---|
| `GET` | `/state` | Aktywny profil + jego dane + lista profili |
| `GET` | `/blocked` | Lista stron aktywnego profilu *(kompat. wsteczna)* |
| `POST` | `/blocked` | `{site, profile?}` — dodaje stronę |
| `DELETE` | `/blocked` | `{site, profile?}` — usuwa stronę |
| `GET` | `/profiles` | Wszystkie profile |
| `PUT` | `/profiles/<nazwa>` | Tworzy/aktualizuje profil |
| `DELETE` | `/profiles/<nazwa>` | Usuwa profil |
| `POST` | `/active-profile` | `{profile, color?, blockedSites?}` — zmienia aktywny |
| `GET` | `/health` | Stan serwera |

## Integracja z Context Switcher Pro (Python)

### Przy przełączaniu profilu

W `core/profile_manager.py` po `switch_profile()` dodaj POST do serwera:

```python
import requests

def notify_extension(profile):
    try:
        requests.post("http://localhost:8765/active-profile",
                      json={
                          "profile": profile.name,
                          "color": getattr(profile, "color", "#4A90E2"),
                          "blockedSites": getattr(profile, "blocked_sites", [])
                      },
                      timeout=1.0)
    except requests.RequestException:
        pass  # serwer może nie działać — nie blokujemy głównej aplikacji
```

### Przy edycji profilu (dodaniu nowych stron do blokowania)

```python
requests.put(f"http://localhost:8765/profiles/{profile.name}",
             json={
                 "color": profile.color,
                 "blockedSites": profile.blocked_sites
             },
             timeout=1.0)
```

### Propozycja: użyj serwera jako SSOT listy blokowania

Zamiast trzymać listę w `profiles.json` głównej aplikacji i replikować do `blocked.json`,
możesz czytać ją bezpośrednio z `http://localhost:8765/profiles`. Wtedy dodanie strony
z przeglądarki od razu widać w Context Switcher Pro (po odświeżeniu GUI).

Alternatywnie — i to zalecane — Context Switcher Pro posiada źródłową listę w swoim
`profiles.json`, a `blocked.json` jest pochodną generowaną przy każdej zmianie profilu.
Wtedy dodanie strony z przeglądarki musi trafić z powrotem do `profiles.json`
(np. obserwator pliku `blocked.json`, który synchronizuje zmiany).

## Pliki

```
├── manifest.json     # MV3, uprawnienia: declarativeNetRequest, tabs, alarms, storage
├── background.js     # Service worker: sync, reguły DNR, message API
├── content.js        # Wstrzykiwany do stron: łapie SPA (pushState/replaceState/popstate)
├── popup.html/css/js # UI rozszerzenia w pasku
├── blocked.html/js   # Strona blokady
├── blocked.json      # Dane (zarządzane przez serwer)
├── server.py         # Flask, 8765
└── icon.png
```

## Jak działa blokowanie

1. **Domeny bez ścieżki** (`facebook.com`) → `declarativeNetRequest` w tle → przeglądarka
   przekierowuje żądanie do `blocked.html` zanim strona się załaduje (szybkie, niezawodne).

2. **Wpisy ze ścieżką** (`youtube.com/shorts`) → `content.js` obserwuje `history.pushState`
   i `replaceState` (bo YouTube nie przeładowuje strony przy klikaniu w Shorts). Przy
   dopasowaniu robi `window.location.replace()` do strony blokady.

Podział wynika z tego, że `declarativeNetRequest` nie widzi nawigacji SPA — dopiero
żądania HTTP. Dlatego wpisy z paths wymagają content scriptu.
