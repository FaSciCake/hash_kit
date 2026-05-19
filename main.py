import hashlib
import sys
import os
from PySide6.QtGui import QIcon
from pathlib import Path
from typing import Optional, List, Dict
from PySide6.QtCore import (
    QThread, Signal, Qt, QMutex, QMutexLocker,
    QTimer, QUrl
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit,
    QCheckBox, QFileDialog, QGroupBox, QListWidget,
    QListWidgetItem, QSizePolicy, QAbstractItemView, QFrame, QToolTip,
    QTabWidget, QMessageBox
)
from PySide6.QtGui import (
    QTextCursor, QDragEnterEvent, QDropEvent,
    QColor, QPalette, QDesktopServices
)

# docxtpl imports
from datetime import datetime
from docxtpl import DocxTemplate
import traceback

# ─── Light palette forced for all OS modes ────────────────────────────────────
LIGHT_STYLESHEET = """
QMainWindow {
    background-color: #f5f6fa;
}
QWidget {
    color: #2d2d2d;
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #dde1ea;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: 600;
    color: #444;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #666;
}

QPushButton {
    background-color: #ffffff;
    color: #2d2d2d;
    border: 1px solid #d0d5e0;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #eef2ff;
    border-color: #aab8f5;
}
QPushButton:pressed {
    background-color: #dde5ff;
}
QPushButton:disabled {
    background-color: #f0f0f0;
    color: #aaaaaa;
    border-color: #e0e0e0;
}

QPushButton#primaryBtn {
    background-color: #4a6cf7;
    color: white;
    border: none;
    font-weight: 600;
    padding: 6px 20px;
}
QPushButton#primaryBtn:hover {
    background-color: #3d5ee8;
}
QPushButton#primaryBtn:disabled {
    background-color: #c5cdf7;
    color: #eef0ff;
}

QPushButton#dangerBtn {
    background-color: #fff0f0;
    color: #e53e3e;
    border: 1px solid #fcc;
}
QPushButton#dangerBtn:hover {
    background-color: #ffe0e0;
}

QListWidget {
    background-color: #ffffff;
    border: 1px solid #dde1ea;
    border-radius: 8px;
    outline: none;
}
QListWidget::item {
    padding: 0px;
    border: none;
}
QListWidget::item:selected {
    background: transparent;
}

QTextEdit {
    background-color: #1e2030;
    color: #c0caf5;
    border: 1px solid #3d4166;
    border-radius: 8px;
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    padding: 6px;
}

QProgressBar {
    background-color: #e8eaf6;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #4a6cf7;
    border-radius: 4px;
}

QCheckBox {
    spacing: 6px;
    color: #444;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #c0c8e0;
    border-radius: 4px;
    background: white;
}
QCheckBox::indicator:checked {
    background-color: #4a6cf7;
    border-color: #4a6cf7;
    image: none;
}

QLabel {
    color: #444;
    background: transparent;
}

QScrollBar:vertical {
    background: #f0f2f8;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #c8cedf;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QStatusBar {
    background-color: #eef0f8;
    color: #666;
    border-top: 1px solid #dde1ea;
    font-size: 11px;
    padding: 2px 8px;
}

QToolTip {
    background-color: #ffffff;
    color: #2d2d2d;
    border: 1px solid #c8cfe0;
    border-radius: 5px;
    padding: 4px 8px;
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
    font-weight: normal;
    opacity: 240;
}
"""


def apply_light_palette(app: QApplication):
    """
    Force light palette regardless of OS dark/light mode.

    Key insight: Qt tooltips use the *Inactive* color group of QPalette,
    not Active. Windows 11 dark mode sets Inactive.ToolTipBase and
    Inactive.ToolTipText to dark values, which is why all our previous
    attempts failed — we were only setting the Active group.
    We must set both groups, AND call QToolTip.setPalette() which is the
    global static override that actually wins over the native style.
    """
    pal = QPalette()

    # ── Active group (normal widget colors) ───────────────────────────────
    for group in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
        pal.setColor(group, QPalette.Window, QColor("#f5f6fa"))
        pal.setColor(group, QPalette.WindowText, QColor("#2d2d2d"))
        pal.setColor(group, QPalette.Base, QColor("#ffffff"))
        pal.setColor(group, QPalette.AlternateBase, QColor("#f0f2f8"))
        pal.setColor(group, QPalette.Text, QColor("#2d2d2d"))
        pal.setColor(group, QPalette.Button, QColor("#ffffff"))
        pal.setColor(group, QPalette.ButtonText, QColor("#2d2d2d"))
        pal.setColor(group, QPalette.BrightText, QColor("#ff0000"))
        pal.setColor(group, QPalette.Link, QColor("#4a6cf7"))
        pal.setColor(group, QPalette.Highlight, QColor("#4a6cf7"))
        pal.setColor(group, QPalette.HighlightedText, QColor("#ffffff"))
        # Tooltip colors must be set on every group — Qt picks Inactive for tooltips
        pal.setColor(group, QPalette.ToolTipBase, QColor("#ffffff"))
        pal.setColor(group, QPalette.ToolTipText, QColor("#2d2d2d"))

    # Disabled overrides
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor("#aaaaaa"))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#aaaaaa"))
    pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#aaaaaa"))

    app.setPalette(pal)

    # ── QToolTip global static palette ────────────────────────────────────
    # This is the authoritative override. QToolTip renders using its own
    # static palette, independent of widget palettes. Setting it here beats
    # the Windows 11 native dark style unconditionally.
    tip_pal = QPalette()
    for group in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
        tip_pal.setColor(group, QPalette.ToolTipBase, QColor("#ffffff"))
        tip_pal.setColor(group, QPalette.ToolTipText, QColor("#2d2d2d"))
        tip_pal.setColor(group, QPalette.Window, QColor("#ffffff"))
        tip_pal.setColor(group, QPalette.WindowText, QColor("#2d2d2d"))
        tip_pal.setColor(group, QPalette.Text, QColor("#2d2d2d"))
    QToolTip.setPalette(tip_pal)


