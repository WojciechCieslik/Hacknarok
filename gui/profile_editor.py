"""
ProfileEditor – dialog do tworzenia i edycji profili.

Zawiera kreator z konfiguracją nazwy, ikony, koloru, opisu i listy akcji.
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QSlider, QFileDialog, QListWidget, QListWidgetItem,
    QGroupBox, QFormLayout, QTextEdit, QWidget, QCheckBox,
    QMessageBox, QSpinBox, QScrollArea, QFrame, QSizePolicy
)

from core.profile_manager import Profile
from core.system_controller import SystemController

# Dostępne ikony profilu
PROFILE_ICONS = [
    "🏢", "📚", "🎬", "🎮", "🎵", "💻", "🧘", "☕",
    "🌙", "🏠", "🎨", "📝", "🔧", "🏃", "📱", "🖥️",
    "🧠", "🎯", "⚡", "🌟",
]

# Dostępne kolory profilu
PROFILE_COLORS = [
    ("#3b82f6", "Niebieski"),
    ("#7c3aed", "Fioletowy"),
    ("#10b981", "Zielony"),
    ("#f59e0b", "Pomarańczowy"),
    ("#ef4444", "Czerwony"),
    ("#06b6d4", "Cyjanowy"),
    ("#ec4899", "Różowy"),
    ("#8b5cf6", "Lawendowy"),
    ("#14b8a6", "Morski"),
    ("#f97316", "Mandarynkowy"),
]

# Typy akcji
ACTION_TYPES = [
    ("launch_app", "🚀 Uruchom aplikację"),
    ("kill_process", "💀 Zakończ proces"),
    ("set_volume", "🔊 Ustaw głośność"),
    ("set_wallpaper", "🖼️ Zmień tapetę"),
    ("set_theme", "🌙 Zmień motyw"),
    ("set_power_plan", "⚡ Plan zasilania"),
    ("block_process", "🚫 Blokuj proces"),
]


class ActionConfigWidget(QFrame):
    """Widget konfiguracji pojedynczej akcji."""

    removeRequested = Signal(int)  # index

    def __init__(self, index: int, action_dict: dict = None, parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("cardFrame")
        self.setStyleSheet("QFrame#cardFrame { padding: 12px; }")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)

        # Nagłówek z typem akcji i przyciskiem usunięcia
        header = QHBoxLayout()

        self.type_combo = QComboBox()
        for atype, label in ACTION_TYPES:
            self.type_combo.addItem(label, atype)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        header.addWidget(self.type_combo, 1)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(28, 28)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #ef4444;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background: rgba(239,68,68,0.1); }
        """)
        remove_btn.clicked.connect(lambda: self.removeRequested.emit(self.index))
        header.addWidget(remove_btn)

        self._layout.addLayout(header)

        # Kontener na pola konfiguracyjne
        self.config_container = QWidget()
        self.config_layout = QFormLayout(self.config_container)
        self.config_layout.setContentsMargins(0, 4, 0, 0)
        self.config_layout.setSpacing(6)
        self._layout.addWidget(self.config_container)

        # Pola do przechowywania wartości
        self._path_edit = None
        self._args_edit = None
        self._process_edit = None
        self._volume_slider = None
        self._volume_label = None
        self._wallpaper_edit = None
        self._theme_combo = None
        self._power_combo = None

        # Załaduj istniejące dane
        if action_dict:
            atype = action_dict.get("type", "launch_app")
            idx = next(
                (i for i, (t, _) in enumerate(ACTION_TYPES) if t == atype), 0
            )
            self.type_combo.setCurrentIndex(idx)
            self._build_config(atype, action_dict)
        else:
            self._build_config("launch_app")

    def _on_type_changed(self, idx):
        atype = self.type_combo.currentData()
        self._build_config(atype)

    def _clear_config(self):
        while self.config_layout.rowCount() > 0:
            self.config_layout.removeRow(0)
        self._path_edit = None
        self._args_edit = None
        self._process_edit = None
        self._volume_slider = None
        self._volume_label = None
        self._wallpaper_edit = None
        self._theme_combo = None
        self._power_combo = None

    def _build_config(self, action_type: str, data: dict = None):
        self._clear_config()
        data = data or {}

        if action_type == "launch_app":
            self._path_edit = QLineEdit(data.get("path", ""))
            self._path_edit.setPlaceholderText("Ścieżka do aplikacji...")
            browse_btn = QPushButton("📂")
            browse_btn.setFixedWidth(40)
            browse_btn.clicked.connect(self._browse_app)
            row = QHBoxLayout()
            row.addWidget(self._path_edit, 1)
            row.addWidget(browse_btn)
            w = QWidget()
            w.setLayout(row)
            self.config_layout.addRow("Ścieżka:", w)

            self._args_edit = QLineEdit(
                " ".join(data.get("args", []))
            )
            self._args_edit.setPlaceholderText("Argumenty (opcjonalne)...")
            self.config_layout.addRow("Argumenty:", self._args_edit)

        elif action_type in ("kill_process", "block_process"):
            self._process_edit = QLineEdit(data.get("process_name", ""))
            self._process_edit.setPlaceholderText("np. Teams.exe, discord.exe...")
            self.config_layout.addRow("Proces:", self._process_edit)

        elif action_type == "set_volume":
            slider_row = QHBoxLayout()
            self._volume_slider = QSlider(Qt.Orientation.Horizontal)
            self._volume_slider.setRange(0, 100)
            self._volume_slider.setValue(data.get("level", 50))
            self._volume_slider.setTickInterval(10)
            self._volume_label = QLabel(f"{self._volume_slider.value()}%")
            self._volume_label.setFixedWidth(40)
            self._volume_slider.valueChanged.connect(
                lambda v: self._volume_label.setText(f"{v}%")
            )
            slider_row.addWidget(self._volume_slider, 1)
            slider_row.addWidget(self._volume_label)
            w = QWidget()
            w.setLayout(slider_row)
            self.config_layout.addRow("Poziom:", w)

        elif action_type == "set_wallpaper":
            self._wallpaper_edit = QLineEdit(data.get("image_path", ""))
            self._wallpaper_edit.setPlaceholderText("Ścieżka do obrazu...")
            browse_btn = QPushButton("📂")
            browse_btn.setFixedWidth(40)
            browse_btn.clicked.connect(self._browse_wallpaper)
            row = QHBoxLayout()
            row.addWidget(self._wallpaper_edit, 1)
            row.addWidget(browse_btn)
            w = QWidget()
            w.setLayout(row)
            self.config_layout.addRow("Obraz:", w)

        elif action_type == "set_theme":
            self._theme_combo = QComboBox()
            self._theme_combo.addItem("🌙 Ciemny", True)
            self._theme_combo.addItem("☀️ Jasny", False)
            if data.get("dark", True) is False:
                self._theme_combo.setCurrentIndex(1)
            self.config_layout.addRow("Motyw:", self._theme_combo)

        elif action_type == "set_power_plan":
            self._power_combo = QComboBox()
            plans = SystemController.get_power_plans()
            for plan in plans:
                self._power_combo.addItem(plan["name"], plan["guid"])
            # Ustaw aktualny
            guid = data.get("guid", "")
            for i in range(self._power_combo.count()):
                if self._power_combo.itemData(i) == guid:
                    self._power_combo.setCurrentIndex(i)
                    break
            self.config_layout.addRow("Plan:", self._power_combo)

    def _browse_app(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz aplikację", "",
            "Pliki wykonywalne (*.exe);;Wszystkie pliki (*)"
        )
        if path and self._path_edit:
            self._path_edit.setText(path)

    def _browse_wallpaper(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz tapetę", "",
            "Obrazy (*.png *.jpg *.jpeg *.bmp);;Wszystkie pliki (*)"
        )
        if path and self._wallpaper_edit:
            self._wallpaper_edit.setText(path)

    def get_action_dict(self) -> dict:
        """Zwróć dict opisujący tę akcję."""
        atype = self.type_combo.currentData()
        result = {"type": atype}

        if atype == "launch_app":
            result["path"] = self._path_edit.text() if self._path_edit else ""
            args_text = self._args_edit.text().strip() if self._args_edit else ""
            result["args"] = args_text.split() if args_text else []
            result["label"] = os.path.basename(result["path"])

        elif atype in ("kill_process", "block_process"):
            result["process_name"] = (
                self._process_edit.text() if self._process_edit else ""
            )

        elif atype == "set_volume":
            result["level"] = (
                self._volume_slider.value() if self._volume_slider else 50
            )

        elif atype == "set_wallpaper":
            result["image_path"] = (
                self._wallpaper_edit.text() if self._wallpaper_edit else ""
            )

        elif atype == "set_theme":
            result["dark"] = (
                self._theme_combo.currentData() if self._theme_combo else True
            )

        elif atype == "set_power_plan":
            if self._power_combo:
                result["guid"] = self._power_combo.currentData() or ""
                result["name"] = self._power_combo.currentText()
            else:
                result["guid"] = ""
                result["name"] = ""

        return result


