"""
Scheduler – harmonogram automatycznego przełączania profili.

Sprawdza co 30 sekund, czy nadeszła zaplanowana pora przełączenia profilu.
"""

import json
import os
import logging
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule.json")

# Nazwy dni tygodnia po polsku
DAY_NAMES = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]
DAY_NAMES_FULL = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]


class ScheduleEntry:
    """Pojedynczy wpis harmonogramu."""

    def __init__(self, profile_name: str, hour: int, minute: int, days: list[int] = None,
                 enabled: bool = True):
        """
        Args:
            profile_name: nazwa profilu do aktywacji
            hour: godzina (0-23)
            minute: minuta (0-59)
            days: lista dni tygodnia (0=Pon, 6=Ndz), None = codziennie
            enabled: czy wpis jest włączony
        """
        self.profile_name = profile_name
        self.hour = hour
        self.minute = minute
        self.days = days if days is not None else list(range(7))
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            "profile_name": self.profile_name,
            "hour": self.hour,
            "minute": self.minute,
            "days": self.days,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleEntry":
        return cls(
            profile_name=data["profile_name"],
            hour=data["hour"],
            minute=data["minute"],
            days=data.get("days", list(range(7))),
            enabled=data.get("enabled", True),
        )

    def matches_now(self) -> bool:
        """Sprawdź, czy wpis pasuje do bieżącej godziny i dnia."""
        if not self.enabled:
            return False
        now = datetime.now()
        # day_of_week: 0=Pon, 6=Ndz
        return (
            now.weekday() in self.days
            and now.hour == self.hour
            and now.minute == self.minute
        )

    def get_time_str(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def get_days_str(self) -> str:
        if len(self.days) == 7:
            return "Codziennie"
        if self.days == list(range(5)):
            return "Pon–Pt"
        if self.days == [5, 6]:
            return "Weekend"
        return ", ".join(DAY_NAMES[d] for d in sorted(self.days))


class Scheduler(QObject):
    """Harmonogram automatycznego przełączania profili."""

    scheduleTriggered = Signal(str)  # nazwa profilu do przełączenia

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: list[ScheduleEntry] = []
        self._timer = QTimer(self)
        self._timer.setInterval(30_000)  # co 30 sekund
        self._timer.timeout.connect(self._check)
        self._last_triggered: Optional[str] = None  # zapobiega re-triggering
        self._last_triggered_minute: int = -1
        self.load()

    def start(self):
        """Uruchom harmonogram."""
        self._timer.start()
        logger.info("Harmonogram uruchomiony")

    def stop(self):
        """Zatrzymaj harmonogram."""
        self._timer.stop()
        logger.info("Harmonogram zatrzymany")

    def _check(self):
        """Sprawdź, czy jakaś reguła harmonogramu pasuje do aktualnego czasu."""
        now = datetime.now()
        current_minute_key = f"{now.weekday()}-{now.hour}-{now.minute}"

        # Zapobiegnij wielokrotnemu uruchomieniu w tej samej minucie
        if current_minute_key == self._last_triggered:
            return

        for entry in self.entries:
            if entry.matches_now():
                self._last_triggered = current_minute_key
                logger.info(
                    f"Harmonogram: pora na profil '{entry.profile_name}' "
                    f"({entry.get_time_str()})"
                )
                self.scheduleTriggered.emit(entry.profile_name)
                return

    # ─── CRUD ────────────────────────────────────────────────────

    def add_entry(self, entry: ScheduleEntry):
        self.entries.append(entry)
        self.save()

    def remove_entry(self, index: int):
        if 0 <= index < len(self.entries):
            self.entries.pop(index)
            self.save()

    def update_entry(self, index: int, entry: ScheduleEntry):
        if 0 <= index < len(self.entries):
            self.entries[index] = entry
            self.save()

    # ─── Zapis / Odczyt ─────────────────────────────────────────

    def load(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(SCHEDULE_FILE):
            try:
                with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.entries = [ScheduleEntry.from_dict(e) for e in data.get("entries", [])]
                logger.info(f"Wczytano {len(self.entries)} wpisów harmonogramu")
            except Exception as e:
                logger.error(f"Błąd wczytywania harmonogramu: {e}")
                self.entries = []
        else:
            self._create_defaults()
            self.save()

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            data = {"entries": [e.to_dict() for e in self.entries]}
            with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Błąd zapisu harmonogramu: {e}")

    def _create_defaults(self):
        """Utwórz domyślne wpisy harmonogramu."""
        self.entries = [
            ScheduleEntry("Praca", 9, 0, list(range(5))),      # Pon-Pt 9:00
            ScheduleEntry("Rozrywka", 17, 0, list(range(5))),  # Pon-Pt 17:00
        ]
