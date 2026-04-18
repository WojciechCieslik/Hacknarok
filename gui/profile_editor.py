"""
ProfileEditor – dialog tworzenia i edycji profilu.

Sekcje: podstawy, głośność, motyw, tapeta, zablokowane aplikacje.
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSlider,
    QWidget, QCheckBox, QMessageBox, QScrollArea, QFrame,
    QFileDialog,
)

from core.profile_manager import Profile
from core.system_controller import SystemController

# ─── Stałe ──────────────────────────────────────────────────────────

PROFILE_ICONS = [
    "🏢", "📚", "🎬", "🎮", "🎵", "💻", "🧘", "☕",
    "🌙", "🏠", "🎨", "📝", "🔧", "🏃", "📱", "🖥️",
    "🧠", "🎯", "⚡", "🌟",
]

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

# Popularne aplikacje do blokowania
WELL_KNOWN_APPS = [
    {"display_name": "Google Chrome",         "process_name": "chrome.exe"},
    {"display_name": "Mozilla Firefox",       "process_name": "firefox.exe"},
    {"display_name": "Microsoft Edge",        "process_name": "msedge.exe"},
    {"display_name": "Discord",               "process_name": "Discord.exe"},
    {"display_name": "Spotify",               "process_name": "Spotify.exe"},
    {"display_name": "Steam",                 "process_name": "steam.exe"},
    {"display_name": "Microsoft Teams",       "process_name": "ms-teams.exe"},
    {"display_name": "Microsoft Teams (classic)", "process_name": "Teams.exe"},
    {"display_name": "Slack",                 "process_name": "slack.exe"},
    {"display_name": "WhatsApp",              "process_name": "WhatsApp.exe"},
    {"display_name": "Telegram",              "process_name": "Telegram.exe"},
    {"display_name": "Signal",                "process_name": "Signal.exe"},
    {"display_name": "Zoom",                  "process_name": "Zoom.exe"},
    {"display_name": "Skype",                 "process_name": "Skype.exe"},
    {"display_name": "OBS Studio",            "process_name": "obs64.exe"},
    {"display_name": "VLC Media Player",      "process_name": "vlc.exe"},
    {"display_name": "Epic Games Launcher",   "process_name": "EpicGamesLauncher.exe"},
    {"display_name": "Battle.net",            "process_name": "Battle.net.exe"},
    {"display_name": "GOG Galaxy",            "process_name": "GalaxyClient.exe"},
    {"display_name": "Origin / EA App",       "process_name": "EADesktop.exe"},
    {"display_name": "Messenger",             "process_name": "Messenger.exe"},
    {"display_name": "Twitter / X",           "process_name": "Twitter.exe"},
    {"display_name": "TikTok",                "process_name": "TikTok.exe"},
    {"display_name": "Outlook",               "process_name": "OUTLOOK.EXE"},
    {"display_name": "Twitch Desktop",        "process_name": "Twitch.exe"},
    {"display_name": "Xbox App",              "process_name": "XboxApp.exe"},
]


# ─── Dialog edytora ─────────────────────────────────────────────────

class ProfileEditorDialog(QDialog):
    """Dialog tworzenia / edycji profilu."""

    profileSaved = Signal(dict)

    def __init__(self, profile: Profile = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edytuj profil" if profile else "Nowy profil")
        self.setMinimumSize(640, 720)
        self.resize(680, 820)

        self._editing = profile
        self._app_rows: list[tuple[QCheckBox, str, str]] = []

        self._setup_ui(profile)

    # ─── Budowa UI ───────────────────────────────────────────────

    def _setup_ui(self, profile: Profile = None):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(12)

        cl.addWidget(self._section_basics(profile))
        cl.addWidget(self._section_volume(profile))
        cl.addWidget(self._section_theme(profile))
        cl.addWidget(self._section_wallpaper(profile))
        cl.addWidget(self._section_apps(profile))
        cl.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # Pasek przycisków
        btn_bar = QFrame()
        btn_bar.setStyleSheet(
            "QFrame { background: #111827; border-top: 1px solid #1e293b; }"
        )
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(20, 12, 20, 12)

        cancel = QPushButton("✕  Anuluj")
        cancel.setMinimumHeight(44)
        cancel.setMinimumWidth(130)
        cancel.clicked.connect(self.reject)
        bl.addWidget(cancel)
        bl.addStretch()

        save = QPushButton("💾  Zapisz profil")
        save.setObjectName("primaryButton")
        save.setMinimumHeight(44)
        save.setMinimumWidth(180)
        save.clicked.connect(self._on_save)
        bl.addWidget(save)

        root.addWidget(btn_bar)

    # ─── Pomocnik ramki sekcji ───────────────────────────────────

    def _make_section(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("cardFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        lbl = QLabel(title)
        lbl.setObjectName("sectionTitle")
        layout.addWidget(lbl)

        return frame, layout

    # ─── Sekcja: Podstawowe ──────────────────────────────────────

    def _section_basics(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("📌  Podstawowe informacje")

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_edit = QLineEdit(profile.name if profile else "")
        self.name_edit.setPlaceholderText("Nazwa profilu...")
        form.addRow("Nazwa:", self.name_edit)

        self.icon_combo = QComboBox()
        for ico in PROFILE_ICONS:
            self.icon_combo.addItem(ico, ico)
        if profile:
            idx = next((i for i, ic in enumerate(PROFILE_ICONS) if ic == profile.icon), 0)
            self.icon_combo.setCurrentIndex(idx)
        self.icon_combo.setStyleSheet("font-size: 18px;")
        self.icon_combo.setFixedWidth(120)
        form.addRow("Ikona:", self.icon_combo)

        self.color_combo = QComboBox()
        for hex_val, name in PROFILE_COLORS:
            self.color_combo.addItem(f"●  {name}", hex_val)
        if profile:
            idx = next(
                (i for i, (h, _) in enumerate(PROFILE_COLORS) if h == profile.color), 0
            )
            self.color_combo.setCurrentIndex(idx)
        form.addRow("Kolor:", self.color_combo)

        layout.addLayout(form)
        return frame

    # ─── Sekcja: Głośność ────────────────────────────────────────

    def _section_volume(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("🔊  Głośność")

        existing_level: int | None = None
        if profile:
            for a in profile.actions:
                if a.get("type") == "set_volume":
                    existing_level = a.get("level", 50)
                    break

        self.volume_enabled_cb = QCheckBox("Ustaw głośność przy aktywacji profilu")
        self.volume_enabled_cb.setChecked(existing_level is not None)
        self.volume_enabled_cb.stateChanged.connect(
            lambda s: self._vol_widget.setVisible(bool(s))
        )
        layout.addWidget(self.volume_enabled_cb)

        self._vol_widget = QWidget()
        vl = QHBoxLayout(self._vol_widget)
        vl.setContentsMargins(0, 4, 0, 0)

        mute_lbl = QLabel("0%")
        mute_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        vl.addWidget(mute_lbl)

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(existing_level if existing_level is not None else 50)
        vl.addWidget(self._vol_slider, 1)

        self._vol_label = QLabel(f"{self._vol_slider.value()}%")
        self._vol_label.setFixedWidth(40)
        self._vol_label.setStyleSheet("color: #f1f5f9; font-size: 13px; font-weight: bold;")
        self._vol_slider.valueChanged.connect(
            lambda v: self._vol_label.setText(f"{v}%")
        )
        vl.addWidget(self._vol_label)

        layout.addWidget(self._vol_widget)
        self._vol_widget.setVisible(self.volume_enabled_cb.isChecked())

        return frame

    # ─── Sekcja: Motyw ───────────────────────────────────────────

    def _section_theme(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("🌙  Motyw systemu")

        existing_dark: bool | None = None
        if profile:
            for a in profile.actions:
                if a.get("type") == "set_theme":
                    existing_dark = a.get("dark", True)
                    break

        self.theme_enabled_cb = QCheckBox("Zmień motyw przy aktywacji profilu")
        self.theme_enabled_cb.setChecked(existing_dark is not None)
        self.theme_enabled_cb.stateChanged.connect(
            lambda s: self._theme_widget.setVisible(bool(s))
        )
        layout.addWidget(self.theme_enabled_cb)

        self._theme_widget = QWidget()
        tl = QHBoxLayout(self._theme_widget)
        tl.setContentsMargins(0, 4, 0, 0)
        tl.setSpacing(8)

        btn_style = """
            QPushButton {
                background: #1e293b; color: #94a3b8;
                border: 1px solid #334155; border-radius: 7px;
                padding: 8px 24px; font-size: 13px; min-height: 22px;
            }
            QPushButton:checked {
                background: #7c3aed; color: #fff; border-color: #7c3aed;
            }
            QPushButton:hover:!checked { background: #2d3a4a; }
        """
        self._theme_dark_btn = QPushButton("🌙  Ciemny")
        self._theme_dark_btn.setCheckable(True)
        self._theme_dark_btn.setStyleSheet(btn_style)
        self._theme_dark_btn.setChecked(existing_dark is not False)

        self._theme_light_btn = QPushButton("☀️  Jasny")
        self._theme_light_btn.setCheckable(True)
        self._theme_light_btn.setStyleSheet(btn_style)
        self._theme_light_btn.setChecked(existing_dark is False)

        self._theme_dark_btn.clicked.connect(self._on_theme_dark)
        self._theme_light_btn.clicked.connect(self._on_theme_light)

        tl.addWidget(self._theme_dark_btn)
        tl.addWidget(self._theme_light_btn)
        tl.addStretch()

        layout.addWidget(self._theme_widget)
        self._theme_widget.setVisible(self.theme_enabled_cb.isChecked())

        return frame

    def _on_theme_dark(self):
        self._theme_dark_btn.setChecked(True)
        self._theme_light_btn.setChecked(False)

    def _on_theme_light(self):
        self._theme_light_btn.setChecked(True)
        self._theme_dark_btn.setChecked(False)

    # ─── Sekcja: Tapeta ──────────────────────────────────────────

    def _section_wallpaper(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("🖼️  Tapeta pulpitu")

        existing_path = ""
        if profile:
            for a in profile.actions:
                if a.get("type") == "set_wallpaper":
                    existing_path = a.get("image_path", "")
                    break

        self.wallpaper_enabled_cb = QCheckBox("Zmień tapetę przy aktywacji profilu")
        self.wallpaper_enabled_cb.setChecked(bool(existing_path))
        self.wallpaper_enabled_cb.stateChanged.connect(
            lambda s: self._wp_widget.setVisible(bool(s))
        )
        layout.addWidget(self.wallpaper_enabled_cb)

        self._wp_widget = QWidget()
        wl = QHBoxLayout(self._wp_widget)
        wl.setContentsMargins(0, 4, 0, 0)
        wl.setSpacing(8)

        self._wp_path_edit = QLineEdit(existing_path)
        self._wp_path_edit.setPlaceholderText("Ścieżka do obrazu (jpg / png / bmp)...")
        self._wp_path_edit.setReadOnly(False)
        wl.addWidget(self._wp_path_edit, 1)

        browse_btn = QPushButton("📁  Przeglądaj...")
        browse_btn.setMinimumHeight(36)
        browse_btn.clicked.connect(self._on_browse_wallpaper)
        wl.addWidget(browse_btn)

        layout.addWidget(self._wp_widget)
        self._wp_widget.setVisible(self.wallpaper_enabled_cb.isChecked())

        return frame

    def _on_browse_wallpaper(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz tapetę",
            os.path.expanduser("~"),
            "Obrazy (*.jpg *.jpeg *.png *.bmp *.webp);;Wszystkie pliki (*.*)",
        )
        if path:
            self._wp_path_edit.setText(path)

    # ─── Sekcja: Zablokowane aplikacje ──────────────────────────

    def _section_apps(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("🚫  Zablokowane aplikacje")

        hint = QLabel(
            "Zaznaczone aplikacje będą zamykane gdy profil jest aktywny."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(hint)

        pre_checked: set[str] = set()
        if profile:
            for a in profile.actions:
                if a.get("type") == "block_process":
                    pre_checked.add(a.get("process_name", "").lower())

        # Wyszukiwarka + odśwież
        search_row = QHBoxLayout()
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("🔍  Szukaj aplikacji...")
        self._search_edit.textChanged.connect(self._filter_apps)
        search_row.addWidget(self._search_edit, 1)

        refresh_btn = QPushButton("🔄  Odśwież")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setToolTip("Odśwież listę uruchomionych aplikacji")
        refresh_btn.clicked.connect(self._refresh_apps)
        search_row.addWidget(refresh_btn)
        layout.addLayout(search_row)

        # Lista aplikacji
        apps_scroll = QScrollArea()
        apps_scroll.setWidgetResizable(True)
        apps_scroll.setFixedHeight(260)
        apps_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #334155;
                border-radius: 8px;
                background: #0f172a;
            }
        """)

        self._apps_container = QWidget()
        self._apps_layout = QVBoxLayout(self._apps_container)
        self._apps_layout.setContentsMargins(10, 8, 10, 8)
        self._apps_layout.setSpacing(2)

        apps_scroll.setWidget(self._apps_container)
        layout.addWidget(apps_scroll)

        self._populate_apps(pre_checked)
        return frame

    # ─── Logika listy aplikacji ──────────────────────────────────

    def _populate_apps(self, pre_checked: set[str] | None = None):
        if pre_checked is None:
            pre_checked = {
                proc.lower() for cb, proc, _ in self._app_rows if cb.isChecked()
            }

        while self._apps_layout.count():
            item = self._apps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._app_rows.clear()

        # Pobierz uruchomione z oknami
        running_apps: list[dict] = []
        try:
            running_apps = SystemController.get_apps_with_windows()
        except Exception:
            pass

        running_names_lc = {a["process_name"].lower() for a in running_apps}

        # Sekcja 1: uruchomione teraz
        if running_apps:
            self._add_section_label("Uruchomione teraz")
            for app in running_apps:
                self._add_app_row(
                    app["process_name"], app["display_name"],
                    is_running=True, checked=app["process_name"].lower() in pre_checked,
                )

        # Separator między sekcjami
        known_apps = [
            a for a in WELL_KNOWN_APPS
            if a["process_name"].lower() not in running_names_lc
        ]

        if known_apps:
            if running_apps:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("QFrame { color: #1e293b; margin: 6px 0; }")
                self._apps_layout.addWidget(sep)

            # Etykieta sekcji – dokładnie raz
            self._add_section_label("Znane aplikacje")
            for app in known_apps:
                self._add_app_row(
                    app["process_name"], app["display_name"],
                    is_running=False, checked=app["process_name"].lower() in pre_checked,
                )

        self._apps_layout.addStretch()

        # Przywróć filtr
        if hasattr(self, "_search_edit"):
            self._filter_apps(self._search_edit.text())

    def _add_app_row(self, proc_name: str, display_name: str,
                     is_running: bool, checked: bool):
        prefix = "🟢  " if is_running else "      "
        cb = QCheckBox(f"{prefix}{display_name}   ({proc_name})")
        cb.setChecked(checked)
        cb.setStyleSheet(
            "color: #f1f5f9; font-size: 12px; padding: 4px 0;"
            " background: transparent;"
        )
        self._app_rows.append((cb, proc_name, display_name))
        self._apps_layout.addWidget(cb)

    def _add_section_label(self, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: #475569; font-size: 10px; font-weight: bold;"
            " text-transform: uppercase; letter-spacing: 1px;"
            " padding: 4px 0 2px 0; background: transparent;"
        )
        self._apps_layout.addWidget(lbl)

    def _refresh_apps(self):
        current_checked = {
            proc.lower() for cb, proc, _ in self._app_rows if cb.isChecked()
        }
        self._populate_apps(current_checked)

    def _filter_apps(self, text: str):
        text = text.lower().strip()
        for cb, proc_name, display_name in self._app_rows:
            if text:
                cb.setVisible(
                    text in display_name.lower() or text in proc_name.lower()
                )
            else:
                cb.setVisible(True)

    # ─── Zapis ───────────────────────────────────────────────────

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa profilu jest wymagana!")
            return

        actions: list[dict] = []

        if self.volume_enabled_cb.isChecked():
            actions.append({"type": "set_volume", "level": self._vol_slider.value()})

        if self.theme_enabled_cb.isChecked():
            actions.append({
                "type": "set_theme",
                "dark": self._theme_dark_btn.isChecked(),
            })

        if self.wallpaper_enabled_cb.isChecked():
            wp_path = self._wp_path_edit.text().strip()
            if wp_path:
                actions.append({"type": "set_wallpaper", "image_path": wp_path})

        for cb, proc_name, display_name in self._app_rows:
            if cb.isChecked():
                actions.append({
                    "type": "block_process",
                    "process_name": proc_name,
                    "display_name": display_name,
                })

        # Zachowaj pozostałe akcje nie obsługiwane przez preset (np. launch_app)
        if self._editing:
            preset_types = {"set_volume", "set_theme", "set_wallpaper", "block_process"}
            for a in self._editing.actions:
                if a.get("type") not in preset_types:
                    actions.append(a)

        data = {
            "name": name,
            "icon": self.icon_combo.currentData(),
            "color": self.color_combo.currentData(),
            "description": "",
            "actions": actions,
        }

        self.profileSaved.emit(data)
        self.accept()