class ProfileEditorDialog(QDialog):
    """Dialog do tworzenia / edycji profili."""

    profileSaved = Signal(dict)  # dane profilu

    def __init__(self, profile: Profile = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edytor profilu" if profile else "Nowy profil")
        self.setMinimumSize(550, 600)
        self.resize(600, 700)
        self._editing = profile
        self._action_widgets: list[ActionConfigWidget] = []

        self._setup_ui(profile)

    def _setup_ui(self, profile: Profile = None):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ── Tytuł ──
        title = QLabel("✏️ Edytuj profil" if profile else "➕ Nowy profil")
        title.setObjectName("titleLabel")
        main_layout.addWidget(title)

        # ── ScrollArea ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(0, 0, 8, 0)

        # ── Podstawowe informacje ──
        info_group = QGroupBox("Informacje podstawowe")
        info_layout = QFormLayout()
        info_layout.setSpacing(10)

        self.name_edit = QLineEdit(profile.name if profile else "")
        self.name_edit.setPlaceholderText("Nazwa profilu...")
        info_layout.addRow("Nazwa:", self.name_edit)

        # Ikona
        icon_row = QHBoxLayout()
        self.icon_combo = QComboBox()
        for ico in PROFILE_ICONS:
            self.icon_combo.addItem(ico, ico)
        if profile:
            idx = next(
                (i for i, ic in enumerate(PROFILE_ICONS) if ic == profile.icon), 0
            )
            self.icon_combo.setCurrentIndex(idx)
        self.icon_combo.setStyleSheet("font-size: 18px;")
        icon_row.addWidget(self.icon_combo)
        icon_row.addStretch()
        w = QWidget()
        w.setLayout(icon_row)
        info_layout.addRow("Ikona:", w)

        # Kolor
        color_row = QHBoxLayout()
        self.color_combo = QComboBox()
        for hex_val, name in PROFILE_COLORS:
            self.color_combo.addItem(f"● {name}", hex_val)
        if profile:
            idx = next(
                (i for i, (h, _) in enumerate(PROFILE_COLORS) if h == profile.color), 0
            )
            self.color_combo.setCurrentIndex(idx)
        color_row.addWidget(self.color_combo)
        color_row.addStretch()
        w = QWidget()
        w.setLayout(color_row)
        info_layout.addRow("Kolor:", w)

        # Opis
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setPlaceholderText("Opis profilu (opcjonalny)...")
        if profile:
            self.desc_edit.setPlainText(profile.description)
        info_layout.addRow("Opis:", self.desc_edit)

        info_group.setLayout(info_layout)
        scroll_layout.addWidget(info_group)

        # ── Akcje ──
        actions_group = QGroupBox("Akcje profilu")
        self.actions_layout = QVBoxLayout()
        self.actions_layout.setSpacing(8)

        # Załaduj istniejące akcje
        if profile and profile.actions:
            for i, action_dict in enumerate(profile.actions):
                self._add_action_widget(action_dict)

        add_action_btn = QPushButton("➕ Dodaj akcję")
        add_action_btn.setObjectName("primaryButton")
        add_action_btn.clicked.connect(lambda: self._add_action_widget())

        self.actions_layout.addWidget(add_action_btn)
        actions_group.setLayout(self.actions_layout)
        scroll_layout.addWidget(actions_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

        # ── Przyciski ──
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        buttons.addStretch()

        save_btn = QPushButton("💾 Zapisz profil")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        buttons.addWidget(save_btn)

        main_layout.addLayout(buttons)

    def _add_action_widget(self, action_dict: dict = None):
        idx = len(self._action_widgets)
        widget = ActionConfigWidget(idx, action_dict)
        widget.removeRequested.connect(self._remove_action)
        self._action_widgets.append(widget)
        # Wstaw przed przyciskiem "Dodaj akcję"
        self.actions_layout.insertWidget(
            self.actions_layout.count() - 1, widget
        )

    def _remove_action(self, index: int):
        for i, w in enumerate(self._action_widgets):
            if w.index == index:
                self.actions_layout.removeWidget(w)
                w.deleteLater()
                self._action_widgets.pop(i)
                break
        # Przenumeruj
        for i, w in enumerate(self._action_widgets):
            w.index = i

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa profilu jest wymagana!")
            return

        actions = [w.get_action_dict() for w in self._action_widgets]

        data = {
            "name": name,
            "icon": self.icon_combo.currentData(),
            "color": self.color_combo.currentData(),
            "description": self.desc_edit.toPlainText().strip(),
            "actions": actions,
        }

        self.profileSaved.emit(data)
        self.accept()