# ─── Hash worker ──────────────────────────────────────────────────────────────
class HashWorker(QThread):
    file_started = Signal(str)
    file_progress = Signal(int, int)
    file_result = Signal(str, str, str)  # path, md5, sha256
    file_error = Signal(str, str)
    finished = Signal(int, int)
    cancelled = Signal()

    def __init__(self, file_list: List[Path], compute_md5: bool, compute_sha256: bool):
        super().__init__()
        self.file_list = file_list
        self.compute_md5 = compute_md5
        self.compute_sha256 = compute_sha256
        self._is_cancelled = False
        self._mutex = QMutex()

    def cancel(self):
        with QMutexLocker(self._mutex):
            self._is_cancelled = True

    def _cancelled(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._is_cancelled

    def _hash_file(self, file_path: Path, algorithm: str) -> str:
        h = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                if self._cancelled():
                    raise InterruptedError()
                h.update(chunk)
        return h.hexdigest()

    def run(self):
        total = len(self.file_list)
        errors = 0
        for idx, fp in enumerate(self.file_list, 1):
            if self._cancelled():
                self.cancelled.emit()
                return
            self.file_progress.emit(idx, total)
            self.file_started.emit(str(fp))
            md5 = sha256 = ""
            try:
                if self.compute_md5:
                    md5 = self._hash_file(fp, 'md5').upper()
                if self.compute_sha256:
                    sha256 = self._hash_file(fp, 'sha256').upper()
                self.file_result.emit(str(fp), md5, sha256)
            except InterruptedError:
                self.cancelled.emit()
                return
            except Exception as e:
                errors += 1
                self.file_error.emit(str(fp), str(e))
                self.file_result.emit(str(fp), "ERROR", "ERROR")
        self.finished.emit(total, errors)


# ─── Report worker (docxtpl) ─────────────────────────────────────────────────
class ReportWorker(QThread):
    finished = Signal(str)   # output path
    error = Signal(str)

    def __init__(self, template_path: Path, output_path: Path, context: dict):
        super().__init__()
        self.template_path = template_path
        self.output_path = output_path
        self.context = context

    def run(self):
        try:
            doc = DocxTemplate(self.template_path)
            doc.render(self.context)
            doc.save(self.output_path)
            self.finished.emit(str(self.output_path))
        except Exception as e:
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")


# ─── File row widget ───────────────────────────────────────────────────────────
class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(0)
        self.setWordWrap(False)
        self.setTextFormat(Qt.PlainText)

    def set_full_text(self, text: str):
        self._full_text = text
        self._update_elided_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided_text()

    def _update_elided_text(self):
        fm = self.fontMetrics()
        available_width = self.width() - 2
        elided = fm.elidedText(self._full_text, Qt.ElideRight, available_width)
        self.setText(elided)


class FileRowWidget(QFrame):
    """
    Expanded state  : number | icon | name | [collapse] [remove]
                      ── unified hash block (click → copies both MD5+SHA256)
    Collapsed state : number | icon | name | [expand] [remove]   (single line)

    Copy interactions:
      • click filename label    → flash → copy filename
      • click hash block        → flash → copy "MD5: xxx\nSHA256: yyy"
      • when BOTH copied        → 2s sweep animation → auto-collapse
    """
    remove_requested = Signal(object)

    # zebra colours
    _BG_ODD = "#ffffff"
    _BG_EVEN = "#f7f8fc"
    _BG_COLLAPSED_ODD = "#edf0f8"
    _BG_COLLAPSED_EVEN = "#e6eaf5"

    def __init__(self, file_path: Path, index: int, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.index = index
        self.md5 = ""
        self.sha256 = ""
        self.hashes_ready = False
        self._name_copied = False
        self._hash_copied = False
        self._is_collapsed = False
        self._sweep_timer = None
        self._flash_timers: List[QTimer] = []
        # reference back to the QListWidgetItem so we can update sizeHint
        self._list_item: Optional[QListWidgetItem] = None

        self.setAutoFillBackground(True)
        self.setObjectName("fileRow")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(0)
        self._apply_row_bg()
        self._init_ui()

    # ── background helper ──────────────────────────────────────────────────
    def _apply_row_bg(self, collapsed: Optional[bool] = None):
        """Set zebra background via stylesheet (beats global QWidget rule)."""
        if collapsed is None:
            collapsed = self._is_collapsed
        is_even = (self.index % 2 == 0)
        if collapsed:
            color = self._BG_COLLAPSED_EVEN if is_even else self._BG_COLLAPSED_ODD
        else:
            color = self._BG_EVEN if is_even else self._BG_ODD

        # Use the frame objectName selector so child widgets are NOT affected
        # by this rule — they inherit transparent backgrounds from their own styles.
        self.setStyleSheet(f"QFrame#fileRow {{ background-color: {color}; }}")

    # ── UI construction ────────────────────────────────────────────────────
    def _init_ui(self):
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(8, 6, 8, 6)
        self._outer.setSpacing(4)

        # ── Top row ────────────────────────────────────────────────────────
        self._top_row = QHBoxLayout()
        self._top_row.setSpacing(8)

        self._num_lbl = QLabel(f"{self.index}.")
        self._num_lbl.setFixedWidth(28)
        self._num_lbl.setStyleSheet("color:#999; font-size:11px; background:transparent;")
        self._top_row.addWidget(self._num_lbl)

        self._icon_lbl = QLabel(self._file_icon())
        self._icon_lbl.setFixedWidth(22)
        self._icon_lbl.setStyleSheet("background:transparent;")
        self._top_row.addWidget(self._icon_lbl)

        # Clickable filename label
        self._name_lbl = ElidedLabel(self.file_path.name)
        self._name_lbl.setToolTip(str(self.file_path))
        self._name_lbl.setCursor(Qt.PointingHandCursor)
        self._name_lbl.setStyleSheet(
            "font-weight: 500; padding: 2px 0;"
        )
        self._name_lbl.mousePressEvent = lambda e: self._on_copy_name()
        self._top_row.addWidget(self._name_lbl)

        # Collapse / expand button
        self._toggle_btn = self._make_icon_btn("▲", "Свернуть")
        self._toggle_btn.clicked.connect(self._on_toggle)
        self._top_row.addWidget(self._toggle_btn)

        # Remove button
        self._remove_btn = self._make_icon_btn("✕", "Удалить")
        self._remove_btn.setObjectName("dangerBtn")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        self._top_row.addWidget(self._remove_btn)

        self._outer.addLayout(self._top_row)

        # ── Hash block – single clickable widget, two lines ────────────────
        self._hash_frame = QWidget()
        self._hash_frame.setObjectName("hashFrame")
        self._hash_frame.setStyleSheet("QWidget#hashFrame { background: transparent; }")
        self._hash_frame.setCursor(Qt.PointingHandCursor)
        self._hash_frame.setToolTip("Нажмите, чтобы скопировать MD5 + SHA256")
        self._hash_frame.mousePressEvent = lambda e: self._on_copy_hashes()

        hash_layout = QVBoxLayout(self._hash_frame)
        hash_layout.setContentsMargins(52, 2, 8, 2)
        hash_layout.setSpacing(2)

        mono_style = (
            "font-family: 'Consolas','JetBrains Mono','Courier New',monospace;"
            "font-size: 11px; color: #555; padding: 1px 4px;"
            "background: transparent;"
        )

        self._md5_lbl = QLabel("MD5  —")
        self._sha256_lbl = QLabel("SHA256  —")
        for lbl in (self._md5_lbl, self._sha256_lbl):
            lbl.setStyleSheet(mono_style)
            lbl.setWordWrap(False)
            # forward mouse press to parent block handler
            lbl.mousePressEvent = lambda e: self._on_copy_hashes()

        hash_layout.addWidget(self._md5_lbl)
        hash_layout.addWidget(self._sha256_lbl)
        self._outer.addWidget(self._hash_frame)

    def _make_icon_btn(self, text: str, tip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(28, 28)
        btn.setToolTip(tip)
        # Must override padding/font-size inline — the global sheet's
        # padding:5px 14px clips content in these small 28×28 buttons.
        # Hover/pressed colors are re-declared here so they aren't lost.
        btn.setStyleSheet(
            "QPushButton         { padding: 0px; font-size: 13px; border-radius: 5px; }"
            "QPushButton:hover   { background-color: #eef2ff; border-color: #aab8f5; }"
            "QPushButton:pressed { background-color: #dde5ff; }"
        )
        return btn

    # ── File icon ──────────────────────────────────────────────────────────
    def _file_icon(self) -> str:
        ext = self.file_path.suffix.lower()
        icons = {
            frozenset(['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']): "🖼️",
            frozenset(['.mp4', '.mkv', '.avi', '.mov', '.wmv']): "🎬",
            frozenset(['.mp3', '.wav', '.flac', '.ogg', '.aac']): "🎵",
            frozenset(['.pdf']): "📄",
            frozenset(['.doc', '.docx']): "📝",
            frozenset(['.zip', '.rar', '.7z', '.tar', '.gz', '.xz']): "🗜️",
            frozenset(['.exe', '.msi', '.dmg', '.deb']): "⚙️",
            frozenset(['.py', '.js', '.ts', '.html', '.css', '.cpp', '.c', '.rs']): "💻",
            frozenset(['.xls', '.xlsx', '.csv']): "📊",
        }
        for ext_set, icon in icons.items():
            if ext in ext_set:
                return icon
        return "📁"

    # ── Hash population ────────────────────────────────────────────────────
    def set_hashes(self, md5: str, sha256: str):
        self.md5 = md5.upper() if md5 not in ("", "ERROR") else md5
        self.sha256 = sha256.upper() if sha256 not in ("", "ERROR") else sha256
        self.hashes_ready = True

        self._md5_lbl.setText(
            f"<span style='color:#999;font-size:10px'>MD5&nbsp;&nbsp;&nbsp;</span>"
            f"&nbsp;{self._fmt(self.md5)}"
        )
        self._sha256_lbl.setText(
            f"<span style='color:#999;font-size:10px'>SHA256</span>"
            f"&nbsp;{self._fmt(self.sha256)}"
        )
        self._md5_lbl.setTextFormat(Qt.RichText)
        self._sha256_lbl.setTextFormat(Qt.RichText)

        # Reset copy state only if not already collapsed
        if not self._is_collapsed:
            self._name_copied = False
            self._hash_copied = False

        # Always refresh the list item size after content change
        self._refresh_item_size()

    def _fmt(self, val: str) -> str:
        if val == "ERROR":
            return "<span style='color:#e53e3e'>ERROR</span>"
        if not val:
            return "<span style='color:#bbb'>—</span>"
        return f"<span style='color:#2a2a3a;font-weight:500'>{val}</span>"

    # ── Size hint refresh ──────────────────────────────────────────────────
    def _refresh_item_size(self):
        """Tell the QListWidget to recalculate this item's height."""
        if self._list_item is not None:
            self._list_item.setSizeHint(self.sizeHint())

    # ── Copy interactions ──────────────────────────────────────────────────
    def _on_copy_name(self):
        # No interaction when row is collapsed
        if self._is_collapsed:
            return
        QApplication.clipboard().setText(self.file_path.name)
        self._flash_widget(self._name_lbl)
        self._name_copied = True
        self._check_both_copied()

    def _on_copy_hashes(self):
        """Copy both MD5 and SHA256 together as formatted text."""
        if not self.hashes_ready:
            return
        if self.md5 in ("", "ERROR") and self.sha256 in ("", "ERROR"):
            return
        text = f"MD5: {self.md5}\nSHA256: {self.sha256}"
        QApplication.clipboard().setText(text)
        self._flash_widget(self._hash_frame)
        self._hash_copied = True
        self._check_both_copied()

    def _flash_widget(self, widget, duration_ms: int = 500):
        """Brief blue background flash on the given widget."""
        if widget is self._hash_frame:
            # _hash_frame uses a scoped stylesheet — override it fully for flash
            flash_ss = "QWidget#hashFrame { background-color: #c8d9ff; border-radius: 4px; }"
            restore_ss = "QWidget#hashFrame { background: transparent; }"
            widget.setStyleSheet(flash_ss)
            t = QTimer(self)
            t.setSingleShot(True)
            t.timeout.connect(lambda: widget.setStyleSheet(restore_ss))
            t.start(duration_ms)
        else:
            orig_ss = widget.styleSheet()
            widget.setStyleSheet(orig_ss + " background-color: #c8d9ff; border-radius: 4px;")
            t = QTimer(self)
            t.setSingleShot(True)
            t.timeout.connect(lambda: widget.setStyleSheet(orig_ss))
            t.start(duration_ms)
        self._flash_timers.append(t)

    def _check_both_copied(self):
        # Guard: never start sweep if the row is already collapsed
        if self._is_collapsed:
            return
        if self._name_copied and self._hash_copied:
            self._start_sweep_collapse()

    # ── Sweep-then-collapse animation ─────────────────────────────────────
    def _start_sweep_collapse(self):
        """0.75-seconds right-to-left blue sweep, then collapse."""
        if self._sweep_timer and self._sweep_timer.isActive():
            return
        self._sweep_step = 0
        self._sweep_total = 50  # 50 × 15ms = 0.75 s
        self._sweep_timer = QTimer(self)
        self._sweep_timer.setInterval(15)
        self._sweep_timer.timeout.connect(self._sweep_tick)
        self._sweep_timer.start()

    def _sweep_tick(self):
        step = self._sweep_step
        total = self._sweep_total
        if step > total:
            self._sweep_timer.stop()
            self._do_collapse()
            return

        progress = step / total  # 0.0 → 1.0  (sweep moves left)
        color_lit = "#c8d9ff"  # used to be "#b8cdff"
        # maintain current zebra base so the sweep overlays cleanly
        if self._is_collapsed:
            # shouldn't happen, but fallback
            color_base = self._BG_COLLAPSED_ODD
        else:
            is_even = (self.index % 2 == 0)
            color_base = self._BG_EVEN if is_even else self._BG_ODD

        if progress <= 0:
            bg = f"background-color: {color_base};"
        elif progress >= 1.0:
            bg = f"background-color: {color_lit};"
        else:
            edge = min(progress + 0.06, 1.0)
            bg = (
                f"background: qlineargradient("
                f"x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {color_lit},"
                f"stop:{progress:.3f} {color_lit},"
                f"stop:{edge:.3f} {color_base},"
                f"stop:1 {color_base});"
            )

        self.setStyleSheet(f"QFrame#fileRow {{ {bg} }}")
        self._sweep_step += 1

    def _do_collapse(self):
        self.setStyleSheet("")  # clear sweep stylesheet
        self._set_collapsed(True)

    # ── Toggle expand/collapse ─────────────────────────────────────────────
    def _on_toggle(self):
        self._set_collapsed(not self._is_collapsed)

    def _set_collapsed(self, collapsed: bool):
        # Cancel any running sweep animation
        if self._sweep_timer and self._sweep_timer.isActive():
            self._sweep_timer.stop()
            self._sweep_timer = None

        self._is_collapsed = collapsed
        self._hash_frame.setVisible(not collapsed)
        if collapsed:
            self._toggle_btn.setText("▼")
            self._toggle_btn.setToolTip("Развернуть")
            self._name_lbl.setStyleSheet(
                "font-weight: 500; color: #8090b0; padding: 2px 0; background: transparent;"
            )
            # Disable pointer cursor and tooltip — no interaction in collapsed state
            self._name_lbl.setCursor(Qt.ArrowCursor)
            self._name_lbl.setToolTip("")
            # Reset copy flags so a filename click won't trigger sweep
            self._name_copied = False
            self._hash_copied = False
        else:
            self._toggle_btn.setText("▲")
            self._toggle_btn.setToolTip("Свернуть")
            self._name_lbl.setStyleSheet(
                "font-weight: 500; color: #2d2d2d; padding: 2px 0; background: transparent;"
            )
            # Restore pointer cursor and full path tooltip
            self._name_lbl.setCursor(Qt.PointingHandCursor)
            self._name_lbl.setToolTip(str(self.file_path))
            # Reset copy state on re-expand so sweep can trigger again
            self._name_copied = False
            self._hash_copied = False

        self._apply_row_bg(collapsed)
        # Critical: update item height so QListWidget allocates correct space
        self._refresh_item_size()

    # ── Helpers ────────────────────────────────────────────────────────────
    def update_index(self, idx: int):
        self.index = idx
        self._num_lbl.setText(f"{idx}.")
        self._apply_row_bg()  # re‑apply zebra stripes after renumbering


# ─── Main window with tabs ────────────────────────────────────────────────────
class HashKitWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: Optional[HashWorker] = None
        self.report_worker: Optional[ReportWorker] = None
        self.file_rows: Dict[str, FileRowWidget] = {}
        self.file_paths: List[Path] = []
        self.compute_md5 = True
        self.compute_sha256 = True
        self._log_lines: List[str] = []
        self.template_path: Optional[Path] = None
        self._init_ui()
        self.setAcceptDrops(True)

    # ── UI construction ────────────────────────────────────────────────────
    def _init_ui(self):
        self.setWindowTitle("HashKit")
        self.setWindowIcon(QIcon(str(resource_path("icons/icon.ico"))))
        self.setMinimumSize(720, 500)

        # Main tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # ========== FILES TAB (original content) ==========
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)
        files_layout.setContentsMargins(16, 14, 16, 10)
        files_layout.setSpacing(10)

        # ── Top toolbar ────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._add_files_btn = QPushButton("+ Добавить файлы")
        self._add_files_btn.setObjectName("primaryBtn")
        self._add_files_btn.setToolTip("Выберите отдельные файлы для добавления")
        self._add_files_btn.clicked.connect(self._browse_add_files)
        toolbar.addWidget(self._add_files_btn)

        self._add_folder_btn = QPushButton("+ Добавить папку")
        self._add_folder_btn.setToolTip("Рекурсивно добавить все файлы из папки")
        self._add_folder_btn.clicked.connect(self._browse_add_folder)
        toolbar.addWidget(self._add_folder_btn)

        toolbar.addSpacing(8)

        self._md5_cb = QCheckBox("MD5")
        self._md5_cb.setChecked(True)
        self._sha256_cb = QCheckBox("SHA256")
        self._sha256_cb.setChecked(True)
        self._md5_cb.toggled.connect(self._update_opts)
        self._sha256_cb.toggled.connect(self._update_opts)
        toolbar.addWidget(self._md5_cb)
        toolbar.addWidget(self._sha256_cb)

        toolbar.addStretch()

        self._log_toggle = QCheckBox("Журнал логов")
        self._log_toggle.setChecked(False)
        self._log_toggle.toggled.connect(self._toggle_log)
        toolbar.addWidget(self._log_toggle)

        self._clear_btn = QPushButton("Очистить всё")
        self._clear_btn.setObjectName("dangerBtn")
        self._clear_btn.clicked.connect(self._clear_all)
        toolbar.addWidget(self._clear_btn)

        files_layout.addLayout(toolbar)

        # ── Drop hint label ────────────────────────────────────────────────
        self._drop_hint = QLabel("Перетащите файлы или папки сюда · или используйте кнопки выше")
        self._drop_hint.setAlignment(Qt.AlignCenter)
        self._drop_hint.setStyleSheet("color: #aaa; font-size: 12px; padding: 4px 0;")
        files_layout.addWidget(self._drop_hint)

        # ── File list ──────────────────────────────────────────────────────
        self._file_list = QListWidget()
        self._file_list.setDragEnabled(False)
        self._file_list.setAcceptDrops(True)
        self._file_list.setSelectionMode(QAbstractItemView.NoSelection)
        self._file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._file_list.viewport().installEventFilter(self)
        self._file_list.setFocusPolicy(Qt.NoFocus)
        self._file_list.viewport().setAcceptDrops(True)
        files_layout.addWidget(self._file_list, stretch=1)

        # ── Live log (hidden by default) ───────────────────────────────────
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setVisible(False)
        self._log_text.setMaximumHeight(160)
        files_layout.addWidget(self._log_text)

        # ── Progress ───────────────────────────────────────────────────────
        prog_group = QGroupBox("Прогресс")
        prog_layout = QVBoxLayout()
        prog_layout.setSpacing(4)
        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._current_lbl = QLabel("Готово")
        self._current_lbl.setStyleSheet("font-size: 11px; color: #777;")
        prog_layout.addWidget(self._progress_bar)
        prog_layout.addWidget(self._current_lbl)
        prog_group.setLayout(prog_layout)
        files_layout.addWidget(prog_group)

        # ── Action buttons ─────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  Запустить хеширование")
        self._start_btn.setObjectName("primaryBtn")
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._start_hashing)

        self._cancel_btn = QPushButton("✕  Отмена")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_hashing)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._cancel_btn)
        btn_row.addStretch()
        files_layout.addLayout(btn_row)

        self.tab_widget.addTab(files_tab, "📁 Файлы")

        # ========== REPORT TAB ==========
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        report_layout.setContentsMargins(16, 14, 16, 10)
        report_layout.setSpacing(12)

        # Template selection
        template_group = QGroupBox("Шаблон документа")
        template_group_layout = QVBoxLayout()
        template_row = QHBoxLayout()
        self._template_path_edit = QLabel("Не выбран")
        self._template_path_edit.setStyleSheet("background:#f0f2f8; padding:6px; border-radius:4px;")
        self._template_path_edit.setWordWrap(True)
        self._template_browse_btn = QPushButton("Обзор...")
        self._template_browse_btn.clicked.connect(self._browse_template)
        template_row.addWidget(self._template_path_edit, stretch=1)
        template_row.addWidget(self._template_browse_btn)
        template_group_layout.addLayout(template_row)
        template_group.setLayout(template_group_layout)
        report_layout.addWidget(template_group)

        # Available variables info
        info_group = QGroupBox("Доступные переменные для шаблона")
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(200)
        info_text.setPlainText(
            "Вы можете использовать следующие переменные в шаблоне:\n\n"
            "• {{ files }} — список словарей, каждый содержит:\n"
            "    {{ file.name }}, {{ file.md5 }}, {{ file.sha256 }}\n"
            "• {{ file_count }} — общее количество файлов\n"
            "• {{ timestamp }} — текущая дата и время\n\n"
            "Пример таблицы в Word:\n"
            "{% for f in files %}\n"
            "{{ f.name }} | {{ f.md5 }} | {{ f.sha256 }}\n"
            "{% endfor %}\n\n"
        )
        info_group.setLayout(QVBoxLayout())
        info_group.layout().addWidget(info_text)
        report_layout.addWidget(info_group)

        # Generate button and status
        self._generate_btn = QPushButton("📄 Создать отчёт")
        self._generate_btn.setObjectName("primaryBtn")
        self._generate_btn.setEnabled(False)
        self._generate_btn.clicked.connect(self._generate_report)
        report_layout.addWidget(self._generate_btn)

        self._report_status = QLabel("Выберите шаблон DOCX и выполните хеширование файлов.")
        self._report_status.setWordWrap(True)
        self._report_status.setStyleSheet("color:#666; padding:4px;")
        report_layout.addWidget(self._report_status)

        report_layout.addStretch()
        self.tab_widget.addTab(report_tab, "📄 Отчёт")

        self.statusBar().showMessage("Перетащите файлы сюда или используйте + Добавить файлы")

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self._file_list.viewport() and event.type() == QEvent.Resize:
            # When the list's viewport resizes, stretch all row widgets
            width = self._file_list.viewport().width()
            for i in range(self._file_list.count()):
                item = self._file_list.item(i)
                w = self._file_list.itemWidget(item)
                if w:
                    w.setFixedWidth(width)
        return super().eventFilter(obj, event)

    # ── File addition ──────────────────────────────────────────────────────
    def _browse_add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Выберите файлы для хеширования", "",
            "All Files (*.*)"
        )
        added = sum(self._add_file(Path(p)) for p in paths)
        if added:
            self._update_start_btn()
            self._update_generate_btn()
            self.statusBar().showMessage(f"Добавлено файлов: {added}", 3000)

    def _browse_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            added = self._add_folder(Path(folder))
            if added:
                self._update_start_btn()
                self._update_generate_btn()
                self.statusBar().showMessage(f"Добавлено файлов из папки: {added}", 3000)

    def _add_file(self, fp: Path) -> int:
        key = str(fp.resolve())
        if key in self.file_rows:
            return 0
        self.file_paths.append(fp)
        row = FileRowWidget(fp, len(self.file_paths))
        row.remove_requested.connect(self._remove_row)
        self.file_rows[key] = row

        item = QListWidgetItem()
        self._file_list.addItem(item)
        item.setSizeHint(row.sizeHint())
        self._file_list.setItemWidget(item, row)

        # back‑reference for size‑hint updates
        row._list_item = item

        row.setFixedWidth(self._file_list.viewport().width())

        # Update drop hint
        self._drop_hint.setVisible(len(self.file_paths) == 0)
        return 1

    def _add_folder(self, folder: Path) -> int:
        added = 0
        for fp in sorted(folder.rglob("*")):
            if fp.is_file():
                added += self._add_file(fp)
        return added

    def _remove_row(self, row: FileRowWidget):
        key = str(row.file_path.resolve())
        if key in self.file_rows:
            del self.file_rows[key]
        for i, p in enumerate(self.file_paths):
            if str(p.resolve()) == key:
                self.file_paths.pop(i)
                break
        for i in range(self._file_list.count()):
            item = self._file_list.item(i)
            if self._file_list.itemWidget(item) is row:
                self._file_list.takeItem(i)
                break
        self._renumber()
        self._update_start_btn()
        self._update_generate_btn()
        self._drop_hint.setVisible(len(self.file_paths) == 0)
        self.statusBar().showMessage("Файл удалён", 2000)

    def _renumber(self):
        for i in range(self._file_list.count()):
            item = self._file_list.item(i)
            w = self._file_list.itemWidget(item)
            if isinstance(w, FileRowWidget):
                w.update_index(i + 1)

    def _clear_all(self):
        self._file_list.clear()
        self.file_rows.clear()
        self.file_paths.clear()
        self._drop_hint.setVisible(True)
        self._update_start_btn()
        self._update_generate_btn()
        self.statusBar().showMessage("Очищено", 2000)

    # ── Drag & drop ────────────────────────────────────────────────────────
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        added = 0
        for url in e.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_file():
                added += self._add_file(p)
            elif p.is_dir():
                added += self._add_folder(p)
        if added:
            self._update_start_btn()
            self._update_generate_btn()
            self.statusBar().showMessage(f"Добавлено файлов: {added}", 3000)
        e.acceptProposedAction()

    # ── Options & start button ──────────────────────────────────────────────
    def _update_opts(self):
        self.compute_md5 = self._md5_cb.isChecked()
        self.compute_sha256 = self._sha256_cb.isChecked()
        self._update_start_btn()

    def _update_start_btn(self):
        ok = bool(self.file_paths) and (self.compute_md5 or self.compute_sha256)
        self._start_btn.setEnabled(ok)

    # ── Report tab helpers ─────────────────────────────────────────────────
    def _browse_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите шаблон DOCX", "",
            "DOCX files (*.docx)"
        )
        if path:
            self.template_path = Path(path)
            self._template_path_edit.setText(str(self.template_path))
            self._update_generate_btn()

    def _update_generate_btn(self):
        """Enable report generation only if a template is selected and hashes are ready."""
        if not self.template_path or not self.file_paths:
            self._generate_btn.setEnabled(False)
            return
        # Check if at least one file has computed hashes
        ready = False
        for row in self.file_rows.values():
            if row.hashes_ready:
                ready = True
                break
        self._generate_btn.setEnabled(ready)

    def _generate_report(self):
        if not self.template_path or not self.template_path.exists():
            self._report_status.setText("❌ Файл шаблона не найден.")
            return
        if not self.file_paths:
            self._report_status.setText("❌ Нет файлов для отчёта.")
            return

        # Ask where to save the output
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт как", "",
            "DOCX files (*.docx)"
        )
        if not out_path:
            return

        # Build context from current data
        files_data = []
        for fp in self.file_paths:
            row = self.file_rows.get(str(fp.resolve()))
            if row:
                files_data.append({
                    'name': fp.name,
                    'md5': row.md5 if row.md5 != "ERROR" else "",
                    'sha256': row.sha256 if row.sha256 != "ERROR" else "",
                })
            else:
                # Should not happen, but fallback
                files_data.append({'name': fp.name, 'md5': "", 'sha256': ""})

        context = {
            'files': files_data,
            'file_count': len(files_data),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'file_names': [f['name'] for f in files_data],
            'md5_list': [f['md5'] for f in files_data],
            'sha256_list': [f['sha256'] for f in files_data],
        }

        # Start background thread
        self._report_status.setText("⏳ Генерация отчёта...")
        self._generate_btn.setEnabled(False)
        self.report_worker = ReportWorker(self.template_path, Path(out_path), context)
        self.report_worker.finished.connect(self._on_report_finished)
        self.report_worker.error.connect(self._on_report_error)
        self.report_worker.start()

    def _on_report_finished(self, output_path: str):
        self._report_status.setText(f"✅ Отчёт сохранён: {output_path}")
        self._generate_btn.setEnabled(True)
        # Ask to open folder
        reply = QMessageBox.question(self, "Готово",
                                     f"Отчёт создан.\nОткрыть папку с файлом?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(output_path).parent)))

    def _on_report_error(self, error_msg: str):
        self._report_status.setText(f"❌ Ошибка: {error_msg.split(chr(10))[0]}")  # show first line only
        self._generate_btn.setEnabled(True)

    # ── Live log ───────────────────────────────────────────────────────────
    def _toggle_log(self, checked: bool):
        self._log_text.setVisible(checked)
        if checked:
            # Replay stored lines so the widget is up to date
            self._log_text.setPlainText("\n".join(self._log_lines))
            self._log_text.moveCursor(QTextCursor.End)

    def _log(self, line: str):
        """Always store, optionally show."""
        self._log_lines.append(line)
        if self._log_toggle.isChecked():
            self._log_text.append(line)
            self._log_text.moveCursor(QTextCursor.End)

    # ── Hashing ────────────────────────────────────────────────────────────
    def _start_hashing(self):
        if not self.file_paths or not (self.compute_md5 or self.compute_sha256):
            return

        # Reset hashes in existing rows
        for row in self.file_rows.values():
            row.set_hashes("", "")
            row.hashes_ready = False

        self._log_lines.clear()
        if self._log_toggle.isChecked():
            self._log_text.clear()

        self._set_ui_busy(True)
        self._progress_bar.setValue(0)
        self._current_lbl.setText("Запуск…")

        self.worker = HashWorker(self.file_paths, self.compute_md5, self.compute_sha256)
        self.worker.file_started.connect(self._on_started)
        self.worker.file_progress.connect(self._on_progress)
        self.worker.file_result.connect(self._on_result)
        self.worker.file_error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.cancelled.connect(self._on_cancelled)
        self.worker.start()

    def _cancel_hashing(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()

    def _on_started(self, path_str: str):
        name = Path(path_str).name
        self._current_lbl.setText(f"Хеширование: {name}")

    def _on_progress(self, cur: int, total: int):
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(cur)

    def _on_result(self, path_str: str, md5: str, sha256: str):
        row = self.file_rows.get(path_str)
        if row:
            row.set_hashes(md5, sha256)

        name = Path(path_str).name
        self._log(name)
        if self.compute_md5:
            self._log(f"MD5: {md5}")
        if self.compute_sha256:
            self._log(f"SHA256: {sha256}")
        self._log("")

    def _on_error(self, path_str: str, msg: str):
        self._log(f"✗ {Path(path_str).name}: {msg}")

    def _on_finished(self, total: int, errors: int):
        self._set_ui_busy(False)
        self._current_lbl.setText("Готово")
        msg = f"Хешировано файлов: {total}"
        if errors:
            msg += f", {errors} ошибка(ы)"
        self.statusBar().showMessage(msg, 6000)
        self._log(f"─── {msg} ───")
        self._update_generate_btn()  # enable report button if conditions met

    def _on_cancelled(self):
        self._set_ui_busy(False)
        self._current_lbl.setText("Отменено")
        self.statusBar().showMessage("Отменено", 4000)
        self._log("─── Cancelled ───")
        self._update_generate_btn()

    def _set_ui_busy(self, busy: bool):
        self._start_btn.setEnabled(not busy)
        self._cancel_btn.setEnabled(busy)
        self._clear_btn.setEnabled(not busy)
        self._add_files_btn.setEnabled(not busy)
        self._add_folder_btn.setEnabled(not busy)
        self._md5_cb.setEnabled(not busy)
        self._sha256_cb.setEnabled(not busy)
        if not busy:
            self._progress_bar.setValue(0)


def resource_path(relative_path):
    try:
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ─── Entry point ──────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_STYLESHEET)
    apply_light_palette(app)

    icon_path = str(resource_path("icons/icon.ico"))
    app.setWindowIcon(QIcon(icon_path))

    window = HashKitWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
