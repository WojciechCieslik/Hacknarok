"""
ProfileManager – zarządzanie profilami.

CRUD profili, zapis/odczyt JSON, przełączanie z zachowaniem poprzedniego stanu.
"""

import json
import os
import copy
import logging
from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.actions import Action, action_from_dict, BlockProcessAction
from core.system_controller import SystemController

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")


@dataclass
class Profile:
    """Profil środowiska."""
    name: str
    icon: str = "🖥️"
    color: str = "#7c3aed"
    description: str = ""
    actions: list[dict] = field(default_factory=list)

    def get_actions(self) -> list[Action]:
        """Zwróć zdeserializowane obiekty akcji."""
        result = []
        for a_dict in self.actions:
            try:
                result.append(action_from_dict(a_dict))
            except Exception as e:
                logger.error(f"Błąd deserializacji akcji: {e}")
        return result

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "icon": self.icon,
            "color": self.color,
            "description": self.description,
            "actions": self.actions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            name=data.get("name", "Bez nazwy"),
            icon=data.get("icon", "🖥️"),
            color=data.get("color", "#7c3aed"),
            description=data.get("description", ""),
            actions=data.get("actions", []),
        )


class ProfileManager(QObject):
    """Menedżer profili – ładowanie, zapis, przełączanie."""

    profileChanged = Signal(str)  # nazwa aktywnego profilu
    profilesUpdated = Signal()    # lista profili się zmieniła

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profiles: list[Profile] = []
        self.active_profile: Optional[Profile] = None
        self._previous_state: dict = {}
        self._blocked_processes: list[str] = []
        self.load()

    # ─── Zapis / Odczyt ─────────────────────────────────────────

    def load(self):
        """Wczytaj profile z pliku JSON."""
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.profiles = [Profile.from_dict(p) for p in data.get("profiles", [])]
                logger.info(f"Wczytano {len(self.profiles)} profil(i)")
            except Exception as e:
                logger.error(f"Błąd wczytywania profili: {e}")
                self.profiles = []
        else:
            self._create_defaults()
            self.save()

    def save(self):
        """Zapisz profile do pliku JSON."""
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            data = {
                "profiles": [p.to_dict() for p in self.profiles],
                "active": self.active_profile.name if self.active_profile else None,
            }
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Profile zapisane")
        except Exception as e:
            logger.error(f"Błąd zapisu profili: {e}")

    # ─── CRUD ────────────────────────────────────────────────────

    def add_profile(self, profile: Profile):
        """Dodaj nowy profil."""
        self.profiles.append(profile)
        self.save()
        self.profilesUpdated.emit()

    def update_profile(self, name: str, updated: Profile):
        """Aktualizuj istniejący profil."""
        for i, p in enumerate(self.profiles):
            if p.name == name:
                self.profiles[i] = updated
                self.save()
                self.profilesUpdated.emit()
                return True
        return False

    def delete_profile(self, name: str):
        """Usuń profil."""
        self.profiles = [p for p in self.profiles if p.name != name]
        if self.active_profile and self.active_profile.name == name:
            self.deactivate_profile()
        self.save()
        self.profilesUpdated.emit()

    def duplicate_profile(self, name: str) -> Optional[Profile]:
        """Duplikuj profil."""
        for p in self.profiles:
            if p.name == name:
                new_name = f"{p.name} (kopia)"
                counter = 2
                existing_names = {pp.name for pp in self.profiles}
                while new_name in existing_names:
                    new_name = f"{p.name} (kopia {counter})"
                    counter += 1
                new_profile = Profile(
                    name=new_name,
                    icon=p.icon,
                    color=p.color,
                    description=p.description,
                    actions=copy.deepcopy(p.actions),
                )
                self.add_profile(new_profile)
                return new_profile
        return None

    def get_profile(self, name: str) -> Optional[Profile]:
        """Pobierz profil po nazwie."""
        for p in self.profiles:
            if p.name == name:
                return p
        return None

    # ─── Przełączanie ────────────────────────────────────────────

    def _capture_state(self) -> dict:
        """Zrób snapshot aktualnego stanu systemu."""
        return {
            "volume": SystemController.get_volume(),
            "wallpaper": SystemController.get_wallpaper(),
            "dark_theme": SystemController.get_theme(),
            "power_plan_guid": SystemController.get_active_power_plan(),
        }

    def switch_profile(self, profile_name: str) -> bool:
        """Przełącz na wybrany profil."""
        profile = self.get_profile(profile_name)
        if not profile:
            logger.error(f"Profil '{profile_name}' nie znaleziony")
            return False

        # Dezaktywuj bieżący profil (blokady)
        if self.active_profile:
            self._stop_blocking()

        # Snapshot przed zmianą
        self._previous_state = self._capture_state()

        # Wykonaj akcje profilu
        actions = profile.get_actions()
        for action in actions:
            try:
                action.execute()
                # Zbierz procesy do blokowania
                if isinstance(action, BlockProcessAction):
                    self._blocked_processes.append(action.process_name)
            except Exception as e:
                logger.error(f"Błąd wykonywania akcji {action.get_description()}: {e}")

        self.active_profile = profile
        self.save()
        self.profileChanged.emit(profile.name)
        logger.info(f"Przełączono na profil: {profile.name}")
        return True

    def deactivate_profile(self):
        """Dezaktywuj bieżący profil i przywróć poprzedni stan."""
        if not self.active_profile:
            return

        self._stop_blocking()

        # Przywróć poprzedni stan
        state = self._previous_state
        if state:
            if "volume" in state:
                SystemController.set_volume(state["volume"])
            if "wallpaper" in state and state["wallpaper"]:
                SystemController.set_wallpaper(state["wallpaper"])
            if "dark_theme" in state:
                SystemController.set_theme(state["dark_theme"])
            if "power_plan_guid" in state and state["power_plan_guid"]:
                SystemController.set_power_plan(state["power_plan_guid"])

        self.active_profile = None
        self._previous_state = {}
        self.save()
        self.profileChanged.emit("")
        logger.info("Profil dezaktywowany – stan przywrócony")

    def _stop_blocking(self):
        """Wyłącz blokowanie procesów."""
        self._blocked_processes.clear()

    def get_blocked_processes(self) -> list[str]:
        """Pobierz listę aktywnie blokowanych procesów."""
        return list(self._blocked_processes)

    def enforce_blocks(self):
        """Wymuś blokady – zabij zablokowane procesy (wywoływane przez timer)."""
        for proc_name in self._blocked_processes:
            SystemController.kill_process(proc_name)

    # ─── Profile domyślne ────────────────────────────────────────

    def _create_defaults(self):
        """Utwórz domyślne profile."""
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
