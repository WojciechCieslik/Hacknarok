"""
Scheduler – harmonogram automatycznego przełączania profili.

Każdy blok działa raz: aktywacja gdy czas wchodzi w przedział,
dezaktywacja gdy czas z niego wychodzi. Jeśli użytkownik przerwie
profil ręcznie w trakcie bloku, blok nie uruchomi się ponownie
(aż do następnego bloku).
"""

import json
import os
import logging
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule.json")

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_NAMES_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class ScheduleBlock:
    """Blok czasowy w harmonogramie tygodniowym."""

    def __init__(self, day: int, start_hour: int, start_min: int,
                 end_hour: int, end_min: int, profile_name: str,
                 enabled: bool = True, source: str = "local"):
        self.day = day
        self.start_hour = start_hour
        self.start_min = start_min
        self.end_hour = end_hour
        self.end_min = end_min
        self.profile_name = profile_name
        self.enabled = enabled
        self.source = source   # "local" lub "server"

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "start_hour": self.start_hour,
            "start_min": self.start_min,
            "end_hour": self.end_hour,
            "end_min": self.end_min,
            "profile_name": self.profile_name,
            "enabled": self.enabled,
            "source": self.source,
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
            source=data.get("source", "local"),
        )

    def start_minutes(self) -> int:
        return self.start_hour * 60 + self.start_min

    def end_minutes(self) -> int:
        return self.end_hour * 60 + self.end_min

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

    def _key(self) -> str:
        return f"{self.day}-{self.start_hour}-{self.start_min}-{self.end_hour}-{self.end_min}-{self.profile_name}"


class Scheduler(QObject):
    # Emitowany raz, gdy blok się rozpoczyna (aktywuj profil)
    scheduleTriggered = Signal(str)
    # Emitowany raz, gdy blok się kończy (dezaktywuj profil)
    scheduleEnded = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocks: list[ScheduleBlock] = []
        self._timer = QTimer(self)
        self._timer.setInterval(20_000)
        self._timer.timeout.connect(self._check)
        # Klucz bloku, którego workflow jest obecnie aktywny (lub "" gdy brak)
        self._active_block_key: str = ""
        # Klucze bloków które użytkownik przerwał ręcznie – nie aktywuj ponownie
        self._skipped_block_keys: set[str] = set()
        self.load()

    def start(self):
        self._timer.start()
        # Pierwsze sprawdzenie od razu
        self._check()
        logger.info("Harmonogram uruchomiony")

    def stop(self):
        self._timer.stop()

    def active_block_is_server(self) -> bool:
        """Zwraca True jeśli aktualnie aktywny blok pochodzi z serwera."""
        current = self._find_current_block()
        return current is not None and getattr(current, "source", "local") == "server"

    def notify_manual_deactivation(self):
        """
        Wywołaj gdy użytkownik ręcznie przerywa profil.
        Aktualnie aktywny blok nie zostanie ponownie uruchomiony –
        chyba że pochodzi z serwera: wtedy jest ignorowany (serwer wymusza).
        """
        if self._active_block_key:
            current = self._find_current_block()
            if current and getattr(current, "source", "local") == "server":
                logger.info(
                    f"Harmonogram: blok serwerowy '{self._active_block_key}' "
                    f"nie może być pominięty"
                )
                return
            self._skipped_block_keys.add(self._active_block_key)
            logger.info(f"Harmonogram: blok '{self._active_block_key}' pominięty do końca okresu")
            self._active_block_key = ""

    def _find_current_block(self) -> ScheduleBlock | None:
        now = datetime.now()
        day, h, m = now.weekday(), now.hour, now.minute
        # Server forsuje swój profil – ma pierwszeństwo nad lokalnym blokiem.
        match = None
        for b in self.blocks:
            if b.enabled and b.contains(day, h, m):
                if b.source == "server":
                    return b
                match = match or b
        return match

    def server_overlap(self, day: int, start_min: int, end_min: int) -> bool:
        """True jeśli jakikolwiek blok z serwera nachodzi na podany przedział."""
        for b in self.blocks:
            if b.source != "server" or b.day != day:
                continue
            if b.start_minutes() < end_min and b.end_minutes() > start_min:
                return True
        return False

    def _check(self):
        current = self._find_current_block()
        current_key = current._key() if current else ""

        # Przejście: poprzedni blok -> koniec
        if self._active_block_key and self._active_block_key != current_key:
            logger.info(f"Harmonogram: zakończono blok '{self._active_block_key}'")
            self._active_block_key = ""
            self.scheduleEnded.emit("")

        if not current:
            # Brak aktywnego bloku teraz – wyczyść pominięcia bloków, które już się skończyły
            # (zapis kluczy, które obejmują inne przedziały, zostanie zresetowany gdy znów
            #  znajdziemy się poza jakimkolwiek blokiem)
            self._skipped_block_keys.clear()
            return

        # Użytkownik pominął ten blok? Nie uruchamiaj go ponownie.
        if current_key in self._skipped_block_keys:
            return

        # Rozpoczynamy nowy blok
        if current_key != self._active_block_key:
            self._active_block_key = current_key
            logger.info(
                f"Harmonogram: aktywuj '{current.profile_name}' "
                f"({current.start_str()}–{current.end_str()})"
            )
            self.scheduleTriggered.emit(current.profile_name)

    # ─── CRUD ────────────────────────────────────────────────────

    def add_block(self, block: ScheduleBlock) -> bool:
        if block.source == "local" and self.server_overlap(
            block.day, block.start_minutes(), block.end_minutes()
        ):
            logger.warning(
                f"Lokalny blok {block.day} {block.start_str()}-{block.end_str()} "
                f"nakłada się na blok serwerowy – odrzucono"
            )
            return False
        self.blocks.append(block)
        self.save()
        return True

    def remove_block(self, index: int) -> bool:
        if 0 <= index < len(self.blocks):
            if self.blocks[index].source == "server":
                logger.warning("Próba usunięcia bloku serwerowego – zablokowana")
                return False
            self.blocks.pop(index)
            self.save()
            return True
        return False

    def clear_blocks_for_profile(self, profile_name: str):
        # Nie usuwaj bloków serwerowych.
        self.blocks = [
            b for b in self.blocks
            if b.profile_name != profile_name or b.source == "server"
        ]
        self.save()

    def rename_profile_in_blocks(self, old_name: str, new_name: str):
        for b in self.blocks:
            if b.profile_name == old_name and b.source == "local":
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
