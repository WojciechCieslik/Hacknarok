"""
ProfileCard – przemysłowy rząd profilu z techniczną typografią.
"""

import os
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)


_MONO = "JetBrains Mono", "IBM Plex Mono", "Consolas", "monospace"


def _hex_to_rgba(hex_color: str, alpha: int) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return hex_color


def _initials(name: str, icon_field: str = "") -> str:
    """Zwróć 1-3 znakowy kod z pola icon (jeśli tekstowe) lub z nazwy profilu."""
    if icon_field:
        clean = re.sub(r"[^A-Za-z0-9]", "", icon_field)
        if clean:
            return clean[:3].upper()
    parts = re.findall(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9]+", name or "")
    if not parts:
        return "::"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _build_details_text(actions: list[dict], blocked_sites: list[str] = None) -> list[str]:
    """Zwróć listę technicznych linii opisu."""
    lines = []
    blocked = []
    for a in actions:
        t = a.get("type", "")
        if t == "set_theme":
            mode = "DARK" if a.get("dark", True) else "LIGHT"
            lines.append(f"THEME        :   {mode}")
        elif t == "set_wallpaper":
            name = os.path.basename(a.get("image_path", "") or "")
            if name:
                lines.append(f"WALLPAPER    :   {name}")
        elif t == "block_process":
            blocked.append(a.get("display_name") or a.get("process_name", "?"))
        elif t == "launch_app":
            label = a.get("label") or a.get("path", "?")
            lines.append(f"LAUNCH       :   {label}")
    if blocked:
        preview = ", ".join(blocked[:3])
        if len(blocked) > 3:
            preview += f"  +{len(blocked) - 3}"
        lines.append(f"BLOCK  APPS  :   {preview}")
    if blocked_sites:
        preview = ", ".join(blocked_sites[:3])
        if len(blocked_sites) > 3:
            preview += f"  +{len(blocked_sites) - 3}"
        lines.append(f"BLOCK  WEB   :   {preview}")
    return lines or ["NO  ACTIONS  CONFIGURED"]


