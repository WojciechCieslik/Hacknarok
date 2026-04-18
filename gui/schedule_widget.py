"""
WeeklyCalendarWidget – wizualny harmonogram tygodniowy.

Kliknij i przeciągnij na kolumnie dnia aby wybrać przedział czasowy,
następnie przypisz profil do tego przedziału.
"""

from datetime import datetime

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QCursor
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QDialog, QComboBox, QPushButton, QFrame, QMenu, QSizePolicy
)

from core.scheduler import Scheduler, ScheduleBlock, DAY_NAMES


# ─── Stałe siatki ────────────────────────────────────────────────────

SLOTS = 48          # 30-minutowych slotów (0..47 → 00:00..23:30)
SLOT_H = 26         # pikseli na slot
TIME_W = 54         # szerokość kolumny z godzinami
HEAD_H = 32         # wysokość nagłówka z dniami


def _slot_to_hm(slot: int) -> tuple[int, int]:
    return slot // 2, (slot % 2) * 30


def _hm_to_slot(hour: int, minute: int) -> int:
    return hour * 2 + (1 if minute >= 30 else 0)


def _hex_to_qcolor(hex_color: str, alpha: int = 255) -> QColor:
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return QColor(r, g, b, alpha)
    return QColor(hex_color)


# ─── Dialog przypisania profilu ───────────────────────────────────────

