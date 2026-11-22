"""Presentation layer: the dark stylesheet and the full PySide6 MainWindow
(preview, tabs, presets, export, settings persistence)."""

from __future__ import annotations

#==============================================================================
# ── STYLE — dark Catppuccin stylesheet
#    (merged from studio/style.py in the v2.5 ten-file edition)
#==============================================================================

"""Application stylesheet (Catppuccin Mocha dark, refined in v2.0 with
menu/tooltip/slider styling and pressed states)."""

STYLE = """
QMainWindow, QDialog { background: #1e1e2e; }
QGroupBox { color: #cdd6f4; font-weight: bold; font-size: 12px; border: 1px solid #45475a; border-radius: 8px; margin-top: 10px; padding-top: 14px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; }
QLabel { color: #cdd6f4; }
QCheckBox { color: #cdd6f4; spacing: 6px; }
QCheckBox:hover { color: #cba6f7; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #45475a; background: #313244; }
QCheckBox::indicator:checked { background: #89b4fa; border-color: #89b4fa; }
QTableWidget { background: #181825; color: #cdd6f4; gridline-color: #313244; border: none; outline: none; border-radius: 6px; }
QTableWidget::item { padding: 4px 6px; border-bottom: 1px solid #11111b; }
QTableWidget::item:selected { background: #89b4fa; color: #1e1e2e; }
QHeaderView::section { background: #1e1e2e; color: #a6adc8; border: none; padding: 4px; font-size: 10px; border-radius: 0; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { background: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px 8px; min-height: 22px; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #313244; color: #cdd6f4; selection-background-color: #89b4fa; selection-color: #1e1e2e; border: 1px solid #45475a; }
QPushButton { background: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px 12px; min-height: 22px; }
QPushButton:hover { background: #45475a; border-color: #89b4fa; }
QPushButton:pressed { background: #585b70; }
QPushButton:disabled { color: #6c7086; border-color: #313244; }
QProgressBar { background: #313244; border: none; border-radius: 4px; text-align: center; color: #cdd6f4; min-height: 20px; }
QProgressBar::chunk { background: #89b4fa; border-radius: 4px; }
QTabWidget::pane { border: 1px solid #45475a; border-radius: 6px; background: #1e1e2e; top: -1px; }
QTabBar::tab { background: #313244; color: #a6adc8; padding: 6px 12px; border: 1px solid #45475a; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
QTabBar::tab:selected { background: #1e1e2e; color: #cdd6f4; border-bottom: 2px solid #89b4fa; }
QTabBar::tab:hover:!selected { background: #45475a; }
QPlainTextEdit { background: #11111b; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; }
QSplitter { background: #11111b; }
QSplitter::handle { background: #181825; }
QSplitter::handle:horizontal { width: 8px; border-left: 1px solid #11111b; border-right: 1px solid #11111b; }
QSplitter::handle:horizontal:hover { background: #45475a; }
QSplitter::handle:vertical { height: 8px; border-top: 1px solid #11111b; border-bottom: 1px solid #11111b; }
QSplitter::handle:vertical:hover { background: #45475a; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: #181825; width: 8px; border: none; border-radius: 4px; }
QScrollBar::handle:vertical { background: #45475a; border-radius: 4px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #181825; height: 8px; border: none; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #45475a; border-radius: 4px; min-width: 20px; }
QScrollBar::handle:horizontal:hover { background: #585b70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QMenu { background: #181825; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 4px; }
QMenu::item { padding: 5px 18px; border-radius: 4px; }
QMenu::item:selected { background: #89b4fa; color: #1e1e2e; }
QMenu::separator { height: 1px; background: #313244; margin: 4px 8px; }
QToolTip { background: #181825; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px; }
QSlider::groove:horizontal { height: 6px; background: #313244; border-radius: 3px; }
QSlider::handle:horizontal { width: 14px; margin: -5px 0; border-radius: 7px; background: #89b4fa; }
QSlider::handle:horizontal:hover { background: #cba6f7; }
QSlider::sub-page:horizontal { background: #585b70; border-radius: 3px; }
"""

#==============================================================================
# ── UI — MainWindow, widgets, shortcuts, persistence
#    (merged from studio/ui.py in the v2.5 ten-file edition)
#==============================================================================

"""Main window UI (v2.1).

New in this edition:
  * Overlays tab: animated progress bar controls
  * Custom WAV key sounds (Audio tab) + background ambience
  * Hardware-encoder auto-detection
  * Workflow presets bar (built-in + user presets)
  * Output format: mp4 / gif / png sequence
  * Drag & drop files onto the batch table
  * Keyboard shortcuts (Ctrl+O/R/S/L/E, Space, Left/Right)
  * Loop toggle & estimated frames in preview, open output folder button
  * Full settings auto-save/restore (was only mode+theme in v1)
"""

import copy
import io
import json
import os
import sys
import time as _time
import wave
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime

import numpy as np

from PySide6.QtCore import (QBuffer, QIODevice, Qt, QThread, QTimer, QUrl, Signal)
from PySide6.QtGui import (QColor, QDesktopServices, QFont, QFontDatabase, QImage, QKeySequence,
                           QPainter, QPalette, QPixmap, QShortcut)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                               QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,
                               QGroupBox, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
                               QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit,
                               QProgressBar, QPushButton, QScrollArea, QSlider, QSpinBox,
                               QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from config import (APP_NAME, APP_VERSION, DEFAULT_PREVIEW_WIDTH, CUSTOM_WAV_PRESET,
                     ENCODERS, ENCODER_AUTO,
                     ENCODER_SOFTWARE, EXT_TO_LANGUAGE, FIT_MODES, INPUT_DIR, JR_VS_SR_LAYOUTS,
                     MULTI_WINDOW_LAYOUTS, OUTPUT_DIR, OUTPUT_FORMATS, QUALITY_PRESETS,
                     RESOLUTIONS, RHYTHM_STYLES, SHORTS_HARD_SEC, SHORTS_WARN_SEC,
                     SETTINGS_FILE, THUMB_SHORTS_SIZE, THUMB_YT_SIZE, WM_POSITIONS,
                     StudioConfig, StudioMode, SUPPORTED_EXTENSIONS, safe_config_from_dict)
from exporter import ExportCommand, VideoExporter
from rendering import KEYBOARD_LAYOUTS
from metadata import derive_title
from audio import MODULAR_SOUND_PRESETS, SimpleSoundGen, load_wav_samples
from config import CUSTOM_WAV_PRESET as WAV_PRESET
from audio import AMBIENCE_PRESETS, list_ambience_presets
from encoders import AUTO_LABEL, detect_encoders, describe_choice, resolve_encoder_choice
from config import (all_preset_names, apply_preset, builtin_names,
                      delete_user_preset, describe_preset, save_user_preset)
from animation import make_strategies
from config import THEMES
from config import convert_shortcodes, format_time, human_duration, logger, read_text_file
from exporter import make_dual_variants

FONT_FAMILIES = ["Consolas", "JetBrains Mono", "Fira Code", "Cascadia Code", "IBM Plex Mono", "monospace"]


def _get_system_fonts():
    try:
        db = QFontDatabase
        families = db.families()
        preferred = ["Consolas", "JetBrains Mono", "Fira Code", "Cascadia Code", "IBM Plex Mono",
                     "DejaVu Sans Mono", "Courier New", "monospace"]
        sys_fams = [f for f in families if f not in preferred and not f.startswith("@")]
        return preferred + sys_fams
    except Exception:
        return ["Consolas", "JetBrains Mono", "Fira Code", "Cascadia Code", "IBM Plex Mono", "monospace"]


@dataclass
class FileItem:
    path: str
    checked: bool = False
    status: str = "Pending"


class BatchTableWidget(QTableWidget):
    """File list with shift-range checkbox toggling and drag & drop import."""
    files_dropped = Signal(list)

    def __init__(self, rows=0, columns=0, parent=None):
        super().__init__(rows, columns, parent)
        self._checkbox_anchor = None
        self.setAcceptDrops(True)

    # ---- drag & drop ----
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
            if paths:
                self.files_dropped.emit(paths)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)

    # ---- checkbox toggling ----
    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        item = self.itemAt(pos)
        if not item:
            super().mousePressEvent(event)
            return
        row = item.row()
        chk_item = self.item(row, 0)
        if chk_item is None:
            super().mousePressEvent(event)
            return

        new_state = (chk_item.checkState() == Qt.CheckState.Unchecked)
        modifiers = QApplication.keyboardModifiers()

        if (modifiers & Qt.ShiftModifier) and self._checkbox_anchor is not None and self._checkbox_anchor != row:
            anchor = self._checkbox_anchor
            lo, hi = min(anchor, row), max(anchor, row)
            self.blockSignals(True)
            for i in range(lo, hi + 1):
                ci = self.item(i, 0)
                if ci is not None:
                    ci.setCheckState(Qt.CheckState.Checked if new_state else Qt.CheckState.Unchecked)
            self.blockSignals(False)
            self.itemChanged.emit(chk_item)
        else:
            if item.column() != 0:
                chk_item.setCheckState(Qt.CheckState.Checked if new_state else Qt.CheckState.Unchecked)
            self._checkbox_anchor = row
            self.itemChanged.emit(chk_item)

        if item.column() != 0:
            super().mousePressEvent(event)


