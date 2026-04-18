"""
ProfileManager – zarządzanie profilami.

Każdy profil przechowywany jest jako oddzielny plik JSON w data/profiles/.
Aktywny profil zapamiętywany jest w data/active.json.
"""

import json
import os
import re
import copy
import logging
from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.actions import Action, action_from_dict, BlockProcessAction
from core.system_controller import SystemController

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")
ACTIVE_FILE = os.path.join(DATA_DIR, "active.json")
LEGACY_FILE = os.path.join(DATA_DIR, "profiles.json")


def _safe_filename(name: str) -> str:
    """Zamień nazwę profilu na bezpieczną nazwę pliku (Windows)."""
    safe = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return safe or "profil"


def _profile_path(name: str) -> str:
    return os.path.join(PROFILES_DIR, f"{_safe_filename(name)}.json")


@dataclass
class Profile:
    """Profil środowiska."""
    name: str
    icon: str = "🖥️"
    color: str = "#7c3aed"
    description: str = ""
    actions: list[dict] = field(default_factory=list)
    blocked_sites: list[str] = field(default_factory=list)
    locked: bool = False
    password_hash: str = ""

    def get_actions(self) -> list[Action]:
        result = []
        for a_dict in self.actions:
            try:
                result.append(action_from_dict(a_dict))
            except Exception as e:
                logger.error(f"Błąd deserializacji akcji: {e}")
        return result

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "icon": self.icon,
            "color": self.color,
            "description": self.description,
            "actions": self.actions,
            "blocked_sites": self.blocked_sites,
        }
        if self.locked:
            d["locked"] = True
        if self.password_hash:
            d["password_hash"] = self.password_hash
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        # Odfiltruj przestarzałe akcje (power_plan, kill_process)
        actions = [
            a for a in data.get("actions", [])
            if a.get("type") not in {"set_power_plan", "kill_process"}
        ]
        return cls(
            name=data.get("name", "Bez nazwy"),
            icon=data.get("icon", "🖥️"),
            color=data.get("color", "#7c3aed"),
            description=data.get("description", ""),
            actions=actions,
            blocked_sites=data.get("blocked_sites", []),
            locked=data.get("locked", False),
            password_hash=data.get("password_hash", ""),
        )


