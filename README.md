# Time Guard

Self-enforcing daily planner — switch your environment between work, study, and entertainment modes with one click. Profiles automatically change wallpaper, system theme, block distracting apps, and lock websites in the browser.

> 🇵🇱 [Wersja polska poniżej](#time-guard-pl)

---

## Requirements

- **Python 3.10+** (tested on 3.12)
- **Windows 10/11**
- **Google Chrome** (for the site blocker extension)
- **MongoDB** — one of:
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended, setup handles it automatically)
  - [MongoDB Community Server](https://www.mongodb.com/try/download/community)

---

## Quick start

```bash
git clone <repo-url>
cd Hacknarok

python setup.py
```

`setup.py` does everything in one step:

1. Installs Python dependencies from `requirements.txt`
2. Starts MongoDB (via Docker or system `mongod`)
3. Creates `data/config.json` pointing to localhost
4. Seeds the database with example data
5. Prints Chrome extension installation instructions

After setup completes:

```bash
python main.py
```

---

## Startup modes

| Command | Mode |
|---|---|
| `python main.py` | Offline — local profiles only |
| `python main.py online` | Online — syncs with MongoDB |

---

## Chrome Extension

The extension blocks websites listed in the active profile and lets you manage the blocked list from the browser popup.

After running `setup.py`, follow the printed instructions:

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/extension/` folder

> The extension only works while the app is running (it connects to a local server on port 8765).

---

## Profile passwords

A profile can be locked with a password. When locked, the following all require the password:

- Editing or deleting the profile
- Activating or deactivating the profile
- Adding or removing the profile from the schedule
- Managing blocked websites from the browser extension

Set a password in the profile editor under **Lock / Password protection**.

---

## Configuration (`data/config.json`)

Created automatically by `setup.py`. Edit it manually to change the server, database, or user.

```json
{
  "mongodb_uri":       "mongodb://localhost:27017",
  "mongodb_db":        "timeguard",
  "user_id":           "user_demo",
  "sync_interval_sec": 60
}
```

| Field | Description |
|---|---|
| `mongodb_uri` | MongoDB connection string. Use `mongodb://localhost:27017` for local Docker, or an Atlas URI (`mongodb+srv://...`) for a remote server |
| `mongodb_db` | Database name — must match what the admin is using |
| `user_id` | Unique identifier for this machine/user — used to assign a role in the database |
| `sync_interval_sec` | How often (in seconds) the app checks for schedule/profile updates from the server |

**Example — connecting to a remote Atlas cluster:**

```json
{
  "mongodb_uri":       "mongodb+srv://user:password@cluster.mongodb.net/",
  "mongodb_db":        "timeguard",
  "user_id":           "jan-laptop",
  "sync_interval_sec": 30
}
```

> Changes to `config.json` take effect on the next app start.

---

## Project structure

```
main.py                  # Entry point
setup.py                 # One-shot environment setup
core/
  profile_manager.py     # Profile CRUD and activation logic
  scheduler.py           # Weekly schedule engine
  system_controller.py   # OS-level actions (wallpaper, theme, processes)
  actions.py             # Profile action types
  mongo_sync.py          # MongoDB sync client
gui/
  main_window.py         # Main application window
  profile_card.py        # Profile list card widget
  profile_editor.py      # Profile create/edit dialog
  schedule_widget.py     # Weekly calendar widget
  password_utils.py      # Password prompt helper
data/
  profiles/              # Per-profile JSON files
  schedule.json          # Local weekly schedule
  active.json            # Currently active profile
  config.json            # MongoDB connection config (created by setup.py)
extension/
  extension/             # Chrome extension source
  server.py              # Flask API for the extension
```

---
---

# Time Guard (PL)

Samo-enforsujący się planer dnia — przełącz swoje środowisko między trybami pracy, nauki i rozrywki jednym kliknięciem. Profile automatycznie zmieniają tapetę, motyw systemu, blokują rozpraszające aplikacje i zamykają strony w przeglądarce.

---

## Wymagania

- **Python 3.10+** (testowane na 3.12)
- **Windows 10/11**
- **Google Chrome** (do rozszerzenia blokującego strony)
- **MongoDB** — jedna z opcji:
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (zalecane, setup uruchamia automatycznie)
  - [MongoDB Community Server](https://www.mongodb.com/try/download/community)

---

## Szybki start

```bash
git clone <repo-url>
cd Hacknarok

python setup.py
```

`setup.py` robi wszystko za jednym razem:

1. Instaluje zależności Python z `requirements.txt`
2. Uruchamia MongoDB (przez Docker lub systemowe `mongod`)
3. Tworzy `data/config.json` wskazujący na localhost
4. Seeduje bazę przykładowymi danymi
5. Wyświetla instrukcję instalacji rozszerzenia Chrome

Po zakończeniu setupu:

```bash
python main.py
```

---

## Tryby uruchomienia

| Komenda | Tryb |
|---|---|
| `python main.py` | Offline — tylko lokalne profile |
| `python main.py online` | Online — synchronizacja z MongoDB |

---

## Rozszerzenie Chrome

Rozszerzenie blokuje strony z listy aktywnego profilu i pozwala zarządzać nimi z poziomu popupa w przeglądarce.

Po uruchomieniu `setup.py` wykonaj wyświetlone instrukcje:

1. Otwórz Chrome → `chrome://extensions`
2. Włącz **Tryb dewelopera** (przełącznik w prawym górnym rogu)
3. Kliknij **Załaduj rozpakowane**
4. Wskaż folder `extension/extension/`

> Rozszerzenie działa tylko gdy aplikacja jest uruchomiona (łączy się z lokalnym serwerem na porcie 8765).

---

## Hasła profili

Profil można zabezpieczyć hasłem. Po ustawieniu hasła poniższe operacje wymagają jego podania:

- Edycja lub usunięcie profilu
- Aktywacja lub dezaktywacja profilu
- Dodanie lub usunięcie profilu z harmonogramu
- Zarządzanie zablokowanymi stronami z poziomu rozszerzenia

Hasło ustawia się w edytorze profilu w sekcji **Ochrona hasłem**.

---

## Konfiguracja (`data/config.json`)

Tworzony automatycznie przez `setup.py`. Edytuj ręcznie aby zmienić serwer, bazę lub użytkownika.

```json
{
  "mongodb_uri":       "mongodb://localhost:27017",
  "mongodb_db":        "timeguard",
  "user_id":           "user_demo",
  "sync_interval_sec": 60
}
```

| Pole | Opis |
|---|---|
| `mongodb_uri` | Adres połączenia z MongoDB. Użyj `mongodb://localhost:27017` dla lokalnego Dockera lub URI Atlas (`mongodb+srv://...`) dla zdalnego serwera |
| `mongodb_db` | Nazwa bazy danych — musi być taka sama jak u admina |
| `user_id` | Unikalny identyfikator tego komputera/użytkownika — używany do przypisania roli w bazie |
| `sync_interval_sec` | Co ile sekund aplikacja sprawdza aktualizacje harmonogramu i profili z serwera |

**Przykład — połączenie ze zdalnym klastrem Atlas:**

```json
{
  "mongodb_uri":       "mongodb+srv://user:haslo@cluster.mongodb.net/",
  "mongodb_db":        "timeguard",
  "user_id":           "jan-laptop",
  "sync_interval_sec": 30
}
```

> Zmiany w `config.json` wchodzą w życie po ponownym uruchomieniu aplikacji.