class BlockAssignDialog(QDialog):
    """Dialog wyboru profilu dla zaznaczonego przedziału czasu."""

    def __init__(self, day: int, slot_start: int, slot_end: int,
                 scheduler: Scheduler, profile_names: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Przypisz profil")
        self.setFixedSize(340, 190)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )

        self._day = day
        self._slot_start = slot_start
        self._slot_end = slot_end
        self._scheduler = scheduler

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Ramka
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border: 2px solid #7c3aed;
                border-radius: 12px;
            }
        """)
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(12)

        # Tytuł
        h_start, m_start = _slot_to_hm(slot_start)
        h_end, m_end = _slot_to_hm(slot_end)
        title = QLabel(
            f"📅  {DAY_NAMES[day]}  "
            f"{h_start:02d}:{m_start:02d} – {h_end:02d}:{m_end:02d}"
        )
        title.setStyleSheet(
            "color: #f1f5f9; font-size: 14px; font-weight: bold; border: none;"
        )
        fl.addWidget(title)

        # Combo z profilami
        self._combo = QComboBox()
        for name in profile_names:
            self._combo.addItem(name)
        fl.addWidget(self._combo)

        # Przyciski
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        btn_row.addStretch()

        save_btn = QPushButton("✓  Zapisz")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        fl.addLayout(btn_row)
        root.addWidget(frame)

    def _save(self):
        profile_name = self._combo.currentText()
        if not profile_name:
            self.reject()
            return

        h_start, m_start = _slot_to_hm(self._slot_start)
        h_end, m_end = _slot_to_hm(self._slot_end)

        # Usuń nakładające się bloki tego samego dnia
        self._scheduler.blocks = [
            b for b in self._scheduler.blocks
            if not (
                b.day == self._day
                and b.start_hour * 60 + b.start_min < h_end * 60 + m_end
                and b.end_hour * 60 + b.end_min > h_start * 60 + m_start
            )
        ]

        block = ScheduleBlock(
            day=self._day,
            start_hour=h_start, start_min=m_start,
            end_hour=h_end, end_min=m_end,
            profile_name=profile_name,
        )
        self._scheduler.add_block(block)
        self.accept()


# ─── Siatka kalendarza ────────────────────────────────────────────────

class CalendarGrid(QWidget):
    """Rysowalny widget siatki tygodniowej 7×48."""

    def __init__(self, scheduler: Scheduler, profile_names: list[str], parent=None):
        super().__init__(parent)
        self.scheduler = scheduler
        self.profile_names = profile_names
        self._profile_colors: dict[str, str] = {}

        self._drag_start: tuple[int, int] | None = None  # (day, slot)
        self._drag_end: tuple[int, int] | None = None
        self._drag_day: int = -1

        total_h = HEAD_H + SLOTS * SLOT_H
        self.setMinimumHeight(total_h)
        self.setMinimumWidth(TIME_W + 7 * 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setMouseTracking(True)

    def update_profile_colors(self, colors: dict[str, str]):
        self._profile_colors = colors
        self.update()

    # ── Obliczenia pozycji ────────────────────────────────────────

    def _col_width(self) -> int:
        return max(80, (self.width() - TIME_W) // 7)

    def _pos_to_cell(self, x: int, y: int) -> tuple[int, int] | None:
        if y < HEAD_H or x < TIME_W:
            return None
        col_w = self._col_width()
        day = (x - TIME_W) // col_w
        slot = (y - HEAD_H) // SLOT_H
        if 0 <= day < 7 and 0 <= slot < SLOTS:
            return day, slot
        return None

    def _find_block_at(self, day: int, slot: int) -> int | None:
        """Zwróć indeks bloku obejmującego dany slot lub None."""
        h, m = _slot_to_hm(slot)
        mins = h * 60 + m
        for i, b in enumerate(self.scheduler.blocks):
            if b.day == day:
                start_m = b.start_hour * 60 + b.start_min
                end_m = b.end_hour * 60 + b.end_min
                if start_m <= mins < end_m:
                    return i
        return None

    # ── Rysowanie ─────────────────────────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        col_w = self._col_width()
        total_w = TIME_W + 7 * col_w
        total_h = HEAD_H + SLOTS * SLOT_H
        today = datetime.now().weekday()

        # ── Tło ──
        painter.fillRect(0, 0, total_w, total_h, QColor("#0f172a"))

        # ── Nagłówek dni ──
        for d in range(7):
            x = TIME_W + d * col_w
            is_today = d == today
            bg = QColor("#7c3aed") if is_today else QColor("#1a2332")
            painter.fillRect(x + 1, 1, col_w - 2, HEAD_H - 2, bg)
            painter.setPen(QColor("#ffffff" if is_today else "#94a3b8"))
            f = QFont("Segoe UI", 10)
            f.setBold(is_today)
            painter.setFont(f)
            painter.drawText(
                x, 0, col_w, HEAD_H,
                Qt.AlignmentFlag.AlignCenter,
                DAY_NAMES[d],
            )

        # ── Linie siatki i etykiety godzin ──
        for slot in range(SLOTS + 1):
            y = HEAD_H + slot * SLOT_H
            h, m = _slot_to_hm(slot)

            if slot < SLOTS:
                pen_color = "#1e293b" if m == 0 else "#141f2e"
                painter.setPen(QPen(QColor(pen_color), 1))
                painter.drawLine(TIME_W, y, total_w, y)

            if m == 0:
                painter.setPen(QColor("#475569"))
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(
                    2, y, TIME_W - 6, SLOT_H,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    f"{h:02d}:00",
                )

        # Linia bieżącego czasu
        now = datetime.now()
        if now.weekday() < 7:
            current_slot_frac = now.hour * 2 + now.minute / 30.0
            y_now = int(HEAD_H + current_slot_frac * SLOT_H)
            x_now = TIME_W + now.weekday() * col_w
            pen = QPen(QColor("#ef4444"), 2)
            painter.setPen(pen)
            painter.drawLine(x_now, y_now, x_now + col_w, y_now)
            # Kółko na lewej krawędzi
            painter.setBrush(QColor("#ef4444"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x_now - 4, y_now - 4, 8, 8)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # reset – bez tego brush=czerwony zabarwia bloki

        # ── Pionowe linie kolumn ──
        painter.setPen(QPen(QColor("#1e293b"), 1))
        for d in range(8):
            x = TIME_W + d * col_w
            painter.drawLine(x, 0, x, total_h)

        # ── Bloki profili ──
        for block in self.scheduler.blocks:
            if not block.enabled:
                continue
            start_slot = _hm_to_slot(block.start_hour, block.start_min)
            end_slot = _hm_to_slot(block.end_hour, block.end_min)
            if end_slot <= start_slot:
                continue

            x = TIME_W + block.day * col_w + 2
            y = HEAD_H + start_slot * SLOT_H + 1
            bw = col_w - 4
            bh = (end_slot - start_slot) * SLOT_H - 2

            color_hex = self._profile_colors.get(block.profile_name, "#7c3aed")
            fill = _hex_to_qcolor(color_hex, 160)
            border = _hex_to_qcolor(color_hex, 230)

            # setBrush przed drawRect – inaczej Qt używa poprzedniego brush do wypełnienia
            painter.setBrush(fill)
            painter.setPen(QPen(border, 1))
            painter.drawRect(x, y, bw - 1, bh - 1)

            # Nazwa profilu
            painter.setPen(QColor("#ffffff"))
            f = QFont("Segoe UI", 8)
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(
                x + 4, y + 2, bw - 8, bh - 4,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                block.profile_name,
            )

        # ── Zaznaczenie przeciągania ──
        if self._drag_start and self._drag_end and self._drag_day >= 0:
            d = self._drag_day
            s1, s2 = self._drag_start[1], self._drag_end[1]
            slot_min, slot_max = min(s1, s2), max(s1, s2) + 1

            x = TIME_W + d * col_w + 1
            y = HEAD_H + slot_min * SLOT_H
            sw = col_w - 2
            sh = (slot_max - slot_min) * SLOT_H

            painter.fillRect(x, y, sw, sh, QColor(124, 58, 237, 70))
            painter.setPen(QPen(QColor("#7c3aed"), 2))
            painter.drawRect(x, y, sw - 1, sh - 1)

        painter.end()

    # ── Zdarzenia myszy ───────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            cell = self._pos_to_cell(event.pos().x(), event.pos().y())
            if cell:
                self._drag_start = cell
                self._drag_end = cell
                self._drag_day = cell[0]
                self.update()

        elif event.button() == Qt.MouseButton.RightButton:
            cell = self._pos_to_cell(event.pos().x(), event.pos().y())
            if cell:
                idx = self._find_block_at(*cell)
                if idx is not None:
                    self._show_block_menu(idx, event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self._drag_start and (event.buttons() & Qt.MouseButton.LeftButton):
            cell = self._pos_to_cell(event.pos().x(), event.pos().y())
            if cell and cell[0] == self._drag_day:
                self._drag_end = cell
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_start:
            if self._drag_end:
                self._show_assign_dialog()
            self._drag_start = None
            self._drag_end = None
            self._drag_day = -1
            self.update()

    def _show_assign_dialog(self):
        if not self.profile_names:
            return
        s1, s2 = self._drag_start[1], self._drag_end[1]
        slot_start = min(s1, s2)
        slot_end = max(s1, s2) + 1   # slot_end = pierwszy slot PO bloku
        dlg = BlockAssignDialog(
            day=self._drag_day,
            slot_start=slot_start,
            slot_end=slot_end,
            scheduler=self.scheduler,
            profile_names=self.profile_names,
            parent=self,
        )
        # Wycentruj dialog względem zaznaczenia
        col_w = self._col_width()
        gx = self.mapToGlobal(self.rect().topLeft()).x()
        gy = self.mapToGlobal(self.rect().topLeft()).y()
        dx = gx + TIME_W + self._drag_day * col_w + col_w // 2 - 170
        dy = gy + HEAD_H + slot_start * SLOT_H - 20
        dlg.move(dx, dy)
        dlg.exec()
        self.update()

    def _show_block_menu(self, block_idx: int, global_pos):
        block = self.scheduler.blocks[block_idx]
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1e293b; border: 1px solid #334155; border-radius: 8px; }
            QMenu::item { color: #f1f5f9; padding: 8px 20px; }
            QMenu::item:selected { background: #7c3aed; }
        """)
        del_act = menu.addAction(
            f"🗑️  Usuń  '{block.profile_name}'"
            f"  ({block.start_str()}–{block.end_str()})"
        )
        action = menu.exec(global_pos)
        if action == del_act:
            self.scheduler.remove_block(block_idx)
            self.update()


