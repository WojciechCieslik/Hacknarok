"""
Actions – klasy akcji profilu.

Każda akcja implementuje execute() i undo(), oraz serializację do/z JSON.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from core.system_controller import SystemController

logger = logging.getLogger(__name__)


class Action(ABC):
    """Bazowa klasa abstrakcyjna dla akcji profilu."""

    action_type: str = "base"

    @abstractmethod
    def execute(self) -> bool:
        """Wykonaj akcję. Zwraca True jeśli sukces."""
        pass

    @abstractmethod
    def undo(self) -> bool:
        """Cofnij akcję (przywróć poprzedni stan). Zwraca True jeśli sukces."""
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Serializuj akcję do słownika."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "Action":
        """Deserializuj akcję ze słownika."""
        pass

    def get_description(self) -> str:
        """Opis akcji do wyświetlenia w GUI."""
        return f"[{self.action_type}]"


class LaunchAppAction(Action):
    """Uruchom aplikację."""

    action_type = "launch_app"

    def __init__(self, path: str, args: list[str] = None, label: str = ""):
        self.path = path
        self.args = args or []
        self.label = label or path

    def execute(self) -> bool:
        return SystemController.launch_app(self.path, self.args)

    def undo(self) -> bool:
        import os
        proc_name = os.path.basename(self.path)
        return SystemController.close_process(proc_name) > 0

    def to_dict(self) -> dict:
        return {
            "type": self.action_type,
            "path": self.path,
            "args": self.args,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LaunchAppAction":
        return cls(
            path=data["path"],
            args=data.get("args", []),
            label=data.get("label", ""),
        )

    def get_description(self) -> str:
        return f"🚀 Uruchom: {self.label or self.path}"


class SetWallpaperAction(Action):
    """Zmień tapetę pulpitu."""

    action_type = "set_wallpaper"

    def __init__(self, image_path: str):
        self.image_path = image_path
        self._previous_wallpaper: Optional[str] = None

    def execute(self) -> bool:
        self._previous_wallpaper = SystemController.get_wallpaper()
        return SystemController.set_wallpaper(self.image_path)

    def undo(self) -> bool:
        if self._previous_wallpaper:
            return SystemController.set_wallpaper(self._previous_wallpaper)
        return True

    def to_dict(self) -> dict:
        return {
            "type": self.action_type,
            "image_path": self.image_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SetWallpaperAction":
        return cls(image_path=data["image_path"])

    def get_description(self) -> str:
        import os
        name = os.path.basename(self.image_path)
        return f"🖼️ Tapeta: {name}"


class SetThemeAction(Action):
    """Ustaw motyw ciemny/jasny."""

    action_type = "set_theme"

    def __init__(self, dark: bool):
        self.dark = dark
        self._previous_dark: Optional[bool] = None

    def execute(self) -> bool:
        self._previous_dark = SystemController.get_theme()
        return SystemController.set_theme(self.dark)

    def undo(self) -> bool:
        if self._previous_dark is not None:
            return SystemController.set_theme(self._previous_dark)
        return True

    def to_dict(self) -> dict:
        return {
            "type": self.action_type,
            "dark": self.dark,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SetThemeAction":
        return cls(dark=data["dark"])

    def get_description(self) -> str:
        mode = "ciemny" if self.dark else "jasny"
        return f"🌙 Motyw: {mode}"


class BlockProcessAction(Action):
    """Blokuj proces – zamyka go normalnie przy aktywacji i przy każdej próbie uruchomienia."""

    action_type = "block_process"

    def __init__(self, process_name: str, display_name: str = ""):
        self.process_name = process_name
        self.display_name = display_name or process_name

    def execute(self) -> bool:
        """Zamknij proces jeśli działa – blokada aktywna od teraz."""
        closed = SystemController.close_process(self.process_name)
        if closed:
            logger.info(f"Zablokowano i zamknięto: {self.process_name}")
        else:
            logger.info(f"Blokada aktywna dla: {self.process_name} (proces nie był uruchomiony)")
        return True

    def undo(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "type": self.action_type,
            "process_name": self.process_name,
            "display_name": self.display_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BlockProcessAction":
        return cls(
            process_name=data["process_name"],
            display_name=data.get("display_name", ""),
        )

    def get_description(self) -> str:
        label = self.display_name if self.display_name != self.process_name else self.process_name
        return f"🚫 Blokuj: {label}"


# ─── Rejestr akcji (factory) ────────────────────────────────────

ACTION_REGISTRY: dict[str, type[Action]] = {
    "launch_app": LaunchAppAction,
    "set_wallpaper": SetWallpaperAction,
    "set_theme": SetThemeAction,
    "block_process": BlockProcessAction,
}


def action_from_dict(data: dict) -> Action:
    """Utwórz akcję z dict na podstawie pola 'type'."""
    action_type = data.get("type", "")
    cls = ACTION_REGISTRY.get(action_type)
    if cls is None:
        # Ignoruj nieznane akcje (np. deprecated set_power_plan, kill_process)
        raise ValueError(f"Nieznany typ akcji: {action_type}")
    return cls.from_dict(data)
