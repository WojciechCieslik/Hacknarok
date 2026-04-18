"""
Serwer dla rozszerzenia Bloker Stron / Context Switcher Pro.

Obsługuje:
  GET    /state               -> aktywny profil + jego dane + lista profili
  GET    /blocked             -> lista zablokowanych stron dla aktywnego profilu (kompat. wsteczna)
  POST   /blocked             -> { site, profile? } dodaje stronę do profilu (domyślnie aktywnego)
  DELETE /blocked             -> { site, profile? } usuwa stronę z profilu
  GET    /profiles            -> wszystkie profile
  PUT    /profiles/<name>     -> tworzy/aktualizuje profil  (dla integracji z Context Switcher Pro)
  POST   /active-profile      -> { profile, color?, blockedSites? } zmienia aktywny profil
  GET    /health              -> status serwera

Format pliku blocked.json:
{
  "activeProfile": "Praca",
  "profiles": {
    "Praca":    { "name": "Praca",    "color": "#4A90E2", "blockedSites": [...] },
    "Nauka":    { "name": "Nauka",    "color": "#50C878", "blockedSites": [...] },
    "Rozrywka": { "name": "Rozrywka", "color": "#E74C3C", "blockedSites": [...] }
  }
}

Migruje automatycznie stary format (zwykła lista domen) przy pierwszym uruchomieniu.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import threading
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Pozwala rozszerzeniu Chrome odpytywać ten serwer

BLOCKED_FILE = "blocked.json"
FILE_LOCK = threading.Lock()

DEFAULT_DATA = {
    "activeProfile": "Default",
    "profiles": {
        "Default": {
            "name": "Default",
            "color": "#4A90E2",
            "blockedSites": []
        }
    }
}


# ---------------------------------------------------------------------------
# Ładowanie / zapis danych
# ---------------------------------------------------------------------------
def load_data():
    """Wczytuje dane; migruje stary format (lista) automatycznie."""
    if not os.path.exists(BLOCKED_FILE):
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))  # deep copy

    try:
        with open(BLOCKED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[WARN] Nieprawidłowy blocked.json ({e}). Tworzę nowy.")
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))

    # Migracja ze starego formatu (lista domen) -> nowy format profilowy
    if isinstance(data, list):
        print("[INFO] Migracja ze starego formatu (lista) do nowego (profile).")
        data = {
            "activeProfile": "Default",
            "profiles": {
                "Default": {
                    "name": "Default",
                    "color": "#4A90E2",
                    "blockedSites": data
                }
            }
        }
        save_data(data)

    # Walidacja / naprawa braków
    if not isinstance(data, dict) or "profiles" not in data:
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))

    if "activeProfile" not in data or data["activeProfile"] not in data["profiles"]:
        # Jeśli aktywny profil nie istnieje, wybierz pierwszy dostępny
        if data["profiles"]:
            data["activeProfile"] = next(iter(data["profiles"]))
        else:
            data = json.loads(json.dumps(DEFAULT_DATA))
        save_data(data)

    return data


def save_data(data):
    """Atomowy zapis: pisz do .tmp, potem os.replace()."""
    tmp = BLOCKED_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, BLOCKED_FILE)


# ---------------------------------------------------------------------------
# Narzędzia
# ---------------------------------------------------------------------------
def normalize_site(site: str) -> str:
    """
    Normalizuje wpis domeny:
      - lowercase
      - usuwa http(s)://
      - usuwa www.
      - usuwa końcowy /
    np. 'https://www.YouTube.com/shorts/' -> 'youtube.com/shorts'
    """
    if not isinstance(site, str):
        return ""
    site = site.strip().lower()
    for prefix in ("https://", "http://"):
        if site.startswith(prefix):
            site = site[len(prefix):]
            break
    if site.startswith("www."):
        site = site[4:]
    return site.rstrip("/")


def get_active(data):
    """Zwraca (nazwa, obiekt) aktywnego profilu."""
    name = data.get("activeProfile")
    return name, data["profiles"].get(name, {})


# ---------------------------------------------------------------------------
# Endpointy
# ---------------------------------------------------------------------------
@app.route("/blocked", methods=["GET"])
def get_blocked():
    """Lista domen dla aktywnego profilu (kompatybilność wsteczna)."""
    with FILE_LOCK:
        data = load_data()
    _, prof = get_active(data)
    return jsonify(prof.get("blockedSites", []))


@app.route("/state", methods=["GET"])
def get_state():
    """Pełny stan: aktywny profil + jego dane + nazwy wszystkich profili."""
    with FILE_LOCK:
        data = load_data()
    name, prof = get_active(data)
    return jsonify({
        "activeProfile": name,
        "profile": prof,
        "availableProfiles": list(data["profiles"].keys())
    })


@app.route("/blocked", methods=["POST"])
def add_blocked():
    """Dodaje stronę do profilu (domyślnie aktywnego)."""
    body = request.get_json(silent=True) or {}
    site = normalize_site(body.get("site", ""))
    profile_name = body.get("profile")

    if not site:
        return jsonify({"error": "Brak lub nieprawidłowe pole 'site'"}), 400

    with FILE_LOCK:
        data = load_data()
        target = profile_name or data["activeProfile"]
        if target not in data["profiles"]:
            return jsonify({"error": f"Profil '{target}' nie istnieje"}), 404

        if data["profiles"][target].get("locked", False):
            return jsonify({"error": f"Profil '{target}' jest zablokowany"}), 403

        sites = data["profiles"][target]["blockedSites"]
        if site in sites:
            return jsonify({"ok": True, "site": site, "profile": target,
                            "message": "Już zablokowana"}), 200

        sites.append(site)
        save_data(data)

    print(f"[+] {target}: dodano '{site}'")
    return jsonify({"ok": True, "site": site, "profile": target}), 201


@app.route("/blocked", methods=["DELETE"])
def remove_blocked():
    """Usuwa stronę z profilu (domyślnie aktywnego)."""
    body = request.get_json(silent=True) or {}
    site = normalize_site(body.get("site", ""))
    profile_name = body.get("profile")

    if not site:
        return jsonify({"error": "Brak lub nieprawidłowe pole 'site'"}), 400

    with FILE_LOCK:
        data = load_data()
        target = profile_name or data["activeProfile"]
        if target not in data["profiles"]:
            return jsonify({"error": f"Profil '{target}' nie istnieje"}), 404

        if data["profiles"][target].get("locked", False):
            return jsonify({"error": f"Profil '{target}' jest zablokowany"}), 403

        sites = data["profiles"][target]["blockedSites"]
        if site not in sites:
            return jsonify({"ok": True, "site": site, "profile": target,
                            "message": "Nie było zablokowane"}), 200

        sites.remove(site)
        save_data(data)

    print(f"[-] {target}: usunięto '{site}'")
    return jsonify({"ok": True, "site": site, "profile": target}), 200


@app.route("/profiles", methods=["GET"])
def list_profiles():
    """Zwraca wszystkie profile."""
    with FILE_LOCK:
        data = load_data()
    return jsonify(data["profiles"])


@app.route("/profiles/<name>", methods=["PUT"])
def upsert_profile(name):
    """
    Tworzy/aktualizuje profil. Używane przez Context Switcher Pro przy edycji profili.
    Body: { "color": "#...", "blockedSites": [...] }
    """
    body = request.get_json(silent=True) or {}
    with FILE_LOCK:
        data = load_data()
        existing = data["profiles"].get(name, {})
        data["profiles"][name] = {
            "name": name,
            "color": body.get("color", existing.get("color", "#4A90E2")),
            "blockedSites": [normalize_site(s) for s in body.get(
                "blockedSites", existing.get("blockedSites", [])) if s],
            "locked": existing.get("locked", False)
        }
        save_data(data)
    print(f"[~] Profil '{name}' zaktualizowany ({len(data['profiles'][name]['blockedSites'])} stron)")
    return jsonify({"ok": True, "profile": data["profiles"][name]}), 200


@app.route("/profiles/<name>", methods=["DELETE"])
def delete_profile(name):
    """Usuwa profil. Jeśli był aktywny, wybiera inny."""
    with FILE_LOCK:
        data = load_data()
        if name not in data["profiles"]:
            return jsonify({"error": "Profil nie istnieje"}), 404
        del data["profiles"][name]
        if data["activeProfile"] == name:
            data["activeProfile"] = next(iter(data["profiles"]), "Default")
            if not data["profiles"]:
                data = json.loads(json.dumps(DEFAULT_DATA))
        save_data(data)
    return jsonify({"ok": True, "activeProfile": data["activeProfile"]}), 200


@app.route("/active-profile", methods=["POST"])
def set_active_profile():
    """
    Zmienia aktywny profil. Używane przez Context Switcher Pro przy przełączaniu profilu.
    Body: { "profile": "Praca", "color"?: "#...", "blockedSites"?: [...] }
    Jeśli profil nie istnieje — zostanie utworzony.
    """
    body = request.get_json(silent=True) or {}
    name = body.get("profile", "").strip()

    if not name:
        return jsonify({"error": "Brak pola 'profile'"}), 400

    with FILE_LOCK:
        data = load_data()
        if name not in data["profiles"]:
            data["profiles"][name] = {
                "name": name,
                "color": body.get("color", "#4A90E2"),
                "blockedSites": [normalize_site(s) for s in body.get("blockedSites", []) if s]
            }
        else:
            # Opcjonalnie nadpisz dane profilu, jeśli podano
            if "color" in body:
                data["profiles"][name]["color"] = body["color"]
            if "blockedSites" in body:
                data["profiles"][name]["blockedSites"] = [
                    normalize_site(s) for s in body["blockedSites"] if s
                ]
        data["activeProfile"] = name
        save_data(data)

    print(f"[→] Aktywny profil: {name}")
    return jsonify({"ok": True, "activeProfile": name,
                    "profile": data["profiles"][name]}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "time": datetime.now().isoformat()})


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    data = load_data()
    name, prof = get_active(data)
    print("=" * 55)
    print(" Serwer Bloker Stron – Context Switcher Pro")
    print("=" * 55)
    print(f" URL:             http://localhost:8765")
    print(f" Aktywny profil:  {name}")
    print(f" Dostępne:        {', '.join(data['profiles'].keys())}")
    print(f" Zablokowane ({len(prof.get('blockedSites', []))}):")
    for s in prof.get("blockedSites", []):
        print(f"    • {s}")
    print("=" * 55)
    app.run(port=8765, debug=False)
