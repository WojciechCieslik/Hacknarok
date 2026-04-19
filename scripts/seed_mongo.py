"""
seed_mongo.py – Wypełnia bazę MongoDB przykładowymi danymi.

Użycie:
    python scripts/seed_mongo.py
    python scripts/seed_mongo.py --drop   # czyści kolekcje przed seedowaniem
    python scripts/seed_mongo.py --uri mongodb://localhost:27017

Czyta URI z data/config.json lub data/config.example.json jeśli nie podano --uri.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
except ImportError:
    print("Brakuje pymongo. Zainstaluj: pip install pymongo")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(__file__))

# ─── Dane seed ──────────────────────────────────────────────────

USERS = [
    {"user_id": "user_ania",    "name": "Ania Kowalska",   "email": "ania@example.com"},
    {"user_id": "user_bartek",  "name": "Bartek Nowak",    "email": "bartek@example.com"},
    {"user_id": "user_czarek",  "name": "Czarek Wiśniewski","email": "czarek@example.com"},
    {"user_id": "user_daria",   "name": "Daria Zielińska", "email": "daria@example.com"},
    {"user_id": "user_eryk",    "name": "Eryk Malinowski",  "email": "eryk@example.com"},
]

# Szablony profili – każdy użytkownik dostaje te same + 1-2 indywidualne
BASE_PROFILES = [
    {
        "name": "Praca",
        "icon": "🏢",
        "color": "#3b82f6",
        "description": "Skupienie na pracy – ciemny motyw, brak rozpraszaczy.",
        "actions": [
            {"type": "set_theme", "dark": True},
            {"type": "block_process", "process_name": "Spotify.exe", "display_name": "Spotify"},
        ],
        "blocked_sites": ["youtube.com", "facebook.com", "twitter.com", "reddit.com"],
        "locked": False,
        "password_hash": "",
    },
    {
        "name": "Nauka",
        "icon": "📚",
        "color": "#10b981",
        "description": "Tryb nauki – jasny motyw, cisza.",
        "actions": [
            {"type": "set_theme", "dark": False},
            {"type": "block_process", "process_name": "discord.exe", "display_name": "Discord"},
            {"type": "block_process", "process_name": "Spotify.exe", "display_name": "Spotify"},
        ],
        "blocked_sites": ["youtube.com", "facebook.com", "twitch.tv", "reddit.com", "instagram.com"],
        "locked": False,
        "password_hash": "",
    },
    {
        "name": "Rozrywka",
        "icon": "🎬",
        "color": "#f59e0b",
        "description": "Czas na relaks – ciemny motyw, wszystko dozwolone.",
        "actions": [
            {"type": "set_theme", "dark": True},
        ],
        "blocked_sites": [],
        "locked": False,
        "password_hash": "",
    },
    {
        "name": "Nauka Cyfrówki",
        "icon": "💻",
        "color": "#8b5cf6",
        "description": "Deep work – programowanie, zero przeglądarek.",
        "actions": [
            {"type": "set_theme", "dark": True},
            {"type": "block_process", "process_name": "chrome.exe",  "display_name": "Chrome"},
            {"type": "block_process", "process_name": "firefox.exe", "display_name": "Firefox"},
            {"type": "block_process", "process_name": "Spotify.exe", "display_name": "Spotify"},
        ],
        "blocked_sites": ["youtube.com", "facebook.com", "reddit.com", "twitter.com", "instagram.com", "twitch.tv"],
        "locked": False,
        "password_hash": "",
    },
    {
        "name": "Odpoczynek",
        "icon": "😴",
        "color": "#6b7280",
        "description": "Koniec dnia – tryb wieczorny.",
        "actions": [
            {"type": "set_theme", "dark": True},
        ],
        "blocked_sites": ["praca.example.com"],
        "locked": False,
        "password_hash": "",
    },
]

# Indywidualne profile per użytkownik (opcjonalne)
EXTRA_PROFILES = {
    "user_ania": [
        {
            "name": "Projekt Graficzny",
            "icon": "🎨",
            "color": "#ec4899",
            "description": "Praca w Figmie / Photoshopie.",
            "actions": [
                {"type": "set_theme", "dark": False},
                {"type": "launch_app", "path": "C:\\Program Files\\Adobe\\Photoshop.exe", "args": [], "label": "Photoshop"},
            ],
            "blocked_sites": ["reddit.com", "twitter.com"],
            "locked": False,
            "password_hash": "",
        },
    ],
    "user_bartek": [
        {
            "name": "Gaming",
            "icon": "🎮",
            "color": "#ef4444",
            "description": "Tryb gamingowy – pełny ekran, bez powiadomień.",
            "actions": [
                {"type": "set_theme", "dark": True},
            ],
            "blocked_sites": [],
            "locked": False,
            "password_hash": "",
        },
    ],
    "user_eryk": [
        {
            "name": "Siłownia",
            "icon": "🏋️",
            "color": "#f97316",
            "description": "Muzyka, brak maili.",
            "actions": [
                {"type": "set_theme", "dark": True},
                {"type": "block_process", "process_name": "outlook.exe", "display_name": "Outlook"},
            ],
            "blocked_sites": ["gmail.com", "outlook.com"],
            "locked": False,
            "password_hash": "",
        },
    ],
}

# Tygodniowy harmonogram – day: 0=Pon … 6=Ndz
# Każdy user dostaje ten sam szablon (można rozbudować per-user)
SCHEDULE_TEMPLATE = [
    # Poniedziałek–Piątek: poranny blok pracy
    *[{"day": d, "start_hour": 8,  "start_min": 0,  "end_hour": 12, "end_min": 0,  "profile_name": "Praca",   "enabled": True} for d in range(5)],
    # Poniedziałek–Piątek: popołudniowa nauka
    *[{"day": d, "start_hour": 13, "start_min": 0,  "end_hour": 16, "end_min": 0,  "profile_name": "Nauka",   "enabled": True} for d in range(5)],
    # Poniedziałek–Piątek: wieczór
    *[{"day": d, "start_hour": 20, "start_min": 0,  "end_hour": 23, "end_min": 0,  "profile_name": "Rozrywka","enabled": True} for d in range(5)],
    # Wtorek / Czwartek: deep work w nocy
    {"day": 1,  "start_hour": 21, "start_min": 30, "end_hour": 23, "end_min": 30, "profile_name": "Nauka Cyfrówki", "enabled": True},
    {"day": 3,  "start_hour": 21, "start_min": 30, "end_hour": 23, "end_min": 30, "profile_name": "Nauka Cyfrówki", "enabled": True},
    # Weekend: luźniej
    {"day": 5,  "start_hour": 10, "start_min": 0,  "end_hour": 14, "end_min": 0,  "profile_name": "Nauka",   "enabled": True},
    {"day": 5,  "start_hour": 15, "start_min": 0,  "end_hour": 23, "end_min": 0,  "profile_name": "Rozrywka","enabled": True},
    {"day": 6,  "start_hour": 11, "start_min": 0,  "end_hour": 22, "end_min": 0,  "profile_name": "Rozrywka","enabled": True},
    # Codzienny odpoczynek przed snem
    *[{"day": d, "start_hour": 23, "start_min": 0,  "end_hour": 23, "end_min": 59, "profile_name": "Odpoczynek", "enabled": True} for d in range(7)],
]


def load_config() -> dict:
    for fname in ("config.json", "config.example.json"):
        path = os.path.join(ROOT, "data", fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}


def seed(uri: str, db_name: str, drop: bool):
    print(f"Łączę z MongoDB: {uri!r}, baza: {db_name!r}")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except ConnectionFailure as e:
        print(f"Błąd połączenia: {e}")
        sys.exit(1)

    db = client[db_name]
    users_col    = db["users"]
    profiles_col = db["profiles"]
    schedules_col = db["schedules"]

    if drop:
        print("Czyszczę kolekcje...")
        users_col.drop()
        profiles_col.drop()
        schedules_col.drop()

    now = datetime.now(timezone.utc)

    # ── Użytkownicy ──────────────────────────────────────────────
    inserted_users = 0
    for u in USERS:
        if not users_col.find_one({"user_id": u["user_id"]}):
            users_col.insert_one({**u, "created_at": now})
            inserted_users += 1
    print(f"Użytkownicy: +{inserted_users} (łącznie {users_col.count_documents({})})")

    # ── Profile ──────────────────────────────────────────────────
    inserted_profiles = 0
    for user in USERS:
        uid = user["user_id"]
        profiles = BASE_PROFILES + EXTRA_PROFILES.get(uid, [])
        for p in profiles:
            if not profiles_col.find_one({"user_id": uid, "name": p["name"]}):
                profiles_col.insert_one({"user_id": uid, **p, "updated_at": now})
                inserted_profiles += 1
    print(f"Profile:     +{inserted_profiles} (łącznie {profiles_col.count_documents({})})")

    # ── Harmonogramy ─────────────────────────────────────────────
    inserted_blocks = 0
    for user in USERS:
        uid = user["user_id"]
        existing = {
            f"{b['day']}-{b['start_hour']}-{b['start_min']}-{b['profile_name']}"
            for b in schedules_col.find({"user_id": uid}, {"day":1,"start_hour":1,"start_min":1,"profile_name":1,"_id":0})
        }
        for b in SCHEDULE_TEMPLATE:
            key = f"{b['day']}-{b['start_hour']}-{b['start_min']}-{b['profile_name']}"
            if key not in existing:
                schedules_col.insert_one({"user_id": uid, **b, "created_at": now})
                inserted_blocks += 1
    print(f"Harmonogram: +{inserted_blocks} (łącznie {schedules_col.count_documents({})})")

    print("\nGotowe!")
    client.close()


def main():
    parser = argparse.ArgumentParser(description="Seed MongoDB dla projektu Time Guard")
    parser.add_argument("--uri",  help="MongoDB URI (nadpisuje config)")
    parser.add_argument("--db",   help="Nazwa bazy danych (nadpisuje config)")
    parser.add_argument("--drop", action="store_true", help="Wyczyść kolekcje przed seedowaniem")
    args = parser.parse_args()

    cfg = load_config()
    uri     = args.uri  or cfg.get("mongodb_uri",  "mongodb://localhost:27017")
    db_name = args.db   or cfg.get("mongodb_db",   "timeguard")

    seed(uri, db_name, args.drop)


if __name__ == "__main__":
    main()
