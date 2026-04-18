"""
ProfileCard – wiersz profilu na liście.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)


def _hex_to_rgba(hex_color: str, alpha: int) -> str:
    """Konwertuje '#rrggbb' + alpha (0-255) na 'rgba(r,g,b,a)'."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return hex_color


class ProfileCard(QFrame):
    switchClicked = Signal(str)
    editClicked = Signal(str)
    deleteClicked = Signal(str)
    duplicateClicked = Signal(str)

    def __init__(
        self,
        name: str,
        icon: str = "🖥️",
        color: str = "#7c3aed",
        description: str = "",
        actions_count: int = 0,
        is_active: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.profile_name = name
        self.profile_color = color
        self._is_active = is_active

        self.setObjectName("activeCardFrame" if is_active else "cardFrame")
        self.setFixedHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._setup_ui(name, icon, color, description, actions_count, is_active)

    def _setup_ui(self, name, icon, color, description, actions_count, is_active):
        root = QHBoxLayout(self)
        root.setContentsMargins(14, 8, 14, 8)
        root.setSpacing(12)

        # ── Ikona ──
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 20))
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            f"background: {_hex_to_rgba(color, 34)}; border-radius: 10px;"
        )
        root.addWidget(icon_label)

        # ── Info ──
        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name)
        name_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {color}; background: transparent;")
        info.addWidget(name_label)

        if is_active:
            sub = QLabel("● AKTYWNY")
            sub.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold; background: transparent;")
        elif description:
            sub = QLabel(description)
            sub.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        else:
            sub = QLabel(f"{actions_count} akcji")
            sub.setStyleSheet("color: #64748b; font-size: 11px; background: transparent;")
        info.addWidget(sub)

        root.addLayout(info, 1)

        # ── Przyciski po prawej ──
        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        btn_col.setContentsMargins(0, 0, 0, 0)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        top_row.setContentsMargins(0, 0, 0, 0)

        if is_active:
            act_btn = self._make_btn("⏹", "#ef4444", "Dezaktywuj profil")
        else:
            act_btn = self._make_btn("▶", color, "Aktywuj profil")
        act_btn.clicked.connect(lambda: self.switchClicked.emit(self.profile_name))
        top_row.addWidget(act_btn)

        edit_btn = self._make_btn("✎", "#94a3b8", "Edytuj profil")
        edit_btn.clicked.connect(lambda: self.editClicked.emit(self.profile_name))
        top_row.addWidget(edit_btn)

        del_btn = self._make_btn("✕", "#ef4444", "Usuń profil")
        del_btn.clicked.connect(lambda: self.deleteClicked.emit(self.profile_name))
        top_row.addWidget(del_btn)

        btn_col.addLayout(top_row)

        dup_row = QHBoxLayout()
        dup_row.setContentsMargins(0, 0, 0, 0)
        dup_row.addStretch()
        dup_btn = self._make_btn("⊔", "#64748b", "Duplikuj profil", size=22)
        dup_btn.clicked.connect(lambda: self.duplicateClicked.emit(self.profile_name))
        dup_row.addWidget(dup_btn)
        btn_col.addLayout(dup_row)

        root.addLayout(btn_col)

    def _make_btn(self, symbol: str, color: str, tooltip: str, size: int = 30) -> QPushButton:
        btn = QPushButton(symbol)
        btn.setFixedSize(size, size)
        btn.setToolTip(tooltip)
        font = QFont("Segoe UI Symbol", size // 3 + 3)
        font.setBold(True)
        btn.setFont(font)
        hover_bg = _hex_to_rgba(color, 40)
        pressed_bg = _hex_to_rgba(color, 80)
        border_dim = _hex_to_rgba(color, 100)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {border_dim};
                border-radius: 6px;
                color: {color};
                padding: 0px;
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
