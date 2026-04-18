"""
ProfileCard – wiersz profilu na liście z rozwijalnymi szczegółami.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)


def _hex_to_rgba(hex_color: str, alpha: int) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return hex_color


def _build_details_text(actions: list[dict], blocked_sites: list[str] = None) -> list[str]:
    lines = []
    blocked = []
    for a in actions:
        t = a.get("type", "")
        if t == "set_theme":
            lines.append("MOTYW  ciemny" if a.get("dark", True) else "MOTYW  jasny")
        elif t == "set_wallpaper":
            import os
            name = os.path.basename(a.get("image_path", "") or "")
            if name:
                lines.append(f"TAPETA  {name}")
        elif t == "block_process":
            blocked.append(a.get("display_name") or a.get("process_name", "?"))
        elif t == "launch_app":
            label = a.get("label") or a.get("path", "?")
            lines.append(f"LAUNCH  {label}")
    if blocked:
        preview = ", ".join(blocked[:3])
        if len(blocked) > 3:
            preview += f"  (+{len(blocked) - 3})"
        lines.append(f"BLOKUJE  {preview}")
    if blocked_sites:
        preview = ", ".join(blocked_sites[:3])
        if len(blocked_sites) > 3:
            preview += f"  (+{len(blocked_sites) - 3})"
        lines.append(f"STRONY  {preview}")
    return lines or ["-- brak skonfigurowanych akcji --"]


class ProfileCard(QFrame):
    switchClicked = Signal(str)
    editClicked = Signal(str)
    deleteClicked = Signal(str)

    _COLLAPSED_H = 82

    def __init__(
        self,
        name: str,
        icon: str = "SYS",
        color: str = "#7c3aed",
        description: str = "",
        actions_count: int = 0,
        actions: list[dict] = None,
        blocked_sites: list[str] = None,
        is_active: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.profile_name = name
        self.profile_color = color
        self._is_active = is_active
        self._expanded = False

        self.setObjectName("activeCardFrame" if is_active else "cardFrame")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self._COLLAPSED_H)

        self._setup_ui(name, icon, color, description, actions_count,
                       actions or [], blocked_sites or [], is_active)

    def _setup_ui(self, name, icon, color, description, actions_count,
                  actions, blocked_sites, is_active):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Górny wiersz (zawsze widoczny) ──────────────────────
        top = QFrame()
        top.setFixedHeight(self._COLLAPSED_H)
        top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top.setStyleSheet("background: transparent; border: none;")

        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(14, 8, 14, 8)
        top_layout.setSpacing(12)

        # Ikona
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("JetBrains Mono, Consolas, Courier New", 9))
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            f"background: {_hex_to_rgba(color, 20)};"
            f"color: {color};"
            f"border: 1px solid {_hex_to_rgba(color, 80)};"
            f"font-family: 'JetBrains Mono', 'Consolas', monospace;"
            f"font-size: 9px; font-weight: bold; letter-spacing: 1px;"
        )
        top_layout.addWidget(icon_label)

        # Info (nazwa + stan)
        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name.upper())
        name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(
            f"color: {color}; background: transparent; letter-spacing: 1px;"
        )
        info.addWidget(name_label)

        if is_active:
            sub = QLabel(">> AKTYWNY")
            sub.setStyleSheet(
                "color: #00C853; font-size: 10px; font-weight: bold;"
                " background: transparent; letter-spacing: 2px;"
                " font-family: 'JetBrains Mono', 'Consolas', monospace;"
            )
        elif description:
            sub = QLabel(description)
            sub.setStyleSheet(
                "color: #666666; font-size: 11px; background: transparent;"
            )
        else:
            sub = QLabel(f"{actions_count} akcji skonfigurowanych")
            sub.setStyleSheet(
                "color: #444444; font-size: 10px; background: transparent;"
                " letter-spacing: 1px; font-family: 'JetBrains Mono', 'Consolas', monospace;"
            )
        info.addWidget(sub)

        top_layout.addLayout(info, 1)

        # Przyciski akcji (prawa kolumna)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.setContentsMargins(0, 0, 0, 0)

        if is_active:
            act_btn = self._make_btn("STOP", "#FF1744")
        else:
            act_btn = self._make_btn("RUN", color)
        act_btn.clicked.connect(lambda: self.switchClicked.emit(self.profile_name))
        btn_row.addWidget(act_btn)

        edit_btn = self._make_btn("EDIT", "#555555")
        edit_btn.clicked.connect(lambda: self.editClicked.emit(self.profile_name))
        btn_row.addWidget(edit_btn)

        del_btn = self._make_btn("DEL", "#FF1744")
        del_btn.clicked.connect(lambda: self.deleteClicked.emit(self.profile_name))
        btn_row.addWidget(del_btn)

        self._expand_btn = self._make_btn("[+]", "#444444")
        self._expand_btn.clicked.connect(self._toggle_expand)
        btn_row.addWidget(self._expand_btn)

        top_layout.addLayout(btn_row)

        root.addWidget(top)

        # ── Sekcja szczegółów (ukryta domyślnie) ─────────────────
        self._details = QFrame()
        self._details.setVisible(False)
        self._details.setStyleSheet(
            f"background: {_hex_to_rgba(color, 6)};"
            f"border-top: 1px solid {_hex_to_rgba(color, 40)};"
        )

        det_layout = QVBoxLayout(self._details)
        det_layout.setContentsMargins(62, 8, 14, 10)
        det_layout.setSpacing(2)

        detail_lines = _build_details_text(actions, blocked_sites)
        for line in detail_lines:
            lbl = QLabel(line)
            lbl.setStyleSheet(
                "color: #555555; font-size: 10px; background: transparent; border: none;"
                " font-family: 'JetBrains Mono', 'Consolas', monospace; letter-spacing: 1px;"
            )
            det_layout.addWidget(lbl)

        # Wysokość szczegółów: 10 (padding) + n*16px + 10
        self._details_h = 20 + len(detail_lines) * 17
        self._details.setFixedHeight(self._details_h)

        root.addWidget(self._details)

    def _toggle_expand(self):
        self._expanded = not self._expanded
        self._details.setVisible(self._expanded)
        self._expand_btn.setText("[-]" if self._expanded else "[+]")
        new_h = self._COLLAPSED_H + (self._details_h if self._expanded else 0)
        self.setFixedHeight(new_h)
        # Poinformuj layout rodzica o zmianie rozmiaru
        if self.parent():
            self.parent().updateGeometry()
            if hasattr(self.parent(), "adjustSize"):
                self.parent().adjustSize()

    def _make_btn(self, label: str, color: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setMinimumHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        f = QFont("JetBrains Mono, Consolas, Courier New", 9)
        f.setBold(True)
        btn.setFont(f)
        hover_bg = _hex_to_rgba(color, 20)
        pressed_bg = _hex_to_rgba(color, 50)
        border_dim = _hex_to_rgba(color, 80)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {border_dim};
                border-radius: 0px;
                color: {color};
                padding: 4px 10px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                border-color: {color};
            }}
            QPushButton:pressed {{
                background: {pressed_bg};
            }}
        """)
        return btn