class ProfileManager(QObject):
    """Menedżer profili – ładowanie, zapis, przełączanie."""

    profileChanged = Signal(str)
    profilesUpdated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profiles: list[Profile] = []
        self.active_profile: Optional[Profile] = None
        self._previous_state: dict = {}
        self._blocked_processes: list[str] = []
        self.manual_override: bool = False
        self.load()

    # ─── Zapis / Odczyt ─────────────────────────────────────────

    def load(self):
        """Wczytaj profile – migruje stary format jeśli potrzeba."""
        os.makedirs(PROFILES_DIR, exist_ok=True)

        if os.path.exists(LEGACY_FILE):
            self._migrate_legacy()
            return

        self.profiles = []
        for filename in sorted(os.listdir(PROFILES_DIR)):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(PROFILES_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.profiles.append(Profile.from_dict(json.load(f)))
            except Exception as e:
                logger.error(f"Błąd wczytywania profilu {filename}: {e}")

        if not self.profiles:
            self._create_defaults()
            self._save_all_files()

        active_name = self._load_active_name()
        if active_name:
            self.active_profile = self.get_profile(active_name)

        logger.info(f"Wczytano {len(self.profiles)} profil(i)")

    def _load_active_name(self) -> Optional[str]:
        if not os.path.exists(ACTIVE_FILE):
            return None
        try:
            with open(ACTIVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("active")
        except Exception:
            return None

    def _save_active(self):
        try:
            with open(ACTIVE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {"active": self.active_profile.name if self.active_profile else None},
                    f, ensure_ascii=False,
                )
        except Exception as e:
            logger.error(f"Błąd zapisu active.json: {e}")

    def _write_profile_file(self, profile: Profile):
        try:
            with open(_profile_path(profile.name), "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Błąd zapisu profilu '{profile.name}': {e}")

    def _delete_profile_file(self, name: str):
        path = _profile_path(name)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.error(f"Błąd usuwania pliku profilu '{name}': {e}")

    def _save_all_files(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        for profile in self.profiles:
            self._write_profile_file(profile)
        self._save_active()

    def save(self):
        self._save_active()

    def _migrate_legacy(self):
        logger.info("Migracja profiles.json → data/profiles/...")
        try:
            with open(LEGACY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.profiles = [Profile.from_dict(p) for p in data.get("profiles", [])]
            active_name = data.get("active")

            os.makedirs(PROFILES_DIR, exist_ok=True)
            self._save_all_files()

            if active_name:
                self.active_profile = self.get_profile(active_name)
                self._save_active()

            os.rename(LEGACY_FILE, LEGACY_FILE + ".bak")
            logger.info(f"Migracja zakończona. Backup: {LEGACY_FILE}.bak")
        except Exception as e:
            logger.error(f"Błąd migracji: {e}")
            self._create_defaults()
            self._save_all_files()

    # ─── CRUD ────────────────────────────────────────────────────

    def add_profile(self, profile: Profile):
        self.profiles.append(profile)
        self._write_profile_file(profile)
        self._save_active()
        self.profilesUpdated.emit()

    def update_profile(self, old_name: str, updated: Profile) -> bool:
        for i, p in enumerate(self.profiles):
            if p.name == old_name:
                if old_name != updated.name:
                    self._delete_profile_file(old_name)
                    if self.active_profile and self.active_profile.name == old_name:
                        self.active_profile = updated
                self.profiles[i] = updated
                self._write_profile_file(updated)
                self._save_active()
                self.profilesUpdated.emit()
                return True
        return False

    def delete_profile(self, name: str):
        self._delete_profile_file(name)
        self.profiles = [p for p in self.profiles if p.name != name]
        if self.active_profile and self.active_profile.name == name:
            self._stop_blocking()
            self.active_profile = None
            self._previous_state = {}
        self._save_active()
        self.profilesUpdated.emit()

    def duplicate_profile(self, name: str) -> Optional[Profile]:
        for p in self.profiles:
            if p.name == name:
                new_name = f"{p.name} (kopia)"
                counter = 2
                existing = {pp.name for pp in self.profiles}
                while new_name in existing:
                    new_name = f"{p.name} (kopia {counter})"
                    counter += 1
                new_profile = Profile(
                    name=new_name,
                    icon=p.icon,
                    color=p.color,
                    description=p.description,
                    actions=copy.deepcopy(p.actions),
                    blocked_sites=copy.deepcopy(p.blocked_sites),
                    locked=p.locked,
                    password_hash=p.password_hash,
                )
                self.add_profile(new_profile)
                return new_profile
        return None

    def get_profile(self, name: str) -> Optional[Profile]:
        for p in self.profiles:
            if p.name == name:
                return p
        return None

    # ─── Przełączanie ────────────────────────────────────────────

    def _capture_state(self) -> dict:
        return {
            "volume": SystemController.get_volume(),
            "wallpaper": SystemController.get_wallpaper(),
            "dark_theme": SystemController.get_theme(),
        }

    def switch_profile(self, profile_name: str, manual: bool = False) -> bool:
        profile = self.get_profile(profile_name)
        if not profile:
            logger.error(f"Profil '{profile_name}' nie znaleziony")
            return False

        if self.active_profile:
            self._stop_blocking()

        try:
            self._previous_state = self._capture_state()
        except Exception as e:
            logger.error(f"Błąd przechwytywania stanu systemu: {e}")
            self._previous_state = {}

        for action in profile.get_actions():
            try:
                action.execute()
                if isinstance(action, BlockProcessAction):
                    self._blocked_processes.append(action.process_name)
            except Exception as e:
                logger.error(f"Błąd wykonywania akcji {action.get_description()}: {e}")

        self.active_profile = profile
        self.manual_override = manual
        self._save_active()
        self.profileChanged.emit(profile.name)
        logger.info(f"Przełączono na profil: {profile.name}")
        return True

    def deactivate_profile(self):
        if not self.active_profile:
            return

        self._stop_blocking()

        state = self._previous_state
        if state:
            if "volume" in state:
                SystemController.set_volume(state["volume"])
            if "wallpaper" in state and state["wallpaper"]:
                SystemController.set_wallpaper(state["wallpaper"])
            if "dark_theme" in state:
                SystemController.set_theme(state["dark_theme"])

        self.active_profile = None
        self._previous_state = {}
        self.manual_override = False
        self._save_active()
        self.profileChanged.emit("")
        logger.info("Profil dezaktywowany – stan przywrócony")

    def _stop_blocking(self):
        self._blocked_processes.clear()

    def get_blocked_processes(self) -> list[str]:
        return list(self._blocked_processes)

    def enforce_blocks(self):
        """Zamknij zablokowane procesy gdy ponownie się uruchomią."""
        if not self._blocked_processes:
            return
        for proc_name in self._blocked_processes:
            try:
                SystemController.close_process(proc_name)
            except Exception as e:
                logger.error(f"Błąd egzekwowania blokady {proc_name}: {e}")

    # ─── Profile domyślne ────────────────────────────────────────

    def _create_defaults(self):
        self.profiles = [
            Profile(
                name="Praca",
                icon="🏢",
                color="#3b82f6",
                description="Skup się na pracy – wyłącz rozpraszacze, ciemny motyw, niska głośność.",
                actions=[
                    {"type": "set_volume", "level": 30},
                    {"type": "set_theme", "dark": True},
                ],
            ),
            Profile(
                name="Nauka",
                icon="📚",
                color="#10b981",
                description="Tryb nauki – skupienie, cisza, jasny motyw.",
                actions=[
                    {"type": "set_volume", "level": 20},
                    {"type": "set_theme", "dark": False},
                ],
            ),
            Profile(
                name="Rozrywka",
                icon="🎬",
                color="#f59e0b",
                description="Czas na relaks – głośna muzyka, ciemny motyw.",
                actions=[
                    {"type": "set_volume", "level": 80},
                    {"type": "set_theme", "dark": True},
                ],
            ),
        ]
        logger.info("Utworzono domyślne profile")