class ProfileCard(QFrame):
    switchClicked = Signal(str)
    editClicked = Signal(str)
    deleteClicked = Signal(str)

    _COLLAPSED_H = 90

    def __init__(
        self,
        name: str,
        icon: str = "",
        color: str = "#5968ff",
        description: str = "",
        actions_count: int = 0,
        actions: list[dict] = None,
        blocked_sites: list[str] = None,
        is_active: bool = False,
        is_server: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.profile_name = name
        self.profile_color = color
        self._is_active = is_active
        self._is_server = is_server
        self._expanded = False

        self.setObjectName("activeCardFrame" if is_active else "cardFrame")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self._COLLAPSED_H)

        self._setup_ui(name, icon, color, description, actions_count,
                       actions or [], blocked_sites or [], is_active, is_server)

    def _setup_ui(self, name, icon, color, description, actions_count,
                  actions, blocked_sites, is_active, is_server):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top = QFrame()
        top.setFixedHeight(self._COLLAPSED_H)
        top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top.setStyleSheet("background: transparent; border: none;")

        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(16, 10, 14, 10)
        top_layout.setSpacing(16)

        badge = QLabel(_initials(name, icon))
        badge_font = QFont()
        badge_font.setFamilies(list(_MONO))
        badge_font.setPointSize(13)
        badge_font.setBold(True)
        badge.setFont(badge_font)
        badge.setFixedSize(54, 54)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background: {_hex_to_rgba(color, 48)};"
            f"color: {color};"
            f"border: 1px solid {_hex_to_rgba(color, 220)};"
            f"border-left: 3px solid {color};"
            f"letter-spacing: 2px;"
        )
        top_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(4)
        info.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name.upper())
        name_font = QFont()
        name_font.setFamilies(list(_MONO))
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet(
            f"color: {color}; background: transparent; letter-spacing: 3px;"
        )
        info.addWidget(name_label)

        if is_active:
            sub = QLabel("///  ACTIVE  ///  ENFORCING")
            sub.setStyleSheet(
                "color: #3fb98a; font-size: 10px; font-weight: 700;"
                "font-family: 'JetBrains Mono','Consolas',monospace;"
                "letter-spacing: 2.5px; background: transparent;"
            )
        elif is_server:
            sub = QLabel("☁  CLOUD  //  LOCKED  //  SERVER  ENFORCED")
            sub.setStyleSheet(
                "color: #7d8aff; font-size: 10px; font-weight: 700;"
                "font-family: 'JetBrains Mono','Consolas',monospace;"
                "letter-spacing: 2.5px; background: transparent;"
            )
        elif description:
            sub = QLabel(description)
            sub.setStyleSheet(
                "color: #aab3d8; font-size: 11px; background: transparent;"
                "font-family: 'Inter','Segoe UI',sans-serif;"
            )
        else:
            sub = QLabel(f"ACTIONS  :   {actions_count:02d}")
            sub.setStyleSheet(
                "color: #727aa3; font-size: 10px; letter-spacing: 2px;"
                "font-family: 'JetBrains Mono','Consolas',monospace;"
                "background: transparent;"
            )
        info.addWidget(sub)

        top_layout.addLayout(info, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.setContentsMargins(0, 0, 0, 0)

        if is_active:
            act_btn = self._make_btn("DEACTIVATE", "#e5484d")
        else:
            act_btn = self._make_btn("ACTIVATE", color)
        act_btn.clicked.connect(lambda: self.switchClicked.emit(self.profile_name))
        btn_row.addWidget(act_btn)
        if is_server:
            act_btn.setEnabled(False)

        edit_btn = self._make_btn("EDIT", "#aab3d8")
        if is_server:
            edit_btn.setEnabled(False)
            edit_btn.setToolTip("Profil z serwera – edycja zablokowana")
        else:
            edit_btn.clicked.connect(lambda: self.editClicked.emit(self.profile_name))
        btn_row.addWidget(edit_btn)

        del_btn = self._make_btn("REMOVE", "#e5484d")
        if is_server:
            del_btn.setEnabled(False)
            del_btn.setToolTip("Profil z serwera – usuwanie zablokowane")
        else:
            del_btn.clicked.connect(lambda: self.deleteClicked.emit(self.profile_name))
        btn_row.addWidget(del_btn)

        self._expand_btn = self._make_btn("v  SPEC", "#727aa3")
        self._expand_btn.clicked.connect(self._toggle_expand)
        btn_row.addWidget(self._expand_btn)

        top_layout.addLayout(btn_row)

        root.addWidget(top)

        self._details = QFrame()
        self._details.setVisible(False)
        self._details.setStyleSheet(
            f"background: {_hex_to_rgba(color, 18)};"
            f"border-top: 1px solid {_hex_to_rgba(color, 120)};"
            "border-left: none; border-right: none; border-bottom: none;"
        )

        det_layout = QVBoxLayout(self._details)
        det_layout.setContentsMargins(88, 10, 16, 12)
        det_layout.setSpacing(4)

        detail_lines = _build_details_text(actions, blocked_sites)
        for line in detail_lines:
            lbl = QLabel(line)
            lbl.setStyleSheet(
                "color: #aab3d8; font-size: 10px; background: transparent;"
                "font-family: 'JetBrains Mono','Consolas',monospace;"
                "letter-spacing: 1px; border: none;"
            )
            det_layout.addWidget(lbl)

        self._details_h = 22 + len(detail_lines) * 18
        self._details.setFixedHeight(self._details_h)

        root.addWidget(self._details)

    def _toggle_expand(self):
        self._expanded = not self._expanded
        self._details.setVisible(self._expanded)
        self._expand_btn.setText("^  HIDE" if self._expanded else "v  SPEC")
        new_h = self._COLLAPSED_H + (self._details_h if self._expanded else 0)
        self.setFixedHeight(new_h)
        if self.parent():
            self.parent().updateGeometry()
            if hasattr(self.parent(), "adjustSize"):
                self.parent().adjustSize()

    def _make_btn(self, label: str, color: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setMinimumHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        f = QFont()
        f.setFamilies(list(_MONO))
        f.setPointSize(9)
        f.setBold(True)
        btn.setFont(f)
        hover_bg = _hex_to_rgba(color, 50)
        pressed_bg = _hex_to_rgba(color, 100)
        border_dim = _hex_to_rgba(color, 130)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {border_dim};
                border-radius: 0;
                color: {color};
                padding: 4px 12px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                border-color: {color};
            }}
            QPushButton:pressed {{
                background: {pressed_bg};
            }}
            QPushButton:disabled {{
                color: rgba(170, 179, 216, 70);
                border: 1px dashed rgba(170, 179, 216, 60);
                background: transparent;
            }}
        """)
        return btn
