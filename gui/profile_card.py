"""
ProfileCard – wiersz profilu na liście z rozwijalnymi szczegółami.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)


def _hex_to_rgba(hex_color: str, alpha: int) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return hex_color


def _build_details_text(actions: list[dict]) -> list[str]:
    """Zwróć listę czytelnych linii opisu akcji profilu."""
    lines = []
    blocked = []
    for a in actions:
        t = a.get("type", "")
        if t == "set_volume":
            lines.append(f"🔊  Głośność: {a.get('level', '?')}%")
        elif t == "set_theme":
            lines.append("🌙  Motyw: ciemny" if a.get("dark", True) else "☀️  Motyw: jasny")
        elif t == "block_process":
            blocked.append(a.get("display_name") or a.get("process_name", "?"))
        elif t == "launch_app":
            label = a.get("label") or a.get("path", "?")
            lines.append(f"🚀  Uruchamia: {label}")
    if blocked:
        preview = ", ".join(blocked[:3])
        if len(blocked) > 3:
            preview += f"  (+{len(blocked) - 3})"
        lines.append(f"🚫  Blokuje: {preview}")
    return lines or ["Brak skonfigurowanych akcji"]


class ProfileCard(QFrame):
    switchClicked = Signal(str)
    editClicked = Signal(str)
    deleteClicked = Signal(str)
    duplicateClicked = Signal(str)

    _COLLAPSED_H = 82

    def __init__(
        self,
        name: str,
        icon: str = "🖥️",
        color: str = "#7c3aed",
        description: str = "",
        actions_count: int = 0,
        actions: list[dict] = None,
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
                       actions or [], is_active)

    def _setup_ui(self, name, icon, color, description, actions_count,
                  actions, is_active):
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
        icon_label.setFont(QFont("Segoe UI Emoji", 20))
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            f"background: {_hex_to_rgba(color, 34)}; border-radius: 10px;"
        )
        top_layout.addWidget(icon_label)

        # Info (nazwa + stan)
        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name)
        name_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {color}; background: transparent;")
        info.addWidget(name_label)

        if is_active:
            sub = QLabel("● AKTYWNY")
            sub.setStyleSheet(
                "color: #10b981; font-size: 11px; font-weight: bold; background: transparent;"
            )
        elif description:
            sub = QLabel(description)
            sub.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        else:
            sub = QLabel(f"{actions_count} akcji")
            sub.setStyleSheet("color: #64748b; font-size: 11px; background: transparent;")
        info.addWidget(sub)

        top_layout.addLayout(info, 1)

        # Przyciski akcji (prawa kolumna)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.setContentsMargins(0, 0, 0, 0)

        if is_active:
            act_btn = self._make_btn("⏹  Dezaktywuj", "#ef4444")
        else:
            act_btn = self._make_btn("▶  Aktywuj", color)
        act_btn.clicked.connect(lambda: self.switchClicked.emit(self.profile_name))
        btn_row.addWidget(act_btn)

        edit_btn = self._make_btn("✎  Edytuj", "#94a3b8")
        edit_btn.clicked.connect(lambda: self.editClicked.emit(self.profile_name))
        btn_row.addWidget(edit_btn)

        dup_btn = self._make_btn("⊔  Duplikuj", "#64748b")
        dup_btn.clicked.connect(lambda: self.duplicateClicked.emit(self.profile_name))
        btn_row.addWidget(dup_btn)

        del_btn = self._make_btn("✕  Usuń", "#ef4444")
        del_btn.clicked.connect(lambda: self.deleteClicked.emit(self.profile_name))
        btn_row.addWidget(del_btn)

        self._expand_btn = self._make_btn("˅  Szczegóły", "#64748b")
        self._expand_btn.clicked.connect(self._toggle_expand)
        btn_row.addWidget(self._expand_btn)

        top_layout.addLayout(btn_row)

        root.addWidget(top)

        # ── Sekcja szczegółów (ukryta domyślnie) ─────────────────
        self._details = QFrame()
        self._details.setVisible(False)
        self._details.setStyleSheet(
            f"background: {_hex_to_rgba(color, 12)};"
            f"border-top: 1px solid {_hex_to_rgba(color, 60)};"
            "border-radius: 0 0 12px 12px; border-left: none; border-right: none;"
        )

        det_layout = QVBoxLayout(self._details)
        det_layout.setContentsMargins(62, 8, 14, 10)
        det_layout.setSpacing(3)

        detail_lines = _build_details_text(actions)
        for line in detail_lines:
            lbl = QLabel(line)
            lbl.setStyleSheet(
                "color: #94a3b8; font-size: 11px; background: transparent; border: none;"
            )
            det_layout.addWidget(lbl)

        # Wysokość szczegółów: 10 (padding) + n*16px + 10
        self._details_h = 20 + len(detail_lines) * 17
        self._details.setFixedHeight(self._details_h)

        root.addWidget(self._details)

    def _toggle_expand(self):
        self._expanded = not self._expanded
        self._details.setVisible(self._expanded)
        self._expand_btn.setText("˄  Zwiń" if self._expanded else "˅  Szczegóły")
        new_h = self._COLLAPSED_H + (self._details_h if self._expanded else 0)
        self.setFixedHeight(new_h)
        # Poinformuj layout rodzica o zmianie rozmiaru
        if self.parent():
            self.parent().updateGeometry()
            if hasattr(self.parent(), "adjustSize"):
                self.parent().adjustSize()

    def _make_btn(self, label: str, color: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setMinimumHeight(34)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        btn.setFont(f)
        hover_bg = _hex_to_rgba(color, 40)
        pressed_bg = _hex_to_rgba(color, 80)
        border_dim = _hex_to_rgba(color, 100)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {border_dim};
                border-radius: 6px;
                color: {color};
                padding: 4px 10px;
                font-size: 12px;
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

