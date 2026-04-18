COLORS = {
    "bg_primary":   "#0c0c0c",
    "bg_secondary": "#101010",
    "bg_card":      "#141414",
    "bg_card_hover":"#1a1a1a",
    "bg_input":     "#111111",
    "bg_surface":   "#161616",

    "accent":        "#4488FF",
    "accent_dim":    "#1a3a88",
    "accent_active": "#00C853",
    "accent_warn":   "#FFAB00",
    "accent_danger": "#FF1744",
    "accent_danger_dark": "#CC0033",

    "text_primary":   "#E8E8E8",
    "text_secondary": "#888888",
    "text_muted":     "#444444",

    "border":        "#1E1E1E",
    "border_bright": "#2A2A2A",
    "border_focus":  "#4488FF",
    "border_active": "#00C853",
}


MAIN_STYLESHEET = f"""
/* ── Global ───────────────────────────────────────────────────── */
QMainWindow {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
}}

QWidget {{
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
    background-color: transparent;
}}

QWidget#centralWidget {{
    background-color: {COLORS["bg_primary"]};
}}

/* ── Labels ───────────────────────────────────────────────────── */
QLabel {{
    color: {COLORS["text_primary"]};
    background: transparent;
    padding: 0px;
}}

QLabel#titleLabel {{
    font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
    font-size: 18px;
    font-weight: bold;
    color: {COLORS["accent"]};
    letter-spacing: 2px;
    text-transform: uppercase;
}}

QLabel#subtitleLabel {{
    font-size: 11px;
    color: {COLORS["text_muted"]};
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QLabel#sectionTitle {{
    font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
    font-size: 10px;
    font-weight: bold;
    color: {COLORS["text_secondary"]};
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 6px 0px;
    border-bottom: 1px solid {COLORS["border_bright"]};
    margin-bottom: 4px;
}}

QLabel#activeWindowLabel {{
    font-size: 11px;
    color: {COLORS["text_secondary"]};
    padding: 4px 10px;
    background: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
}}

/* ── Buttons ──────────────────────────────────────────────────── */
QPushButton {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    min-height: 18px;
}}

QPushButton:hover {{
    background-color: {COLORS["bg_card_hover"]};
    color: {COLORS["text_primary"]};
    border-left: 2px solid {COLORS["accent"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["accent_dim"]};
    color: {COLORS["accent"]};
}}

QPushButton#primaryButton {{
    background: {COLORS["accent"]};
    border: none;
    color: {COLORS["bg_primary"]};
    font-weight: bold;
    padding: 10px 24px;
    font-size: 12px;
    letter-spacing: 2px;
}}

QPushButton#primaryButton:hover {{
    background: #6699FF;
    color: {COLORS["bg_primary"]};
}}

QPushButton#primaryButton:pressed {{
    background: {COLORS["accent_dim"]};
    color: {COLORS["accent"]};
}}

QPushButton#dangerButton {{
    background-color: {COLORS["accent_danger"]};
    border: none;
    color: white;
    letter-spacing: 1px;
}}

QPushButton#dangerButton:hover {{
    background-color: {COLORS["accent_danger_dark"]};
    border-left: none;
}}

QPushButton#switchButton {{
    background: {COLORS["accent"]};
    border: none;
    color: {COLORS["bg_primary"]};
    font-size: 12px;
    font-weight: bold;
    padding: 12px 28px;
    letter-spacing: 2px;
    min-height: 26px;
}}

QPushButton#switchButton:hover {{
    background: #6699FF;
    border-left: none;
}}

QPushButton#deactivateButton {{
    background-color: {COLORS["accent_danger"]};
    border: none;
    color: white;
    font-weight: bold;
    padding: 12px 28px;
    font-size: 12px;
    letter-spacing: 2px;
    min-height: 26px;
}}

QPushButton#deactivateButton:hover {{
    background-color: {COLORS["accent_danger_dark"]};
    border-left: none;
}}

QPushButton#addButton {{
    background: transparent;
    border: 1px dashed {COLORS["border_bright"]};
    color: {COLORS["text_muted"]};
    font-size: 20px;
    letter-spacing: 0px;
    min-height: 100px;
}}

QPushButton#addButton:hover {{
    border-color: {COLORS["accent"]};
    color: {COLORS["accent"]};
    background: rgba(68, 136, 255, 0.04);
}}

/* ── Inputs ───────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {COLORS["accent"]};
}}

QLineEdit:focus {{
    border-color: {COLORS["border_focus"]};
    border-left: 2px solid {COLORS["accent"]};
}}

QTextEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    padding: 8px;
    font-size: 13px;
}}

QTextEdit:focus {{
    border-color: {COLORS["border_focus"]};
    border-left: 2px solid {COLORS["accent"]};
}}

/* ── ComboBox ─────────────────────────────────────────────────── */
QComboBox {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    padding: 7px 10px;
    font-size: 13px;
    min-height: 18px;
}}

QComboBox:hover {{
    border-color: {COLORS["accent"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS["text_secondary"]};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    selection-background-color: {COLORS["accent"]};
    selection-color: {COLORS["bg_primary"]};
    padding: 2px;
    outline: none;
}}

/* ── Slider ───────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: {COLORS["bg_input"]};
    height: 4px;
    border-radius: 0px;
}}

QSlider::handle:horizontal {{
    background: {COLORS["accent"]};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 0px;
}}

QSlider::handle:horizontal:hover {{
    background: #6699FF;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS["accent"]};
    border-radius: 0px;
}}

/* ── SpinBox ──────────────────────────────────────────────────── */
QSpinBox {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    padding: 7px;
    font-size: 13px;
}}

QSpinBox:focus {{
    border-color: {COLORS["border_focus"]};
}}

/* ── CheckBox ─────────────────────────────────────────────────── */
QCheckBox {{
    color: {COLORS["text_primary"]};
    spacing: 8px;
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    background: {COLORS["bg_input"]};
}}

QCheckBox::indicator:checked {{
    background: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["accent"]};
}}

/* ── GroupBox ─────────────────────────────────────────────────── */
QGroupBox {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-left: 3px solid {COLORS["accent"]};
    border-radius: 0px;
    margin-top: 16px;
    padding: 18px 14px 14px 14px;
    font-size: 10px;
    font-weight: bold;
    color: {COLORS["text_secondary"]};
    letter-spacing: 2px;
    text-transform: uppercase;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

/* ── ScrollArea ───────────────────────────────────────────────── */
QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS["bg_secondary"]};
    width: 4px;
    border-radius: 0px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["border_bright"]};
    border-radius: 0px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["accent"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {COLORS["bg_secondary"]};
    height: 4px;
    border-radius: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS["border_bright"]};
    border-radius: 0px;
    min-width: 30px;
}}

/* ── TabWidget ────────────────────────────────────────────────── */
QTabWidget::pane {{
    background: {COLORS["bg_primary"]};
    border: 1px solid {COLORS["border"]};
    border-top: none;
    border-radius: 0px;
}}

QTabBar::tab {{
    background: {COLORS["bg_secondary"]};
    color: {COLORS["text_muted"]};
    border: 1px solid {COLORS["border"]};
    border-bottom: none;
    border-radius: 0px;
    padding: 8px 20px;
    margin-right: 1px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QTabBar::tab:selected {{
    background: {COLORS["bg_primary"]};
    color: {COLORS["accent"]};
    border-top: 2px solid {COLORS["accent"]};
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background: {COLORS["bg_card"]};
    color: {COLORS["text_secondary"]};
}}

/* ── Dialog ───────────────────────────────────────────────────── */
QDialog {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
}}

/* ── Menu ─────────────────────────────────────────────────────── */
QMenu {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    padding: 2px;
}}

QMenu::item {{
    padding: 7px 20px;
    font-size: 12px;
    letter-spacing: 1px;
}}

QMenu::item:selected {{
    background-color: {COLORS["accent"]};
    color: {COLORS["bg_primary"]};
}}

QMenu::separator {{
    height: 1px;
    background: {COLORS["border"]};
    margin: 2px 0;
}}

/* ── ListWidget ───────────────────────────────────────────────── */
QListWidget {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 0px;
    padding: 2px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 0px;
    margin: 1px;
}}

QListWidget::item:selected {{
    background-color: {COLORS["accent"]};
    color: {COLORS["bg_primary"]};
}}

QListWidget::item:hover:!selected {{
    background-color: {COLORS["bg_card_hover"]};
    border-left: 2px solid {COLORS["accent"]};
}}

/* ── ProgressBar ──────────────────────────────────────────────── */
QProgressBar {{
    background-color: {COLORS["bg_input"]};
    border: none;
    border-radius: 0px;
    height: 8px;
    text-align: center;
    font-size: 9px;
    color: transparent;
}}

QProgressBar::chunk {{
    border-radius: 0px;
    background: {COLORS["accent"]};
}}

/* ── ToolTip ──────────────────────────────────────────────────── */
QToolTip {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_bright"]};
    border-radius: 0px;
    padding: 5px 8px;
    font-size: 11px;
}}

/* ── StatusBar ────────────────────────────────────────────────── */
QStatusBar {{
    background: {COLORS["bg_secondary"]};
    color: {COLORS["text_muted"]};
    border-top: 1px solid {COLORS["border"]};
    font-size: 10px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    letter-spacing: 1px;
    padding: 2px;
}}

/* ── Custom frames ────────────────────────────────────────────── */
QFrame#cardFrame {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-left: 3px solid {COLORS["border_bright"]};
    border-radius: 0px;
}}

QFrame#activeCardFrame {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border_bright"]};
    border-left: 3px solid {COLORS["accent_active"]};
    border-radius: 0px;
}}

QPushButton#profileAddButton {{
    background: transparent;
    border: 1px dashed {COLORS["border_bright"]};
    color: {COLORS["text_muted"]};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-align: left;
    padding-left: 16px;
    text-transform: uppercase;
    border-radius: 0px;
}}

QPushButton#profileAddButton:hover {{
    border-color: {COLORS["accent"]};
    color: {COLORS["accent"]};
    background: rgba(68, 136, 255, 0.04);
}}

QFrame#overloadFrame {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-left: 3px solid {COLORS["accent"]};
    border-radius: 0px;
    padding: 14px;
}}

QFrame#separator {{
    background-color: {COLORS["border"]};
    max-height: 1px;
}}
"""
