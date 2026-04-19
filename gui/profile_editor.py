"""
ProfileEditor – dialog tworzenia i edycji profilu.

Sekcje: podstawy, motyw, tapeta, zablokowane aplikacje, strony www.
"""

import hashlib
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QWidget, QCheckBox, QMessageBox, QScrollArea, QFrame,
    QFileDialog,
)

from core.profile_manager import Profile
from core.system_controller import SystemController
from gui.styles import COLORS

# ─── Stałe ──────────────────────────────────────────────────────────

PROFILE_ICONS = [
    "WRK", "STD", "FOC", "DEV", "OPS", "LAB", "BLD", "SYS",
    "FUN", "GME", "MUS", "ART", "REC", "CHL", "EAT", "NAP",
    "RUN", "GYM", "OUT", "ZEN",
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
        self.setWindowTitle("Edit Profile" if profile else "New Profile")
        self.setMinimumSize(560, 480)
        self.resize(640, 620)
        if parent is not None:
            screen = parent.screen() if hasattr(parent, "screen") else None
            if screen is not None:
                avail = screen.availableGeometry()
                w = min(680, int(avail.width() * 0.9))
                h = min(720, int(avail.height() * 0.85))
                self.resize(w, h)

        self._editing = profile
        self._app_rows: list[tuple[QCheckBox, str, str]] = []
        self._site_rows: list[str] = []

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
        cl.addWidget(self._section_theme(profile))
        cl.addWidget(self._section_wallpaper(profile))
        cl.addWidget(self._section_apps(profile))
        cl.addWidget(self._section_websites(profile))
        cl.addWidget(self._section_password(profile))
        cl.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # Pasek przycisków
        btn_bar = QFrame()
        btn_bar.setStyleSheet(
            "QFrame { background: #0d1230; border-top: 1px solid #2a3372; }"
        )
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(20, 12, 20, 12)

        cancel = QPushButton("CANCEL")
        cancel.setMinimumHeight(44)
        cancel.setMinimumWidth(130)
        cancel.clicked.connect(self.reject)
        bl.addWidget(cancel)
        bl.addStretch()

        save = QPushButton("COMMIT  PROFILE")
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
        frame, layout = self._make_section("BASICS  //  IDENTIFICATION")

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_edit = QLineEdit(profile.name if profile else "")
        self.name_edit.setPlaceholderText("profile name...")
        form.addRow("NAME:", self.name_edit)

        self.icon_combo = QComboBox()
        for ico in PROFILE_ICONS:
            self.icon_combo.addItem(ico, ico)
        if profile:
            idx = next((i for i, ic in enumerate(PROFILE_ICONS) if ic == profile.icon), 0)
            self.icon_combo.setCurrentIndex(idx)
        self.icon_combo.setFixedWidth(140)
        form.addRow("CODE:", self.icon_combo)

        self.color_combo = QComboBox()
        for hex_val, name in PROFILE_COLORS:
            self.color_combo.addItem(f"[ {name.upper()} ]", hex_val)
        if profile:
            idx = next(
                (i for i, (h, _) in enumerate(PROFILE_COLORS) if h == profile.color), 0
            )
            self.color_combo.setCurrentIndex(idx)
        form.addRow("COLOR:", self.color_combo)

        layout.addLayout(form)
        return frame

    # ─── Sekcja: Motyw ───────────────────────────────────────────

    def _section_theme(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("THEME  //  SYSTEM  APPEARANCE")

        existing_dark: bool | None = None
        if profile:
            for a in profile.actions:
                if a.get("type") == "set_theme":
                    existing_dark = a.get("dark", True)
                    break

        self.theme_enabled_cb = QCheckBox("Switch OS theme on profile activation")
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
                background: #141a44; color: #aab3d8;
                border: 1px solid #2a3372; border-radius: 0;
                padding: 9px 24px;
                font-family: 'JetBrains Mono','Consolas',monospace;
                font-size: 11px; font-weight: 700; letter-spacing: 2px;
                min-height: 22px;
            }
            QPushButton:checked {
                background: #3a47d4; color: #e8ecf5; border-color: #7d8aff;
            }
            QPushButton:hover:!checked { background: #1b2458; color: #e8ecf5; }
        """
        self._theme_dark_btn = QPushButton("DARK")
        self._theme_dark_btn.setCheckable(True)
        self._theme_dark_btn.setStyleSheet(btn_style)
        self._theme_dark_btn.setChecked(existing_dark is not False)

        self._theme_light_btn = QPushButton("LIGHT")
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
        frame, layout = self._make_section("WALLPAPER  //  DESKTOP  IMAGE")

        existing_path = ""
        if profile:
            for a in profile.actions:
                if a.get("type") == "set_wallpaper":
                    existing_path = a.get("image_path", "")
                    break

        self.wallpaper_enabled_cb = QCheckBox("Set wallpaper on profile activation")
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
        self._wp_path_edit.setPlaceholderText("path to image (jpg / png / bmp)...")
        self._wp_path_edit.setReadOnly(False)
        wl.addWidget(self._wp_path_edit, 1)

        browse_btn = QPushButton("BROWSE")
        browse_btn.setMinimumHeight(36)
        browse_btn.clicked.connect(self._on_browse_wallpaper)
        wl.addWidget(browse_btn)

        layout.addWidget(self._wp_widget)
        self._wp_widget.setVisible(self.wallpaper_enabled_cb.isChecked())

        return frame

    def _on_browse_wallpaper(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "SELECT WALLPAPER",
            os.path.expanduser("~"),
            "Images (*.jpg *.jpeg *.png *.bmp *.webp);;All files (*.*)",
        )
        if path:
            self._wp_path_edit.setText(path)

    # ─── Sekcja: Zablokowane aplikacje ──────────────────────────

    def _section_apps(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("APPS  //  BLOCKED  PROCESSES")

        hint = QLabel(
            "Checked processes will be terminated while this profile is active."
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
        self._search_edit.setPlaceholderText("search processes...")
        self._search_edit.textChanged.connect(self._filter_apps)
        search_row.addWidget(self._search_edit, 1)

        refresh_btn = QPushButton("RELOAD")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setToolTip("Refresh running application list")
        refresh_btn.clicked.connect(self._refresh_apps)
        search_row.addWidget(refresh_btn)
        layout.addLayout(search_row)

        # Lista aplikacji
        apps_scroll = QScrollArea()
        apps_scroll.setWidgetResizable(True)
        apps_scroll.setFixedHeight(260)
        apps_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #2a3372;
                border-radius: 0;
                background: #0d1230;
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
            self._add_section_label("RUNNING  NOW")
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
                sep.setStyleSheet("QFrame { color: #2a3372; margin: 6px 0; }")
                self._apps_layout.addWidget(sep)

            # Etykieta sekcji – dokładnie raz
            self._add_section_label("KNOWN  APPLICATIONS")
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
        prefix = "[ LIVE ]  " if is_running else "[ ---- ]  "
        cb = QCheckBox(f"{prefix}{display_name}   ({proc_name})")
        cb.setChecked(checked)
        color = "#7d8aff" if is_running else "#aab3d8"
        cb.setStyleSheet(
            f"color: {color}; font-size: 11px; padding: 4px 0;"
            "font-family: 'JetBrains Mono','Consolas',monospace;"
            " letter-spacing: 0.5px; background: transparent;"
        )
        self._app_rows.append((cb, proc_name, display_name))
        self._apps_layout.addWidget(cb)

    def _add_section_label(self, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: #7d8aff; font-size: 9px; font-weight: 700;"
            "font-family: 'JetBrains Mono','Consolas',monospace;"
            " letter-spacing: 3px;"
            " padding: 8px 0 4px 0; background: transparent;"
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

    # ─── Sekcja: Zablokowane strony www ─────────────────────────

    def _section_websites(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("WEB  //  BLOCKED  DOMAINS")

        hint = QLabel("Domains blocked by the Chrome extension while profile is active.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(hint)

        # Lista istniejących stron
        self._sites_container = QWidget()
        self._sites_layout = QVBoxLayout(self._sites_container)
        self._sites_layout.setContentsMargins(0, 0, 0, 0)
        self._sites_layout.setSpacing(4)

        sites_scroll = QScrollArea()
        sites_scroll.setWidgetResizable(True)
        sites_scroll.setFixedHeight(160)
        sites_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #2a3372;
                border-radius: 0;
                background: #0d1230;
            }
        """)
        sites_scroll.setWidget(self._sites_container)
        layout.addWidget(sites_scroll)

        initial_sites = list(profile.blocked_sites) if profile else []
        self._site_rows = []
        self._sites_layout.addStretch()
        for site in initial_sites:
            self._add_site_row(site)

        # Wiersz dodawania
        add_row = QHBoxLayout()
        self._site_input = QLineEdit()
        self._site_input.setPlaceholderText("e.g. facebook.com  or  reddit.com/r/...")
        self._site_input.setMinimumHeight(36)
        add_row.addWidget(self._site_input, 1)

        add_site_btn = QPushButton("+  ADD")
        add_site_btn.setMinimumHeight(36)
        add_site_btn.clicked.connect(self._on_add_site)
        add_row.addWidget(add_site_btn)
        layout.addLayout(add_row)

        self._site_input.returnPressed.connect(self._on_add_site)

        # Zabezpieczenie hasłem
        return frame

    # ─── Sekcja: Ochrona hasłem ─────────────────────────────────

    def _section_password(self, profile: Profile = None) -> QFrame:
        frame, layout = self._make_section("🔒  PASSWORD  //  SECURITY")

        hint = QLabel(
            "A password-protected profile requires the password to edit it, "
            "add/remove it from the schedule, or modify the blocked-sites list "
            "in the browser extension."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color: {COLORS['text_mute']}; font-size: 11px;"
            f"font-family: 'JetBrains Mono','Consolas',monospace; letter-spacing: 0.5px;"
        )
        layout.addWidget(hint)

        self.lock_cb = QCheckBox("Enable password protection")
        self.lock_cb.setChecked(profile.locked if profile else False)
        self.lock_cb.stateChanged.connect(lambda s: self._lock_widget.setVisible(bool(s)))
        layout.addWidget(self.lock_cb)

        self._lock_widget = QWidget()
        ll = QFormLayout(self._lock_widget)
        ll.setContentsMargins(0, 4, 0, 0)
        ll.setSpacing(8)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        placeholder = (
            "New password (leave empty to keep current)"
            if profile and profile.password_hash
            else "Set password..."
        )
        self._password_edit.setPlaceholderText(placeholder)
        self._password_edit.setMinimumHeight(36)
        ll.addRow("PASSWORD:", self._password_edit)

        layout.addWidget(self._lock_widget)
        self._lock_widget.setVisible(self.lock_cb.isChecked())

        return frame

    def _add_site_row(self, site: str):
        row = QWidget()
        row.setStyleSheet("""
            QWidget#siteRow {
                background: #141a44;
                border-radius: 0;
                border: 1px solid #2a3372;
                border-left: 2px solid #5968ff;
            }
            QWidget#siteRow:hover { background: #1b2458; border-left-color: #7d8aff; }
        """)
        row.setObjectName("siteRow")
        row.setFixedHeight(36)

        rl = QHBoxLayout(row)
        rl.setContentsMargins(10, 0, 6, 0)
        rl.setSpacing(8)

        marker = QLabel("URL")
        marker.setStyleSheet(
            "background: transparent; color: #7d8aff; font-size: 9px;"
            "font-family: 'JetBrains Mono','Consolas',monospace;"
            "font-weight: 700; letter-spacing: 2px;"
        )
        rl.addWidget(marker)

        lbl = QLabel(site)
        lbl.setStyleSheet(
            "color: #e8ecf5; font-size: 11px; background: transparent;"
            "font-family: 'JetBrains Mono','Consolas',monospace;"
        )
        rl.addWidget(lbl, 1)

        del_btn = QPushButton("REMOVE")
        del_btn.setFixedHeight(28)
        del_btn.setMinimumWidth(82)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e5484d;
                border: 1px solid rgba(229, 72, 77, 0.45);
                border-radius: 0;
                padding: 2px 10px;
                font-family: 'JetBrains Mono','Consolas',monospace;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: #e5484d;
                color: #e8ecf5;
                border-color: #e5484d;
            }
            QPushButton:pressed {
                background: #b83238;
            }
        """)
        del_btn.clicked.connect(lambda: self._remove_site_row(site, row))
        rl.addWidget(del_btn)

        # wstaw przed stretch
        count = self._sites_layout.count()
        self._sites_layout.insertWidget(count - 1, row)
        self._site_rows.append(site)

    def _remove_site_row(self, site: str, row_widget: QWidget):
        if site in self._site_rows:
            self._site_rows.remove(site)
        row_widget.deleteLater()

    def _on_add_site(self):
        raw = self._site_input.text().strip()
        if not raw:
            return
        site = self._normalize_site(raw)
        if not site:
            return
        if site not in self._site_rows:
            self._add_site_row(site)
        self._site_input.clear()

    @staticmethod
    def _normalize_site(site: str) -> str:
        site = site.strip().lower()
        for prefix in ("https://", "http://"):
            if site.startswith(prefix):
                site = site[len(prefix):]
                break
        if site.startswith("www."):
            site = site[4:]
        return site.rstrip("/")

    # ─── Zapis ───────────────────────────────────────────────────

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "ERROR", "Profile name is required.")
            return

        actions: list[dict] = []

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
            preset_types = {"set_theme", "set_wallpaper", "block_process"}
            for a in self._editing.actions:
                if a.get("type") not in preset_types:
                    actions.append(a)

        locked = self.lock_cb.isChecked()
        password_hash = ""
        if locked:
            new_pw = self._password_edit.text()
            if new_pw:
                password_hash = hashlib.sha256(new_pw.encode()).hexdigest()
            elif self._editing and self._editing.locked:
                password_hash = self._editing.password_hash

        data = {
            "name": name,
            "icon": self.icon_combo.currentData(),
            "color": self.color_combo.currentData(),
            "description": "",
            "actions": actions,
            "blocked_sites": list(self._site_rows),
            "locked": locked,
            "password_hash": password_hash,
        }

        self.profileSaved.emit(data)
        self.accept()
