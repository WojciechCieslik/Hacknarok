"""
ProfileCard – widget karty profilu.

Wyświetla informacje o profilu z przyciskami przełączania, edycji i usuwania.
"""

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsOpacityEffect, QMenu, QSizePolicy
)


class ProfileCard(QFrame):
    """Karta profilu – wyświetla nazwę, ikonę, akcje i przyciski."""

    switchClicked = Signal(str)    # nazwa profilu
    editClicked = Signal(str)      # nazwa profilu
    deleteClicked = Signal(str)    # nazwa profilu
    duplicateClicked = Signal(str) # nazwa profilu

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
        self.setFixedHeight(200)
        self.setMinimumWidth(200)
        self.setMaximumWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._setup_ui(name, icon, color, description, actions_count, is_active)

    def _setup_ui(self, name, icon, color, description, actions_count, is_active):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # ── Nagłówek: ikona + nazwa ──
        header = QHBoxLayout()
        header.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 28))
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            f"background: {color}22; border-radius: 12px; padding: 4px;"
        )
        header.addWidget(icon_label)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)

        name_label = QLabel(name)
        name_label.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {color};")
        name_col.addWidget(name_label)

        if is_active:
            status = QLabel("● AKTYWNY")
            status.setStyleSheet(f"color: #10b981; font-size: 11px; font-weight: bold;")
        else:
            status = QLabel(f"{actions_count} akcji")
            status.setStyleSheet("color: #94a3b8; font-size: 11px;")
        name_col.addWidget(status)

        header.addLayout(name_col)
        header.addStretch()

        # Menu kontekstowe (3 kropki)
        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(32, 32)
        menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.05);
                color: #f1f5f9;
            }
        """)
        menu_btn.clicked.connect(self._show_menu)
        header.addWidget(menu_btn, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addLayout(header)

        # ── Opis ──
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
            desc_label.setMaximumHeight(36)
            layout.addWidget(desc_label)

        layout.addStretch()

        # ── Przycisk główny ──
        if is_active:
            btn = QPushButton("⏹ Dezaktywuj")
            btn.setObjectName("deactivateButton")
        else:
            btn = QPushButton("▶ Przełącz")
            btn.setObjectName("switchButton")
        btn.setFixedHeight(40)
        btn.clicked.connect(lambda: self.switchClicked.emit(self.profile_name))
        layout.addWidget(btn)

    def _show_menu(self):
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Edytuj")
        duplicate_action = menu.addAction("📋 Duplikuj")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Usuń")

        edit_action.triggered.connect(lambda: self.editClicked.emit(self.profile_name))
        duplicate_action.triggered.connect(lambda: self.duplicateClicked.emit(self.profile_name))
        delete_action.triggered.connect(lambda: self.deleteClicked.emit(self.profile_name))

        menu.exec(self.cursor().pos())

    def enterEvent(self, event):
        if not self._is_active:
            self.setStyleSheet(
                self.styleSheet()
                + f"QFrame#{self.objectName()} {{ border-color: {self.profile_color}; }}"
            )
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._is_active:
            self.setStyleSheet("")
        super().leaveEvent(event)
