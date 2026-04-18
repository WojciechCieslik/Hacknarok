"""
OverloadMonitor – Monitor Przebodźcowania.

Monitoruje aktywne okno co 2 sekundy, analizuje treść
i oblicza wskaźnik przebodźcowania (0-10).
"""

import json
import os
import logging
from collections import deque
from typing import Optional, Protocol

from PySide6.QtCore import QObject, QTimer, Signal

from core.system_controller import SystemController

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OVERRIDES_FILE = os.path.join(DATA_DIR, "overrides.json")


# ─── Interfejs analizatora AI ────────────────────────────────────

class AIAnalyzer(Protocol):
    """Interfejs analizatora przebodźcowania."""

    def analyze(self, window_title: str, process_name: str) -> int:
        """Analizuj aktywne okno i zwróć score 0-10."""
        ...


# ─── Implementacja regułowa ─────────────────────────────────────

class RuleBasedAnalyzer:
    """
    Analizator regułowy – ocenia przebodźcowanie na podstawie
    słów kluczowych w tytule okna i nazwie procesu.
    """

    # Procesy/słowa kluczowe → score (0-10)
    PROCESS_SCORES: dict[str, int] = {
        # Wysoka stymulacja (7-10)
        "tiktok": 9,
        "instagram": 8,
        "twitter": 8,
        "facebook": 8,
        "reddit": 7,
        "youtube": 7,
        "twitch": 8,
        "discord": 6,
        "telegram": 5,
        "whatsapp": 5,
        "messenger": 5,
        # Średnia stymulacja (4-6)
        "chrome": 5,
        "firefox": 5,
        "msedge": 5,
        "edge": 5,
        "brave": 5,
        "opera": 5,
        "slack": 5,
        "teams": 5,
        "outlook": 4,
        "thunderbird": 4,
        # Niska stymulacja (1-3)
        "code": 2,
        "devenv": 2,
        "pycharm": 2,
        "idea": 2,
        "rider": 2,
        "webstorm": 2,
        "notepad": 1,
        "notepad++": 1,
        "winword": 2,
        "excel": 2,
        "powerpnt": 2,
        "calc": 1,
        "explorer": 1,
        "terminal": 2,
        "windowsterminal": 2,
        "powershell": 2,
        "cmd": 2,
        "matlab": 2,
        "blender": 3,
        "gimp": 3,
        "photoshop": 3,
    }

    # Słowa kluczowe w tytule okna → modyfikator score
    TITLE_KEYWORDS: dict[str, int] = {
        # Wysoka stymulacja
        "tiktok": 9,
        "instagram": 8,
        "twitter": 8,
        "x.com": 8,
        "facebook": 8,
        "reddit": 7,
        "youtube": 7,
        "twitch": 8,
        "news": 6,
        "wiadomości": 6,
        "onet": 6,
        "wp.pl": 6,
        "pudelek": 9,
        "plotek": 9,
        "gry": 6,
        "game": 6,
        "steam": 6,
        # Średnia
        "gmail": 4,
        "email": 4,
        "chat": 5,
        "slack": 5,
        "teams": 5,
        "spotkanie": 4,
        "meeting": 4,
        # Niska
        "visual studio": 2,
        "pycharm": 2,
        "dokumentacja": 2,
        "docs": 3,
        "stack overflow": 3,
        "stackoverflow": 3,
        "github": 3,
        "gitlab": 3,
        "wikipedia": 3,
        "kurs": 2,
        "tutorial": 3,
        "learn": 2,
        "nauka": 2,
        "word": 2,
        "excel": 2,
        "powerpoint": 2,
    }

    def analyze(self, window_title: str, process_name: str) -> int:
        """Analizuj przebodźcowanie na podstawie reguł."""
        if not window_title and not process_name:
            return 0

        score = 5  # Domyślna wartość

        # Sprawdź nazwę procesu
        proc_lower = process_name.lower().replace(".exe", "")
        if proc_lower in self.PROCESS_SCORES:
            score = self.PROCESS_SCORES[proc_lower]

        # Sprawdź tytuł okna (modyfikuje wynik)
        title_lower = window_title.lower()
        best_title_score = None
        for keyword, kw_score in self.TITLE_KEYWORDS.items():
            if keyword in title_lower:
                if best_title_score is None or kw_score > best_title_score:
                    best_title_score = kw_score

        if best_title_score is not None:
            # Użyj wyższego z dwóch wyników
            score = max(score, best_title_score)

        return max(0, min(10, score))