class _EncoderDetectThread(QThread):
    """Probe hardware encoders off the UI thread (deep probe can take seconds)."""
    done = Signal(object)

    def __init__(self, deep=True, parent=None):
        super().__init__(parent)
        self._deep = deep

    def run(self):
        try:
            scan = detect_encoders(deep=self._deep, use_cache=True)
        except Exception:
            logger.error("Encoder detection failed", exc_info=True)
            scan = None
        self.done.emit(scan)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1400, 900)
        self.config = StudioConfig()
        global FONT_FAMILIES
        FONT_FAMILIES = _get_system_fonts()
        self.strategies = make_strategies()
        self.export_commands = deque()
        self.current_command = None
        self._items, self._item_paths = [], set()
        self._exporter = None
        self._batch_cancelled = False
        self.batch_total = 0; self.batch_done = 0; self.batch_start_time = 0
        self._detect_thread = None

        self._preview_animating = False
        self._preview_anim_t = 0.0
        self._preview_progress = 0.3
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(200)
        self._debounce_timer.timeout.connect(self._invalidate_preview)
        self._preview_timer = QTimer(self)
        self._preview_timer.setInterval(33)
        self._preview_timer.timeout.connect(self._advance_preview)
        self._cached_mp = None
        self._preview_scratch = None
        self._audio_player = QMediaPlayer()
        self._audio_out = QAudioOutput()
        self._audio_player.setAudioOutput(self._audio_out)
        self._audio_buf = None
        self._wav_cache_key, self._wav_cache = None, None

        self._build_ui()
        self._connect_signals()
        self._add_shortcuts()
        self._load_settings()
        self._scan_dir(str(INPUT_DIR))
        if not self.config.thumb_headline:
            self._autofill_headline()
        QTimer.singleShot(500, self._update_preview)
        # quick (non-probing) encoder availability hint; full probe on button
        QTimer.singleShot(150, lambda: self._on_encoders_detected(
            detect_encoders(deep=False, use_cache=True)))

    # =================================================================
    # UI construction
    # =================================================================
    def _build_ui(self):
        root = QSplitter(Qt.Horizontal)
        self.setCentralWidget(root)

        left = QWidget()
        left.setMinimumWidth(300)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        header = QFrame(); header.setFixedHeight(40)
        header.setStyleSheet("QFrame { background: #1e1e2e; border-bottom: 1px solid #11111b; }")
        hl = QHBoxLayout(header); hl.setContentsMargins(12, 0, 8, 0)
        hdr_lbl = QLabel("\U0001F4C2 FILE BATCH & GLOBAL")
        hdr_lbl.setStyleSheet("font-weight: bold; color: #cdd6f4;")
        hl.addWidget(hdr_lbl); hl.addStretch()
        left_layout.addWidget(header)

        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.setHandleWidth(6)
        left_layout.addWidget(left_splitter, 1)

        file_batch_widget = QWidget()
        ll = QVBoxLayout(file_batch_widget)
        ll.setContentsMargins(8, 8, 8, 8); ll.setSpacing(8)

        br1 = QHBoxLayout(); br1.setContentsMargins(0, 0, 0, 0)
        self.scan_btn = QPushButton("\U0001F504 Scan")
        self.scan_btn.setToolTip("Re-scan the ./input folder (Ctrl+R)")
        self.scan_btn.clicked.connect(lambda: self._scan_dir(str(INPUT_DIR)))
        br1.addWidget(self.scan_btn)
        self.add_btn = QPushButton("\u2795 Add")
        self.add_btn.setToolTip("Add files (Ctrl+O). You can also drag & drop files here.")
        self.add_btn.clicked.connect(self._add_files)
        br1.addWidget(self.add_btn)
        self.clear_btn = QPushButton("\u2716 Clear")
        self.clear_btn.clicked.connect(self._clear_list)
        br1.addWidget(self.clear_btn)
        br1.addStretch()
        self.recursive_chk = QCheckBox("Sub"); self.recursive_chk.setChecked(True)
        br1.addWidget(self.recursive_chk)
        br1.addWidget(QLabel("Depth:"))
        self.depth_sp = QSpinBox(); self.depth_sp.setRange(1, 99); self.depth_sp.setValue(10)
        self.depth_sp.setFixedWidth(50)
        br1.addWidget(self.depth_sp)
        ll.addLayout(br1)

        sel_row = QHBoxLayout(); sel_row.setContentsMargins(0, 0, 0, 0)
        self.select_all_btn = QPushButton("\u2611 Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        sel_row.addWidget(self.select_all_btn)
        self.deselect_all_btn = QPushButton("\u2610 Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        sel_row.addWidget(self.deselect_all_btn)
        sel_row.addStretch()
        sel_count_lbl = QLabel("0 selected")
        sel_count_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        sel_row.addWidget(sel_count_lbl)
        self._sel_count_lbl = sel_count_lbl
        ll.addLayout(sel_row)

        self.table = BatchTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["", "File", "Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.table.files_dropped.connect(self._add_paths)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed); hdr.resizeSection(0, 36)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Fixed); hdr.resizeSection(2, 100)
        ll.addWidget(self.table)
        left_splitter.addWidget(file_batch_widget)

        self.common_tabs = QTabWidget(); self.common_tabs.setDocumentMode(True)

        # ---------------- Video tab ----------------
        v_tab_content = QWidget()
        vfl = QFormLayout(v_tab_content)
        vfl.setSpacing(6); vfl.setContentsMargins(8, 8, 8, 8)
        vfl.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.theme_cb = QComboBox(); self.theme_cb.addItems(list(THEMES.keys()))
        vfl.addRow("Theme:", self.theme_cb)
        self.res_cb = QComboBox(); self.res_cb.addItems(list(RESOLUTIONS.keys()))
        vfl.addRow("Resolution:", self.res_cb)
        self.fps_sp = QSpinBox(); self.fps_sp.setRange(15, 60); self.fps_sp.setSingleStep(15)
        self.fps_sp.setValue(30)
        vfl.addRow("FPS:", self.fps_sp)
        self.encoder_cb = QComboBox(); self.encoder_cb.addItems(ENCODERS)
        vfl.addRow("Encoder:", self.encoder_cb)
        enc_row = QHBoxLayout(); enc_row.setContentsMargins(0, 0, 0, 0)
        self.enc_detect_btn = QPushButton("\U0001F50D Detect")
        self.enc_detect_btn.setToolTip("Probe which hardware encoders actually work "
                                       "on this machine (NVENC / QSV / AMF / VideoToolbox / VAAPI)")
        self.enc_detect_btn.clicked.connect(self._detect_encoders)
        enc_row.addWidget(self.enc_detect_btn)
        self.enc_info_lbl = QLabel("")
        self.enc_info_lbl.setStyleSheet("color: #a6adc8; font-size: 10px;")
        self.enc_info_lbl.setWordWrap(True)
        enc_row.addWidget(self.enc_info_lbl, 1)
        vfl.addRow("HW Probe:", enc_row)
        self.outfmt_cb = QComboBox(); self.outfmt_cb.addItems(OUTPUT_FORMATS)
        self.outfmt_cb.setToolTip("mp4 = video | gif = animated GIF (2-pass palette) | png = frame sequence folder")
        vfl.addRow("Output Format:", self.outfmt_cb)
        self.quality_cb = QComboBox(); self.quality_cb.addItems(QUALITY_PRESETS)
        self.quality_cb.setCurrentText("Balanced")
        self.quality_cb.setToolTip("High = CRF 16 archive master | Balanced = recommended for YouTube | "
                                   "Small = smaller upload, faster encode")
        vfl.addRow("Quality:", self.quality_cb)
        self.dual_render_chk = QCheckBox("Batch: render YouTube 16:9 + Shorts 9:16 versions")
        self.dual_render_chk.setToolTip("Every checked file exports twice: <name>_yt.mp4 (1920x1080) and\n"
                                        "<name>_shorts.mp4 (1080x1920, gets #shorts metadata). mp4 only.")
        vfl.addRow(self.dual_render_chk)
        self.yt_extras_chk = QCheckBox("Generate YT Extras (thumbnails)")
        self.yt_extras_chk.setChecked(True)
        vfl.addRow(self.yt_extras_chk)
        self.output_template_edit = QLineEdit(); self.output_template_edit.setText("{name}_{date}")
        self.output_template_edit.setToolTip("Placeholders: {name}, {date}, {lang}")
        vfl.addRow("Output Name:", self.output_template_edit)

        qt_row = QHBoxLayout(); qt_row.setContentsMargins(0, 0, 0, 0)
        for txt, secs in [("30s", 30), ("1m", 60), ("2m", 120), ("3m", 180), ("5m", 300)]:
            btn = QPushButton(txt); btn.setFixedWidth(40)
            btn.setToolTip(f"Auto-adjust timings so the video lands on ~{secs}s "
                           "(solves the WPM for you)")
            btn.clicked.connect(lambda checked=False, s=secs: self._apply_target_duration(s))
            qt_row.addWidget(btn)
        qt_row.addStretch()
        vfl.addRow("Quick Target:", qt_row)

        # ---------------- Timing & Rhythm (v2.4) ----------------
        timing_grp = QGroupBox("Timing & Rhythm (Auto-Adjust)")
        tgl = QFormLayout(timing_grp); tgl.setSpacing(6)
        self.rhythm_style_cb = QComboBox(); self.rhythm_style_cb.addItems(RHYTHM_STYLES)
        self.rhythm_style_cb.setCurrentText("Natural")   # fresh-install default
        self.rhythm_style_cb.setToolTip("Classic = v1 fixed pauses | Natural = human bursts +\n"
                                        "word gaps (default) | Cinematic = thinking pauses,\n"
                                        "paragraph breaths and a slow warm-up")
        tgl.addRow("Rhythm:", self.rhythm_style_cb)
        int_row = QHBoxLayout(); int_row.setContentsMargins(0, 0, 0, 0)
        self.rhythm_intensity_sl = QSlider(Qt.Horizontal); self.rhythm_intensity_sl.setRange(50, 150)
        self.rhythm_intensity_sl.setValue(100)
        self.rhythm_intensity_sl.setToolTip("50% = subtle and steady, 150% = very expressive pauses")
        self.rhythm_intensity_lbl = QLabel("100%")
        self.rhythm_intensity_lbl.setMinimumWidth(38)
        self.rhythm_intensity_lbl.setStyleSheet("color: #a6adc8; font-family: monospace;")
        int_row.addWidget(self.rhythm_intensity_sl, 1); int_row.addWidget(self.rhythm_intensity_lbl)
        tgl.addRow("Expressiveness:", int_row)
        self.timing_fit_cb = QComboBox(); self.timing_fit_cb.addItems(FIT_MODES)
        self.timing_fit_cb.setToolTip("Off = use the WPM spinboxes | Target Duration = solve the\n"
                                      "WPM so the video hits the target below | Audio Length = solve\n"
                                      "it so the video ends exactly with your BGM/ambience file")
        tgl.addRow("Auto-Fit:", self.timing_fit_cb)
        tgt_row = QHBoxLayout(); tgt_row.setContentsMargins(0, 0, 0, 0)
        self.timing_target_sp = QDoubleSpinBox(); self.timing_target_sp.setRange(3.0, 7200.0)
        self.timing_target_sp.setValue(60.0); self.timing_target_sp.setSuffix("s")
        self.timing_target_sp.setDecimals(1); self.timing_target_sp.setSingleStep(5.0)
        tgt_row.addWidget(self.timing_target_sp, 1)
        tgl.addRow("Target:", tgt_row)
        self.timing_est_lbl = QLabel("Est. total: —")
        self.timing_est_lbl.setStyleSheet("color: #a6e3a1; font-size: 11px; font-family: monospace;")
        self.timing_est_lbl.setWordWrap(True)
        tgl.addRow(self.timing_est_lbl)
        vfl.addRow(timing_grp)

        v_tab = QScrollArea(); v_tab.setWidgetResizable(True)
        v_tab.setWidget(v_tab_content); v_tab.setFrameShape(QFrame.NoFrame)
        self.common_tabs.addTab(v_tab, "Video")

        # ---------------- Audio tab ----------------
        a_tab_content = QWidget()
        afl = QFormLayout(a_tab_content)
        afl.setSpacing(6); afl.setContentsMargins(8, 8, 8, 8)
        afl.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.sound_chk = QCheckBox("Enable Audio"); self.sound_chk.setChecked(True)
        afl.addRow(self.sound_chk)
        self.preset_cb = QComboBox()
        self.preset_cb.addItems(list(MODULAR_SOUND_PRESETS.keys()) + [WAV_PRESET])
        afl.addRow("Preset:", self.preset_cb)
        self.stereo_chk = QCheckBox("Binaural ASMR")
        afl.addRow(self.stereo_chk)
        self.vol_sp = QSpinBox(); self.vol_sp.setRange(0, 100); self.vol_sp.setValue(50)
        self.vol_sp.setSuffix("%")
        afl.addRow("Volume:", self.vol_sp)
        test_row = QHBoxLayout(); test_row.setContentsMargins(0, 0, 0, 0)
        self.test_sound_btn = QPushButton("\U0001F50A Test Sound")
        self.test_sound_btn.setStyleSheet(
            "QPushButton { background: #89b4fa; color: #1e1e2e; font-weight: bold; border: none; border-radius: 4px; padding: 6px; }")
        self.test_sound_btn.clicked.connect(self._test_sound)
        test_row.addWidget(self.test_sound_btn)
        afl.addRow("Preview:", test_row)

        wav_grp = QGroupBox("Custom Key Sounds (WAV)")
        wgl = QFormLayout(wav_grp); wgl.setSpacing(4)
        self.wav_chk = QCheckBox("Use my WAV files as key clicks")
        wgl.addRow(self.wav_chk)
        wav_btn_row = QHBoxLayout(); wav_btn_row.setContentsMargins(0, 0, 0, 0)
        self.wav_load_btn = QPushButton("\U0001F4C2 Load WAV Files\u2026")
        self.wav_load_btn.clicked.connect(self._load_custom_wav_files)
        wav_btn_row.addWidget(self.wav_load_btn)
        wgl.addRow(wav_btn_row)
        self.wav_info_lbl = QLabel("No files loaded")
        self.wav_info_lbl.setStyleSheet("color: #a6adc8; font-size: 10px;")
        self.wav_info_lbl.setWordWrap(True)
        wgl.addRow(self.wav_info_lbl)
        afl.addRow(wav_grp)

        bgm_row = QHBoxLayout(); bgm_row.setContentsMargins(0, 0, 0, 0)
        self.bgm_edit = QLineEdit(); self.bgm_edit.setPlaceholderText("BGM MP3 path")
        bgm_btn = QPushButton("..."); bgm_btn.setFixedWidth(30)
        bgm_btn.clicked.connect(self._browse_bgm)
        bgm_row.addWidget(self.bgm_edit); bgm_row.addWidget(bgm_btn)
        afl.addRow("BGM:", bgm_row)
        self.bgm_vol_sp = QSpinBox(); self.bgm_vol_sp.setRange(0, 100); self.bgm_vol_sp.setValue(30)
        self.bgm_vol_sp.setSuffix("%")
        afl.addRow("BGM Vol:", self.bgm_vol_sp)
        self.bgm_duck_chk = QCheckBox("Sidechain Ducking"); self.bgm_duck_chk.setChecked(True)
        afl.addRow(self.bgm_duck_chk)
        self.loudnorm_chk = QCheckBox("YouTube loudness (-14 LUFS)")
        self.loudnorm_chk.setChecked(True)
        self.loudnorm_chk.setToolTip("Normalize the exported audio to YouTube's target loudness\n"
                                     "(-14 LUFS integrated, -1.5 dBTP) - recommended (mp4 only)")
        afl.addRow(self.loudnorm_chk)

        amb_grp = QGroupBox("Background Ambience")
        agl = QFormLayout(amb_grp); agl.setSpacing(4)
        self.amb_chk = QCheckBox("Layer a background ambience under the keys")
        agl.addRow(self.amb_chk)
        self.amb_preset_cb = QComboBox()
        self.amb_preset_cb.addItems(list_ambience_presets())
        self.amb_preset_cb.setToolTip("Procedurally generated soundscapes (deterministic, royalty-free)")
        agl.addRow("Preset:", self.amb_preset_cb)
        amb_file_row = QHBoxLayout(); amb_file_row.setContentsMargins(0, 0, 0, 0)
        self.amb_path_edit = QLineEdit(); self.amb_path_edit.setPlaceholderText(
            "Optional custom audio (wav/mp3/\u2026) overrides the preset")
        amb_browse = QPushButton("..."); amb_browse.setFixedWidth(30)
        amb_browse.clicked.connect(self._browse_ambience)
        amb_file_row.addWidget(self.amb_path_edit); amb_file_row.addWidget(amb_browse)
        agl.addRow("Custom File:", amb_file_row)
        self.amb_evolve_chk = QCheckBox("Procedurally evolve the file (recommended for long videos)")
        self.amb_evolve_chk.setToolTip(
            "Extends the file with slow varispeed ghosts, a half-speed deep layer and\n"
            "long gain drifts, so a short WAV never sounds like an obvious loop.\n"
            "Turn off for a plain verbatim loop of the file.")
        self.amb_evolve_chk.setChecked(True)
        agl.addRow("", self.amb_evolve_chk)
        self.amb_vol_sp = QSpinBox(); self.amb_vol_sp.setRange(0, 100); self.amb_vol_sp.setValue(35)
        self.amb_vol_sp.setSuffix("%")
        agl.addRow("Ambience Vol:", self.amb_vol_sp)
        afl.addRow(amb_grp)

        a_tab = QScrollArea(); a_tab.setWidgetResizable(True)
        a_tab.setWidget(a_tab_content); a_tab.setFrameShape(QFrame.NoFrame)
        self.common_tabs.addTab(a_tab, "Audio")

        # ---------------- Overlays tab (NEW) ----------------
        o_tab_content = QWidget()
        ofl = QFormLayout(o_tab_content)
        ofl.setSpacing(6); ofl.setContentsMargins(8, 8, 8, 8)
        ofl.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)

        pbar_grp = QGroupBox("Progress Bar")
        pgl = QFormLayout(pbar_grp); pgl.setSpacing(4)
        self.pbar_chk = QCheckBox("Show animated progress bar")
        pgl.addRow(self.pbar_chk)
        self.pbar_color_edit = QLineEdit(); self.pbar_color_edit.setPlaceholderText("accent  (or hex, e.g. #ff79c6)")
        self.pbar_color_edit.setToolTip("'accent' = theme accent color, or any hex color like #ff79c6")
        pgl.addRow("Bar Color:", self.pbar_color_edit)
        ofl.addRow(pbar_grp)

        o_tab = QScrollArea(); o_tab.setWidgetResizable(True)
        o_tab.setWidget(o_tab_content); o_tab.setFrameShape(QFrame.NoFrame)
        self.common_tabs.addTab(o_tab, "Overlays")

        # ---------------- YouTube & Shorts tab (v2.3) ----------------
        ys_tab_content = QWidget()
        yfl = QFormLayout(ys_tab_content)
        yfl.setSpacing(6); yfl.setContentsMargins(8, 8, 8, 8)
        yfl.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)

        brand_grp = QGroupBox("Branding")
        bgl = QFormLayout(brand_grp); bgl.setSpacing(4)
        self.wm_chk = QCheckBox("Show @handle watermark")
        bgl.addRow(self.wm_chk)
        self.wm_edit = QLineEdit(); self.wm_edit.setPlaceholderText("@yourhandle")
        bgl.addRow("Handle:", self.wm_edit)
        self.wm_pos_cb = QComboBox(); self.wm_pos_cb.addItems(WM_POSITIONS)
        self.wm_pos_cb.setCurrentText("Top Right")
        bgl.addRow("Position:", self.wm_pos_cb)
        self.wm_opacity_sp = QSpinBox(); self.wm_opacity_sp.setRange(0, 100)
        self.wm_opacity_sp.setValue(40); self.wm_opacity_sp.setSuffix("%")
        bgl.addRow("Opacity:", self.wm_opacity_sp)
        self.intro_chk = QCheckBox("Intro title card (1.5s fade)")
        bgl.addRow(self.intro_chk)
        self.intro_edit = QLineEdit(); self.intro_edit.setPlaceholderText(
            "Title text (blank = file name, e.g. 'Sorting Algorithms')")
        bgl.addRow("Intro Text:", self.intro_edit)
        self.outro_chk = QCheckBox("Outro card + Subscribe pill (2.2s)")
        bgl.addRow(self.outro_chk)
        self.outro_edit = QLineEdit(); self.outro_edit.setPlaceholderText("Thanks for watching!")
        bgl.addRow("Outro Text:", self.outro_edit)
        yfl.addRow(brand_grp)

        shorts_grp = QGroupBox("Shorts Assistant (9:16)")
        sgl = QFormLayout(shorts_grp); sgl.setSpacing(4)
        self.punch_zoom_chk = QCheckBox("Punch-in zoom (subtle Ken Burns)")
        self.punch_zoom_chk.setToolTip("Slowly zooms the code window ~5% over the video\n"
                                       "(vertical outputs only - great for Shorts retention)")
        sgl.addRow(self.punch_zoom_chk)
        self.shorts_guides_chk = QCheckBox("Safe-zone guides in preview")
        self.shorts_guides_chk.setToolTip("Overlay the areas YouTube's UI covers on Shorts\n"
                                          "(title top, buttons right, caption bottom). Preview only!")
        sgl.addRow(self.shorts_guides_chk)
        self.shorts_guard_lbl = QLabel("Shorts guard: enable a 9:16 resolution")
        self.shorts_guard_lbl.setStyleSheet("color: #a6adc8; font-size: 11px; font-family: monospace;")
        self.shorts_guard_lbl.setWordWrap(True)
        sgl.addRow("Duration:", self.shorts_guard_lbl)
        yfl.addRow(shorts_grp)

        thumb_grp = QGroupBox("Thumbnail Studio")
        tgl = QFormLayout(thumb_grp); tgl.setSpacing(4)
        self.thumb_headline_edit = QLineEdit()
        self.thumb_headline_edit.setPlaceholderText("Auto-filled from the file name - edit freely")
        tgl.addRow("Headline:", self.thumb_headline_edit)
        thumb_btn_row = QHBoxLayout(); thumb_btn_row.setContentsMargins(0, 0, 0, 0)
        self.thumb_auto_btn = QPushButton("\u21bb Auto")
        self.thumb_auto_btn.setFixedWidth(56)
        self.thumb_auto_btn.setToolTip("Re-fill the headline from the first checked file name")
        self.thumb_auto_btn.clicked.connect(self._autofill_headline)
        thumb_btn_row.addWidget(self.thumb_auto_btn)
        self.thumb_yt_btn = QPushButton(f"Save YT Thumb ({THUMB_YT_SIZE[0]}\u00d7{THUMB_YT_SIZE[1]})")
        self.thumb_yt_btn.clicked.connect(lambda: self._save_thumbnail("yt"))
        thumb_btn_row.addWidget(self.thumb_yt_btn, 1)
        self.thumb_shorts_btn = QPushButton("Shorts Cover")
        self.thumb_shorts_btn.setToolTip(f"Vertical cover {THUMB_SHORTS_SIZE[0]}\u00d7{THUMB_SHORTS_SIZE[1]}")
        self.thumb_shorts_btn.clicked.connect(lambda: self._save_thumbnail("shorts"))
        thumb_btn_row.addWidget(self.thumb_shorts_btn, 1)
        tgl.addRow("Generate:", thumb_btn_row)
        yfl.addRow(thumb_grp)

        meta_grp = QGroupBox("SEO Metadata")
        mgl = QFormLayout(meta_grp); mgl.setSpacing(4)
        self.write_metadata_chk = QCheckBox("Write .description.txt + .metadata.json on export")
        self.write_metadata_chk.setChecked(True)
        self.write_metadata_chk.setToolTip("Title, description with chapters (intro/coding/outro),\n"
                                           "tags and #hashtags - written next to every mp4 export")
        mgl.addRow(self.write_metadata_chk)
        yfl.addRow(meta_grp)

        ys_tab = QScrollArea(); ys_tab.setWidgetResizable(True)
        ys_tab.setWidget(ys_tab_content); ys_tab.setFrameShape(QFrame.NoFrame)
        self.common_tabs.addTab(ys_tab, "YouTube & Shorts")

        # ---------------- Keyboard tab ----------------
        k_tab_content = QWidget()
        kfl = QFormLayout(k_tab_content)
        kfl.setSpacing(6); kfl.setContentsMargins(8, 8, 8, 8)
        kfl.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.kb_enabled_chk = QCheckBox("Show Keyboard Overlay")
        kfl.addRow(self.kb_enabled_chk)
        self.kb_layout_cb = QComboBox(); self.kb_layout_cb.addItems(list(KEYBOARD_LAYOUTS.keys()))
        kfl.addRow("KB Layout:", self.kb_layout_cb)
        self.kb_position_cb = QComboBox()
        self.kb_position_cb.addItems(["Bottom Center", "Bottom Right", "Bottom Left",
                                      "Top Center", "Top Right", "Top Left"])
        kfl.addRow("KB Position:", self.kb_position_cb)
        self.kb_opacity_sp = QDoubleSpinBox(); self.kb_opacity_sp.setRange(0.1, 1.0)
        self.kb_opacity_sp.setSingleStep(0.05); self.kb_opacity_sp.setValue(0.82)
        kfl.addRow("KB Opacity:", self.kb_opacity_sp)

        fx_grp = QGroupBox("Visual Effects")
        fxfl = QFormLayout(fx_grp); fxfl.setSpacing(4)
        self.glow_chk = QCheckBox("Ambient glow behind window")
        self.glow_chk.setChecked(True)
        fxfl.addRow(self.glow_chk)
        self.cursor_style_cb = QComboBox()
        self.cursor_style_cb.addItems(["Beam", "Block", "Underline", "Outline"])
        fxfl.addRow("Cursor Style:", self.cursor_style_cb)
        self.cursor_blink_chk = QCheckBox("Blinking cursor")
        fxfl.addRow(self.cursor_blink_chk)
        kfl.addRow(fx_grp)

        k_tab = QScrollArea(); k_tab.setWidgetResizable(True)
        k_tab.setWidget(k_tab_content); k_tab.setFrameShape(QFrame.NoFrame)
        self.common_tabs.addTab(k_tab, "Keyboard & FX")

        # ---------------- Custom code tab ----------------
        c_tab_content = QWidget()
        cvl = QVBoxLayout(c_tab_content)
        cvl.setSpacing(6); cvl.setContentsMargins(8, 8, 8, 8)
        self.use_custom_chk = QCheckBox("Use Custom Code (ignores file list)")
        cvl.addWidget(self.use_custom_chk)
        self.custom_editor = QPlainTextEdit()
        self.custom_editor.setPlaceholderText("Supports shortcodes: :rocket: -> \U0001F680")
        cvl.addWidget(self.custom_editor)

        c_tab = QScrollArea(); c_tab.setWidgetResizable(True)
        c_tab.setWidget(c_tab_content); c_tab.setFrameShape(QFrame.NoFrame)
        self.common_tabs.addTab(c_tab, "Custom")

        left_splitter.addWidget(self.common_tabs)
        left_splitter.setSizes([250, 450])
        left_splitter.setStretchFactor(0, 0)
        left_splitter.setStretchFactor(1, 1)

        # ---------------- bottom bar ----------------
        bottom_bar = QVBoxLayout()
        bottom_bar.setContentsMargins(8, 4, 8, 8); bottom_bar.setSpacing(6)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("%v / %m  (%p%)")
        bottom_bar.addWidget(self.progress_bar)

        br2 = QHBoxLayout(); br2.setContentsMargins(0, 0, 0, 0)
        self.preset_cb2 = QComboBox()
        self._rebuild_preset_combo()
        self.preset_cb2.setToolTip("Workflow presets: one click applies a curated configuration\n"
                                   "(built-ins + your saved presets)")
        br2.addWidget(self.preset_cb2, 1)
        self.preset_save_btn = QPushButton("\U0001F4BE")
        self.preset_save_btn.setFixedWidth(34)
        self.preset_save_btn.setToolTip("Save the current settings as a preset")
        self.preset_save_btn.clicked.connect(self._save_preset)
        br2.addWidget(self.preset_save_btn)
        self.preset_del_btn = QPushButton("\U0001F5D1")
        self.preset_del_btn.setFixedWidth(34)
        self.preset_del_btn.setToolTip("Delete the selected user preset")
        self.preset_del_btn.clicked.connect(self._delete_preset)
        br2.addWidget(self.preset_del_btn)
        bottom_bar.addLayout(br2)

        br2b = QHBoxLayout(); br2b.setContentsMargins(0, 0, 0, 0)
        self.export_btn = QPushButton("\U0001F3AC Export")
        self.export_btn.setToolTip("Export all checked files (Ctrl+E)")
        self.export_btn.setStyleSheet(
            "QPushButton { background: #a6e3a1; color: #1e1e2e; font-weight: bold; border: none; border-radius: 6px; padding: 8px; }")
        self.export_btn.clicked.connect(self._start_export)
        br2b.addWidget(self.export_btn, 1)
        self.skip_btn = QPushButton("\u23ED Skip"); self.skip_btn.setFixedWidth(60)
        self.skip_btn.setEnabled(False)
        self.skip_btn.clicked.connect(self._skip_current)
        br2b.addWidget(self.skip_btn)
        self.cancel_btn = QPushButton("\u2716"); self.cancel_btn.setFixedWidth(36)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_export)
        br2b.addWidget(self.cancel_btn)
        bottom_bar.addLayout(br2b)

        br3 = QHBoxLayout(); br3.setContentsMargins(0, 0, 0, 0)
        self.save_proj_btn = QPushButton("\U0001F4BE Save")
        self.save_proj_btn.setToolTip("Save project (Ctrl+S)")
        self.save_proj_btn.clicked.connect(self._save_project)
        br3.addWidget(self.save_proj_btn)
        self.load_proj_btn = QPushButton("\U0001F4C2 Load")
        self.load_proj_btn.setToolTip("Load project (Ctrl+L)")
        self.load_proj_btn.clicked.connect(self._load_project)
        br3.addWidget(self.load_proj_btn)
        self.open_out_btn = QPushButton("\u2197 Output")
        self.open_out_btn.setToolTip("Open the output folder (Ctrl+Shift+O)")
        self.open_out_btn.clicked.connect(self._open_output_folder)
        br3.addWidget(self.open_out_btn)
        bottom_bar.addLayout(br3)

        info_row = QHBoxLayout(); info_row.setContentsMargins(0, 0, 0, 0)
        self.batch_info_lbl = QLabel("Ready to export.")
        self.batch_info_lbl.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        info_row.addWidget(self.batch_info_lbl, 1)
        bottom_bar.addLayout(info_row)

        left_layout.addLayout(bottom_bar)
        root.addWidget(left)

        self.mode_tabs = QTabWidget()
        root.addWidget(self.mode_tabs)
        root.setSizes([400, 1000])
        root.setStretchFactor(0, 0)
        root.setStretchFactor(1, 1)

        self._build_multi_window_tab()
        self._build_jr_vs_sr_tab()
        self._build_code_yt_tab()
        self._build_text_emoji_tab()

        self.mode_tabs.currentChanged.connect(lambda idx: (self._on_mode_changed(idx), self._debounce_timer.start()))

    # =================================================================
    # Mode tabs
    # =================================================================
    def _create_font_controls(self, prefix):
        font_cb = QComboBox(); font_cb.addItems(FONT_FAMILIES)
        font_sz_auto = QCheckBox("Auto")
        fs_row = QHBoxLayout(); fs_row.setContentsMargins(0, 0, 0, 0)
        fs_row.addWidget(font_sz_auto)
        font_sz_sp = QSpinBox(); font_sz_sp.setRange(8, 72); font_sz_sp.setValue(22)
        font_sz_sp.setEnabled(False)
        fs_row.addWidget(font_sz_sp)
        font_sz_auto.toggled.connect(font_sz_sp.setEnabled)
        setattr(self, f"{prefix}_font_cb", font_cb)
        setattr(self, f"{prefix}_font_sz_auto", font_sz_auto)
        setattr(self, f"{prefix}_font_sz_sp", font_sz_sp)
        return font_cb, fs_row

    def _create_font_group(self, prefix, label_text):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        font_cb = QComboBox(); font_cb.addItems(FONT_FAMILIES)
        font_sz_auto = QCheckBox("Auto")
        font_sz_sp = QSpinBox(); font_sz_sp.setRange(8, 72); font_sz_sp.setValue(22)
        font_sz_sp.setEnabled(False)

        fs_row = QHBoxLayout(); fs_row.setContentsMargins(0, 0, 0, 0)
        fs_row.addWidget(font_sz_auto); fs_row.addWidget(font_sz_sp)
        font_sz_auto.toggled.connect(font_sz_sp.setEnabled)

        setattr(self, f"{prefix}_font_cb", font_cb)
        setattr(self, f"{prefix}_font_sz_auto", font_sz_auto)
        setattr(self, f"{prefix}_font_sz_sp", font_sz_sp)

        layout.addRow(label_text, font_cb)
        layout.addRow("Size:", fs_row)
        return widget

    def _build_mode_tab(self, mode: StudioMode):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        splitter = QSplitter(Qt.Horizontal)
        settings_scroll = QScrollArea(); settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.NoFrame)
        settings_scroll.setMinimumWidth(280)
        settings_widget = QWidget()
        s_layout = QVBoxLayout(settings_widget)
        s_layout.setContentsMargins(8, 8, 8, 8); s_layout.setSpacing(8)
        preview_widget = QWidget()
        p_layout = QVBoxLayout(preview_widget)
        p_layout.setContentsMargins(8, 8, 8, 8); p_layout.setSpacing(8)
        lbl = QLabel(); lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("background: #11111b; border-radius: 8px;")
        lbl.setMinimumSize(640, 360)
        lbl.setFocusPolicy(Qt.ClickFocus)
        p_layout.addWidget(lbl, 1)
        stats_row = QHBoxLayout(); stats_row.setContentsMargins(0, 0, 0, 0)
        stats_lbl = QLabel("Render: 0ms | Chars: 0/0")
        stats_lbl.setStyleSheet("color: #a6adc8; font-size: 11px; font-family: monospace;")
        stats_row.addWidget(stats_lbl); stats_row.addStretch()
        guide_pad_chk = QCheckBox("Pad"); guide_pad_chk.toggled.connect(self._debounce_timer.start)
        guide_chrome_chk = QCheckBox("Chrome"); guide_chrome_chk.toggled.connect(self._debounce_timer.start)
        guide_code_chk = QCheckBox("Code"); guide_code_chk.toggled.connect(self._debounce_timer.start)
        loop_chk = QCheckBox("Loop"); loop_chk.setChecked(True)
        loop_chk.setToolTip("Restart preview automatically when it reaches the end")
        stats_row.addWidget(loop_chk)
        stats_row.addWidget(guide_pad_chk); stats_row.addWidget(guide_chrome_chk); stats_row.addWidget(guide_code_chk)
        p_layout.addLayout(stats_row)
        ctrls = QHBoxLayout(); ctrls.setContentsMargins(0, 0, 0, 0)
        prev_btn = QPushButton("\u25C0"); prev_btn.setFixedWidth(40)
        prev_btn.setToolTip("Step one frame back (Left arrow)")
        prev_btn.clicked.connect(lambda: self._step_frame(-1))
        ctrls.addWidget(prev_btn)
        play_btn = QPushButton("\u25B6 Animate"); play_btn.setFixedWidth(110)
        play_btn.setToolTip("Play/pause preview (Space)")
        play_btn.setStyleSheet(
            "QPushButton { background: #a6e3a1; color: #1e1e2e; font-weight: bold; border: none; border-radius: 6px; padding: 6px; }")
        ctrls.addWidget(play_btn)
        next_btn = QPushButton("\u25B6"); next_btn.setFixedWidth(40)
        next_btn.setToolTip("Step one frame forward (Right arrow)")
        next_btn.clicked.connect(lambda: self._step_frame(1))
        ctrls.addWidget(next_btn)
        slider = QSlider(Qt.Horizontal); slider.setRange(0, 1000)
        time_lbl = QLabel("0:00 / 0:00")
        time_lbl.setStyleSheet("color: #a6e3a1; font-family: monospace;")
        time_lbl.setMinimumWidth(120)
        ctrls.addWidget(slider, 1); ctrls.addWidget(time_lbl)
        p_layout.addLayout(ctrls)
        settings_scroll.setWidget(settings_widget)
        splitter.addWidget(settings_scroll); splitter.addWidget(preview_widget)
        splitter.setSizes([450, 1000])
        splitter.setStretchFactor(0, 0); splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)
        self.mode_tabs.addTab(tab, mode.value.split(" ")[0])
        return s_layout, lbl, play_btn, slider, time_lbl, prev_btn, next_btn, stats_lbl, guide_pad_chk, guide_chrome_chk, guide_code_chk, loop_chk

    def _update_mw_layout_visibility(self):
        n_panes = MULTI_WINDOW_LAYOUTS.get(self.mw_layout_cb.currentText(), 1)
        self.mw_font_grp1.setVisible(n_panes >= 1)
        self.mw_font_grp2.setVisible(n_panes >= 2)
        self.mw_font_grp3.setVisible(n_panes >= 3)
        self.mw_font_grp4.setVisible(n_panes >= 4)

        has_multi = n_panes >= 2
        self.diff_highlight_mw_chk.setVisible(has_multi)
        self.sync_mw_chk.setVisible(has_multi)

        self.mw_ratio_container.setVisible(n_panes == 2)

        self._debounce_timer.start()

    def _build_multi_window_tab(self):
        (s_layout, lbl, play_btn, slider, time_lbl, prev_btn, next_btn, stats_lbl,
         g_pad, g_chrome, g_code, loop_chk) = self._build_mode_tab(StudioMode.MULTI_WINDOW)
        grp = QGroupBox("Multi-Window Settings")
        fl = QFormLayout(grp); fl.setSpacing(6)

        self.mw_layout_cb = QComboBox(); self.mw_layout_cb.addItems(list(MULTI_WINDOW_LAYOUTS.keys()))
        fl.addRow("Layout:", self.mw_layout_cb)

        self.mw_font_grp1 = self._create_font_group("mw", "Window 1 Font:")
        self.mw_font_grp2 = self._create_font_group("mw_2", "Window 2 Font:")
        self.mw_font_grp3 = self._create_font_group("mw_3", "Window 3 Font:")
        self.mw_font_grp4 = self._create_font_group("mw_4", "Window 4 Font:")
        fl.addRow(self.mw_font_grp1)
        fl.addRow(self.mw_font_grp2)
        fl.addRow(self.mw_font_grp3)
        fl.addRow(self.mw_font_grp4)

        self.mw_layout_cb.currentIndexChanged.connect(self._update_mw_layout_visibility)

        self.mw_wpm_sp = QSpinBox(); self.mw_wpm_sp.setRange(30, 300); self.mw_wpm_sp.setValue(100)
        fl.addRow("WPM:", self.mw_wpm_sp)
        self.mw_typo_sp = QDoubleSpinBox(); self.mw_typo_sp.setRange(0.0, 0.2)
        self.mw_typo_sp.setSingleStep(0.01)
        fl.addRow("Typo Rate:", self.mw_typo_sp)
        self.mw_shorts_chk = QCheckBox("Auto-adjust for Shorts (<3 min)")
        fl.addRow(self.mw_shorts_chk)
        self.diff_highlight_mw_chk = QCheckBox("Dynamic Diff Highlighting")
        self.diff_highlight_mw_chk.setChecked(True)
        fl.addRow(self.diff_highlight_mw_chk)
        self.sync_mw_chk = QCheckBox("Synchronized Typing Completion")
        self.sync_mw_chk.setChecked(True)
        fl.addRow(self.sync_mw_chk)

        self.mw_ratio_container = QWidget()
        ratio_layout = QHBoxLayout(self.mw_ratio_container)
        ratio_layout.setContentsMargins(0, 0, 0, 0); ratio_layout.setSpacing(6)
        ratio_layout.addWidget(QLabel("Pane Ratio:"))
        self.mw_ratio_sp = QSpinBox(); self.mw_ratio_sp.setRange(10, 90); self.mw_ratio_sp.setValue(50)
        self.mw_ratio_sp.setSuffix("%")
        ratio_layout.addWidget(self.mw_ratio_sp); ratio_layout.addStretch()
        fl.addRow(self.mw_ratio_container)
        s_layout.addWidget(grp); s_layout.addStretch()

        self.mw_preview_lbl = lbl; self.mw_play_btn = play_btn; self.mw_slider = slider
        self.mw_time_lbl = time_lbl
        self.mw_prev_btn = prev_btn; self.mw_next_btn = next_btn; self.mw_stats_lbl = stats_lbl
        self.mw_g_pad = g_pad; self.mw_g_chrome = g_chrome; self.mw_g_code = g_code
        self.mw_loop_chk = loop_chk
        self.mw_play_btn.clicked.connect(lambda: self._toggle_preview(StudioMode.MULTI_WINDOW))
        self.mw_slider.valueChanged.connect(lambda v: self._on_slider_changed(StudioMode.MULTI_WINDOW, v))
        self.mw_layout_cb.setCurrentText(self.config.layout_mw)
        self._update_mw_layout_visibility()

    def _build_jr_vs_sr_tab(self):
        (s_layout, lbl, play_btn, slider, time_lbl, prev_btn, next_btn, stats_lbl,
         g_pad, g_chrome, g_code, loop_chk) = self._build_mode_tab(StudioMode.JR_VS_SR)
        grp = QGroupBox("Junior vs Senior Settings")
        fl = QFormLayout(grp); fl.setSpacing(6)
        font_cb_jr, fs_row_jr = self._create_font_controls("jr")
        fl.addRow("Junior Font:", font_cb_jr); fl.addRow("Junior Size:", fs_row_jr)
        font_cb_sr, fs_row_sr = self._create_font_controls("sr")
        fl.addRow("Senior Font:", font_cb_sr); fl.addRow("Senior Size:", fs_row_sr)
        self.jr_layout_cb = QComboBox(); self.jr_layout_cb.addItems(JR_VS_SR_LAYOUTS)
        fl.addRow("Layout:", self.jr_layout_cb)
        self.jr_wpm_sp = QSpinBox(); self.jr_wpm_sp.setRange(30, 300); self.jr_wpm_sp.setValue(90)
        fl.addRow("Junior WPM:", self.jr_wpm_sp)
        self.sr_wpm_sp = QSpinBox(); self.sr_wpm_sp.setRange(30, 300); self.sr_wpm_sp.setValue(130)
        fl.addRow("Senior WPM:", self.sr_wpm_sp)
        self.jr_typo_sp = QDoubleSpinBox(); self.jr_typo_sp.setRange(0.0, 0.2)
        self.jr_typo_sp.setSingleStep(0.01)
        fl.addRow("Typo Rate (Jr):", self.jr_typo_sp)
        self.jr_sound_cb = QComboBox()
        self.jr_sound_cb.addItems(list(MODULAR_SOUND_PRESETS.keys()) + [WAV_PRESET])
        fl.addRow("Junior Sound:", self.jr_sound_cb)
        self.sr_sound_cb = QComboBox()
        self.sr_sound_cb.addItems(list(MODULAR_SOUND_PRESETS.keys()) + [WAV_PRESET])
        fl.addRow("Senior Sound:", self.sr_sound_cb)
        s_layout.addWidget(grp)
        custom_grp = QGroupBox("Dual Custom Code (Overrides JSON/File)")
        cl = QVBoxLayout(custom_grp); cl.setSpacing(4)
        cl.addWidget(QLabel("Junior Code:"))
        self.jr_custom_editor = QPlainTextEdit(); self.jr_custom_editor.setMaximumHeight(150)
        cl.addWidget(self.jr_custom_editor)
        cl.addWidget(QLabel("Senior Code:"))
        self.sr_custom_editor = QPlainTextEdit(); self.sr_custom_editor.setMaximumHeight(150)
        cl.addWidget(self.sr_custom_editor)
        s_layout.addWidget(custom_grp); s_layout.addStretch()
        self.jr_preview_lbl = lbl; self.jr_play_btn = play_btn; self.jr_slider = slider
        self.jr_time_lbl = time_lbl
        self.jr_prev_btn = prev_btn; self.jr_next_btn = next_btn; self.jr_stats_lbl = stats_lbl
        self.jr_g_pad = g_pad; self.jr_g_chrome = g_chrome; self.jr_g_code = g_code
        self.jr_loop_chk = loop_chk
        self.jr_play_btn.clicked.connect(lambda: self._toggle_preview(StudioMode.JR_VS_SR))
        self.jr_slider.valueChanged.connect(lambda v: self._on_slider_changed(StudioMode.JR_VS_SR, v))

    def _build_code_yt_tab(self):
        (s_layout, lbl, play_btn, slider, time_lbl, prev_btn, next_btn, stats_lbl,
         g_pad, g_chrome, g_code, loop_chk) = self._build_mode_tab(StudioMode.CODE_YT)
        grp = QGroupBox("Code YT Settings")
        fl = QFormLayout(grp); fl.setSpacing(6)
        font_cb, fs_row = self._create_font_controls("yt")
        fl.addRow("Font:", font_cb); fl.addRow("Font Size:", fs_row)
        self.yt_wpm_sp = QSpinBox(); self.yt_wpm_sp.setRange(30, 300); self.yt_wpm_sp.setValue(100)
        fl.addRow("WPM:", self.yt_wpm_sp)
        self.yt_typo_sp = QDoubleSpinBox(); self.yt_typo_sp.setRange(0.0, 0.2)
        self.yt_typo_sp.setSingleStep(0.01)
        fl.addRow("Typo Rate:", self.yt_typo_sp)
        dur_row = QHBoxLayout(); dur_row.setContentsMargins(0, 0, 0, 0)
        for txt, secs in [("30s", 30), ("1m", 60), ("2m", 120), ("3m", 180)]:
            btn = QPushButton(txt); btn.setFixedWidth(40)
            btn.clicked.connect(lambda checked=False, s=secs: self._apply_target_duration(s))
            dur_row.addWidget(btn)
        dur_row.addStretch(); fl.addRow("Quick Target:", dur_row)
        self.yt_zoom_chk = QCheckBox("Cinematic Ken Burns Zoom")
        fl.addRow(self.yt_zoom_chk)
        self.yt_focus_chk = QCheckBox("Code Block Focus (Dimming)")
        fl.addRow(self.yt_focus_chk)
        s_layout.addWidget(grp); s_layout.addStretch()
        self.yt_preview_lbl = lbl; self.yt_play_btn = play_btn; self.yt_slider = slider
        self.yt_time_lbl = time_lbl
        self.yt_prev_btn = prev_btn; self.yt_next_btn = next_btn; self.yt_stats_lbl = stats_lbl
        self.yt_g_pad = g_pad; self.yt_g_chrome = g_chrome; self.yt_g_code = g_code
        self.yt_loop_chk = loop_chk
        self.yt_play_btn.clicked.connect(lambda: self._toggle_preview(StudioMode.CODE_YT))
        self.yt_slider.valueChanged.connect(lambda v: self._on_slider_changed(StudioMode.CODE_YT, v))

    def _build_text_emoji_tab(self):
        (s_layout, lbl, play_btn, slider, time_lbl, prev_btn, next_btn, stats_lbl,
         g_pad, g_chrome, g_code, loop_chk) = self._build_mode_tab(StudioMode.TEXT_EMOJI)
        grp = QGroupBox("Text & Emoji Settings")
        fl = QFormLayout(grp); fl.setSpacing(6)
        font_cb, fs_row = self._create_font_controls("txt")
        fl.addRow("Font:", font_cb); fl.addRow("Font Size:", fs_row)
        self.txt_wpm_sp = QSpinBox(); self.txt_wpm_sp.setRange(30, 300); self.txt_wpm_sp.setValue(100)
        fl.addRow("WPM:", self.txt_wpm_sp)
        self.txt_typo_sp = QDoubleSpinBox(); self.txt_typo_sp.setRange(0.0, 0.2)
        self.txt_typo_sp.setSingleStep(0.01)
        fl.addRow("Typo Rate:", self.txt_typo_sp)
        self.txt_shorts_chk = QCheckBox("Auto-adjust for Shorts (<3 min)")
        fl.addRow(self.txt_shorts_chk)
        self.ascii_chk = QCheckBox("ASCII Art Mode (Centered)")
        fl.addRow(self.ascii_chk)
        self.txt_clean_chk = QCheckBox("Clean Text Spacing"); self.txt_clean_chk.setChecked(True)
        fl.addRow(self.txt_clean_chk)
        self.txt_markdown_chk = QCheckBox("Markdown Support (**bold**, *italic*)")
        fl.addRow(self.txt_markdown_chk)
        self.txt_crt_chk = QCheckBox("CRT / Terminal Filter")
        fl.addRow(self.txt_crt_chk)
        self.txt_bubbles_chk = QCheckBox("Chat Bubble Mode")
        fl.addRow(self.txt_bubbles_chk)
        s_layout.addWidget(grp); s_layout.addStretch()
        self.txt_preview_lbl = lbl; self.txt_play_btn = play_btn; self.txt_slider = slider
        self.txt_time_lbl = time_lbl
        self.txt_prev_btn = prev_btn; self.txt_next_btn = next_btn; self.txt_stats_lbl = stats_lbl
        self.txt_g_pad = g_pad; self.txt_g_chrome = g_chrome; self.txt_g_code = g_code
        self.txt_loop_chk = loop_chk
        self.txt_play_btn.clicked.connect(lambda: self._toggle_preview(StudioMode.TEXT_EMOJI))
        self.txt_slider.valueChanged.connect(lambda v: self._on_slider_changed(StudioMode.TEXT_EMOJI, v))

    # =================================================================
    # Target duration / codes
    # =================================================================
    def _apply_target_duration(self, secs):
        """Quick-target chips (30s/1m/2m/...): auto-adjust timings so the
        finished video lands on ~secs (v2.4 solver; was a manual WPM guess)."""
        secs = float(secs)
        self.config.timing_fit = "Target Duration"
        self.config.timing_target = secs
        for w, val in ((self.timing_fit_cb, "Target Duration"),
                       (self.timing_target_sp, secs)):
            w.blockSignals(True)
            w.setValue(val) if hasattr(w, "setValue") else w.setCurrentText(val)
            w.blockSignals(False)
        self._invalidate_preview()
        self.statusBar().showMessage(
            f"Auto-fit on: timings adjusted to land on ~{human_duration(int(secs))}", 3000)

    def _update_timing_label(self, dur: float):
        """Live estimate under the Timing & Rhythm group (v2.4)."""
        if not hasattr(self, "timing_est_lbl"):
            return
        if dur <= 0:
            self.timing_est_lbl.setText("Est. total: —")
            return
        frames = int(dur * self.config.fps)
        txt = f"Est. total: {format_time(dur)} · {frames} frames"
        fit = getattr(self.config, "timing_fit", "Off")
        if fit != "Off" and getattr(self, "_cached_mp", None):
            try:
                wpms = [p[1].profile.wpm for p in self._cached_mp.panes]
                txt += f" · solved WPM ≈{max(int(w) for w in wpms)}"
            except Exception:
                pass
        self.timing_est_lbl.setText(txt)

    def _get_jr_sr_codes(self):
        if self.config.use_custom or (self.config.jr_custom_code and self.config.sr_custom_code):
            code1 = convert_shortcodes(self.config.jr_custom_code) if self.config.jr_custom_code else "def junior():\n    pass"
            code2 = convert_shortcodes(self.config.sr_custom_code) if self.config.sr_custom_code else "def senior():\n    pass"
            lang, t1, t2 = "python", "junior.py", "senior.py"
        else:
            checked = [f for f in self._items if f.checked]
            if not checked:
                c, l, t = self.strategies[StudioMode.JR_VS_SR]._get_code(self.config, self._items, self.config.custom_code)
                code1, code2, lang, t1, t2 = c, c, l, t, t
            else:
                it = checked[0]
                ext = os.path.splitext(it.path)[1].lower()
                if ext == ".json":
                    try:
                        with open(it.path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        code1 = convert_shortcodes(data.get("junior_code", ""))
                        code2 = convert_shortcodes(data.get("senior_code", ""))
                        lang = data.get("language", "python")
                        title = data.get("title", os.path.basename(it.path))
                        t1, t2 = f"{title} (Junior)", f"{title} (Senior)"
                        if not code1.strip():
                            code1 = "# Junior code missing in JSON"
                        if not code2.strip():
                            code2 = "# Senior code missing in JSON"
                    except Exception:
                        c, l, t = self.strategies[StudioMode.JR_VS_SR]._get_code(self.config, self._items, self.config.custom_code)
                        code1, code2, lang, t1, t2 = c, c, l, t, t
                else:
                    c, l, t = self.strategies[StudioMode.JR_VS_SR]._get_code(self.config, self._items, self.config.custom_code)
                    code1, code2, lang, t1, t2 = c, c, l, t, t
        return code1, code2, lang, t1, t2

    # =================================================================
    # Preview
    # =================================================================
    def _preview_scale(self) -> float:
        w, _h = RESOLUTIONS.get(self.config.resolution, (1920, 1080))
        return min(1.0, DEFAULT_PREVIEW_WIDTH / max(w, 1))

    def _step_frame(self, direction: int):
        if not self._cached_mp:
            return
        fps = self.config.fps
        dt = direction / fps
        dur = self._cached_mp.duration()
        self._preview_anim_t = max(0, min(dur, self._preview_anim_t + dt))
        self._preview_progress = self._preview_anim_t / dur if dur > 0 else 0
        self._update_preview()

    def _invalidate_preview(self):
        self._cached_mp = None
        self._preview_scratch = None
        self._update_preview()

    def _update_preview(self):
        if self._cached_mp is None:
            strategy = self.strategies[self.config.mode]
            try:
                # Render preview at reduced scale for smooth interactive playback
                self._cached_mp = strategy.build_panes(self.config, self._items, self.config.custom_code,
                                                       scale=self._preview_scale())
            except Exception:
                logger.error("Preview build failed", exc_info=True)
                self._cached_mp = None
            if self._cached_mp:
                self._preview_scratch = QImage(self._cached_mp.frame_w, self._cached_mp.frame_h,
                                               QImage.Format.Format_RGB32)
        if not self._cached_mp:
            return
        t_start = _time.perf_counter()
        t = self._cached_mp.duration() * self._preview_progress

        if self.config.mode == StudioMode.MULTI_WINDOW:
            active_lbl, active_g_pad, active_g_chrome, active_g_code = self.mw_preview_lbl, self.mw_g_pad, self.mw_g_chrome, self.mw_g_code
            active_slider, active_time_lbl, active_stats = self.mw_slider, self.mw_time_lbl, self.mw_stats_lbl
        elif self.config.mode == StudioMode.JR_VS_SR:
            active_lbl, active_g_pad, active_g_chrome, active_g_code = self.jr_preview_lbl, self.jr_g_pad, self.jr_g_chrome, self.jr_g_code
            active_slider, active_time_lbl, active_stats = self.jr_slider, self.jr_time_lbl, self.jr_stats_lbl
        elif self.config.mode == StudioMode.CODE_YT:
            active_lbl, active_g_pad, active_g_chrome, active_g_code = self.yt_preview_lbl, self.yt_g_pad, self.yt_g_chrome, self.yt_g_code
            active_slider, active_time_lbl, active_stats = self.yt_slider, self.yt_time_lbl, self.yt_stats_lbl
        elif self.config.mode == StudioMode.TEXT_EMOJI:
            active_lbl, active_g_pad, active_g_chrome, active_g_code = self.txt_preview_lbl, self.txt_g_pad, self.txt_g_chrome, self.txt_g_code
            active_slider, active_time_lbl, active_stats = self.txt_slider, self.txt_time_lbl, self.txt_stats_lbl
        else:
            return

        draw_guides = active_g_pad.isChecked() or active_g_chrome.isChecked() or active_g_code.isChecked()
        # kb_trail=True: the preview renders sequentially on the GUI thread,
        # so the v3 keyboard afterglow trail is safe here (export stays
        # stateless — its frames render concurrently).
        img = self._cached_mp.render_frame(t, self._preview_scratch,
                                           draw_guides=draw_guides, kb_trail=True)
        if self.config.shorts_guides and self.config.resolution.endswith("(9:16)"):
            self._draw_shorts_guides(img)
        if self.config.txt_crt:
            qp = QPainter(img)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(QColor(0, 0, 0, 80))
            for y in range(0, img.height(), 3):
                qp.drawRect(0, y, img.width(), 1)
            qp.setBrush(QColor(0, 255, 0, 20))
            qp.drawRect(0, 0, img.width(), img.height())
            qp.end()
        active_lbl.setPixmap(QPixmap.fromImage(img).scaled(
            active_lbl.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        render_time = (_time.perf_counter() - t_start) * 1000
        dur = self._cached_mp.duration()
        self._update_shorts_guard(dur)
        active_time_lbl.setText(f"{format_time(t)} / {format_time(dur)}  (\u2248{int(dur * self.config.fps)} frames)")
        self._update_timing_label(dur)
        total_chars = sum(len(a.display_chars) for _, a, _ in self._cached_mp.panes)
        visible_chars = sum(a.visible_at(t) for _, a, _ in self._cached_mp.panes)
        active_stats.setText(f"Render: {render_time:.1f}ms | Chars: {visible_chars}/{total_chars}")
        if not self._preview_animating:
            active_slider.blockSignals(True)
            active_slider.setValue(int(self._preview_progress * 1000))
            active_slider.blockSignals(False)

    def _on_slider_changed(self, mode, val):
        if mode != self.config.mode:
            return
        self._preview_progress = val / 1000.0
        self._preview_anim_t = self._preview_progress * (self._cached_mp.duration() if self._cached_mp else 0)
        self._update_preview()

    def _loop_enabled(self) -> bool:
        try:
            if self.config.mode == StudioMode.MULTI_WINDOW:
                return self.mw_loop_chk.isChecked()
            if self.config.mode == StudioMode.JR_VS_SR:
                return self.jr_loop_chk.isChecked()
            if self.config.mode == StudioMode.CODE_YT:
                return self.yt_loop_chk.isChecked()
            if self.config.mode == StudioMode.TEXT_EMOJI:
                return self.txt_loop_chk.isChecked()
        except AttributeError:
            pass
        return True

    def _set_play_btn_text(self, mode, playing: bool):
        text = "\u23F8 Pause" if playing else "\u25B6 Animate"
        if mode == StudioMode.MULTI_WINDOW:
            self.mw_play_btn.setText(text)
        elif mode == StudioMode.JR_VS_SR:
            self.jr_play_btn.setText(text)
        elif mode == StudioMode.CODE_YT:
            self.yt_play_btn.setText(text)
        elif mode == StudioMode.TEXT_EMOJI:
            self.txt_play_btn.setText(text)

    def _toggle_preview(self, mode):
        if mode != self.config.mode:
            return
        if self._preview_animating:
            self._preview_animating = False
            self._preview_timer.stop()
            self._audio_player.stop()
            self._set_play_btn_text(mode, False)
        else:
            if self._cached_mp is None:
                return
            self._preview_animating = True
            if self._preview_anim_t >= self._cached_mp.duration():
                self._preview_anim_t = 0
            self._set_play_btn_text(mode, True)

            if self.config.sound_enabled:
                try:
                    custom = self._get_custom_wav_samples() if self.config.sound_preset == WAV_PRESET else None
                    if self.config.mode == StudioMode.JR_VS_SR:
                        sg1 = SimpleSoundGen(preset=self.config.jr_sound, stereo=self.config.stereo,
                                             custom_samples=custom)
                        pcm1 = sg1.generate_pcm(self._cached_mp.panes[0][1].char_timestamps(), 1.0)
                        sg2 = SimpleSoundGen(preset=self.config.sr_sound, stereo=self.config.stereo,
                                             custom_samples=custom)
                        pcm2 = sg2.generate_pcm(self._cached_mp.panes[1][1].char_timestamps(), 1.0)

                        max_len = max(len(pcm1), len(pcm2))
                        mix = np.zeros(max_len, dtype=np.int32)
                        mix[:len(pcm1)] += pcm1
                        mix[:len(pcm2)] += pcm2
                        pcm = np.clip(mix, -32768, 32767).astype(np.int16)

                        channels, sample_rate = (2 if self.config.stereo else 1), sg1.sr
                    else:
                        sg = SimpleSoundGen(preset=self.config.sound_preset, stereo=self.config.stereo,
                                            custom_samples=custom)
                        pcm = sg.generate_pcm(self._cached_mp.char_timestamps_all(), 1.0)
                        channels, sample_rate = (2 if sg.stereo else 1), sg.sr

                    if len(pcm) > 0:
                        # layer the ambience bed under the key clicks (v2.1)
                        if getattr(self.config, "amb_enabled", False):
                            from audio import build_ambience_bed, mix_ambience
                            chans = 2 if channels == 2 else 1
                            bed = build_ambience_bed(self.config,
                                                     len(pcm) / (chans * sample_rate),
                                                     sample_rate)
                            pcm = mix_ambience(pcm, sample_rate, chans, bed,
                                               getattr(self.config, "amb_volume", 35))
                        buf = io.BytesIO()
                        with wave.open(buf, "w") as wf:
                            wf.setnchannels(channels)
                            wf.setsampwidth(2)
                            wf.setframerate(sample_rate)
                            wf.writeframes(pcm.tobytes())
                        self._audio_buf = QBuffer()
                        self._audio_buf.setData(buf.getvalue())
                        self._audio_buf.open(QIODevice.ReadOnly)
                        self._audio_out.setVolume(self.config.volume / 100.0)
                        self._audio_player.setSourceDevice(self._audio_buf, QUrl())
                        self._audio_player.play()
                except Exception:
                    logger.error("Failed to generate preview audio", exc_info=True)
            self._preview_timer.start()

    def _advance_preview(self):
        if not self._cached_mp:
            return
        self._preview_anim_t += 0.033
        dur = self._cached_mp.duration()
        if self._preview_anim_t >= dur:
            if self._loop_enabled():
                self._preview_anim_t = 0.0
                self._preview_progress = 0.0
                self._update_preview()
                return
            self._preview_anim_t = dur
            self._toggle_preview(self.config.mode)
        self._preview_progress = self._preview_anim_t / dur if dur > 0 else 0
        self._update_preview()

    # =================================================================
    # Shortcuts & keyboard
    # =================================================================
    def _add_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self._add_files)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, activated=self._open_output_folder)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=lambda: self._scan_dir(str(INPUT_DIR)))
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._save_project)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._load_project)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._start_export)

    def _editor_focused(self) -> bool:
        fw = QApplication.focusWidget()
        return isinstance(fw, (QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox))

    def keyPressEvent(self, e):
        if self._editor_focused():
            super().keyPressEvent(e)
            return
        key = e.key()
        if key == Qt.Key_Space:
            self._toggle_preview(self.config.mode)
            e.accept()
            return
        if key in (Qt.Key_Left, Qt.Key_Right):
            self._step_frame(1 if key == Qt.Key_Right else -1)
            e.accept()
            return
        super().keyPressEvent(e)

    # =================================================================
    # Files
    # =================================================================
    def _add_paths(self, paths):
        added = 0
        for p in paths:
            if p and p not in self._item_paths and os.path.isfile(p):
                self._items.append(FileItem(path=p, checked=True))
                self._item_paths.add(p)
                added += 1
        if added:
            self._refresh_table()
            self._update_sel_count()
            if not self.thumb_headline_edit.text().strip():
                self._autofill_headline()
            self._debounce_timer.start()
            self.statusBar().showMessage(f"Added {added} file(s)", 3000)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Files", "",
            "All Supported Files (*.py *.js *.ts *.java *.c *.cpp *.cs *.go *.rs *.rb *.php *.swift "
            "*.kt *.sh *.sql *.html *.css *.json *.yaml *.yml *.toml *.txt *.md *.csv *.asc *.emoji *.json);;"
            "All Files (*)")
        self._add_paths(paths)

    def _clear_list(self):
        self._items.clear()
        self._item_paths.clear()
        self._refresh_table()
        self._update_sel_count()
        self._invalidate_preview()

    def _scan_dir(self, path):
        self._items.clear()
        self._item_paths.clear()
        if os.path.isdir(path):
            max_depth = self.config.scan_depth if self.config.recursive_scan else 1
            skip_dirs = {".git", ".hg", ".svn", "__pycache__", "node_modules", ".venv", "venv", ".env",
                         ".idea", ".vscode", "dist", "build", ".tox", ".mypy_cache", ".pytest_cache"}
            found = []
            for dirpath, dirnames, filenames in os.walk(path):
                rel = os.path.relpath(dirpath, path)
                depth = 1 if rel == "." else rel.count(os.sep) + 2
                if depth > max_depth:
                    dirnames.clear()
                    continue
                dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
                for fname in sorted(filenames):
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        found.append(FileItem(path=os.path.join(dirpath, fname), checked=True))
            self._items = found
            self._item_paths = {it.path for it in found}
        self._refresh_table()
        self._update_sel_count()
        self._debounce_timer.start()

    def _select_all(self):
        for it in self._items:
            it.checked = True
        self._refresh_table(); self._update_sel_count(); self._debounce_timer.start()

    def _deselect_all(self):
        for it in self._items:
            it.checked = False
        self._refresh_table(); self._update_sel_count(); self._debounce_timer.start()

    def _update_sel_count(self):
        count = sum(1 for it in self._items if it.checked)
        total = len(self._items)
        self._sel_count_lbl.setText(f"{count}/{total} selected")

    def _refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._items))
        for i, item in enumerate(self._items):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked if item.checked else Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, chk)
            self.table.setItem(i, 1, QTableWidgetItem(os.path.basename(item.path)))
            self.table.setItem(i, 2, QTableWidgetItem(item.status))
        self.table.blockSignals(False)

    def _on_item_changed(self, item):
        row = item.row()
        if item.column() == 0 and 0 <= row < len(self._items):
            self._items[row].checked = item.checkState() == Qt.CheckState.Checked
            self._update_sel_count()
            if not self.thumb_headline_edit.text().strip():
                self._autofill_headline()
            self._debounce_timer.start()

    def _on_table_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        if row >= len(self._items):
            return
        menu = QMenu(self)
        export_action = menu.addAction("Export This File Only")
        open_file_action = menu.addAction("Open File")
        open_dir_action = menu.addAction("Open Containing Folder")
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        path = self._items[row].path
        if action == export_action:
            for it in self._items:
                it.checked = False
            self._items[row].checked = True
            self._refresh_table()
            self._start_export()
        elif action == open_file_action:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif action == open_dir_action:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path) or "."))

    # =================================================================
    # Signals
    # =================================================================
    def _connect_signals(self):
        def update_config(key, value):
            setattr(self.config, key, value)
            self._debounce_timer.start()

        self.theme_cb.currentTextChanged.connect(lambda v: update_config('theme', v))
        self.res_cb.currentTextChanged.connect(lambda v: update_config('resolution', v))
        self.fps_sp.valueChanged.connect(lambda v: update_config('fps', v))
        self.sound_chk.toggled.connect(lambda v: update_config('sound_enabled', v))
        self.preset_cb.currentTextChanged.connect(lambda v: update_config('sound_preset', v))
        self.stereo_chk.toggled.connect(lambda v: update_config('stereo', v))
        self.vol_sp.valueChanged.connect(lambda v: update_config('volume', v))
        self.encoder_cb.currentTextChanged.connect(lambda v: update_config('encoder', v))
        self.outfmt_cb.currentTextChanged.connect(lambda v: update_config('output_format', v))
        self.bgm_edit.textChanged.connect(lambda v: update_config('bgm_path', v))
        self.bgm_vol_sp.valueChanged.connect(lambda v: update_config('bgm_volume', v))
        self.bgm_duck_chk.toggled.connect(lambda v: update_config('bgm_duck', v))
        self.wav_chk.toggled.connect(lambda v: update_config('use_custom_wav', v))
        self.amb_chk.toggled.connect(lambda v: update_config('amb_enabled', v))
        self.amb_preset_cb.currentTextChanged.connect(lambda v: update_config('amb_preset', v))
        self.amb_path_edit.textChanged.connect(lambda v: update_config('amb_path', v))
        self.amb_evolve_chk.toggled.connect(lambda v: update_config('amb_evolve', v))
        self.amb_vol_sp.valueChanged.connect(lambda v: update_config('amb_volume', v))
        self.preset_cb2.currentTextChanged.connect(self._on_preset_selected)
        self.use_custom_chk.toggled.connect(lambda v: update_config('use_custom', v))
        self.custom_editor.textChanged.connect(lambda: update_config('custom_code', self.custom_editor.toPlainText()))
        self.yt_extras_chk.toggled.connect(lambda v: update_config('yt_extras', v))
        self.recursive_chk.toggled.connect(lambda v: update_config('recursive_scan', v))
        self.depth_sp.valueChanged.connect(lambda v: update_config('scan_depth', v))
        self.output_template_edit.textChanged.connect(lambda v: update_config('output_template', v))
        self.pbar_chk.toggled.connect(lambda v: update_config('progress_bar_enabled', v))
        self.pbar_color_edit.textChanged.connect(lambda v: update_config('progress_bar_color', v.strip() or "accent"))
        self.quality_cb.currentTextChanged.connect(lambda v: update_config('quality_preset', v))
        self.dual_render_chk.toggled.connect(lambda v: update_config('dual_render', v))
        self.loudnorm_chk.toggled.connect(lambda v: update_config('yt_loudnorm', v))
        self.wm_chk.toggled.connect(lambda v: update_config('wm_enabled', v))
        self.wm_edit.textChanged.connect(lambda v: update_config('wm_text', v))
        self.wm_pos_cb.currentTextChanged.connect(lambda v: update_config('wm_position', v))
        self.wm_opacity_sp.valueChanged.connect(lambda v: update_config('wm_opacity', v))
        self.intro_chk.toggled.connect(lambda v: update_config('intro_enabled', v))
        self.intro_edit.textChanged.connect(lambda v: update_config('intro_text', v))
        self.outro_chk.toggled.connect(lambda v: update_config('outro_enabled', v))
        self.outro_edit.textChanged.connect(lambda v: update_config('outro_text', v))
        self.punch_zoom_chk.toggled.connect(lambda v: update_config('punch_zoom', v))
        self.shorts_guides_chk.toggled.connect(lambda v: update_config('shorts_guides', v))
        self.thumb_headline_edit.textChanged.connect(lambda v: update_config('thumb_headline', v))
        self.write_metadata_chk.toggled.connect(lambda v: update_config('write_metadata', v))
        # Timing & Rhythm (v2.4)
        self.rhythm_style_cb.currentTextChanged.connect(lambda v: update_config('rhythm_style', v))
        self.rhythm_intensity_sl.valueChanged.connect(
            lambda v: (self.rhythm_intensity_lbl.setText(f"{v}%"),
                       update_config('rhythm_intensity', v)))
        self.timing_fit_cb.currentTextChanged.connect(lambda v: update_config('timing_fit', v))
        self.timing_target_sp.valueChanged.connect(lambda v: update_config('timing_target', float(v)))
        self.glow_chk.toggled.connect(lambda v: update_config('glow_enabled', v))
        self.cursor_style_cb.currentTextChanged.connect(lambda v: update_config('cursor_style', v))
        self.cursor_blink_chk.toggled.connect(lambda v: update_config('cursor_blink', v))
        self.kb_enabled_chk.toggled.connect(lambda v: update_config('kb_enabled', v))
        self.kb_layout_cb.currentTextChanged.connect(lambda v: update_config('kb_layout', v))
        self.kb_position_cb.currentTextChanged.connect(lambda v: update_config('kb_position', v))
        self.kb_opacity_sp.valueChanged.connect(lambda v: update_config('kb_opacity', v))
        self.mw_font_cb.currentTextChanged.connect(lambda v: update_config('font_mw', v))
        self.mw_font_sz_auto.toggled.connect(lambda v: update_config('font_sz_auto_mw', v))
        self.mw_font_sz_sp.valueChanged.connect(lambda v: update_config('font_sz_mw', v))
        self.mw_2_font_cb.currentTextChanged.connect(lambda v: update_config('font_mw_2', v))
        self.mw_2_font_sz_auto.toggled.connect(lambda v: update_config('font_sz_auto_mw_2', v))
        self.mw_2_font_sz_sp.valueChanged.connect(lambda v: update_config('font_sz_mw_2', v))
        self.mw_3_font_cb.currentTextChanged.connect(lambda v: update_config('font_mw_3', v))
        self.mw_3_font_sz_auto.toggled.connect(lambda v: update_config('font_sz_auto_mw_3', v))
        self.mw_3_font_sz_sp.valueChanged.connect(lambda v: update_config('font_sz_mw_3', v))
        self.mw_4_font_cb.currentTextChanged.connect(lambda v: update_config('font_mw_4', v))
        self.mw_4_font_sz_auto.toggled.connect(lambda v: update_config('font_sz_auto_mw_4', v))
        self.mw_4_font_sz_sp.valueChanged.connect(lambda v: update_config('font_sz_mw_4', v))
        self.mw_layout_cb.currentTextChanged.connect(lambda v: update_config('layout_mw', v))
        self.mw_wpm_sp.valueChanged.connect(lambda v: update_config('wpm_mw', v))
        self.mw_typo_sp.valueChanged.connect(lambda v: update_config('typo_mw', v))
        self.mw_shorts_chk.toggled.connect(lambda v: update_config('shorts_mw', v))
        self.diff_highlight_mw_chk.toggled.connect(lambda v: update_config('diff_highlight_mw', v))
        self.sync_mw_chk.toggled.connect(lambda v: update_config('sync_mw', v))
        self.mw_ratio_sp.valueChanged.connect(lambda v: update_config('mw_ratio', v))
        self.jr_font_cb.currentTextChanged.connect(lambda v: update_config('font_jr', v))
        self.jr_font_sz_auto.toggled.connect(lambda v: update_config('font_sz_auto_jr', v))
        self.jr_font_sz_sp.valueChanged.connect(lambda v: update_config('font_sz_jr', v))
        self.sr_font_cb.currentTextChanged.connect(lambda v: update_config('font_sr', v))
        self.sr_font_sz_auto.toggled.connect(lambda v: update_config('font_sz_auto_sr', v))
        self.sr_font_sz_sp.valueChanged.connect(lambda v: update_config('font_sz_sr', v))
        self.jr_layout_cb.currentTextChanged.connect(lambda v: update_config('layout_jr', v))
        self.jr_wpm_sp.valueChanged.connect(lambda v: update_config('jr_wpm', v))
        self.sr_wpm_sp.valueChanged.connect(lambda v: update_config('sr_wpm', v))
        self.jr_typo_sp.valueChanged.connect(lambda v: update_config('typo_jr', v))
        self.jr_sound_cb.currentTextChanged.connect(lambda v: update_config('jr_sound', v))
        self.sr_sound_cb.currentTextChanged.connect(lambda v: update_config('sr_sound', v))
        self.jr_custom_editor.textChanged.connect(lambda: update_config('jr_custom_code', self.jr_custom_editor.toPlainText()))
        self.sr_custom_editor.textChanged.connect(lambda: update_config('sr_custom_code', self.sr_custom_editor.toPlainText()))
        self.yt_font_cb.currentTextChanged.connect(lambda v: update_config('font_yt', v))
        self.yt_font_sz_auto.toggled.connect(lambda v: update_config('font_sz_auto_yt', v))
        self.yt_font_sz_sp.valueChanged.connect(lambda v: update_config('font_sz_yt', v))
        self.yt_wpm_sp.valueChanged.connect(lambda v: update_config('wpm_yt', v))
        self.yt_typo_sp.valueChanged.connect(lambda v: update_config('typo_yt', v))
        self.yt_zoom_chk.toggled.connect(lambda v: update_config('yt_zoom', v))
        self.yt_focus_chk.toggled.connect(lambda v: update_config('yt_focus', v))
        self.txt_font_cb.currentTextChanged.connect(lambda v: update_config('font_txt', v))
        self.txt_font_sz_auto.toggled.connect(lambda v: update_config('font_sz_auto_txt', v))
        self.txt_font_sz_sp.valueChanged.connect(lambda v: update_config('font_sz_txt', v))
        self.txt_wpm_sp.valueChanged.connect(lambda v: update_config('wpm_txt', v))
        self.txt_typo_sp.valueChanged.connect(lambda v: update_config('typo_txt', v))
        self.txt_shorts_chk.toggled.connect(lambda v: update_config('shorts_txt', v))
        self.ascii_chk.toggled.connect(lambda v: update_config('ascii_art', v))
        self.txt_clean_chk.toggled.connect(lambda v: update_config('txt_clean', v))
        self.txt_markdown_chk.toggled.connect(lambda v: update_config('txt_markdown', v))
        self.txt_crt_chk.toggled.connect(lambda v: update_config('txt_crt', v))
        self.txt_bubbles_chk.toggled.connect(lambda v: update_config('txt_bubbles', v))

    def _on_mode_changed(self, idx):
        self.config.mode = list(StudioMode)[idx]
        self._debounce_timer.start()

    # =================================================================
    # Workflow presets & encoder detection (v2.1)
    # =================================================================
    def _rebuild_preset_combo(self, select_name=None):
        self.preset_cb2.blockSignals(True)
        try:
            self.preset_cb2.clear()
            names = all_preset_names()
            self.preset_cb2.addItems(names)
            for i, name in enumerate(names):
                desc = describe_preset(name)
                if desc:
                    self.preset_cb2.setItemData(i, desc, Qt.ToolTipRole)
            if select_name:
                self.preset_cb2.setCurrentText(select_name)
        finally:
            self.preset_cb2.blockSignals(False)

    def _on_preset_selected(self, name):
        if not name:
            return
        try:
            self.config = apply_preset(self.config, name)
        except KeyError:
            return
        self._apply_config_to_ui()
        self._invalidate_preview()
        self.statusBar().showMessage(f"Preset applied: {name} — {describe_preset(name)}", 5000)

    def _save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset",
                                        "Preset name (saved to the presets folder):")
        if not ok or not name.strip():
            return
        name = name.strip()
        try:
            save_user_preset(name, self.config)
        except Exception as e:
            QMessageBox.warning(self, "Save Preset", f"Could not save preset:\n{e}")
            return
        self._rebuild_preset_combo(select_name=name)
        self.statusBar().showMessage(f"Preset saved: {name}", 4000)

    def _delete_preset(self):
        name = self.preset_cb2.currentText()
        if not name or name in builtin_names():
            QMessageBox.information(self, "Delete Preset",
                                    "Built-in presets cannot be deleted.\n"
                                    "Select a user preset instead.")
            return
        if delete_user_preset(name):
            self._rebuild_preset_combo(select_name="Default")
            self.statusBar().showMessage(f"Preset deleted: {name}", 4000)

    def _detect_encoders(self):
        if self._detect_thread and self._detect_thread.isRunning():
            return
        self.enc_detect_btn.setEnabled(False)
        self.enc_info_lbl.setText("Probing hardware encoders\u2026")
        self._detect_thread = _EncoderDetectThread(deep=True, parent=self)
        self._detect_thread.done.connect(self._on_encoders_detected)
        self._detect_thread.start()

    def _on_encoders_detected(self, scan):
        self.enc_detect_btn.setEnabled(True)
        if scan is None:
            self.enc_info_lbl.setText("Detection failed (ffmpeg missing?)")
            return
        working = scan.working_hw()
        enc_id, _ = resolve_encoder_choice(self.config.encoder, deep=False)
        if self.config.encoder == ENCODER_AUTO:
            chosen = describe_choice(enc_id, scan)
            self.enc_info_lbl.setText(f"Auto \u2192 {chosen}")
        elif working:
            self.enc_info_lbl.setText("Working: " + ", ".join(w.label for w in working))
        else:
            self.enc_info_lbl.setText("No hardware encoder works on this machine \u2014 "
                                      "the software encoder will be used.")
        self.enc_info_lbl.setToolTip("\n".join(scan.summary_lines()))

    def _browse_ambience(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Ambience Audio", "",
                                              "Audio Files (*.wav *.mp3 *.m4a *.ogg *.flac);;All Files (*)")
        if path:
            self.amb_path_edit.setText(path)

    # =================================================================
    # Custom WAV / sound
    # =================================================================
    def _load_custom_wav_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select key-click WAV files", "",
                                                "WAV Audio (*.wav);;All Files (*)")
        if not paths:
            return
        self.config.custom_wav_paths = "|".join(paths)
        self.config.use_custom_wav = True
        self.wav_chk.setChecked(True)
        names = ", ".join(os.path.basename(p) for p in paths)
        n = len(load_wav_samples(paths))
        self.wav_info_lbl.setText(f"{n} sample(s): {names}")
        if self.preset_cb.findText(WAV_PRESET) >= 0 and self.preset_cb.currentText() != WAV_PRESET:
            self.preset_cb.setCurrentText(WAV_PRESET)
        self._debounce_timer.start()
        self.statusBar().showMessage(f"Loaded {n} custom WAV sample(s)", 3000)

    def _get_custom_wav_samples(self):
        paths = [p for p in (self.config.custom_wav_paths or "").split("|") if p]
        if not paths:
            return None
        key = self.config.custom_wav_paths
        if key != self._wav_cache_key or self._wav_cache is None:
            self._wav_cache = load_wav_samples(paths) or None
            self._wav_cache_key = key
        return self._wav_cache

    def _test_sound(self):
        try:
            custom = self._get_custom_wav_samples() if self.config.sound_preset == WAV_PRESET else None
            sg = SimpleSoundGen(preset=self.config.sound_preset, stereo=self.config.stereo,
                                custom_samples=custom)
            sample_text = "hello world 123"
            timestamps = []
            t = 0.0
            for ch in sample_text:
                timestamps.append((t, ch))
                t += 0.10 if ch == " " else 0.06

            pcm = sg.generate_pcm(timestamps, 1.0)
            if len(pcm) > 0:
                buf = io.BytesIO()
                with wave.open(buf, "w") as wf:
                    wf.setnchannels(2 if sg.stereo else 1)
                    wf.setsampwidth(2)
                    wf.setframerate(sg.sr)
                    wf.writeframes(pcm.tobytes())
                self._audio_player.stop()
                self._audio_buf = QBuffer()
                self._audio_buf.setData(buf.getvalue())
                self._audio_buf.open(QIODevice.ReadOnly)
                self._audio_out.setVolume(self.config.volume / 100.0)
                self._audio_player.setSourceDevice(self._audio_buf, QUrl())
                self._audio_player.play()
                self.statusBar().showMessage(
                    f"\U0001F50A Testing: {self.config.sound_preset} | Vol: {self.config.volume}% | Stereo: {self.config.stereo}", 3000)
        except Exception as e:
            logger.error("Audio test failed", exc_info=True)
            self.statusBar().showMessage(f"Audio test failed: {e}", 3000)

    def _browse_bgm(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Background Music", "",
                                              "Audio Files (*.mp3 *.wav *.m4a)")
        if path:
            self.bgm_edit.setText(path)

    def _open_output_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(OUTPUT_DIR)))

    # =================================================================
    # YouTube & Shorts helpers (v2.3)
    # =================================================================
    def _current_source_name(self) -> str:
        """First checked file, or the custom-code sentinel."""
        if self.config.use_custom:
            return "custom_code.py"
        for it in self._items:
            if it.checked:
                return os.path.basename(it.path)
        return "custom_code.py"

    def _autofill_headline(self):
        self.thumb_headline_edit.setText(derive_title(self._current_source_name()))

    def _save_thumbnail(self, kind: str):
        """Render a full-resolution thumbnail from the current settings."""
        from rendering import save_thumbnails
        try:
            strategy = self.strategies[self.config.mode]
            mp = strategy.build_panes(self.config, self._items, self.config.custom_code)
            if mp is None:
                raise RuntimeError("nothing to render - add a file or enable Custom Code")
            head = self.thumb_headline_edit.text().strip()
            if not head:
                head = derive_title(self._current_source_name())
                self.thumb_headline_edit.setText(head)
            name = derive_title(self._current_source_name()).replace(" ", "_") or "thumbnail"
            base = str(OUTPUT_DIR / name)
            paths = save_thumbnails(mp, self.config, base, headline=head,
                                    variants=kind)
            if paths:
                QMessageBox.information(self, "Thumbnail saved",
                                        "\n".join(os.path.basename(p) for p in paths)
                                        + f"\n\nFolder: {OUTPUT_DIR}")
            else:
                QMessageBox.warning(self, "Thumbnail", "Could not save the thumbnail.")
        except Exception as e:
            logger.error("Thumbnail generation failed", exc_info=True)
            QMessageBox.critical(self, "Thumbnail failed", str(e))

    def _update_shorts_guard(self, dur: float):
        """Two-tier Shorts duration warning (yellow >60s, red >180s)."""
        vertical = self.config.resolution.endswith("(9:16)")
        if not vertical:
            self.shorts_guard_lbl.setText("enable a 9:16 resolution for Shorts guard")
            self.shorts_guard_lbl.setStyleSheet("color: #a6adc8; font-size: 11px; font-family: monospace;")
            return
        stamp = format_time(dur)
        if dur > SHORTS_HARD_SEC:
            self.shorts_guard_lbl.setText(
                f"\u26a0 {stamp} - over {SHORTS_HARD_SEC}s: NOT eligible as a Short")
            self.shorts_guard_lbl.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 11px;")
        elif dur > SHORTS_WARN_SEC:
            self.shorts_guard_lbl.setText(
                f"\u26a0 {stamp} - over {SHORTS_WARN_SEC}s (fine up to {SHORTS_HARD_SEC}s)")
            self.shorts_guard_lbl.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 11px;")
        else:
            self.shorts_guard_lbl.setText(f"\u2713 {stamp} - fits classic Shorts (\u2264{SHORTS_WARN_SEC}s)")
            self.shorts_guard_lbl.setStyleSheet("color: #a6e3a1; font-size: 11px;")

    def _draw_shorts_guides(self, img):
        """Preview-only overlay of the Shorts UI safe zones (never exported)."""
        p = QPainter(img)
        w, h = img.width(), img.height()
        fill = QColor(255, 0, 90, 26)
        border = QColor(255, 0, 90, 140)
        zones = [
            QRect(0, 0, w, int(h * 0.12)),                      # title / sound
            QRect(0, h - int(h * 0.17), w, int(h * 0.17)),      # caption / description
            QRect(w - int(w * 0.18), int(h * 0.12),             # action rail
                  int(w * 0.18), int(h * 0.55)),
        ]
        pen = p.pen()
        for z in zones:
            p.fillRect(z, fill)
        p.setPen(border)
        for z in zones:
            p.drawRect(z)
        p.setPen(pen)
        p.end()

    # =================================================================
    # Export
    # =================================================================
    def _estimate_total_frames(self, items) -> int:
        """Rough pre-export estimate of the total frame count."""
        try:
            cfg = self.config
            from config import INTRO_DURATION, OUTRO_DURATION
            branding = (INTRO_DURATION if cfg.intro_enabled else 0.0) + \
                       (OUTRO_DURATION if cfg.outro_enabled else 0.0)
            total = 0
            rate = lambda wpm: max(1.0, wpm * 5 / 60.0)
            for it in items:
                if cfg.use_custom and it.path == "custom_code.py":
                    code = convert_shortcodes(cfg.custom_code)
                elif os.path.exists(it.path):
                    code = read_text_file(it.path, cfg.txt_clean)
                else:
                    continue
                chars = max(1, len(code))
                if cfg.mode == StudioMode.JR_VS_SR:
                    dur = max(chars / rate(cfg.jr_wpm), chars / rate(cfg.sr_wpm)) + 2.0
                elif cfg.mode == StudioMode.MULTI_WINDOW:
                    dur = chars / rate(cfg.wpm_mw) + 2.0
                elif cfg.mode == StudioMode.CODE_YT:
                    dur = chars / rate(cfg.wpm_yt) + 2.0
                else:
                    dur = chars / rate(cfg.wpm_txt) + 2.0
                total += int((dur + branding) * cfg.fps)
            if cfg.dual_render and cfg.output_format == "mp4":
                total *= 2
            return total
        except Exception:
            return 0

    def _start_export(self):
        if self.config.use_custom:
            items = [FileItem(path="custom_code.py", checked=True)]
        else:
            items = [it for it in self._items if it.checked]
        if not items:
            QMessageBox.information(self, "Nothing selected",
                                    "Check files to export or enable Custom Code.")
            return

        for it in self._items:
            if it.checked:
                it.status = "Pending"
        self._refresh_table()

        self.export_commands.clear()
        self._batch_cancelled = False
        self.batch_done = 0
        self.batch_start_time = _time.time()

        fmt = self.config.output_format
        date_str = datetime.now().strftime("%Y%m%d")
        dual = self.config.dual_render and fmt == "mp4"
        for item in items:
            base_name = os.path.splitext(os.path.basename(item.path))[0]
            lang = EXT_TO_LANGUAGE.get(os.path.splitext(item.path)[1].lower(), "text")
            try:
                out_name = self.config.output_template.format(name=base_name, date=date_str, lang=lang)
            except (KeyError, IndexError):
                out_name = f"{base_name}_{date_str}"
            if dual:
                yt_cfg, sh_cfg = make_dual_variants(self.config)
                for cfg_v, suffix, label_tag in ((yt_cfg, "_yt", "YouTube 16:9"),
                                                 (sh_cfg, "_shorts", "Shorts 9:16")):
                    out_path = str(OUTPUT_DIR / f"{out_name}{suffix}.mp4")
                    cmd = ExportCommand(item=item, output_path=out_path, config=copy.deepcopy(cfg_v))
                    cmd.status = "Pending"
                    self.export_commands.append(cmd)
            elif fmt == "png":
                out_path = str(OUTPUT_DIR / f"{out_name}_frames")
                cmd = ExportCommand(item=item, output_path=out_path, config=copy.deepcopy(self.config))
                cmd.status = "Pending"
                self.export_commands.append(cmd)
            else:
                out_path = str(OUTPUT_DIR / f"{out_name}.{fmt}")
                cmd = ExportCommand(item=item, output_path=out_path, config=copy.deepcopy(self.config))
                cmd.status = "Pending"
                self.export_commands.append(cmd)

        self.batch_total = len(self.export_commands)
        est_frames = self._estimate_total_frames(items)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, self.batch_total)
        self.progress_bar.setValue(0)
        self.export_btn.setEnabled(False)
        self.skip_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.batch_info_lbl.setText(
            f"Starting batch of {self.batch_total} ({fmt}) | \u2248{est_frames} frames total")
        self._process_export_queue()

    def _process_export_queue(self):
        if not self.export_commands:
            self.export_btn.setEnabled(True)
            self.skip_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.batch_info_lbl.setText("Batch complete! Files are in the output folder.")
            QMessageBox.information(self, "Done", "Batch export complete!")
            return

        self.current_command = self.export_commands.popleft()
        self.current_command.status = "Running"
        self.current_command.item.status = "Running"
        self._refresh_table()

        self.statusBar().showMessage(f"Preparing {os.path.basename(self.current_command.output_path)}...")
        QApplication.processEvents()

        strategy = self.strategies[self.current_command.config.mode]
        try:
            self.current_command.mp = strategy.build_panes(
                self.current_command.config, [self.current_command.item],
                self.current_command.config.custom_code)
        except Exception as e:
            logger.error(f"Failed to build panes for {self.current_command.output_path}", exc_info=True)
            self._on_item_failed(self.current_command, str(e))
            return

        if not self.current_command.mp:
            self._on_item_failed(self.current_command, "Empty renderer")
            return

        self._exporter = VideoExporter(self.current_command)
        self._exporter.progress.connect(self._on_export_progress)
        self._exporter.status.connect(lambda s: self.statusBar().showMessage(s))
        self._exporter.finished_ok.connect(lambda p: self._on_item_done(self.current_command, p))
        self._exporter.error.connect(lambda e: self._on_item_failed(self.current_command, e))
        self._exporter.start()

    def _on_export_progress(self, p):
        item_name = os.path.basename(self.current_command.output_path)
        self.statusBar().showMessage(f"Rendering {item_name}: {p}%")

        total_progress = self.batch_done + (p / 100.0)
        pct = int((total_progress / self.batch_total) * 100) if self.batch_total > 0 else 0

        elapsed = _time.time() - self.batch_start_time
        if total_progress > 0:
            eta = (elapsed / total_progress) * (self.batch_total - total_progress)
            eta_str = f"{int(eta // 60)}m {int(eta % 60)}s"
        else:
            eta_str = "..."

        self.batch_info_lbl.setText(
            f"Item {self.batch_done + 1}/{self.batch_total} | Overall: {pct}% | ETA: {eta_str}")
        self.progress_bar.setValue(int(total_progress))

    def _on_item_done(self, cmd, path):
        cmd.item.status = "Done"
        self.batch_done += 1
        self._refresh_table()
        self.progress_bar.setValue(self.batch_done)
        self._process_export_queue()

    def _on_item_failed(self, cmd, err):
        if self._batch_cancelled:
            cmd.item.status = "Cancelled"
            self._refresh_table()
            return

        cmd.item.status = "Skipped" if err == "Cancelled" else "Failed"
        self.batch_done += 1
        self._refresh_table()
        self.progress_bar.setValue(self.batch_done)
        self.statusBar().showMessage(f"Item {os.path.basename(cmd.output_path)} {cmd.item.status}.", 2000)
        self._process_export_queue()

    def _skip_current(self):
        if self._exporter:
            self.statusBar().showMessage(f"Skipping {os.path.basename(self.current_command.output_path)}...")
            self._exporter.cancel()

    def _cancel_export(self):
        self._batch_cancelled = True
        if self._exporter:
            self._exporter.cancel()
        self.export_commands.clear()
        if self.current_command:
            self.current_command.item.status = "Cancelled"
        self._refresh_table()
        self.export_btn.setEnabled(True)
        self.skip_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.batch_info_lbl.setText("Batch cancelled")
        self.statusBar().showMessage("Batch export cancelled", 3000)

    # =================================================================
    # Config <-> UI sync, project & settings persistence
    # =================================================================
    def _apply_config_to_ui(self):
        cfg = self.config
        self.mode_tabs.setCurrentIndex(list(StudioMode).index(cfg.mode))
        self.theme_cb.setCurrentText(cfg.theme)
        self.res_cb.setCurrentText(cfg.resolution)
        self.fps_sp.setValue(cfg.fps)
        self.sound_chk.setChecked(cfg.sound_enabled)
        self.preset_cb.setCurrentText(cfg.sound_preset)
        self.stereo_chk.setChecked(cfg.stereo)
        self.vol_sp.setValue(cfg.volume)
        self.encoder_cb.setCurrentText(cfg.encoder)
        self.outfmt_cb.setCurrentText(cfg.output_format)
        self.bgm_edit.setText(cfg.bgm_path)
        self.bgm_vol_sp.setValue(cfg.bgm_volume)
        self.bgm_duck_chk.setChecked(cfg.bgm_duck)
        self.use_custom_chk.setChecked(cfg.use_custom)
        self.custom_editor.setPlainText(cfg.custom_code)
        self.yt_extras_chk.setChecked(cfg.yt_extras)

        # Overlays
        self.pbar_chk.setChecked(cfg.progress_bar_enabled)
        self.pbar_color_edit.setText(cfg.progress_bar_color)

        # YouTube & Shorts (v2.3)
        self.quality_cb.setCurrentText(cfg.quality_preset if cfg.quality_preset in QUALITY_PRESETS else "Balanced")
        self.dual_render_chk.setChecked(cfg.dual_render)
        self.loudnorm_chk.setChecked(cfg.yt_loudnorm)
        self.wm_chk.setChecked(cfg.wm_enabled)
        self.wm_edit.setText(cfg.wm_text)
        self.wm_pos_cb.setCurrentText(cfg.wm_position if cfg.wm_position in WM_POSITIONS else "Top Right")
        self.wm_opacity_sp.setValue(int(cfg.wm_opacity))
        self.intro_chk.setChecked(cfg.intro_enabled)
        self.intro_edit.setText(cfg.intro_text)
        self.outro_chk.setChecked(cfg.outro_enabled)
        self.outro_edit.setText(cfg.outro_text)
        self.punch_zoom_chk.setChecked(cfg.punch_zoom)
        self.shorts_guides_chk.setChecked(cfg.shorts_guides)
        self.thumb_headline_edit.setText(cfg.thumb_headline)
        self.write_metadata_chk.setChecked(cfg.write_metadata)

        # Timing & Rhythm (v2.4)
        self.rhythm_style_cb.setCurrentText(
            cfg.rhythm_style if cfg.rhythm_style in RHYTHM_STYLES else "Natural")
        self.rhythm_intensity_sl.setValue(int(cfg.rhythm_intensity))
        self.rhythm_intensity_lbl.setText(f"{int(cfg.rhythm_intensity)}%")
        self.timing_fit_cb.setCurrentText(
            cfg.timing_fit if cfg.timing_fit in FIT_MODES else "Off")
        self.timing_target_sp.setValue(float(cfg.timing_target))

        # Keyboard & FX
        self.kb_enabled_chk.setChecked(cfg.kb_enabled)
        self.kb_layout_cb.setCurrentText(cfg.kb_layout)
        self.kb_position_cb.setCurrentText(cfg.kb_position)
        self.kb_opacity_sp.setValue(cfg.kb_opacity)
        self.glow_chk.setChecked(cfg.glow_enabled)
        self.cursor_style_cb.setCurrentText(cfg.cursor_style)
        self.cursor_blink_chk.setChecked(cfg.cursor_blink)

        # Custom WAV
        self.wav_chk.setChecked(cfg.use_custom_wav)
        paths = [p for p in cfg.custom_wav_paths.split("|") if p]
        if paths:
            self.wav_info_lbl.setText(f"{len(paths)} file(s) configured: " +
                                      ", ".join(os.path.basename(p) for p in paths[:4]) +
                                      (" ..." if len(paths) > 4 else ""))

        # Background ambience (v2.1)
        self.amb_chk.setChecked(getattr(cfg, "amb_enabled", False))
        if getattr(cfg, "amb_preset", "Rain") in list_ambience_presets():
            self.amb_preset_cb.setCurrentText(cfg.amb_preset)
        self.amb_path_edit.setText(getattr(cfg, "amb_path", ""))
        self.amb_evolve_chk.setChecked(bool(getattr(cfg, "amb_evolve", True)))
        self.amb_vol_sp.setValue(getattr(cfg, "amb_volume", 35))

        # Workflow presets combo (v2.1)
        self._rebuild_preset_combo()

        self.recursive_chk.setChecked(cfg.recursive_scan)
        self.depth_sp.setValue(cfg.scan_depth)
        self.output_template_edit.setText(cfg.output_template)

        self.mw_font_cb.setCurrentText(cfg.font_mw)
        self.mw_font_sz_auto.setChecked(cfg.font_sz_auto_mw)
        self.mw_font_sz_sp.setValue(cfg.font_sz_mw)
        self.mw_2_font_cb.setCurrentText(cfg.font_mw_2)
        self.mw_2_font_sz_auto.setChecked(cfg.font_sz_auto_mw_2)
        self.mw_2_font_sz_sp.setValue(cfg.font_sz_mw_2)
        self.mw_3_font_cb.setCurrentText(cfg.font_mw_3)
        self.mw_3_font_sz_auto.setChecked(cfg.font_sz_auto_mw_3)
        self.mw_3_font_sz_sp.setValue(cfg.font_sz_mw_3)
        self.mw_4_font_cb.setCurrentText(cfg.font_mw_4)
        self.mw_4_font_sz_auto.setChecked(cfg.font_sz_auto_mw_4)
        self.mw_4_font_sz_sp.setValue(cfg.font_sz_mw_4)
        self.mw_layout_cb.setCurrentText(cfg.layout_mw)
        self._update_mw_layout_visibility()
        self.mw_wpm_sp.setValue(cfg.wpm_mw)
        self.mw_typo_sp.setValue(cfg.typo_mw)
        self.mw_shorts_chk.setChecked(cfg.shorts_mw)
        self.diff_highlight_mw_chk.setChecked(cfg.diff_highlight_mw)
        self.sync_mw_chk.setChecked(cfg.sync_mw)
        self.mw_ratio_sp.setValue(cfg.mw_ratio)

        self.jr_font_cb.setCurrentText(cfg.font_jr)
        self.jr_font_sz_auto.setChecked(cfg.font_sz_auto_jr)
        self.jr_font_sz_sp.setValue(cfg.font_sz_jr)
        self.sr_font_cb.setCurrentText(cfg.font_sr)
        self.sr_font_sz_auto.setChecked(cfg.font_sz_auto_sr)
        self.sr_font_sz_sp.setValue(cfg.font_sz_sr)
        self.jr_layout_cb.setCurrentText(cfg.layout_jr)
        self.jr_wpm_sp.setValue(cfg.jr_wpm)
        self.sr_wpm_sp.setValue(cfg.sr_wpm)
        self.jr_typo_sp.setValue(cfg.typo_jr)
        self.jr_sound_cb.setCurrentText(cfg.jr_sound)
        self.sr_sound_cb.setCurrentText(cfg.sr_sound)
        self.jr_custom_editor.setPlainText(cfg.jr_custom_code)
        self.sr_custom_editor.setPlainText(cfg.sr_custom_code)

        self.yt_font_cb.setCurrentText(cfg.font_yt)
        self.yt_font_sz_auto.setChecked(cfg.font_sz_auto_yt)
        self.yt_font_sz_sp.setValue(cfg.font_sz_yt)
        self.yt_wpm_sp.setValue(cfg.wpm_yt)
        self.yt_typo_sp.setValue(cfg.typo_yt)
        self.yt_zoom_chk.setChecked(cfg.yt_zoom)
        self.yt_focus_chk.setChecked(cfg.yt_focus)

        self.txt_font_cb.setCurrentText(cfg.font_txt)
        self.txt_font_sz_auto.setChecked(cfg.font_sz_auto_txt)
        self.txt_font_sz_sp.setValue(cfg.font_sz_txt)
        self.txt_wpm_sp.setValue(cfg.wpm_txt)
        self.txt_typo_sp.setValue(cfg.typo_txt)
        self.txt_shorts_chk.setChecked(cfg.shorts_txt)
        self.ascii_chk.setChecked(cfg.ascii_art)
        self.txt_clean_chk.setChecked(cfg.txt_clean)
        self.txt_markdown_chk.setChecked(cfg.txt_markdown)
        self.txt_crt_chk.setChecked(cfg.txt_crt)
        self.txt_bubbles_chk.setChecked(cfg.txt_bubbles)

    def _save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Studio Project (*.studio)")
        if not path:
            return
        config_dict = asdict(self.config)
        config_dict["mode"] = self.config.mode.value
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)
        self.statusBar().showMessage("Project saved!", 3000)

    def _load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Studio Project (*.studio)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.config = safe_config_from_dict(data)
        except Exception:
            logger.error("Failed to load project file", exc_info=True)
            QMessageBox.warning(self, "Load Error", "Failed to load project. The file might be corrupted.")
            return

        self._apply_config_to_ui()
        self.statusBar().showMessage("Project loaded!", 3000)
        self._invalidate_preview()

    def _load_settings(self):
        """Restore full app state (v1 only kept mode+theme)."""
        if not SETTINGS_FILE.exists():
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            geom = data.pop("_geometry", None)
            if geom:
                try:
                    from PySide6.QtCore import QByteArray
                    self.restoreGeometry(QByteArray.fromHex(geom.encode("ascii")))
                except Exception:
                    pass
            self.config = safe_config_from_dict(data)
            self._apply_config_to_ui()
        except Exception:
            logger.error("Failed to load settings.json", exc_info=True)

    def closeEvent(self, e):
        try:
            data = asdict(self.config)
            data["mode"] = self.config.mode.value
            data["_geometry"] = bytes(self.saveGeometry().toHex()).decode("ascii")
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            logger.error("Failed to save settings", exc_info=True)
        super().closeEvent(e)


# =====================================================================
# ENTRY POINT
# =====================================================================
def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor("#1e1e2e"))
    pal.setColor(QPalette.ColorRole.WindowText, QColor("#cdd6f4"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#313244"))
    pal.setColor(QPalette.ColorRole.Text, QColor("#cdd6f4"))
    pal.setColor(QPalette.ColorRole.Button, QColor("#313244"))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor("#cdd6f4"))
    pal.setColor(QPalette.ColorRole.Highlight, QColor("#89b4fa"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#1e1e2e"))
    app.setPalette(pal)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
