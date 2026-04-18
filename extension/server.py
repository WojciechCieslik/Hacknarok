"""
Serwer dla rozszerzenia Bloker Stron / Context Switcher Pro.

Źródłem prawdy są pliki data/profiles/*.json oraz data/active.json
zarządzane przez główną aplikację Context Switcher Pro.

Endpointy:
  GET    /state               -> aktywny profil + jego dane + lista profili
  GET    /blocked             -> lista zablokowanych stron dla aktywnego profilu
  POST   /blocked             -> { site, password? } dodaje stronę do profilu
  DELETE /blocked             -> { site, password? } usuwa stronę z profilu
  GET    /profiles            -> wszystkie profile
  POST   /active-profile      -> { profile } zmienia aktywny profil
  GET    /health              -> status serwera
"""

import hashlib
import json
import os
import re
import threading
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(_BASE_DIR, "data", "profiles")
ACTIVE_FILE = os.path.join(_BASE_DIR, "data", "active.json")

FILE_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Obsługa plików
# ---------------------------------------------------------------------------

def _safe_filename(name: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return safe or "profil"


def _profile_path(name: str) -> str:
    return os.path.join(PROFILES_DIR, f"{_safe_filename(name)}.json")


def _read_profile(name: str) -> dict | None:
    path = _profile_path(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_profile(data: dict):
    name = data.get("name", "")
    path = _profile_path(name)
    tmp = path + ".tmp"
    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def _list_profiles() -> dict[str, dict]:
    """Zwraca słownik {nazwa: dane_profilu} dla wszystkich profili."""
    result = {}
    if not os.path.exists(PROFILES_DIR):
        return result
    for filename in sorted(os.listdir(PROFILES_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(PROFILES_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                p = json.load(f)
            name = p.get("name")
            if name:
                result[name] = p
        except Exception:
            pass
    return result


def _read_active_name() -> str | None:
    if not os.path.exists(ACTIVE_FILE):
        return None
    try:
        with open(ACTIVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("active")
    except Exception:
        return None


def _write_active_name(name: str | None):
    tmp = ACTIVE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"active": name}, f, ensure_ascii=False)
    os.replace(tmp, ACTIVE_FILE)


def _profile_for_extension(p: dict) -> dict:
    """Konwertuje profil z formatu aplikacji na format zrozumiały przez rozszerzenie."""
    return {
        "name": p.get("name", ""),
        "color": p.get("color", "#4A90E2"),
        "blockedSites": p.get("blocked_sites", []),
        "locked": p.get("locked", False),
    }


# ---------------------------------------------------------------------------
# Narzędzia
# ---------------------------------------------------------------------------

def normalize_site(site: str) -> str:
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


def verify_password(profile_data: dict, password: str) -> bool:
    stored = profile_data.get("password_hash", "")
    if not stored:
        return False
    return hashlib.sha256(password.encode()).hexdigest() == stored


# ---------------------------------------------------------------------------
# Endpointy
# ---------------------------------------------------------------------------

@app.route("/state", methods=["GET"])
def get_state():
    with FILE_LOCK:
        profiles = _list_profiles()
        active_name = _read_active_name()

    if not active_name or active_name not in profiles:
        active_name = next(iter(profiles), None)

    active_profile = _profile_for_extension(profiles[active_name]) if active_name else {}

    return jsonify({
        "activeProfile": active_name,
        "profile": active_profile,
        "availableProfiles": list(profiles.keys()),
    })


@app.route("/blocked", methods=["GET"])
def get_blocked():
    with FILE_LOCK:
        profiles = _list_profiles()
        active_name = _read_active_name()

    if not active_name or active_name not in profiles:
        active_name = next(iter(profiles), None)

    if not active_name:
        return jsonify([])

    return jsonify(profiles[active_name].get("blocked_sites", []))


@app.route("/blocked", methods=["POST"])
def add_blocked():
    body = request.get_json(silent=True) or {}
    site = normalize_site(body.get("site", ""))
    password = body.get("password", "")

    if not site:
        return jsonify({"error": "Brak lub nieprawidłowe pole 'site'"}), 400

    with FILE_LOCK:
        profiles = _list_profiles()
        active_name = _read_active_name()
        if not active_name or active_name not in profiles:
            active_name = next(iter(profiles), None)
        if not active_name:
            return jsonify({"error": "Brak aktywnego profilu"}), 404

        profile = profiles[active_name]

        if profile.get("locked", False):
            if not password or not verify_password(profile, password):
                return jsonify({"error": "Profil chroniony hasłem"}), 403

        sites = profile.setdefault("blocked_sites", [])
        if site in sites:
            return jsonify({"ok": True, "site": site, "message": "Już zablokowana"}), 200

        sites.append(site)
        _write_profile(profile)

    print(f"[+] {active_name}: dodano '{site}'")
    return jsonify({"ok": True, "site": site, "profile": active_name}), 201


@app.route("/blocked", methods=["DELETE"])
def remove_blocked():
    body = request.get_json(silent=True) or {}
    site = normalize_site(body.get("site", ""))
    password = body.get("password", "")

    if not site:
        return jsonify({"error": "Brak lub nieprawidłowe pole 'site'"}), 400

    with FILE_LOCK:
        profiles = _list_profiles()
        active_name = _read_active_name()
        if not active_name or active_name not in profiles:
            active_name = next(iter(profiles), None)
        if not active_name:
            return jsonify({"error": "Brak aktywnego profilu"}), 404

        profile = profiles[active_name]

        if profile.get("locked", False):
            if not password or not verify_password(profile, password):
                return jsonify({"error": "Profil chroniony hasłem"}), 403

        sites = profile.get("blocked_sites", [])
        if site not in sites:
            return jsonify({"ok": True, "site": site, "message": "Nie było zablokowane"}), 200

        sites.remove(site)
        profile["blocked_sites"] = sites
        _write_profile(profile)

    print(f"[-] {active_name}: usunięto '{site}'")
    return jsonify({"ok": True, "site": site, "profile": active_name}), 200


@app.route("/profiles", methods=["GET"])
def list_profiles_endpoint():
    with FILE_LOCK:
        profiles = _list_profiles()
    return jsonify({name: _profile_for_extension(p) for name, p in profiles.items()})


@app.route("/active-profile", methods=["POST"])
def set_active_profile():
    body = request.get_json(silent=True) or {}
    name = body.get("profile", "").strip()
    if not name:
        return jsonify({"error": "Brak pola 'profile'"}), 400

    with FILE_LOCK:
        profiles = _list_profiles()
        if name not in profiles:
            return jsonify({"error": f"Profil '{name}' nie istnieje"}), 404
        _write_active_name(name)
        profile = profiles[name]

    print(f"[→] Aktywny profil: {name}")
    return jsonify({"ok": True, "activeProfile": name,
                    "profile": _profile_for_extension(profile)}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "time": datetime.now().isoformat()})


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(PROFILES_DIR, exist_ok=True)
    profiles = _list_profiles()
    active_name = _read_active_name()
    if not active_name or active_name not in profiles:
        active_name = next(iter(profiles), None)

    print("=" * 55)
    print(" Serwer Bloker Stron – Context Switcher Pro")
    print("=" * 55)
    print(f" URL:             http://localhost:8765")
    print(f" Aktywny profil:  {active_name or '(brak)'}")
    print(f" Dostępne:        {', '.join(profiles.keys()) or '(brak profili)'}")
    if active_name and active_name in profiles:
        sites = profiles[active_name].get("blocked_sites", [])
        print(f" Zablokowane ({len(sites)}):")
        for s in sites:
            print(f"    • {s}")
    print(f" Katalog profili: {PROFILES_DIR}")
    print("=" * 55)
    app.run(port=8765, debug=False)