# ─── Monitor przebodźcowania ────────────────────────────────────

class OverloadMonitor(QObject):
    """
    Monitor przebodźcowania – polluje aktywne okno co 2 sekundy,
    analizuje treść i emituje sygnał ze score.
    """

    scoreChanged = Signal(int, str, str)  # score, window_title, process_name

    def __init__(self, parent=None, analyzer: Optional[AIAnalyzer] = None):
        super().__init__(parent)
        self.analyzer = analyzer or RuleBasedAnalyzer()
        self.current_score: int = 0
        self.current_title: str = ""
        self.current_process: str = ""
        self.history: deque = deque(maxlen=100)
        self._overrides: dict[str, int] = {}  # process_name -> manual score

        self._timer = QTimer(self)
        self._timer.setInterval(2000)  # co 2 sekundy
        self._timer.timeout.connect(self.update)

        self._load_overrides()

    def start(self):
        """Uruchom monitoring."""
        self._timer.start()
        logger.info("Monitor przebodźcowania uruchomiony")

    def stop(self):
        """Zatrzymaj monitoring."""
        self._timer.stop()
        logger.info("Monitor przebodźcowania zatrzymany")

    def update(self):
        """Pobierz info o aktywnym oknie i oblicz score."""
        try:
            title, process = SystemController.get_active_window_info()
            self.current_title = title
            self.current_process = process

            # Sprawdź ręczne korekty
            proc_key = process.lower()
            if proc_key in self._overrides:
                score = self._overrides[proc_key]
            else:
                score = self.analyzer.analyze(title, process)

            self.current_score = score
            self.history.append({
                "score": score,
                "title": title,
                "process": process,
            })

            self.scoreChanged.emit(score, title, process)
        except Exception as e:
            logger.error(f"Błąd aktualizacji monitora: {e}")

    # ─── Ręczne korekty ─────────────────────────────────────────

    def set_override(self, process_name: str, score: int):
        """Ustaw ręczną korektę dla procesu."""
        self._overrides[process_name.lower()] = max(0, min(10, score))
        self._save_overrides()
        logger.info(f"Ręczna korekta: {process_name} → {score}")

    def remove_override(self, process_name: str):
        """Usuń ręczną korektę."""
        self._overrides.pop(process_name.lower(), None)
        self._save_overrides()

    def get_overrides(self) -> dict[str, int]:
        """Pobierz wszystkie ręczne korekty."""
        return dict(self._overrides)

    def _load_overrides(self):
        """Wczytaj ręczne korekty z pliku."""
        if os.path.exists(OVERRIDES_FILE):
            try:
                with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
                    self._overrides = json.load(f)
            except Exception:
                self._overrides = {}

    def _save_overrides(self):
        """Zapisz ręczne korekty do pliku."""
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(OVERRIDES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._overrides, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Błąd zapisu korekt: {e}")

    # ─── Poziomy ─────────────────────────────────────────────────

    @staticmethod
    def get_level_name(score: int) -> str:
        """Zwróć nazwę poziomu przebodźcowania."""
        if score <= 3:
            return "Niski"
        elif score <= 6:
            return "Średni"
        elif score <= 9:
            return "Wysoki"
        else:
            return "Krytyczny"

    @staticmethod
    def get_level_color(score: int) -> str:
        """Zwróć kolor odpowiadający poziomowi."""
        if score <= 3:
            return "#10b981"  # zielony
        elif score <= 6:
            return "#f59e0b"  # żółty/pomarańczowy
        elif score <= 9:
            return "#ef4444"  # czerwony
        else:
            return "#dc2626"  # ciemnoczerwony

    @staticmethod
    def get_level_emoji(score: int) -> str:
        """Zwróć emoji odpowiadające poziomowi."""
        if score <= 3:
            return "😌"
        elif score <= 6:
            return "😐"
        elif score <= 9:
            return "😰"
        else:
            return "🔥"

    def get_average_score(self, last_n: int = 20) -> float:
        """Oblicz średni score z ostatnich N odczytów."""
        if not self.history:
            return 0.0
        recent = list(self.history)[-last_n:]
        return sum(h["score"] for h in recent) / len(recent)
