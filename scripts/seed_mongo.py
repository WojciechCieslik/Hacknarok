"""
seed_mongo.py – inicjalizacja MongoDB Atlas aktualnymi lokalnymi profilami.

Użycie:
    python scripts/seed_mongo.py

Co robi:
1. Wczytuje URI / user_id z data/config.json (lub env TIMEGUARD_MONGO_URI).
2. Tworzy bazę `timeguard` z kolekcjami: users, groups, profiles,
   user_schedules, schedule_change_log.
3. Zakłada indeksy.
4. Wgrywa lokalne profile z data/profiles/*.json do kolekcji `profiles`.
5. Wgrywa lokalny harmonogram z data/schedule.json jako dokument
   user_schedules dla user_id z configu.
6. Tworzy wpis w users dla tego user_id (jeśli nie istnieje).

Bezpieczeństwo: skrypt jest idempotentny – używa upsert po `name`
(profile) i po `user_id` (user_schedules/users).
"""

import json
import os
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from core.mongo_sync import load_config, PROFILES_DIR, SCHEDULE_FILE  # noqa: E402

try:
    from pymongo import MongoClient, ASCENDING
except ImportError:
    print("Brak pymongo. Zainstaluj: pip install pymongo", file=sys.stderr)
    sys.exit(1)


def now_utc():
    return datetime.now(timezone.utc)


def load_local_profiles() -> list[dict]:
    profiles = []
    if not os.path.isdir(PROFILES_DIR):
        return profiles
    for fn in sorted(os.listdir(PROFILES_DIR)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(PROFILES_DIR, fn), "r", encoding="utf-8") as f:
            profiles.append(json.load(f))
    return profiles


def load_local_blocks() -> list[dict]:
    if not os.path.exists(SCHEDULE_FILE):
        return []
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("blocks", [])


def ensure_indexes(db):
    db.users.create_index([("user_id", ASCENDING)], unique=True)
    db.users.create_index([("username", ASCENDING)], unique=True, sparse=True)
    db.groups.create_index([("name", ASCENDING)], unique=True)
    db.profiles.create_index([("name", ASCENDING)], unique=True)
    db.profiles.create_index([("updated_at", ASCENDING)])
    db.user_schedules.create_index([("user_id", ASCENDING)], unique=True)
    db.schedule_change_log.create_index(
        [("user_id", ASCENDING), ("timestamp", ASCENDING)]
    )


def seed_profiles(db, profiles: list[dict]) -> int:
    count = 0
    for p in profiles:
        name = p.get("name")
        if not name:
            continue
        doc = {
            "name": name,
            "icon": p.get("icon", "🖥️"),
            "color": p.get("color", "#7c3aed"),
            "description": p.get("description", ""),
            "actions": p.get("actions", []),
            "blocked_sites": p.get("blocked_sites", []),
            "locked": bool(p.get("locked", False)),
            "password_hash": p.get("password_hash", ""),
            "updated_at": now_utc(),
        }
        res = db.profiles.update_one(
            {"name": name},
            {
                "$set": doc,
                "$setOnInsert": {"created_at": now_utc(), "version": 1},
                "$inc": {},  # version bump only on real change – keep simple here
            },
            upsert=True,
        )
        if res.upserted_id or res.modified_count:
            count += 1
    return count


def seed_user(db, user_id: str):
    db.users.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "username": user_id,
                "email": "",
                "groups": [],
                "created_at": now_utc(),
            },
            "$set": {"updated_at": now_utc()},
        },
        upsert=True,
    )


def seed_schedule(db, user_id: str, blocks: list[dict]):
    db.user_schedules.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "blocks": blocks,
                "updated_at": now_utc(),
            },
            "$setOnInsert": {"created_at": now_utc(), "version": 1},
        },
        upsert=True,
    )


def main():
    cfg = load_config()
    uri = cfg.get("mongodb_uri")
    if not uri:
        print("Brak mongodb_uri w data/config.json (albo TIMEGUARD_MONGO_URI).")
        sys.exit(1)
    user_id = cfg.get("user_id", "user_demo")
    db_name = cfg.get("mongodb_db", "timeguard")

    print(f"Łączenie z MongoDB ({db_name})…")
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    db = client[db_name]

    print("Tworzenie indeksów…")
    ensure_indexes(db)

    profiles = load_local_profiles()
    blocks = load_local_blocks()

    print(f"Seeding profiles → kolekcja 'profiles' ({len(profiles)} lokalnie)…")
    changed = seed_profiles(db, profiles)
    print(f"  zaktualizowano/wstawiono: {changed}")

    print(f"Seeding użytkownika '{user_id}' → kolekcja 'users'…")
    seed_user(db, user_id)

    print(f"Seeding harmonogramu dla '{user_id}' → user_schedules ({len(blocks)} bloków)…")
    seed_schedule(db, user_id, blocks)

    print("Gotowe. Dane dostępne w MongoDB Atlas.")
    client.close()


if __name__ == "__main__":
    main()