# ─── Główny widget harmonogramu ───────────────────────────────────────

class WeeklyCalendarWidget(QWidget):
    """Wizualny harmonogram tygodniowy."""

    def __init__(self, scheduler: Scheduler, profile_names: list[str], parent=None):
        super().__init__(parent)
        self.scheduler = scheduler

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Nagłówek ──
        header = QHBoxLayout()
        title = QLabel("📅  Harmonogram tygodniowy")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        hint = QLabel("Przeciągnij na dniu aby dodać blok  ·  PPM na bloku aby usunąć")
        hint.setStyleSheet("color: #475569; font-size: 11px;")
        header.addWidget(hint)
        layout.addLayout(header)

        # ── Scroll area z siatką ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; }")

        self._grid = CalendarGrid(scheduler, profile_names)
        self._scroll.setWidget(self._grid)
        layout.addWidget(self._scroll, 1)

        # Przewiń do teraźniejszości po wyrenderowaniu layoutu
        QTimer.singleShot(80, self.scroll_to_now)

    def scroll_to_now(self):
        """Przewiń tak, aby bieżąca godzina była widoczna na środku ekranu."""
        now = datetime.now()
        y_now = HEAD_H + int((now.hour * 2 + now.minute / 30.0) * SLOT_H)
        viewport_h = self._scroll.viewport().height()
        target = max(0, y_now - viewport_h // 2)
        self._scroll.verticalScrollBar().setValue(target)

    def update_profile_names(self, names: list[str]):
        self._grid.profile_names = names
        self._grid.update()

    def update_profile_colors(self, colors: dict[str, str]):
        self._grid.update_profile_colors(colors)
