"""
Scheduler – harmonogram automatycznego przełączania profili.

Bloki czasowe (ScheduleBlock) zastąpiły trigger-based ScheduleEntry.
"""

import json
import os
import logging
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule.json")

DAY_NAMES = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]
DAY_NAMES_FULL = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]


class ScheduleBlock:
    """Blok czasowy w harmonogramie tygodniowym."""

    def __init__(self, day: int, start_hour: int, start_min: int,
                 end_hour: int, end_min: int, profile_name: str,
                 enabled: bool = True):
        self.day = day
        self.start_hour = start_hour
        self.start_min = start_min
        self.end_hour = end_hour
        self.end_min = end_min
        self.profile_name = profile_name
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "start_hour": self.start_hour,
            "start_min": self.start_min,
            "end_hour": self.end_hour,
            "end_min": self.end_min,
            "profile_name": self.profile_name,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleBlock":
        return cls(
            day=data["day"],
            start_hour=data["start_hour"],
            start_min=data.get("start_min", 0),
            end_hour=data["end_hour"],
            end_min=data.get("end_min", 0),
            profile_name=data["profile_name"],
            enabled=data.get("enabled", True),
        )

    def contains(self, weekday: int, hour: int, minute: int) -> bool:
        if weekday != self.day:
            return False
        start_m = self.start_hour * 60 + self.start_min
        end_m = self.end_hour * 60 + self.end_min
        return start_m <= hour * 60 + minute < end_m

    def start_str(self) -> str:
        return f"{self.start_hour:02d}:{self.start_min:02d}"

    def end_str(self) -> str:
        return f"{self.end_hour:02d}:{self.end_min:02d}"


class Scheduler(QObject):
    scheduleTriggered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocks: list[ScheduleBlock] = []
        self._timer = QTimer(self)
        self._timer.setInterval(30_000)
        self._timer.timeout.connect(self._check)
        self._last_triggered: str = ""
        self.load()

    def start(self):
        self._timer.start()
        logger.info("Harmonogram uruchomiony")

    def stop(self):
        self._timer.stop()

    def _check(self):
        now = datetime.now()
        day, h, m = now.weekday(), now.hour, now.minute

        for block in self.blocks:
            if block.enabled and block.contains(day, h, m):
                key = f"{block.day}-{block.start_hour}-{block.start_min}"
                if key != self._last_triggered:
                    self._last_triggered = key
                    logger.info(
                        f"Harmonogram: aktywuj '{block.profile_name}' "
                        f"({block.start_str()}–{block.end_str()})"
                    )
                    self.scheduleTriggered.emit(block.profile_name)
                return

        # Żaden blok nie jest aktywny – wyzeruj klucz aby re-trigger był możliwy
        if self._last_triggered:
            self._last_triggered = ""

    # ─── CRUD ────────────────────────────────────────────────────

    def add_block(self, block: ScheduleBlock):
        self.blocks.append(block)
        self.save()

    def remove_block(self, index: int):
        if 0 <= index < len(self.blocks):
            self.blocks.pop(index)
            self.save()

    def clear_blocks_for_profile(self, profile_name: str):
        self.blocks = [b for b in self.blocks if b.profile_name != profile_name]
        self.save()

    def rename_profile_in_blocks(self, old_name: str, new_name: str):
        for b in self.blocks:
            if b.profile_name == old_name:
                b.profile_name = new_name
        self.save()

    # ─── Zapis / Odczyt ─────────────────────────────────────────

    def load(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(SCHEDULE_FILE):
            self.blocks = []
            self.save()
            return
        try:
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "blocks" in data:
                self.blocks = [ScheduleBlock.from_dict(b) for b in data["blocks"]]
            elif "entries" in data:
                # Migracja starego formatu trigger → blok godzinny
                self.blocks = []
                for e in data["entries"]:
                    h = e.get("hour", 9)
                    days = e.get("days", list(range(7)))
                    for d in days:
                        self.blocks.append(ScheduleBlock(
                            day=d,
                            start_hour=h, start_min=0,
                            end_hour=(h + 1) % 24, end_min=0,
                            profile_name=e["profile_name"],
                            enabled=e.get("enabled", True),
                        ))
                self.save()
                logger.info("Migracja harmonogramu: entries → blocks")
            else:
                self.blocks = []

            logger.info(f"Wczytano {len(self.blocks)} bloków harmonogramu")
        except Exception as e:
            logger.error(f"Błąd wczytywania harmonogramu: {e}")
            self.blocks = []

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
                json.dump({"blocks": [b.to_dict() for b in self.blocks]}, f,
                          indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Błąd zapisu harmonogramu: {e}")
