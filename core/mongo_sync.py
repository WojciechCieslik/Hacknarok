"""
MongoSync – synchronizacja profili i harmonogramu z MongoDB Atlas.

Klient jest READ-ONLY: baza jest źródłem prawdy, aplikacja tylko pobiera
dane dla wskazanego `user_id`. Lokalne edycje w UI zostaną nadpisane
przy następnej synchronizacji.

Konfiguracja: data/config.json (szablon: data/config.example.json).
URI można też nadpisać zmienną środowiskową TIMEGUARD_MONGO_URI.
"""

from __future__ import annotations

import json
import os
import logging
import threading
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def load_config() -> dict:
    cfg = {
        "mongodb_uri": "",
        "mongodb_db": "timeguard",
        "user_id": "user_demo",
        "sync_interval_sec": 60,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            logger.error(f"Błąd wczytywania config.json: {e}")

    env_uri = os.environ.get("TIMEGUARD_MONGO_URI")
    if env_uri:
        cfg["mongodb_uri"] = env_uri
    return cfg


def _safe_filename(name: str) -> str:
    import re
    safe = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return safe or "profil"


class MongoSync(QObject):
    """Okresowy pull z MongoDB – profile + harmonogram użytkownika."""

    syncStarted = Signal()
    syncFinished = Signal(bool, str)      # (success, message)
    dataUpdated = Signal()                # emit gdy pliki na dysku uległy zmianie

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self._client = None
        self._last_sync: Optional[datetime] = None
        self._last_error: str = ""
        self._syncing = False
        self._lock = threading.Lock()

        self._timer = QTimer(self)
        interval = max(10, int(self.config.get("sync_interval_sec", 60)))
        self._timer.setInterval(interval * 1000)
        self._timer.timeout.connect(self.sync_async)

    # ─── Public API ─────────────────────────────────────────────

    @property
    def user_id(self) -> str:
        return self.config.get("user_id", "user_demo")

    @property
    def last_sync(self) -> Optional[datetime]:
        return self._last_sync

    @property
    def is_configured(self) -> bool:
        return bool(self.config.get("mongodb_uri"))

    def start_auto_sync(self):
        if not self.is_configured:
            logger.warning("MongoSync: brak mongodb_uri – auto-sync wyłączony")
            return
        self._timer.start()
        self.sync_async()

    def stop(self):
        self._timer.stop()
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def sync_async(self):
        """Uruchom synchronizację w tle (bez blokowania UI)."""
        if self._syncing:
            return
        t = threading.Thread(target=self._sync_safe, daemon=True)
        t.start()

    # ─── Internals ──────────────────────────────────────────────

    def _sync_safe(self):
        with self._lock:
            if self._syncing:
                return
            self._syncing = True
        try:
            self.syncStarted.emit()
            self._sync()
            self._last_sync = datetime.now()
            self._last_error = ""
            self.syncFinished.emit(True, self._last_sync.strftime("%H:%M:%S"))
            self.dataUpdated.emit()
        except Exception as e:
            logger.error(f"MongoSync: błąd synchronizacji: {e}")
            self._last_error = str(e)
            self.syncFinished.emit(False, str(e))
        finally:
            self._syncing = False

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from pymongo import MongoClient
        except ImportError as e:
            raise RuntimeError(
                "Brak pakietu pymongo – zainstaluj przez: pip install pymongo"
            ) from e
        uri = self.config.get("mongodb_uri", "")
        if not uri:
            raise RuntimeError("Brak mongodb_uri w data/config.json")
        self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # trigger connection check
        self._client.admin.command("ping")
        return self._client

    def _db(self):
        return self._get_client()[self.config.get("mongodb_db", "timeguard")]

    def _sync(self):
        db = self._db()

        # 1) Harmonogram użytkownika
        sched_doc = db.user_schedules.find_one({"user_id": self.user_id})
        blocks = sched_doc.get("blocks", []) if sched_doc else []

        # 2) Profile – pobierz wszystkie dokumenty z kolekcji profiles
        profile_docs = list(db.profiles.find({}))

        # 3) Zapis na dysk
        self._write_profiles(profile_docs)
        self._write_schedule(blocks)

        logger.info(
            f"MongoSync: pobrano {len(profile_docs)} profili, "
            f"{len(blocks)} bloków harmonogramu (user_id={self.user_id})"
        )

    def _write_profiles(self, docs: list[dict]):
        os.makedirs(PROFILES_DIR, exist_ok=True)

        server_filenames = set()
        for doc in docs:
            name = doc.get("name")
            if not name:
                continue
            out = {
                "name": name,
                "icon": doc.get("icon", "🖥️"),
                "color": doc.get("color", "#7c3aed"),
                "description": doc.get("description", ""),
                "actions": doc.get("actions", []),
                "blocked_sites": doc.get("blocked_sites", []),
            }
            if doc.get("locked"):
                out["locked"] = True
            if doc.get("password_hash"):
                out["password_hash"] = doc["password_hash"]

            filename = f"{_safe_filename(name)}.json"
            server_filenames.add(filename)
            path = os.path.join(PROFILES_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)

        # Usuń lokalne pliki profili, których nie ma już na serwerze
        if docs:
            for existing in os.listdir(PROFILES_DIR):
                if existing.endswith(".json") and existing not in server_filenames:
                    try:
                        os.remove(os.path.join(PROFILES_DIR, existing))
                        logger.info(f"MongoSync: usunięto nieaktualny profil {existing}")
                    except OSError as e:
                        logger.error(f"Nie udało się usunąć {existing}: {e}")

    def _write_schedule(self, blocks: list[dict]):
        os.makedirs(DATA_DIR, exist_ok=True)
        cleaned = []
        for b in blocks:
            cleaned.append({
                "day": int(b.get("day", 0)),
                "start_hour": int(b.get("start_hour", 0)),
                "start_min": int(b.get("start_min", 0)),
                "end_hour": int(b.get("end_hour", 0)),
                "end_min": int(b.get("end_min", 0)),
                "profile_name": b.get("profile_name", ""),
                "enabled": bool(b.get("enabled", True)),
            })
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump({"blocks": cleaned}, f, indent=2, ensure_ascii=False)
