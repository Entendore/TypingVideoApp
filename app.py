#!/usr/bin/env python3
"""TypingVideoApp v1.0.0 — single-file typing-video studio (PySide6).

Source code in, upload-ready video out: syntax-highlighted code that types
itself with a synchronized on-screen keyboard, mechanical key sounds and 34
procedural ambience soundscapes; exports MP4 / GIF / PNG with hardware-encoder
auto-detection, parallel + batch + dual YouTube/Shorts rendering, thumbnail
studio and an SEO metadata writer.

Quick start:
    python app.py                                                      # GUI
    python app.py --headless demo.py -o out/demo.mp4 --ambience Rain   # CLI
    python app.py --headless --list-presets|--list-encoders|--list-themes|--list-sounds

Docs: README.md (full manual)  ·  Tests: python -m pytest test_app.py
"""
from __future__ import annotations

# Legacy module-name aliases: any dynamic `import config` or string-form
# patch target ("audio.render_ambience") resolves to this same module,
# keeping third-party code and tests written against the ten-file edition
# working unchanged.
import sys as _sys
for _legacy_name in ("config", "metadata", "rendering", "animation",
                     "audio", "encoders", "exporter", "ui", "main"):
    _sys.modules.setdefault(_legacy_name, _sys.modules[__name__])
del _sys, _legacy_name

##############
#                              ══ 1 - CONFIG ══                             
# StudioConfig, constants, 12 themes, text utilities, workflow presets
# (was: config.py in the ten-file edition)
##############

"""Foundation layer: StudioConfig, constants, 12 themes, text/grapheme
utilities and workflow presets (built-in + user JSON presets)."""


#==============================================================================
# ── CONFIG — StudioConfig dataclass, constants, modes
#    (merged from studio/config.py in the v2.5 ten-file edition)
#==============================================================================

"""Configuration, constants and enums for TypingVideoApp.

This module is Qt-free so it can be unit-tested headlessly.
"""

from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path

# ------------------------------------------------------------------ paths
CWD = Path.cwd()
INPUT_DIR = CWD / "input"
OUTPUT_DIR = CWD / "output"
TEMP_DIR = CWD / "temp"
SETTINGS_FILE = CWD / "settings.json"

for _d in (INPUT_DIR, OUTPUT_DIR, TEMP_DIR):
    _d.mkdir(parents=True, exist_ok=True)

APP_NAME = "TypingVideoApp"
APP_VERSION = "1.1.0"

# ------------------------------------------------------------------ timing
# Rhythm styles for the typing engine (see animation.py)
RHYTHM_STYLES = ["Classic", "Natural", "Cinematic"]
# Auto-fit modes (see animation.py)
FIT_MODES = ["Off", "Target Duration", "Audio Length"]
# UI bounds for manual WPM spinboxes
WPM_MIN, WPM_MAX = 30, 300

# ------------------------------------------------------------------ youtube
# Quality presets (map to CRF/CQ per encoder, see encoders.py)
QUALITY_PRESETS = ["High", "Balanced", "Small"]
# Branding card durations (seconds) — kept Qt-free so batch.py can use them
INTRO_DURATION = 1.5
OUTRO_DURATION = 2.2
# Shorts guard thresholds (seconds): yellow > WARN, red > HARD limit
SHORTS_WARN_SEC = 60
SHORTS_HARD_SEC = 180
LOUDNORM_FILTER = "loudnorm=I=-14:TP=-1.5:LRA=11"
WM_POSITIONS = ["Top Left", "Top Right", "Bottom Left", "Bottom Right"]
# Thumbnail canvas sizes (w, h)
THUMB_YT_SIZE = (1280, 720)
THUMB_SHORTS_SIZE = (1080, 1920)

# ------------------------------------------------------------------ modes
class StudioMode(Enum):
    MULTI_WINDOW = "Multi-Window Code Comparison"
    JR_VS_SR = "Junior vs Senior Dev"
    CODE_YT = "Single Window Code (YouTube Optimised)"
    TEXT_EMOJI = "Text & Emoji (Single Window)"


SUPPORTED_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".sh", ".bash", ".zsh",
    ".sql", ".html", ".htm", ".css", ".scss", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".txt", ".md", ".lua", ".dart", ".r", ".m",
    ".csv", ".asc", ".ascii", ".art", ".ans", ".nfo", ".diz", ".emoji", ".emo"
})

EXT_TO_LANGUAGE = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".c": "c", ".cpp": "cpp",
    ".cs": "csharp", ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".kt": "kotlin", ".sh": "bash", ".sql": "sql", ".html": "html", ".css": "css", ".scss": "scss",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown", ".txt": "text",
    ".csv": "text", ".asc": "text", ".ascii": "text", ".art": "text", ".ans": "text",
    ".nfo": "text", ".diz": "text", ".emoji": "text", ".emo": "text"
}

# Category groups used by the batch-file filter row ("Type" combo).
# Every supported extension must belong to at least one category so the
# "Sync Filter to Mode" button can always produce a non-empty view.
FILE_CATEGORIES = {
    "All": set(SUPPORTED_EXTENSIONS),
    "Code": {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
             ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".sh", ".bash",
             ".zsh", ".lua", ".dart", ".r", ".m"},
    "Markup/Web": {".html", ".htm", ".css", ".scss", ".md"},
    "Config/Data": {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sql", ".csv"},
    "Text/Art": {".txt", ".asc", ".ascii", ".art", ".ans", ".nfo", ".diz", ".emoji", ".emo"},
}

MULTI_WINDOW_LAYOUTS = {
    "1 Window (Single)": 1,
    "2 Windows (Split)": 2,
    "4 Windows (Grid)": 4,
    "Git Conflict (3-Pane)": 3
}
JR_VS_SR_LAYOUTS = ["Side by Side (50/50)", "Stacked (50/50)", "Junior Big (70/30)", "Senior Big (70/30)"]
RESOLUTIONS = {
    "1920x1080": (1920, 1080), "1280x720": (1280, 720), "3840x2160": (3840, 2160),
    "1080x1920 (9:16)": (1080, 1920), "720x1280 (9:16)": (720, 1280)
}

# Display names shown in the GUI. "Auto (Hardware)" probes the machine at
# export time and picks the fastest working hardware encoder, falling back to
# software when none is available (see encoders.py).
ENCODER_AUTO = "Auto (Hardware)"
ENCODER_SOFTWARE = "YouTube Optimised (H.264/AAC)"
ENCODERS = [
    ENCODER_AUTO,
    ENCODER_SOFTWARE,
    "NVENC (NVIDIA)",
    "QSV (Intel)",
    "AMF (AMD)",
    "VAAPI (Linux)",
    "VideoToolbox (macOS)",
]

AUDIO_SAMPLE_RATE = 48000

CUSTOM_WAV_PRESET = "Custom (WAV)"
CURSOR_STYLES = ["Beam", "Block", "Underline", "Outline"]
OUTPUT_FORMATS = ["mp4", "gif", "png"]
# Rough throughput used only for the pre-export "estimated frames" hint.
DEFAULT_PREVIEW_WIDTH = 960


# ------------------------------------------------------------------ config
@dataclass
class StudioConfig:
    mode: StudioMode = StudioMode.CODE_YT
    theme: str = "Dracula"
    resolution: str = "1920x1080"
    fps: int = 30
    sound_enabled: bool = True
    sound_preset: str = "Mechanical"
    stereo: bool = False
    volume: int = 50
    bgm_path: str = ""
    bgm_volume: int = 30
    bgm_duck: bool = True
    use_custom: bool = False
    custom_code: str = ""

    kb_enabled: bool = False
    kb_layout: str = "QWERTY"
    kb_position: str = "Bottom Center"
    kb_opacity: float = 0.82

    # Multi-Window Settings
    layout_mw: str = "2 Windows (Split)"
    wpm_mw: int = 100
    typo_mw: float = 0.0
    shorts_mw: bool = False
    diff_highlight_mw: bool = True
    sync_mw: bool = True
    mw_ratio: int = 50

    # Multi-Window Fonts (Up to 4 panes)
    font_mw: str = "Consolas"
    font_sz_auto_mw: bool = False
    font_sz_mw: int = 22
    font_mw_2: str = "Consolas"
    font_sz_auto_mw_2: bool = False
    font_sz_mw_2: int = 22
    font_mw_3: str = "Consolas"
    font_sz_auto_mw_3: bool = False
    font_sz_mw_3: int = 22
    font_mw_4: str = "Consolas"
    font_sz_auto_mw_4: bool = False
    font_sz_mw_4: int = 22

    # Jr vs Sr Settings
    layout_jr: str = "Side by Side (50/50)"
    jr_wpm: int = 90
    sr_wpm: int = 130
    typo_jr: float = 0.03
    jr_custom_code: str = ""
    sr_custom_code: str = ""
    hud_jr: bool = True
    jr_sound: str = "Mechanical"
    sr_sound: str = "ASMR Deep Thock"

    # Jr vs Sr Fonts
    font_jr: str = "Consolas"
    font_sz_auto_jr: bool = False
    font_sz_jr: int = 22
    font_sr: str = "Consolas"
    font_sz_auto_sr: bool = False
    font_sz_sr: int = 22

    # Code YT Settings
    wpm_yt: int = 100
    typo_yt: float = 0.0
    shorts_yt: bool = False
    yt_zoom: bool = False
    yt_focus: bool = False
    font_yt: str = "Consolas"
    font_sz_auto_yt: bool = False
    font_sz_yt: int = 22

    # Text & Emoji Settings
    wpm_txt: int = 100
    typo_txt: float = 0.0
    shorts_txt: bool = False
    ascii_art: bool = False
    txt_markdown: bool = False
    ansi_colors: bool = False                # render ANSI ESC[...m colour sequences
    txt_crt: bool = False
    txt_bubbles: bool = False
    txt_clean: bool = True
    font_txt: str = "Consolas"
    font_sz_auto_txt: bool = False
    font_sz_txt: int = 22

    # Global Extras
    yt_extras: bool = True
    recursive_scan: bool = True
    scan_depth: int = 10
    output_template: str = "{name}_{date}"

    # ---- NEW in v2.0 -------------------------------------------------
    # Overlays
    progress_bar_enabled: bool = False
    progress_bar_color: str = "accent"      # "accent" (theme) or hex like "#ff79c6"
    # Visual effects
    glow_enabled: bool = True               # ambient glow behind the code window
    cursor_style: str = "Beam"              # Beam | Block | Underline | Outline
    cursor_blink: bool = False
    # Custom key sounds
    use_custom_wav: bool = False
    custom_wav_paths: str = ""              # paths joined with "|"
    # Export
    output_format: str = "mp4"              # mp4 | gif | png
    encoder: str = ENCODER_AUTO
    # Background ambience (layered under the key sounds)
    amb_enabled: bool = False
    amb_preset: str = "Rain"
    amb_path: str = ""                      # custom audio file overrides the preset
    amb_evolve: bool = True                 # procedurally evolve the file (no obvious looping)
    amb_volume: int = 35                    # 0-100
    amb_music: bool = True                  # procedural music layer under every bed
    amb_music_volume: int = 45              # 0-100 (music level inside the bed)

    # ---- NEW in v2.3 (YouTube & Shorts pack) -------------------------
    # Upload-ready encoding
    quality_preset: str = "Balanced"        # High | Balanced | Small (CRF/CQ map)
    yt_loudnorm: bool = True                # normalize audio to -14 LUFS (mp4)
    # One-click batch: render a 16:9 YouTube video AND a 9:16 Shorts version
    dual_render: bool = False
    # Branding overlays
    wm_enabled: bool = False                # persistent @handle watermark
    wm_text: str = ""                       # e.g. "@yourhandle"
    wm_position: str = "Top Right"
    wm_opacity: int = 40                    # 0-100
    intro_enabled: bool = False             # 1.5s title card before typing
    intro_text: str = ""                    # defaults to the source title
    intro_handle: str = ""                  # defaults to wm_text
    outro_enabled: bool = False             # 2.2s outro with subscribe pill
    outro_text: str = "Thanks for watching!"
    # Shorts assistant
    punch_zoom: bool = False                # subtle Ken Burns punch-in (9:16)
    shorts_guides: bool = False             # preview-only safe-zone overlays
    # Thumbnail studio
    thumb_headline: str = ""                # auto-filled from the source name
    # SEO metadata written next to each mp4 export
    write_metadata: bool = True

    # ---- NEW in v2.4 (Smart Timing) ----------------------------------
    # Typing rhythm personality of the animator
    rhythm_style: str = "Natural"           # Classic | Natural | Cinematic
    rhythm_intensity: int = 100             # 50-150 % (0 expr -> 150 expressive)
    # Auto-adjust timings: solve WPM so the video hits a duration exactly
    timing_fit: str = "Off"                 # Off | Target Duration | Audio Length
    timing_target: float = 60.0             # seconds (Target Duration mode)

    # ---- NEW in v1.0 (Parallel rendering) ---------------------------
    # GUI batch: how many renders may run at the same time (1 = sequential;
    # 2-4 overlaps e.g. the YouTube/Shorts variants of dual rendering).  The
    # frame-render threads are divided between the running renders so the
    # machine is never oversubscribed.
    parallel_renders: int = 1               # 1-4


def safe_config_from_dict(data: dict) -> StudioConfig:
    """Build a StudioConfig from a dict, silently dropping unknown keys.

    Makes project/settings files forward & backward compatible instead of
    raising TypeError when fields change between versions (fixes a bug in
    the v1 `_load_project` implementation).
    """
    known = {f.name for f in fields(StudioConfig)}
    payload = {k: v for k, v in (data or {}).items() if k in known}
    if "mode" in payload and isinstance(payload["mode"], str):
        try:
            payload["mode"] = StudioMode(payload["mode"])
        except ValueError:
            payload["mode"] = StudioMode.CODE_YT
    return StudioConfig(**payload)

#==============================================================================
# ── THEMES — 12 color themes
#    (merged from studio/themes.py in the v2.5 ten-file edition)
#==============================================================================

"""Color themes for rendered code windows.

Every theme defines the same key set:
  background, foreground, comment, keyword, string, number, function,
  builtin, decorator, operator, class_name, line_number, current_line,
  cursor, title_bar, title_text, window_border, junior_accent,
  senior_accent, error
"""

DEFAULT_THEME = "Dracula"

THEMES = {
    "Dracula": {
        "background": "#282a36", "foreground": "#f8f8f2", "comment": "#6272a4",
        "keyword": "#ff79c6", "string": "#f1fa8c", "number": "#bd93f9",
        "function": "#50fa7b", "builtin": "#8be9fd", "decorator": "#50fa7b",
        "operator": "#ff79c6", "class_name": "#8be9fd", "line_number": "#6272a4",
        "current_line": "#44475a", "cursor": "#f8f8f2", "title_bar": "#21222c",
        "title_text": "#8be9fd", "window_border": "#191a21",
        "junior_accent": "#8be9fd", "senior_accent": "#50fa7b", "error": "#ff5555",
    },
    "One Dark": {
        "background": "#282c34", "foreground": "#abb2bf", "comment": "#5c6370",
        "keyword": "#c678dd", "string": "#98c379", "number": "#d19a66",
        "function": "#61afef", "builtin": "#e5c07b", "decorator": "#56b6c2",
        "operator": "#c678dd", "class_name": "#e5c07b", "line_number": "#4b5263",
        "current_line": "#2c313c", "cursor": "#528bff", "title_bar": "#21252b",
        "title_text": "#61afef", "window_border": "#181a1f",
        "junior_accent": "#61afef", "senior_accent": "#98c379", "error": "#e06c75",
    },
    "Tokyo Night": {
        "background": "#1a1b26", "foreground": "#c0caf5", "comment": "#565f89",
        "keyword": "#bb9af7", "string": "#9ece6a", "number": "#ff9e64",
        "function": "#7aa2f7", "builtin": "#2ac3de", "decorator": "#bb9af7",
        "operator": "#89ddff", "class_name": "#2ac3de", "line_number": "#414868",
        "current_line": "#292e42", "cursor": "#c0caf5", "title_bar": "#16161e",
        "title_text": "#7aa2f7", "window_border": "#101014",
        "junior_accent": "#7aa2f7", "senior_accent": "#9ece6a", "error": "#f7768e",
    },
    "Nord": {
        "background": "#2e3440", "foreground": "#d8dee9", "comment": "#616e88",
        "keyword": "#81a1c1", "string": "#a3be8c", "number": "#b48ead",
        "function": "#88c0d0", "builtin": "#8fbcbb", "decorator": "#81a1c1",
        "operator": "#81a1c1", "class_name": "#8fbcbb", "line_number": "#4c566a",
        "current_line": "#3b4252", "cursor": "#d8dee9", "title_bar": "#242933",
        "title_text": "#88c0d0", "window_border": "#232831",
        "junior_accent": "#88c0d0", "senior_accent": "#a3be8c", "error": "#bf616a",
    },
    "Monokai": {
        "background": "#272822", "foreground": "#f8f8f2", "comment": "#75715e",
        "keyword": "#f92672", "string": "#e6db74", "number": "#ae81ff",
        "function": "#a6e22e", "builtin": "#66d9ef", "decorator": "#a6e22e",
        "operator": "#f92672", "class_name": "#66d9ef", "line_number": "#75715e",
        "current_line": "#3e3d32", "cursor": "#f8f8f0", "title_bar": "#1e1f1c",
        "title_text": "#a6e22e", "window_border": "#141511",
        "junior_accent": "#f92672", "senior_accent": "#a6e22e", "error": "#f92672",
    },
    "GitHub Dark": {
        "background": "#0d1117", "foreground": "#c9d1d9", "comment": "#8b949e",
        "keyword": "#ff7b72", "string": "#a5d6ff", "number": "#79c0ff",
        "function": "#d2a8ff", "builtin": "#79c0ff", "decorator": "#ffa657",
        "operator": "#ff7b72", "class_name": "#ffa657", "line_number": "#484f58",
        "current_line": "#161b22", "cursor": "#c9d1d9", "title_bar": "#010409",
        "title_text": "#58a6ff", "window_border": "#30363d",
        "junior_accent": "#58a6ff", "senior_accent": "#3fb950", "error": "#f85149",
    },
    "Solarized Dark": {
        "background": "#002b36", "foreground": "#93a1a1", "comment": "#586e75",
        "keyword": "#859900", "string": "#2aa198", "number": "#d33682",
        "function": "#268bd2", "builtin": "#b58900", "decorator": "#cb4b16",
        "operator": "#859900", "class_name": "#b58900", "line_number": "#586e75",
        "current_line": "#073642", "cursor": "#93a1a1", "title_bar": "#001f27",
        "title_text": "#268bd2", "window_border": "#001419",
        "junior_accent": "#268bd2", "senior_accent": "#859900", "error": "#dc322f",
    },
    "Catppuccin Mocha": {
        "background": "#1e1e2e", "foreground": "#cdd6f4", "comment": "#6c7086",
        "keyword": "#cba6f7", "string": "#a6e3a1", "number": "#fab387",
        "function": "#89b4fa", "builtin": "#94e2d5", "decorator": "#f5c2e7",
        "operator": "#89dceb", "class_name": "#f9e2af", "line_number": "#6c7086",
        "current_line": "#313244", "cursor": "#f5e0dc", "title_bar": "#181825",
        "title_text": "#89b4fa", "window_border": "#11111b",
        "junior_accent": "#89b4fa", "senior_accent": "#a6e3a1", "error": "#f38ba8",
    },
    "Gruvbox Dark": {
        "background": "#282828", "foreground": "#ebdbb2", "comment": "#928374",
        "keyword": "#fb4934", "string": "#b8bb26", "number": "#d3869b",
        "function": "#fabd2f", "builtin": "#8ec07c", "decorator": "#8ec07c",
        "operator": "#fb4934", "class_name": "#fabd2f", "line_number": "#928374",
        "current_line": "#3c3836", "cursor": "#ebdbb2", "title_bar": "#1d2021",
        "title_text": "#fabd2f", "window_border": "#161819",
        "junior_accent": "#fabd2f", "senior_accent": "#b8bb26", "error": "#fb4934",
    },
    "Rosé Pine": {
        "background": "#191724", "foreground": "#e0def4", "comment": "#6e6a86",
        "keyword": "#c4a7e7", "string": "#f6c177", "number": "#eb6f92",
        "function": "#9ccfd8", "builtin": "#ebbcba", "decorator": "#ebbcba",
        "operator": "#c4a7e7", "class_name": "#ebbcba", "line_number": "#6e6a86",
        "current_line": "#1f1d2e", "cursor": "#e0def4", "title_bar": "#1f1d2e",
        "title_text": "#c4a7e7", "window_border": "#110f1a",
        "junior_accent": "#c4a7e7", "senior_accent": "#9ccfd8", "error": "#eb6f92",
    },
    "Everforest Dark": {
        "background": "#2d353b", "foreground": "#d3c6aa", "comment": "#7a8478",
        "keyword": "#e67e80", "string": "#a7c080", "number": "#d699b6",
        "function": "#83c092", "builtin": "#dbbc7f", "decorator": "#e69875",
        "operator": "#e67e80", "class_name": "#dbbc7f", "line_number": "#7a8478",
        "current_line": "#343f44", "cursor": "#d3c6aa", "title_bar": "#232a2e",
        "title_text": "#83c092", "window_border": "#1d252a",
        "junior_accent": "#83c092", "senior_accent": "#a7c080", "error": "#e67e80",
    },
    "Kanagawa": {
        "background": "#1f1f28", "foreground": "#dcd7ba", "comment": "#727169",
        "keyword": "#957fb8", "string": "#98bb6c", "number": "#d27e99",
        "function": "#7e9cd8", "builtin": "#7aa89f", "decorator": "#ffa066",
        "operator": "#957fb8", "class_name": "#7aa89f", "line_number": "#727169",
        "current_line": "#2a2a37", "cursor": "#dcd7ba", "title_bar": "#16161d",
        "title_text": "#7e9cd8", "window_border": "#101017",
        "junior_accent": "#7e9cd8", "senior_accent": "#98bb6c", "error": "#e46876",
    },
}


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES[DEFAULT_THEME])

#==============================================================================
# ── UTILS — text/grapheme helpers, logging
#    (merged from studio/utils.py in the v2.5 ten-file edition)
#==============================================================================

"""Shared helpers: logging, grapheme handling, emoji shortcodes, file reading,
lexer factory and time formatting (Qt-free)."""

import logging
import os
import re
import sys
import unicodedata
from bisect import bisect_right
from functools import lru_cache, partial
from typing import List, Optional

# ------------------------------------------------------------------ logging
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("TypingVideoApp")
    logger.setLevel(logging.DEBUG)

    # avoid duplicate handlers on reload
    if logger.handlers:
        return logger

    file_handler = logging.FileHandler("typingvideoapp.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(logging.Formatter("[!] %(levelname)s: %(message)s"))
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()

# ------------------------------------------------------------------ text
ZWJ = "\u200d"
VS16 = "\ufe0f"

EMOJI_SHORTCODES = {
    ":rocket:": "\U0001f680", ":fire:": "\U0001f525", ":sparkles:": "\u2728",
    ":heart:": "\u2764\ufe0f", ":check:": "\u2705", ":tada:": "\U0001f389",
    ":eyes:": "\U0001f440", ":brain:": "\U0001f9e0", ":warning:": "\u26a0\ufe0f",
    ":100:": "\U0001f4af", ":thinking:": "\U0001f914", ":bug:": "\U0001f41b",
}


def split_graphemes(text: str) -> List[str]:
    """Split into user-perceived characters (emoji ZWJ sequences kept intact)."""
    graphemes, i, n = [], 0, len(text)
    while i < n:
        c, i = text[i], i + 1
        while i < n:
            nxt = text[i]
            if nxt == ZWJ or nxt == VS16 or unicodedata.combining(nxt) != 0:
                c += nxt
                i += 1
                if c[-1] == ZWJ and i < n:
                    c += text[i]
                    i += 1
            else:
                break
        graphemes.append(c)
    return graphemes


def is_emoji(char: str) -> bool:
    """True for real emoji / pictographs, False for plain symbols.

    Only category ``So`` (Symbol, other: the block where emoji live) plus
    ZWJ / VS16 sequences count.  Math (``=`` ``+`` ``<`` ``>`` ``|``),
    modifier (``^`` ``´``) and currency (``$`` ``€``) symbols used to be
    classified as emoji here, which fired the "pop" scale animation on
    every operator typed — the reported glitchy ``=`` visuals.
    """
    if not char:
        return False
    if ZWJ in char or VS16 in char:
        return True
    cat = unicodedata.category(char[0])
    return cat.startswith("So")


def convert_shortcodes(text: str) -> str:
    for code, emoji in EMOJI_SHORTCODES.items():
        text = text.replace(code, emoji)
    return text


# ------------------------------------------------------------------ ANSI
# ANSI terminal art (.ans / .nfo exports, neofetch dumps, ...).  Sequences
# look like ESC[<codes>m and must never reach the typing timeline as visible
# characters — they are either translated into per-character colors or
# stripped, depending on the `ansi_colors` toggle.
ANSI_SEQ_RE = re.compile(r"\x1b\[[0-9;]*m")

ANSI_COLORS_16 = {
    "30": "#000000", "31": "#ff5555", "32": "#50fa7b", "33": "#f1fa8c",
    "34": "#bd93f9", "35": "#ff79c6", "36": "#8be9fd", "37": "#f8f8f2",
    "90": "#6272a4", "91": "#ff6e6e", "92": "#69ff94", "93": "#ffffa5",
    "94": "#d6acff", "95": "#ff92df", "96": "#a4ffff", "97": "#ffffff",
}


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences, leaving only visible characters."""
    return ANSI_SEQ_RE.sub("", text)


def parse_ansi(text: str):
    """Split ANSI-styled text into visible characters + per-char color hex.

    Returns ``(visible_text, colors)`` where ``colors[i]`` is the hex string
    (or ``None`` for default) of ``visible_text[i]``.  Unterminated sequences
    and unknown codes are ignored gracefully.
    """
    chars: List[str] = []
    colors: List[Optional[str]] = []
    current: Optional[str] = None
    pos = 0
    for m in ANSI_SEQ_RE.finditer(text):
        for ch in text[pos:m.start()]:
            chars.append(ch)
            colors.append(current)
        codes = m.group(0)[2:-1].split(";")
        if any(c == "0" or c == "" for c in codes):
            current = None
        for c in codes:
            if c in ANSI_COLORS_16:
                current = ANSI_COLORS_16[c]
        pos = m.end()
    for ch in text[pos:]:
        chars.append(ch)
        colors.append(current)
    return "".join(chars), colors


def read_text_file(path: str, clean: bool = True) -> str:
    ext = os.path.splitext(path)[1].lower()
    enc = "cp437" if ext in (".nfo", ".diz") else "utf-8"
    try:
        with open(path, "r", encoding=enc) as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    text = convert_shortcodes(text)
    if clean and ext not in (".asc", ".ascii", ".art", ".ans", ".nfo", ".diz", ".emoji", ".emo"):
        text = text.replace("\xa0", " ").replace("\xad", "")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = "\n".join(line.rstrip() for line in text.splitlines())
    return text


class LexerFactory:
    """Cached pygments lexers (Flyweight)."""

    @staticmethod
    @lru_cache(maxsize=50)
    def get_lexer(lang: str):
        try:
            from pygments.lexers import get_lexer_by_name
        except ImportError:
            return None
        try:
            return get_lexer_by_name(lang, stripall=False)
        except Exception:
            try:
                return get_lexer_by_name("text", stripall=False)
            except Exception:
                return None


# ------------------------------------------------------------------ time fmt
def format_time(sec: float) -> str:
    sec = max(0, int(sec))
    return f"{sec // 60}:{sec % 60:02d}"


def human_duration(sec: float) -> str:
    sec = max(0, int(sec))
    return f"{sec // 3600}h {(sec % 3600) // 60}m {sec % 60}s"

#==============================================================================
# ── PRESETS — built-in + user workflow presets
#    (merged from studio/presets.py in the v2.5 ten-file edition)
#==============================================================================

"""Workflow presets: one-click configurations for common outputs.

A preset is a *partial* dict of StudioConfig fields — it is applied on top of
the current configuration so it stays forward-compatible when new fields are
added (unknown keys are ignored by ``safe_config_from_dict``).

Built-in presets ship with the app; user presets are stored as JSON files in
the ``presets/`` directory next to the app (Qt-free, unit-testable).
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional


PRESETS_DIR = Path(__file__).resolve().parent / "presets"

# ------------------------------------------------------------------ built-ins
BUILTIN_PRESETS: Dict[str, dict] = {
    "Default": {},

    "YouTube 1080p Code": {
        "mode": "Single Window Code (YouTube Optimised)",
        "resolution": "1920x1080",
        "fps": 30,
        "theme": "Tokyo Night",
        "wpm_yt": 100,
        "font_yt": "JetBrains Mono",
        "sound_enabled": True,
        "sound_preset": "Mechanical",
        "glow_enabled": True,
        "output_format": "mp4",
        "yt_extras": True,
        "quality_preset": "Balanced",
        "yt_loudnorm": True,
        "write_metadata": True,
    },

    "Shorts Machine (Dual)": {
        # one click -> every checked file renders as 16:9 YouTube + 9:16 Shorts
        "mode": "Single Window Code (YouTube Optimised)",
        "resolution": "1920x1080",
        "fps": 30,
        "theme": "Catppuccin Mocha",
        "wpm_yt": 120,
        "output_format": "mp4",
        "quality_preset": "Balanced",
        "dual_render": True,
        "punch_zoom": True,
        "intro_enabled": True,
        "outro_enabled": True,
        "wm_enabled": True,
        "progress_bar_enabled": True,
        "write_metadata": True,
        # v2.4: auto-adjust timings to a Shorts-safe length (55s < 60s limit,
        # intro/outro cards included in the target)
        "rhythm_style": "Natural",
        "timing_fit": "Target Duration",
        "timing_target": 55.0,
    },

    "Shorts Hook (9:16)": {
        "mode": "Single Window Code (YouTube Optimised)",
        "resolution": "1080x1920 (9:16)",
        "fps": 30,
        "theme": "Dracula",
        "wpm_yt": 130,
        "output_format": "mp4",
        "quality_preset": "Balanced",
        "punch_zoom": True,
        "shorts_guides": True,
        "intro_enabled": True,
        "outro_enabled": True,
        "yt_loudnorm": True,
        "write_metadata": True,
        # v2.4: land under the 60s Shorts limit automatically
        "rhythm_style": "Natural",
        "timing_fit": "Target Duration",
        "timing_target": 55.0,
    },

    "Shorts / TikTok 9:16": {
        "resolution": "1080x1920 (9:16)",
        "fps": 30,
        "font_sz_yt": 30,
        "font_sz_txt": 30,
        "progress_bar_enabled": True,
        "output_format": "mp4",
    },

    "ASMR Lo-Fi": {
        "sound_enabled": True,
        "sound_preset": "ASMR Deep Thock",
        "stereo": True,
        "volume": 60,
        "amb_enabled": True,
        "amb_preset": "Rain",
        "amb_volume": 30,
        "theme": "Rosé Pine",
        "glow_enabled": True,
        "cursor_style": "Beam",
    },

    "GIF Loop for README": {
        "output_format": "gif",
        "fps": 15,
        "resolution": "1280x720",
        "sound_enabled": False,
        "yt_extras": False,
        "glow_enabled": False,
        "wpm_yt": 140,
        # v2.4: keep the loop short no matter how big the snippet is
        "timing_fit": "Target Duration",
        "timing_target": 10.0,
    },

    "Fast Draft (Silent)": {
        "sound_enabled": False,
        "amb_enabled": False,
        "fps": 24,
        "yt_extras": False,
        "glow_enabled": False,
        "output_format": "mp4",
    },

    "Cinematic Code (4K)": {
        "resolution": "3840x2160",
        "fps": 60,
        "theme": "Kanagawa",
        "font_sz_auto_yt": True,
        "glow_enabled": True,
        "cursor_style": "Block",
        "encoder": "Auto (Hardware)",
        "output_format": "mp4",
        # v2.4: expressive rhythm with thinking pauses + warm-up
        "rhythm_style": "Cinematic",
        "rhythm_intensity": 120,
    },

    "Podcast Room": {
        "sound_enabled": True,
        "sound_preset": "Studio ASMR",
        "amb_enabled": True,
        "amb_preset": "Quiet Room",
        "amb_volume": 40,
        "theme": "Catppuccin Mocha",
    },
}


def builtin_names() -> List[str]:
    return list(BUILTIN_PRESETS.keys())


# ------------------------------------------------------------------ user presets
_NAME_RE = re.compile(r'[\\/:*?"<>|\n\r\t]')


def _safe_name(name: str) -> str:
    cleaned = _NAME_RE.sub("_", str(name)).strip()
    return cleaned or "unnamed"


def _user_preset_path(name: str) -> Path:
    return PRESETS_DIR / f"{_safe_name(name)}.json"


def save_user_preset(name: str, config: StudioConfig, overwrite: bool = True) -> Path:
    """Persist the given configuration as a named user preset."""
    from dataclasses import asdict
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    path = _user_preset_path(name)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Preset '{name}' already exists")
    cfg_dict = asdict(config)
    cfg_dict["mode"] = config.mode.value     # Enum -> str for JSON
    payload = {
        "name": name,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": cfg_dict,
    }
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    import os
    os.replace(tmp, path)
    logger.info(f"Saved user preset '{name}' -> {path}")
    return path


def load_user_presets() -> Dict[str, dict]:
    """Return ``{name: config_dict}`` for every saved user preset."""
    out: Dict[str, dict] = {}
    if not PRESETS_DIR.is_dir():
        return out
    for p in sorted(PRESETS_DIR.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = data.get("config", data)
            if isinstance(cfg, dict):
                out[data.get("name") or p.stem] = cfg
        except Exception:
            logger.error(f"Skipping corrupt preset file {p}", exc_info=True)
    return out


def delete_user_preset(name: str) -> bool:
    path = _user_preset_path(name)
    if path.exists():
        try:
            path.unlink()
            return True
        except OSError:
            logger.error(f"Could not delete preset {path}", exc_info=True)
    return False


# ------------------------------------------------------------------ application
def apply_preset(config: StudioConfig, name: str) -> StudioConfig:
    """Apply a built-in or user preset on top of *config* (returns a new object)."""
    if name in BUILTIN_PRESETS:
        overrides = dict(BUILTIN_PRESETS[name])
    else:
        user = load_user_presets()
        if name not in user:
            raise KeyError(f"Unknown preset: {name}")
        overrides = dict(user[name])

    # Presets are partial: start from the current config, overlay known fields.
    base = {f.name: getattr(config, f.name) for f in StudioConfig.__dataclass_fields__.values()}
    base.update({k: v for k, v in overrides.items() if k in base})
    return safe_config_from_dict(base)


def all_preset_names() -> List[str]:
    """Built-in first, then user presets (for GUI combos)."""
    return builtin_names() + sorted(load_user_presets().keys())


def describe_preset(name: str) -> str:
    """One-line summary for tooltips."""
    try:
        cfg = apply_preset(StudioConfig(), name)
        parts = [cfg.resolution, f"{cfg.fps}fps", cfg.theme]
        if cfg.output_format != "mp4":
            parts.append(cfg.output_format.upper())
        if cfg.sound_enabled:
            parts.append(cfg.sound_preset)
        if getattr(cfg, "amb_enabled", False):
            parts.append(f"+{getattr(cfg, 'amb_preset', '')} ambience")
            if getattr(cfg, "amb_music", True):
                parts.append(f"music {getattr(cfg, 'amb_music_volume', 45)}%")
        if getattr(cfg, "timing_fit", "Off") != "Off":
            parts.append(f"auto-fit {cfg.timing_target:.0f}s")
        if getattr(cfg, "rhythm_style", "Natural") != "Natural":
            parts.append(f"{cfg.rhythm_style.lower()} rhythm")
        return " | ".join(parts)
    except Exception:
        return ""

##############
#                             ══ 2 - METADATA ══                            
# SEO title / description / tags / chapters writer
# (was: metadata.py in the ten-file edition)
##############

"""YouTube SEO metadata: title derivation, tag extraction, chapters,
description writer. Qt-free."""


#==============================================================================
# ── METADATA — SEO title/description/tags/chapters (Qt-free)
#    (merged from studio/metadata.py in the v2.5 ten-file edition)
#==============================================================================

"""YouTube SEO metadata generator (Qt-free).

Builds upload-ready metadata (title, description with chapters, tags and
hashtags) for an exported typing video and writes it next to the output:

    <output_base>.description.txt   paste into the YouTube description box
    <output_base>.metadata.json     full metadata (also useful for automation)

Chapters are generated from the branding timeline when intro/outro cards are
enabled (0:00 Intro / Coding / Outro) - YouTube requires at least three
entries starting at 0:00, which the intro+typing+outro structure satisfies.
"""

import json
import os
import re
from collections import Counter
from typing import Dict, Iterable, List, Optional, Tuple


# ------------------------------------------------------------------ stopwords
# Programming keywords + generic words that make poor tags.
_STOPWORDS = frozenset("""
def return import from as if elif else for while try except finally with lambda
yield raise class pass break continue global nonlocal assert del in is not and or
none true false self async await match case print len range str int float list
dict set tuple type isinstance super staticmethod classmethod property exception
function const let var new extends implements interface public private protected
static void boolean string number object class enum export default this super
null undefined async await typeof instanceof package struct impl fn pub use mut
match mod crate where move ref unsafe dyn trait loop crate func defer go chan
select switch case break default package include define using namespace template
typename public private virtual override friend operator sizeof typedef
the a an and or of to in on for with is are was were be been it its this that
code video typing watch subscribe like comment share channel shorts youtube
python javascript typescript java code programming coding learn tutorial
""".split())


def derive_title(source_name: str) -> str:
    """Turn a source file name into a human title.

    "sorting_algorithms.py" -> "Sorting Algorithms"
    "my-cool-script.js"     -> "My Cool Script"
    "custom_code.py"        -> "Custom Code"
    """
    base = os.path.splitext(os.path.basename(str(source_name)))[0]
    base = re.sub(r"[_\-\s]+", " ", base).strip()
    if not base or base.lower() in ("custom code", "custom_code", "preview", "untitled"):
        return "Watch Me Code"
    words = base.split()
    titled = []
    for wd in words:
        titled.append(wd[0].upper() + wd[1:] if wd else wd)
    out = " ".join(titled)
    return out[:64].strip() or "Watch Me Code"


def _split_identifier(ident: str) -> Iterable[str]:
    """Split snake_case / camelCase identifiers into words."""
    for part in re.split(r"[_\-\s]+", ident):
        if not part:
            continue
        # camelCase -> camel Case, foo2Bar -> foo2 Bar
        for w in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", part):
            yield w.lower()


def extract_tags(code: str, lang: str, limit: int = 18) -> List[str]:
    """Frequency-ranked, filtered keywords from the source code."""
    counts: Counter = Counter()
    for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", code or ""):
        for word in _split_identifier(ident):
            if len(word) < 3 or word in _STOPWORDS or word.isdigit():
                continue
            counts[word] += 1
    tags = [w for w, _ in counts.most_common(limit - 6)]
    generic = [lang, "coding", "programming", "learn to code", "developer",
               "software engineer", "typing video", "coding shorts"]
    out: List[str] = []
    for tag in tags + generic:
        if tag and tag not in out:
            out.append(tag)
        if len(out) >= limit:
            break
    return out


def format_chapter_time(sec: float) -> str:
    sec = max(0, int(round(sec)))
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def build_chapters(typing_duration: float, lead: float = 0.0,
                   tail: float = 0.0) -> List[Tuple[str, str]]:
    """Chapter list from the branding timeline (needs all 3 segments)."""
    if lead <= 0 or tail <= 0 or typing_duration <= 0:
        return []
    return [
        ("0:00", "Intro"),
        (format_chapter_time(lead), "Coding"),
        (format_chapter_time(lead + typing_duration), "Outro"),
    ]


def build_metadata(config, source_names: Optional[List[str]] = None,
                   typing_duration: float = 0.0,
                   lead: float = 0.0, tail: float = 0.0,
                   frame_size: Optional[Tuple[int, int]] = None) -> Dict:
    """Assemble the full metadata dict for one exported video."""
    names = [n for n in (source_names or []) if n and n != "custom_code.py"]
    first = names[0] if names else "custom_code.py"
    title = derive_title(first)

    vertical = bool(frame_size and frame_size[1] > frame_size[0])
    is_shorts = vertical

    lang = "code"
    if config is not None:
        try:
            lang = EXT_TO_LANGUAGE.get(
                os.path.splitext(first)[1].lower(), "code")
        except Exception:
            lang = "code"

    code = ""
    if config is not None:
        code = getattr(config, "custom_code", "") or ""
    tags = extract_tags(code, lang if lang != "code" else "coding")

    chapters = build_chapters(typing_duration, lead, tail)

    hook = (f"Watch {title} typed in real time - syntax highlighted, with "
            "satisfying mechanical keyboard sounds.")
    lines: List[str] = [title, "", hook, ""]
    if chapters:
        lines.append("Chapters:")
        lines.extend(f"{stamp} {name}" for stamp, name in chapters)
        lines.append("")
    lines.append("Subscribe for more coding videos - new typing videos every week!")
    lines.append("")
    hashtags = ["#coding", "#programming"]
    if is_shorts:
        hashtags.insert(0, "#shorts")
    if lang and lang != "code":
        hashtags.append(f"#{lang}")
    lines.append(" ".join(hashtags[:5]))
    description = "\n".join(lines).strip() + "\n"

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "hashtags": hashtags,
        "chapters": [{"time": stamp, "name": name} for stamp, name in chapters],
        "is_shorts": is_shorts,
        "category": "Education",
        "privacy": "public",
        "made_for_kids": False,
        "language": lang,
        "source_files": names or [first],
    }


def render_description(meta: Dict) -> str:
    return meta.get("description", "")


def write_metadata_files(config, output_path: str,
                         source_names: Optional[List[str]] = None,
                         typing_duration: float = 0.0,
                         lead: float = 0.0, tail: float = 0.0,
                         frame_size: Optional[Tuple[int, int]] = None) -> List[str]:
    """Write <base>.description.txt and <base>.metadata.json next to the mp4.

    Respects ``config.write_metadata``; never raises. Returns written paths.
    """
    if config is None or not getattr(config, "write_metadata", True):
        return []
    base = os.path.splitext(str(output_path))[0]
    if not base or base.endswith("_frames"):
        return []
    try:
        meta = build_metadata(config, source_names, typing_duration, lead, tail,
                              frame_size)
        desc_path = base + ".description.txt"
        json_path = base + ".metadata.json"
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(render_description(meta))
        payload = dict(meta)
        payload["output"] = str(output_path)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return [desc_path, json_path]
    except Exception:
        logger.error("Failed to write metadata files", exc_info=True)
        return []

##############
#                            ══ 3 - RENDERING ══                            
# renderers, keyboard overlay, branding cards, thumbnails
# (was: rendering.py in the ten-file edition)
##############

"""Visual layer: keyboard layouts + overlay renderer, branding intro/
outro cards and watermark, the YouTube/Shorts thumbnail studio, and
the Studio/MultiPane renderers with progress bar + punch zoom."""


#==============================================================================
# ── KEYBOARD — 9 layouts + overlay renderer
#    (merged from studio/keyboard.py in the v2.5 ten-file edition)
#==============================================================================

"""On-screen keyboard overlay: layouts for 9 layouts and the renderer that
draws the keyboard with per-key press flash animations."""

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen


KEYBOARD_LAYOUTS = {
    "QWERTY": [[("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1), ("]", 1), ("\\", 1.5)], [("Caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("'", 1), ("Enter", 2.25)], [("Shift", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Fn", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "AZERTY": [[("²", 1), ("&", 1), ("é", 1), ("\"", 1), ("'", 1), ("(", 1), ("-", 1), ("è", 1), ("_", 1), ("ç", 1), ("à", 1), (")", 1), ("=", 1), ("Bksp", 2)], [("Tab", 1.5), ("A", 1), ("Z", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("^", 1), ("$", 1), ("Enter", 1.5)], [("Caps", 1.75), ("Q", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), ("M", 1), ("ù", 1), ("*", 1), ("Enter", 2.25)], [("Shift", 1.25), ("<", 1), ("W", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), (",", 1), (";", 1), (":", 1), ("!", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Win", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "QWERTZ": [[("^", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("ß", 1), ("´", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Z", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("Ü", 1), ("+", 1), ("Enter", 1.5)], [("Caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), ("Ö", 1), ("Ä", 1), ("#", 1), ("Enter", 2.25)], [("Shift", 1.25), ("<", 1), ("Y", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("-", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Win", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "Dvorak": [[("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("[", 1), ("]", 1), ("Bksp", 2)], [("Tab", 1.5), ("'", 1), (",", 1), (".", 1), ("P", 1), ("Y", 1), ("F", 1), ("G", 1), ("C", 1), ("R", 1), ("L", 1), ("/", 1), ("=", 1), ("\\", 1.5)], [("Caps", 1.75), ("A", 1), ("O", 1), ("E", 1), ("U", 1), ("I", 1), ("D", 1), ("H", 1), ("T", 1), ("N", 1), ("S", 1), ("-", 1), ("Enter", 2.25)], [("Shift", 2.25), (";", 1), ("Q", 1), ("J", 1), ("K", 1), ("X", 1), ("B", 1), ("M", 1), ("W", 1), ("V", 1), ("Z", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Win", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "Colemak": [[("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("F", 1), ("P", 1), ("G", 1), ("J", 1), ("L", 1), ("U", 1), ("Y", 1), (";", 1), ("[", 1), ("]", 1), ("\\", 1.5)], [("Bksp", 1.75), ("A", 1), ("R", 1), ("S", 1), ("T", 1), ("D", 1), ("H", 1), ("N", 1), ("E", 1), ("I", 1), ("O", 1), ("'", 1), ("Enter", 2.25)], [("Shift", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("K", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Win", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "JIS (Japanese)": [[("半", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("^", 1), ("¥", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("@", 1), ("[", 1), ("]", 1), ("\\", 1.5)], [("Caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), (":", 1), ("Enter", 2.25)], [("Shift", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("_", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("無", 1), ("", 4.25), ("変", 1.25), ("Alt", 1.25), ("Fn", 1.25), ("Ctrl", 1.25)]],
    "Pinyin (Chinese)": [[("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1), ("]", 1), ("\\", 1.5)], [("中", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("'", 1), ("Enter", 2.25)], [("Shift", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Fn", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "Turkish Q": [[("\"", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("*", 1), ("-", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("Ğ", 1), ("Ü", 1), (";", 1.5)], [("Caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), ("Ş", 1), ("İ", 1), ("Enter", 2.25)], [("Shift", 2.25), ("<", 1), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), ("Ö", 1), ("Ç", 1), (".", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Fn", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]]
}

# chars with no NFD decomposition -> base letter whose key should flash
_EXTRA_KEY_BASES = {"ß": "s", "ø": "o", "æ": "a", "œ": "o", "đ": "d", "ł": "l",
                    "ı": "i", "ð": "d", "þ": "p"}


class KeyboardOverlay:
    def __init__(self, video_w, video_h, layout_name="QWERTY", theme=None, opacity=0.82,
                 max_height=None, position="bottom_center"):
        self.video_w, self.video_h, self.theme, self.opacity = video_w, video_h, theme, opacity
        self.layout_name = layout_name
        self.rows = KEYBOARD_LAYOUTS.get(layout_name, KEYBOARD_LAYOUTS["QWERTY"])
        self.char_map = {}
        self._resolve_cache: dict = {}
        for ri, row in enumerate(self.rows):
            for ci, (label, w) in enumerate(row):
                if len(label) == 1:
                    self.char_map[label] = self.char_map[label.lower()] = (ri, ci)
                if label == "":
                    self.char_map[" "] = (ri, ci)
                elif "enter" in label.lower():
                    self.char_map["\n"] = (ri, ci)
                elif "tab" in label.lower():
                    self.char_map["\t"] = (ri, ci)
                elif "bksp" in label.lower():
                    self.char_map["\b"] = (ri, ci)
        # Shifted / AltGr symbols resolve to the key that carries them.
        # v3.1 fixes: the old table had a "+=": "=" typo so "+" never lit any
        # key, and non-US layouts had huge gaps (AZERTY digits, QWERTZ /
        # JIS / Turkish punctuation) — typing "=", "+", "===" or braces then
        # flashed nothing, which read as the keyboard being out of sync with
        # the text on screen.  Tables below map each typed char to the label
        # of the physical key that produces it on that layout.
        base_shift = {"~": "`", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
                      "^": "6", "&": "7", "*": "8", "(": "9", ")": "0", "_": "-",
                      "+": "=", "{": "[", "}": "]", "|": "\\", ":": ";",
                      '"': "'", "<": ",", ">": ".", "?": "/"}
        # per-layout overrides/extra aliases (French AZERTY, German QWERTZ,
        # Japanese JIS, Turkish-Q — national Shift/AltGr conventions)
        layout_shift = {
            "AZERTY": {"1": "&", "2": "é", "3": '"', "4": "'", "5": "(", "6": "-",
                       "7": "è", "8": "_", "9": "ç", "0": "à",       # Shift+&é"'( ...
                       "+": "=", ".": ";", "/": ":", "?": ",", ">": "<",
                       "%": "ù",                                      # Shift+ù
                       "@": "à", "#": '"', "[": "(", "]": ")", "{": "'",
                       "}": "=", "\\": "_", "|": "-", "`": "è", "~": "é"},
            "QWERTZ": {'"': "2", "'": "#", ":": ".", ";": ",", "=": "+",
                       "?": "-", "/": "7", "[": "8", "]": "9", "{": "7",
                       "}": "0", "\\": "ß", "|": "<", "~": "+", "`": "´"},
            "JIS (Japanese)": {'"': "2", "'": "7", "+": ";", "=": "-",
                               "`": "@", "~": "^"},
            "Turkish Q": {"'": "7", '"': "2", "+": "4", "=": "0", "?": "*",
                          "_": "-", ",": ".", "/": ".", "[": "8", "]": "9",
                          "{": "7", "}": "0", "\\": "-", "|": "<",
                          "`": ",", "~": "ü"},
        }
        for s, b in {**base_shift, **layout_shift.get(self.layout_name, {})}.items():
            if s not in self.char_map and b in self.char_map:
                self.char_map[s] = self.char_map[b]

        target_kb_w = int(video_w * 0.65)
        required_unit = target_kb_w / 15.0
        self.key_unit = max(14, min(55, int(required_unit)))
        self.key_gap = max(2, self.key_unit // 14)
        self.key_h = int(self.key_unit * 0.82)
        self._kb_w = int(max(sum(w for _, w in r) for r in self.rows) * self.key_unit
                         + (max(len(r) for r in self.rows) - 1) * self.key_gap)
        self._kb_h = int(len(self.rows) * self.key_h + (len(self.rows) - 1) * self.key_gap)

        self.position = position
        self._kb_x, self._kb_y = 0, 0
        self.key_rects = {}
        self._rebuild_key_rects()

        # v3 key-press FX state: afterglow trail + eased sink.
        # Only used when draw() is called with ``t`` (sequential preview);
        # the export workers call draw() without ``t`` -> fully stateless,
        # so concurrent frame rendering stays deterministic.
        self.TRAIL_LIFE = 0.45        # seconds an afterglow stays visible
        self._trail = {}              # key (ri, ci) -> last press time
        self._last_t = None           # timestamp of the previous stateful draw
        self._prev_key = None
        self._prev_flash = 0.0

    def height_needed(self):
        return self._kb_h + max(16, self.video_h // 30)

    def _apply_position(self, y_target=None):
        m_x = max(8, self.video_w // 60)
        m_y = max(8, self.video_h // 60)

        if "center" in self.position:
            self._kb_x = (self.video_w - self._kb_w) // 2
        elif "right" in self.position:
            self._kb_x = self.video_w - self._kb_w - m_x
        elif "left" in self.position:
            self._kb_x = m_x

        if "top" in self.position:
            self._kb_y = m_y
        else:
            if y_target is not None:
                self._kb_y = y_target
                max_y = self.video_h - self._kb_h - m_y
                min_y = m_y
                if self._kb_y > max_y:
                    self._kb_y = max_y
                if self._kb_y < min_y:
                    self._kb_y = min_y
            else:
                self._kb_y = self.video_h - self._kb_h - m_y

    def _rebuild_key_rects(self):
        self.key_rects = {}
        for ri, row in enumerate(self.rows):
            x = self._kb_x
            for ci, (_, w) in enumerate(row):
                kw = int(w * self.key_unit) - self.key_gap
                y = self._kb_y + ri * (self.key_h + self.key_gap)
                self.key_rects[(ri, ci)] = QRect(x, y, kw, self.key_h)
                x += int(w * self.key_unit)

    def reposition(self, y_target=None):
        self._apply_position(y_target)
        self._rebuild_key_rects()

    def resolve_key(self, ch):
        """Map a typed character to its key position.

        Falls back through: exact char_map hit -> base letter of an accented
        char (NFD: é→e, ü→u; plus ligatures like ß→s) so accented text still
        flashes a plausible key instead of nothing.  Results are cached.
        """
        if not ch:
            return None
        pos = self.char_map.get(ch)
        if pos is not None:
            return pos
        cached = self._resolve_cache.get(ch)
        if cached is not None:
            return cached
        pos = None
        if len(ch) == 1:
            nfd = unicodedata.normalize("NFD", ch)
            base = nfd[0] if nfd else ""
            bases = [base, base.lower(), base.upper(), _EXTRA_KEY_BASES.get(ch, "")]
            # a base letter may resolve directly or case-insensitively
            for cand in bases:
                if not cand:
                    continue
                pos = self.char_map.get(cand)
                if pos is not None:
                    break
                if len(cand) == 1:
                    pos = self.char_map.get(cand.lower())
                    if pos is not None:
                        break
        self._resolve_cache[ch] = pos
        return pos

    def draw(self, p, active_key=None, flash=0.0, t=None):
        """Draw the keyboard overlay.

        Without ``t`` the call is stateless (legacy signature): only the
        active key's flash highlight and eased sink are drawn — safe for the
        concurrent export workers.

        With ``t`` (sequential preview/player) the v3 press FX activate:
        a fading afterglow trail on recently pressed keys, recorded on the
        flash rising edge, pruned after :data:`TRAIL_LIFE`; scrubbing to an
        earlier time resets the trail.
        """
        trail_ages = None
        if t is not None:
            if self._last_t is not None and t < self._last_t:
                self._trail.clear()            # scrubbed backwards -> reset
            if active_key is not None and (
                    self._prev_key != active_key or flash > self._prev_flash):
                self._trail[active_key] = t    # rising edge = a new press
            for k, ts in list(self._trail.items()):
                if t - ts > self.TRAIL_LIFE:
                    del self._trail[k]
            self._last_t = t
            self._prev_key, self._prev_flash = active_key, flash
            trail_ages = {k: t - ts for k, ts in self._trail.items()}

        p.save()
        p.setOpacity(self.opacity)
        p.setRenderHint(QPainter.Antialiasing)
        th = self.theme or THEMES["Dracula"]
        radius = max(3, self.key_unit // 8)

        pad = max(6, self.key_unit // 4)
        p.setPen(QPen(QColor(th["window_border"]), max(1, self.key_unit // 20)))
        p.setBrush(QColor(th["title_bar"]))
        p.drawRoundedRect(self._kb_x - pad, self._kb_y - pad, self._kb_w + 2 * pad, self._kb_h + 2 * pad, radius * 2, radius * 2)

        kbg = QColor(th["background"])
        kbr = QColor(th["window_border"])
        lc = QColor(th["foreground"])
        mc = QColor(th["line_number"])
        hlb = QColor(th["cursor"])

        if flash > 0 and active_key is not None:
            hkf = QColor(int(kbg.red() + (hlb.red() - kbg.red()) * flash),
                         int(kbg.green() + (hlb.green() - kbg.green()) * flash),
                         int(kbg.blue() + (hlb.blue() - kbg.blue()) * flash))
            hlg = QColor(hlb)
            hlg.setAlpha(int(60 * flash))
            hle = max(3, int(self.key_unit * 0.12 * flash))
        else:
            hkf = None

        for (ri, ci), rect in self.key_rects.items():
            label = self.rows[ri][ci][0]
            ia = (active_key is not None and active_key == (ri, ci))

            # eased sink: the pressed key dips by up to 11% of the key unit
            dy = round(self.key_unit * 0.11 * flash) if (ia and flash > 0) else 0

            age = trail_ages.get((ri, ci)) if trail_ages else None
            if ia and hkf is not None:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(hlg)
                p.drawRoundedRect(rect.adjusted(-hle, -hle + dy, hle, hle + dy), radius, radius)
                p.setBrush(hkf)
                p.setPen(QPen(kbr, 1))
            elif age is not None:
                # v3 afterglow trail: fading halo + slightly lit key body
                a = max(0.0, 1.0 - age / self.TRAIL_LIFE)
                p.setPen(Qt.PenStyle.NoPen)
                g = QColor(hlb)
                g.setAlpha(int(70 * a))
                p.setBrush(g)
                p.drawRoundedRect(rect.adjusted(-3, -3, 3, 3), radius, radius)
                p.setBrush(kbg.lighter(100 + int(28 * a)))
                p.setPen(QPen(kbr, 1))
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(kbr.darker(150))
                p.drawRoundedRect(rect.adjusted(0, 3, 0, 3), radius, radius)
                p.setBrush(kbg)
                p.setPen(QPen(kbr, 1))

            body = rect.translated(0, dy) if dy else rect
            p.drawRoundedRect(body, radius, radius)

            if label:
                p.setPen(mc if len(label) > 1 else lc)
                p.setFont(QFont("Segoe UI", max(7, int(self.key_unit * 0.30))))
                p.drawText(body, Qt.AlignCenter, label)
        p.restore()


def make_keyboard_overlay(video_w, video_h, layout_name, theme_name, opacity, max_height, position):
    return KeyboardOverlay(video_w, video_h, layout_name, get_theme(theme_name), opacity, max_height, position)

#==============================================================================
# ── BRANDING — intro/outro cards, subscribe pill, watermark
#    (merged from studio/branding.py in the v2.5 ten-file edition)
#==============================================================================

"""Branding overlays: intro title card, outro card with subscribe pill and a
persistent @handle watermark.

Everything is drawn with QPainter onto the frame the compositor already
created, so the cards inherit the active theme colors and any frame size
(16:9 YouTube or 9:16 Shorts).

Durations live in config.py (INTRO_DURATION / OUTRO_DURATION) so the
Qt-free batch planner can account for them.
"""

import math
from typing import List, Optional, Tuple

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen


_SUB_RED = "#ff0033"
_MARGIN = 0.06          # fraction of the frame kept free on each edge


def _theme(config) -> dict:
    return THEMES.get(getattr(config, "theme", ""), THEMES["Dracula"]) if config else THEMES["Dracula"]


def _wrap_text(fm: QFontMetrics, text: str, max_w: int, max_lines: int = 3) -> List[str]:
    """Greedy word wrap; the last line gets an ellipsis when truncated."""
    lines: List[str] = []
    for raw in text.split("\n"):
        cur = ""
        for word in raw.split():
            candidate = (cur + " " + word).strip()
            if fm.horizontalAdvance(candidate) <= max_w or not cur:
                cur = candidate
            else:
                lines.append(cur)
                cur = word
            if len(lines) >= max_lines:
                break
        if cur and len(lines) < max_lines:
            lines.append(cur)
        if len(lines) >= max_lines:
            break
    if lines and len(lines) == max_lines:
        # verify the tail was not cut mid-word list: add ellipsis if text left
        joined = " ".join(lines)
        if len(joined) < len(" ".join(text.split())):
            lines[-1] = lines[-1].rstrip(" .,;:") + "…"
    return lines or [""]


def _fade_alpha(frac: float, edge: float = 0.18) -> int:
    """Fade in over the first *edge* fraction and out over the last."""
    if frac <= 0:
        return 0
    if frac >= 1:
        return 255
    a = min(1.0, frac / edge, (1.0 - frac) / edge)
    return int(255 * max(0.0, min(1.0, a)))


# ------------------------------------------------------------------ watermark
def draw_watermark(p: QPainter, w: int, h: int, config) -> None:
    """Small persistent handle text in the chosen corner."""
    text = (getattr(config, "wm_text", "") or "").strip()
    if not text or not getattr(config, "wm_enabled", False):
        return
    th = _theme(config)
    size = max(12, int(h * 0.024))
    font = QFont()
    font.setFamilies(["Segoe UI", "Noto Sans", "DejaVu Sans", "sans-serif"])
    font.setPixelSize(size)
    font.setBold(True)
    p.save()
    p.setFont(font)
    alpha = max(0, min(100, int(getattr(config, "wm_opacity", 40)))) * 255 // 100
    color = QColor(th.get("foreground", "#f8f8f2"))
    color.setAlpha(alpha)
    p.setPen(color)
    fm = p.fontMetrics()
    tw = fm.horizontalAdvance(text)
    pad = int(min(w, h) * _MARGIN * 0.5)
    pos = getattr(config, "wm_position", "Top Right")
    if pos not in WM_POSITIONS:
        pos = "Top Right"
    if "Left" in pos:
        x = pad
    else:
        x = w - tw - pad
    y = pad + fm.ascent() if "Top" in pos else h - pad - fm.descent()
    # soft shadow for legibility on any background
    shadow = QColor(0, 0, 0, min(180, alpha + 60))
    p.setPen(shadow)
    p.drawText(x + 1, y + 1, text)
    p.setPen(color)
    p.drawText(x, y, text)
    p.restore()


# ------------------------------------------------------------------ intro card
def draw_intro_card(p: QPainter, w: int, h: int, config, frac: float) -> None:
    """Full-frame title card shown before the typing starts.

    ``frac`` is the card progress 0..1 over INTRO_DURATION seconds; the card
    fades in/out at its edges.
    """
    th = _theme(config)
    bg = QColor(th.get("background", "#282a36"))
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(bg)
    p.drawRect(0, 0, w, h)

    alpha = _fade_alpha(frac)

    title = (getattr(config, "intro_text", "") or "").strip()
    if not title:
        title = "Watch Me Code"
    handle = (getattr(config, "intro_handle", "") or
              getattr(config, "wm_text", "") or "").strip()

    accent = QColor(th.get("junior_accent", "#8be9fd"))
    fg = QColor(th.get("foreground", "#f8f8f2"))
    dim = QColor(th.get("comment", "#6272a4"))

    title_size = int(h * 0.085) if h >= w else int(h * 0.055)
    font = QFont()
    font.setFamilies(["Segoe UI", "Noto Sans", "DejaVu Sans", "sans-serif"])
    font.setPixelSize(max(18, title_size))
    font.setBold(True)
    p.setFont(font)
    fm = QFontMetrics(font)
    lines = _wrap_text(fm, title, int(w * 0.82), max_lines=3)
    line_h = int(fm.height() * 1.22)
    block_h = len(lines) * line_h

    handle_size = max(13, int(h * 0.032))
    hfont = QFont()
    hfont.setFamilies(["Segoe UI", "Noto Sans", "DejaVu Sans", "sans-serif"])
    hfont.setPixelSize(handle_size)
    hfm = QFontMetrics(hfont)

    underline_w = int(w * 0.16)
    gap = int(h * 0.045)
    total_h = block_h + (gap + handle_size if handle else 0)
    y = (h - total_h) // 2

    p.setOpacity(alpha / 255.0)
    ty = y
    p.setPen(fg)
    for ln in lines:
        p.drawText(QRect(0, ty, w, line_h),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, ln)
        ty += line_h

    # accent underline
    uy = ty + int(h * 0.012)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(accent)
    p.drawRoundedRect((w - underline_w) // 2, uy, underline_w, max(3, h // 200), 2, 2)
    ty = uy + max(3, h // 200) + gap // 2

    if handle:
        p.setFont(hfont)
        p.setPen(dim)
        p.drawText(QRect(0, ty, w, handle_size + 8),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, handle)
    p.restore()


# ------------------------------------------------------------------ outro card
def _draw_subscribe_pill(p: QPainter, cx: int, cy: int, scale: float, alpha: int) -> None:
    """YouTube-style red Subscribe pill with a little bell."""
    base_w, base_h = 340, 92
    pw, ph = int(base_w * scale), int(base_h * scale)
    x, y = cx - pw // 2, cy - ph // 2

    p.setPen(Qt.PenStyle.NoPen)
    shadow = QColor(0, 0, 0, int(90 * alpha / 255))
    p.setBrush(shadow)
    p.drawRoundedRect(x + 3, y + 5, pw, ph, ph // 2, ph // 2)

    red = QColor(_SUB_RED)
    red.setAlpha(alpha)
    p.setBrush(red)
    p.drawRoundedRect(x, y, pw - int(46 * scale), ph, ph // 2, ph // 2)

    bell_bg = QColor(255, 255, 255, alpha)
    bx = x + pw - int(40 * scale)
    by = y + ph // 2
    br = int(20 * scale)
    p.setBrush(bell_bg)
    p.drawEllipse(bx - br, by - br, br * 2, br * 2)

    font = QFont()
    font.setFamilies(["Segoe UI", "Noto Sans", "DejaVu Sans", "sans-serif"])
    font.setPixelSize(int(38 * scale))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor(255, 255, 255, alpha))
    p.drawText(QRect(x, y, pw - int(46 * scale), ph),
               Qt.AlignmentFlag.AlignCenter, "Subscribe")

    # tiny bell glyph inside the white circle
    bfont = QFont()
    bfont.setPixelSize(int(22 * scale))
    p.setFont(bfont)
    bell_fg = QColor(_SUB_RED)
    bell_fg.setAlpha(alpha)
    p.setPen(bell_fg)
    p.drawText(QRect(bx - br, by - br, br * 2, br * 2),
               Qt.AlignmentFlag.AlignCenter, "\U0001F514")


def draw_outro_card(p: QPainter, w: int, h: int, config, frac: float) -> None:
    """Full-frame outro: message + pulsing subscribe pill."""
    th = _theme(config)
    bg = QColor(th.get("background", "#282a36"))
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(bg)
    p.drawRect(0, 0, w, h)

    alpha = _fade_alpha(frac, edge=0.15)
    p.setOpacity(alpha / 255.0)

    fg = QColor(th.get("foreground", "#f8f8f2"))
    dim = QColor(th.get("comment", "#6272a4"))
    accent = QColor(th.get("junior_accent", "#8be9fd"))

    text = (getattr(config, "outro_text", "") or "Thanks for watching!").strip()
    size = int(h * 0.07) if h >= w else int(h * 0.05)
    font = QFont()
    font.setFamilies(["Segoe UI", "Noto Sans", "DejaVu Sans", "sans-serif"])
    font.setPixelSize(max(16, size))
    font.setBold(True)
    p.setFont(font)
    fm = QFontMetrics(font)
    lines = _wrap_text(fm, text, int(w * 0.8), max_lines=2)
    line_h = int(fm.height() * 1.2)

    pill_cy = int(h * 0.62)
    block_bottom = (h - line_h * len(lines)) // 2 + line_h * len(lines)
    if block_bottom > pill_cy - int(h * 0.08):
        block_top = max(int(h * 0.10), pill_cy - int(h * 0.30) - line_h * len(lines))
    else:
        block_top = (h - line_h * len(lines)) // 2 - int(h * 0.04)

    p.setPen(fg)
    ty = block_top
    for ln in lines:
        p.drawText(QRect(0, ty, w, line_h),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, ln)
        ty += line_h

    # pulsing pill (two gentle pulses over the card)
    pulse = 1.0 + 0.05 * abs(math.sin(frac * math.pi * 2))
    # solid alpha for the pill (card alpha already applied via opacity)
    _draw_subscribe_pill(p, w // 2, pill_cy, pulse, 255)

    handle = (getattr(config, "intro_handle", "") or
              getattr(config, "wm_text", "") or "").strip()
    if handle:
        hsize = max(12, int(h * 0.028))
        hfont = QFont()
        hfont.setFamilies(["Segoe UI", "Noto Sans", "DejaVu Sans", "sans-serif"])
        hfont.setPixelSize(hsize)
        p.setFont(hfont)
        p.setPen(dim)
        p.drawText(QRect(0, pill_cy + int(h * 0.07), w, hsize + 10),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, handle)

    # thin accent line at the very bottom for a finished look
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(accent)
    p.drawRect(0, h - max(3, h // 200), w, max(3, h // 200))
    p.restore()


def branding_durations(config) -> Tuple[float, float]:
    """(lead_in, tail) the branding cards add to the timeline."""
    lead = 0.0
    tail = 0.0
    if config is not None:
        if getattr(config, "intro_enabled", False):
            lead = INTRO_DURATION
        if getattr(config, "outro_enabled", False):
            tail = OUTRO_DURATION
    return lead, tail

#==============================================================================
# ── THUMBNAIL — YouTube/Shorts thumbnail generator
#    (merged from studio/thumbnail.py in the v2.5 ten-file edition)
#==============================================================================

"""Thumbnail studio: YouTube (1280x720) and Shorts cover (1080x1920) images.

A thumbnail is composed from:
  * a themed background with a soft accent glow,
  * the final typing frame rendered as a floating "editor window" card,
  * a big editable headline with an accent underline.

The headline is auto-filled from the source file name (see
``studio.metadata.derive_title``) but can be overridden freely.
"""

import os
from typing import List, Optional, Tuple

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QImage,
                           QLinearGradient, QPainter, QPainterPath)



def auto_headline(source_name: str) -> str:
    """Public alias so the GUI/headless have one obvious entry point."""
    return derive_title(source_name)


def _font(families=("Segoe UI", "Noto Sans", "DejaVu Sans", "sans-serif"),
          size: int = 20, bold: bool = True) -> QFont:
    f = QFont()
    f.setFamilies(list(families))
    f.setPixelSize(max(10, size))
    f.setBold(bold)
    return f


def _wrap(fm: QFontMetrics, text: str, max_w: int, max_lines: int) -> List[str]:
    lines: List[str] = []
    cur = ""
    for word in text.split():
        cand = (cur + " " + word).strip()
        if fm.horizontalAdvance(cand) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    return lines or [""]


def _draw_centered_headline(p: QPainter, text: str, box: QRect, accent: QColor,
                            fg: QColor, max_lines: int, rel_size: float) -> None:
    """Big wrapped headline + accent underline, with a soft drop shadow."""
    size = int(box.height() * rel_size)
    font = _font(size=size)
    p.setFont(font)
    fm = QFontMetrics(font)
    lines = _wrap(fm, text, int(box.width() * 0.94), max_lines)
    line_h = int(fm.height() * 1.18)
    block_h = line_h * len(lines)

    y = box.top() + max(0, (box.height() - block_h) // 2)
    for ln in lines:
        # shadow
        p.setPen(QColor(0, 0, 0, 190))
        p.drawText(QRect(box.left() + 3, y + 4, box.width(), line_h),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, ln)
        p.setPen(fg)
        p.drawText(QRect(box.left(), y, box.width(), line_h),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, ln)
        y += line_h

    # accent underline
    bar_h = max(4, size // 14)
    bar_w = int(box.width() * 0.42)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(accent)
    p.drawRoundedRect(box.left() + (box.width() - bar_w) // 2, y + size // 5,
                      bar_w, bar_h, bar_h // 2, bar_h // 2)


def make_thumbnail(mp, config, headline: str = "",
                   size: Tuple[int, int] = THUMB_YT_SIZE) -> QImage:
    """Compose a thumbnail image from the renderer's final typing frame."""
    w, h = int(size[0]), int(size[1])
    th = THEMES.get(getattr(config, "theme", ""), THEMES["Dracula"])
    bg = QColor(th.get("background", "#282a36"))
    fg = QColor(th.get("foreground", "#f8f8f2"))
    accent = QColor(th.get("junior_accent", "#8be9fd"))

    img = QImage(w, h, QImage.Format_RGB32)
    img.fill(bg)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)

    # --- background: subtle vertical gradient + accent glow --------------
    grad = QLinearGradient(0, 0, 0, h)
    top = bg.darker(105) if bg.lightness() > 60 else bg.lighter(108)
    grad.setColorAt(0.0, top)
    grad.setColorAt(1.0, bg.darker(130))
    p.fillRect(0, 0, w, h, grad)

    p.setPen(Qt.PenStyle.NoPen)
    glow = QColor(accent)
    glow.setAlpha(26)
    p.setBrush(glow)
    p.drawEllipse(int(-w * 0.15), int(-h * 0.25), int(w * 0.9), int(h * 0.9))
    glow2 = QColor(th.get("senior_accent", th.get("junior_accent", "#bd93f9")))
    glow2.setAlpha(20)
    p.setBrush(glow2)
    p.drawEllipse(int(w * 0.55), int(h * 0.65), int(w * 0.65), int(h * 0.65))

    # --- code card: final typing frame -----------------------------------
    vertical = h > w
    if vertical:
        card_w, card_h = int(w * 0.86), int(h * 0.40)
        card_cy = int(h * 0.36)
        head_box = QRect(int(w * 0.05), int(h * 0.60), int(w * 0.90), int(h * 0.26))
        head_rel, head_lines = 0.105, 4
    else:
        card_w, card_h = int(w * 0.60), int(h * 0.58)
        card_cy = int(h * 0.44)
        head_box = QRect(int(w * 0.03), int(h * 0.74), int(w * 0.94), int(h * 0.24))
        head_rel, head_lines = 0.155, 3

    card_x = (w - card_w) // 2
    card_y = card_cy - card_h // 2

    # drop shadow
    p.setPen(Qt.PenStyle.NoPen)
    shadow = QColor(0, 0, 0, 120)
    p.setBrush(shadow)
    p.drawRoundedRect(card_x + 8, card_y + 12, card_w, card_h, 18, 18)

    # render the completed code frame into the card (clipped, rounded)
    path = QPainterPath()
    path.addRoundedRect(QRectF(card_x, card_y, card_w, card_h), 18, 18)
    p.save()
    p.setClipPath(path)
    if mp is not None:
        t_end = getattr(mp, "lead_in", 0.0) + mp.typing_duration()
        frame = mp.render_frame(t_end - 0.001)
        scaled = frame.scaled(card_w, card_h,
                              Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                              Qt.TransformationMode.SmoothTransformation)
        p.drawImage(card_x + (card_w - scaled.width()) // 2,
                    card_y + (card_h - scaled.height()) // 2, scaled)
    else:
        p.fillRect(card_x, card_y, card_w, card_h, QColor(20, 20, 28))
    p.restore()

    # card border
    p.setPen(QColor(255, 255, 255, 34))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(card_x, card_y, card_w, card_h, 18, 18)

    # --- headline ---------------------------------------------------------
    text = (headline or "").strip() or "Watch Me Code"
    _draw_centered_headline(p, text, head_box, accent, fg, head_lines, head_rel)

    p.end()
    return img


def save_thumbnails(mp, config, output_base: str, headline: str = "",
                    variants: str = "both") -> List[str]:
    """Write thumbnails next to an export.

    ``variants``: "yt" (1280x720), "shorts" (1080x1920) or "both".
    Returns the list of written PNG paths.
    """
    base = os.path.splitext(str(output_base))[0]
    if base.endswith("_frames"):
        base = base[:-7]
    head = (headline or getattr(config, "thumb_headline", "") or "").strip()
    if not head:
        src = ""
        names = getattr(config, "_thumb_sources", None)
        if names:
            src = names[0]
        head = auto_headline(src or "Watch Me Code")

    written: List[str] = []
    jobs = []
    if variants in ("yt", "both"):
        jobs.append((THUMB_YT_SIZE, f"{base}_thumbnail_yt.png"))
    if variants in ("shorts", "both"):
        jobs.append((THUMB_SHORTS_SIZE, f"{base}_thumbnail_shorts.png"))
    for size, path in jobs:
        try:
            img = make_thumbnail(mp, config, head, size)
            if img.save(path, "PNG"):
                written.append(path)
        except Exception:
            logger.error(f"Thumbnail generation failed for {path}", exc_info=True)
    return written

#==============================================================================
# ── RENDERING — Studio/MultiPane renderers + overlays
#    (merged from studio/rendering.py in the v2.5 ten-file edition)
#==============================================================================

"""Frame rendering: the single-window code renderer and the multi-pane
compositor with progress-bar overlay.

v2.0 highlights
  * Syntax colors are pre-computed once per pane (char-color map) instead of
    re-lexing the visible prefix on every frame -> orders of magnitude faster.
  * Typos flash in the theme error color.
  * Optional ambient glow behind the code window.
  * Four cursor styles (Beam / Block / Underline / Outline) + optional blink.
  * Animated bottom progress bar.
"""

import re
import threading
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

import numpy as np

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QImage, QLinearGradient,
                           QPainter, QPen)


try:
    from pygments import lex
    _HAS_PYGMENTS = True
except ImportError:
    _HAS_PYGMENTS = False


class StudioRenderer:
    """Renders one code/editor window of arbitrary pixel size."""

    def __init__(self, width, height, theme_name="Dracula", font_family="Consolas", font_size=22,
                 show_line_numbers=True, show_window_chrome=True, padding=24, tab_size=4,
                 language="python", ascii_art_mode=False, config=None, pane_idx=0,
                 line_diffs=None, kb_overlay: Optional[KeyboardOverlay] = None):
        self.width, self.height = width, height
        self.theme = get_theme(theme_name)
        self.font_family, self.font_size = font_family, font_size
        self.show_line_numbers, self.show_window_chrome = show_line_numbers, show_window_chrome
        self.padding = min(padding, max(8, min(width, height) // 30))
        self.tab_size = tab_size
        self.language, self.ascii_art_mode = language, ascii_art_mode
        self.config = config
        self.pane_idx = pane_idx
        self.line_diffs = line_diffs if line_diffs else {}
        self.kb_overlay = kb_overlay
        self.CURSOR_BLINK = 0.53
        self._code_rect = QRect(0, 0, 1, 1)

        _fams = [font_family, "JetBrains Mono", "DejaVu Sans Mono", "Consolas", "monospace",
                 "Noto Color Emoji", "Segoe UI Emoji", "sans-serif"]
        self.font = QFont(self.font_family, self.font_size)
        self.font.setFamilies(list(dict.fromkeys(_fams)))
        self.font.setFixedPitch(True)
        self.fm = QFontMetrics(self.font)
        self.char_w = self.fm.horizontalAdvance("M")
        self.line_h = self.fm.height()
        self._tab_adv = self.char_w * tab_size

        self._qcolors = {k: QColor(v) for k, v in self.theme.items() if isinstance(v, str) and v.startswith("#")}
        self._qc_fg = self._qcolors.get("foreground", QColor("#f8f8f2"))
        self._qc_ln = self._qcolors.get("line_number", QColor("#6272a4"))
        self._qc_cursor = self._qcolors.get("cursor", QColor("#f8f8f2"))
        self._qc_current_line = self._qcolors.get("current_line", QColor("#44475a"))
        self._qc_error = self._qcolors.get("error", QColor("#ff5555"))

        self._token_cache: OrderedDict = OrderedDict()
        self._token_lock = threading.Lock()
        self._token_cache_max = 256

        # char-color map (perf): filled by prepare_code()
        self._units_text: Optional[List[str]] = None
        self._units_colors: Optional[List[QColor]] = None

        self._build_bg_cache()

    # ------------------------------------------------------------ perf core
    def _token_color(self, ttype) -> QColor:
        s = str(ttype)
        if s.startswith("Token.Comment"):
            return self._qcolors.get("comment", self._qc_fg)
        if s.startswith("Token.Keyword"):
            return self._qcolors.get("keyword", self._qc_fg)
        if s.startswith("Token.String"):
            return self._qcolors.get("string", self._qc_fg)
        if s.startswith("Token.Number"):
            return self._qcolors.get("number", self._qc_fg)
        if s.startswith("Token.Name.Function"):
            return self._qcolors.get("function", self._qc_fg)
        if s.startswith("Token.Name.Class"):
            return self._qcolors.get("class_name", self._qc_fg)
        return self._qc_fg

    def prepare_code(self, code: str, is_text: bool = False) -> None:
        """Pre-compute per-character syntax colors by lexing the FULL text once.

        During rendering we then just walk the typed characters and look up
        colors, instead of re-running pygments on every frame. Characters that
        don't match the source (typos) get the theme error color.

        Three specialized paths mirror the classic studio tokenizer set:
          * ANSI escape sequences (ESC[..m) -> per-character terminal colors,
            sequences themselves are stripped from the typed timeline
          * lightweight Markdown highlighting (Text & Emoji mode)
          * regex code fallback when pygments is unavailable
        """
        try:
            units = split_graphemes(code) if is_text else list(code)
            if not units:
                self._units_text = None
                self._units_colors = None
                return
            colors = [self._qc_fg] * len(units)

            if "\x1b[" in code:
                # ANSI terminal art: escape sequences become colors, never glyphs
                visible, per_char = parse_ansi(code)
                units = split_graphemes(visible) if is_text else list(visible)
                colors = [self._qc_fg] * len(units)
                if self.config and getattr(self.config, "ansi_colors", False):
                    pos = 0
                    for gi, u in enumerate(units):
                        if pos >= len(per_char):
                            break
                        hexc = per_char[pos]
                        if hexc:
                            colors[gi] = QColor(hexc)
                        pos += len(u)
            elif is_text and self.config and self.config.mode == StudioMode.TEXT_EMOJI \
                    and self.config.txt_markdown:
                colors = self._colors_for_graphemes(code, units, self._markdown_spans(code))
            elif _HAS_PYGMENTS and self.language not in ("text", "ascii art", "emoji art"):
                lexer = LexerFactory.get_lexer(self.language)
                if lexer is not None:
                    idx = 0
                    for ttype, val in lex(code, lexer):
                        if not val:
                            continue
                        color = self._token_color(ttype)
                        budget = len(val)
                        while budget > 0 and idx < len(units):
                            colors[idx] = color
                            budget -= len(units[idx])
                            idx += 1
            elif self.language not in ("text", "ascii art", "emoji art"):
                # no pygments installed: regex fallback so code still gets
                # comment / string / number / keyword colors
                colors = self._colors_for_chars(code, self._basic_code_spans(code))

            self._units_text = units
            self._units_colors = colors
        except Exception:
            logger.error("prepare_code failed; falling back to per-frame lexing", exc_info=True)
            self._units_text = None
            self._units_colors = None

    # ---- lightweight tokenizers (markdown / ANSI / regex code) ----------
    _MD_TOKEN_RE = re.compile(
        r'(^#{1,6}[ \t]+.*?$|^>[ \t].*?$|^[-*+][ \t]+.*?$|'
        r'\*\*.*?\*\*|\*[^*\n]+?\*|`[^`\n]*`|\[[^\]\n]*\]\([^)\n]*\))',
        re.MULTILINE)

    @classmethod
    def _markdown_spans(cls, text: str) -> List[Tuple[int, int, str]]:
        """(start, end, theme_key) spans for headings/quotes/lists/bold/italic/code/links."""
        spans: List[Tuple[int, int, str]] = []
        for m in cls._MD_TOKEN_RE.finditer(text):
            t = m.group(0)
            if t.startswith("#"):
                key = "keyword"          # headings
            elif t.startswith("`"):
                key = "string"           # inline code
            elif t.startswith("["):
                key = "function"         # links
            elif t.startswith("**"):
                key = "keyword"          # bold
            elif t.startswith("*"):
                key = "number"           # italic
            else:
                key = "comment"          # quotes & list items
            spans.append((m.start(), m.end(), key))
        return spans

    _BASIC_CODE_TOKEN_RE = re.compile(
        r'(\#.*?$|//.*?$|/\*.*?\*/)|("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`)|(\b\d+\.?\d*\b)|(\b[A-Za-z_][A-Za-z0-9_]*\b)',
        re.MULTILINE)
    _BASIC_KEYWORDS = frozenset({
        "def", "class", "import", "from", "return", "if", "else", "elif", "for",
        "while", "try", "except", "finally", "with", "as", "in", "is", "not",
        "and", "or", "True", "False", "None", "public", "private", "void",
        "int", "string", "float", "bool", "func", "fn", "let", "const", "var",
        "function", "new", "this", "self"})

    @classmethod
    def _basic_code_spans(cls, text: str) -> List[Tuple[int, int, str]]:
        """Regex token spans used when pygments is not installed."""
        spans: List[Tuple[int, int, str]] = []
        for m in cls._BASIC_CODE_TOKEN_RE.finditer(text):
            t = m.group(0)
            if t.startswith(("#", "//", "/*")):
                key = "comment"
            elif t[:1] in "\"'`":
                key = "string"
            elif t.isdigit():
                key = "number"
            elif t in cls._BASIC_KEYWORDS:
                key = "keyword"
            else:
                continue
            spans.append((m.start(), m.end(), key))
        return spans

    def _md_color_for(self, key: str) -> QColor:
        return self._qcolors.get(key, self._qc_fg)

    def _colors_for_graphemes(self, code: str, units: List[str],
                              spans: List[Tuple[int, int, str]]) -> List[QColor]:
        """Map token spans (char offsets) onto grapheme-cluster colors."""
        colors = [self._qc_fg] * len(units)
        if not spans:
            return colors
        pos = 0
        for gi, u in enumerate(units):
            for (s, e, key) in spans:
                if pos >= s and pos < e:
                    colors[gi] = self._md_color_for(key)
                    break
            pos += len(u)
        return colors

    def _colors_for_chars(self, code: str,
                          spans: List[Tuple[int, int, str]]) -> List[QColor]:
        colors = [self._qc_fg] * len(code)
        for (s, e, key) in spans:
            col = self._md_color_for(key)
            for i in range(s, min(e, len(colors))):
                colors[i] = col
        return colors

    def _tokenize_pygments(self, text):
        """Fallback tokenizer (used only if prepare_code failed)."""
        if not _HAS_PYGMENTS or self.language in ("text", "ascii art", "emoji art"):
            return [(self._qc_fg, text)]
        with self._token_lock:
            cache_key = text
            if cache_key in self._token_cache:
                self._token_cache.move_to_end(cache_key)
                return self._token_cache[cache_key]
            lexer = LexerFactory.get_lexer(self.language)
            if not lexer:
                return [(self._qc_fg, text)]
            tokens = []
            for ttype, val in lex(text, lexer):
                if val in ("\n", " ", "\t"):
                    tokens.append((self._qc_fg, val))
                    continue
                tokens.append((self._token_color(ttype), val))
            self._token_cache[cache_key] = tokens
            while len(self._token_cache) > self._token_cache_max:
                self._token_cache.popitem(last=False)
            return tokens

    # ------------------------------------------------------------ background
    def _build_bg_cache(self):
        self._bg = QImage(self.width, self.height, QImage.Format_RGB32)
        self._bg.fill(QColor(self.theme["background"]))
        p = QPainter(self._bg)
        p.setRenderHint(QPainter.Antialiasing)
        bg = self._qcolors.get("background", QColor("#282a36"))
        g = QLinearGradient(0, 0, 0, self.height)
        g.setColorAt(0, bg.lighter(105)); g.setColorAt(1, bg)
        p.fillRect(0, 0, self.width, self.height, g)
        pad, chrome_h = self.padding, 42 if self.show_window_chrome else 0
        ww = self.width - 2 * pad

        kb_h = self.kb_overlay.height_needed() if self.kb_overlay else 0
        kb_top = self.kb_overlay and "top" in self.kb_overlay.position

        avail_h = self.height - 2 * pad
        target_wh = avail_h - kb_h

        max_ratio = 1.1 if (self.config is None or self.config.mode != StudioMode.TEXT_EMOJI) else 2.0
        if self.ascii_art_mode:
            max_ratio = float("inf")  # allow ASCII art to fill the entire vertical space

        if target_wh > ww * max_ratio:
            target_wh = int(ww * max_ratio)

        total_block_h = target_wh + kb_h
        start_y = pad + (avail_h - total_block_h) // 2

        wy = start_y + (kb_h if kb_top else 0)
        wh = target_wh
        wx, ww = pad, self.width - 2 * pad

        # NEW: ambient glow behind the window
        if self.config is None or getattr(self.config, "glow_enabled", True):
            accent = self._qcolors.get("cursor", QColor("#f8f8f2"))
            for r, alpha in ((30, 12), (20, 20), (11, 30)):
                c = QColor(accent)
                c.setAlpha(alpha)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(c)
                p.drawRoundedRect(wx - r, wy - r, ww + 2 * r, wh + 2 * r, 16 + r, 16 + r)

        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0, 0, 0, 60))
        p.drawRoundedRect(wx + 4, wy + 4, ww, wh, 12, 12)
        p.setPen(QColor(self.theme["window_border"])); p.setBrush(QColor(self.theme["background"]))
        p.drawRoundedRect(wx, wy, ww, wh, 12, 12)

        if self.show_window_chrome:
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(self.theme["title_bar"]))
            p.drawRoundedRect(wx, wy, ww, chrome_h, 12, 12)
            p.drawRect(wx, wy + chrome_h - 12, ww, 12)
            for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
                p.setBrush(QColor(color)); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPoint(wx + 20 + i * 24, wy + 19), 7, 7)
            self._code_rect = QRect(wx + 4, wy + chrome_h, ww - 8, wh - chrome_h)
        else:
            self._code_rect = QRect(wx + 4, wy, ww - 8, wh)

        if self.kb_overlay:
            if not kb_top:
                self.kb_overlay.reposition(wy + wh + max(8, self.height // 60))
            else:
                self.kb_overlay.reposition(start_y)

        p.end()

    @staticmethod
    def auto_font_size(lines_count, width, height, padding=24, show_chrome=True, show_ln=True,
                       text=None, font_family="Consolas", keyboard_h=0, ascii_art_mode=False):
        chrome_h = 42 if show_chrome else 0
        max_ratio = 1.1 if not ascii_art_mode else float("inf")
        avail_h = height - 2 * padding - keyboard_h
        if avail_h > width * max_ratio:
            avail_h = int(width * max_ratio)

        rh, rw = avail_h - chrome_h, width - 2 * padding - 8
        if rh < 20 or rw < 40 or lines_count < 1:
            return 14
        max_chars = max(max(len(l.replace("\t", "    ")) for l in text.split("\n")), 1) if text else 80

        def lnw(cw):
            return (len(str(lines_count)) * cw + 32 + int(cw * 1.5)) if show_ln else 0

        lo, hi, best = 8, max(14, min(128, int(width / 40))), 14
        while lo <= hi:
            mid = (lo + hi) // 2
            fm = QFontMetrics(QFont(font_family, mid))
            if (lines_count if ascii_art_mode else min(lines_count, 35)) * fm.height() <= rh:
                cw = fm.horizontalAdvance("M")
                if (max_chars if ascii_art_mode else min(max_chars, 120)) * cw + lnw(cw) <= rw:
                    best = mid; lo = mid + 1
                else:
                    hi = mid - 1
            else:
                hi = mid - 1
        return max(8, best)

    # ------------------------------------------------------------ frames
    def render_frame(self, display_chars, num_visible, cursor_visible=True, target=None,
                     active_char=None, key_flash=0.0, title_text="", t=0.0, duration=0.0,
                     hud_data=None, animator=None, draw_guides=False, kb_trail=False):
        img = target if target is not None else QImage(self.width, self.height, QImage.Format_RGB32)
        if target is None:
            img.fill(QColor(self.theme["background"]))
        p = QPainter(img)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.drawImage(0, 0, self._bg)
        cr = self._code_rect
        if self.show_window_chrome:
            p.setPen(QColor(self.theme["title_text"]))
            p.setFont(QFont(self.font_family, max(8, min(12, self.width // 80))))
            p.drawText(QRect(self.padding, cr.top() - 42, cr.width(), 42), Qt.AlignCenter, title_text)

        # ---- build the typed character stream with per-char colors -------
        # Each entry also carries the moment the char was typed (its own
        # timestamp, not the last stream timestamp) so transient per-char
        # effects (emoji pop) track the correct character.
        ts_list = animator._timestamps if animator and hasattr(animator, "_timestamps") else []

        def _ts_of(i: int) -> float:
            return ts_list[i] if i < len(ts_list) else 0.0

        charseq: List[Tuple[str, QColor, bool, float]] = []  # (char, color, matched, typed_at)
        if self._units_colors is not None:
            orig_idx = 0
            units = self._units_text
            colors = self._units_colors
            for i, ch in enumerate(display_chars[:num_visible]):
                ts_i = _ts_of(i)
                if ch == "\b":
                    if charseq:
                        popped = charseq.pop()
                        if popped[2] and orig_idx > 0:
                            orig_idx -= 1
                else:
                    if orig_idx < len(units) and ch == units[orig_idx]:
                        charseq.append((ch, colors[orig_idx], True, ts_i))
                        orig_idx += 1
                    else:
                        # typo or transient char -> theme error color
                        charseq.append((ch, self._qc_error, False, ts_i))
        else:
            # fallback: no color map -> reconstruct text, lex per frame
            out_fb: List[Tuple[str, float]] = []
            for i, ch in enumerate(display_chars[:num_visible]):
                if ch == "\b":
                    if out_fb:
                        out_fb.pop()
                else:
                    out_fb.append((ch, _ts_of(i)))
            for ch, ts_i in out_fb:
                charseq.append((ch, self._qc_fg, False, ts_i))

        # ---- markdown (Text & Emoji mode) --------------------------------
        is_bold = False
        is_italic = False
        if self.config and self.config.mode == StudioMode.TEXT_EMOJI and self.config.txt_markdown:
            new_seq = []
            i = 0
            while i < len(charseq):
                ch = charseq[i][0]
                if ch == "*" and i + 1 < len(charseq) and charseq[i + 1][0] == "*":
                    is_bold = not is_bold
                    i += 2
                    continue
                if ch == "*" and not is_bold:
                    is_italic = not is_italic
                    i += 1
                    continue
                new_seq.append(charseq[i])
                i += 1
            charseq = new_seq

        # ---- split into lines --------------------------------------------
        lines: List[List[Tuple[str, QColor, float]]] = []  # (char, color, typed_at)
        current: List[Tuple[str, QColor, float]] = []
        for ch, color, _m, cts in charseq:
            if ch == "\n":
                lines.append(current)
                current = []
            else:
                current.append((ch, color, cts))
        lines.append(current)

        if self._units_colors is None:
            # fallback path: recolor via pygments on the visible text
            visible_text = "".join(ch for ch, _c, _m, _ts in charseq)
            tokens = self._tokenize_pygments(visible_text)
            lines, current = [], []
            for color, val in tokens:
                if "\n" in val:
                    parts = val.split("\n")
                    for i, part in enumerate(parts):
                        if part:
                            current.append((part, color, 0.0))
                        if i < len(parts) - 1:
                            lines.append(current)
                            current = []
                else:
                    for ch in val:
                        current.append((ch, color, 0.0))
            lines.append(current)

        cursor_line = len(lines) - 1
        total_lines = len(lines)
        max_vis = max(1, -(-cr.height() // self.line_h))
        # Continuous scroll: the view stays anchored to the top until the
        # cursor comes within 5 lines of the bottom, then follows 1:1.  The
        # old two-branch formula (pin to top row 3 / pin 5 from bottom) was
        # discontinuous and made the text visibly jump mid-video.
        scroll = max(0, min(cursor_line - max_vis + 5, total_lines - max_vis))

        ln_gap = max(12, int(self.char_w * 1.5))
        ln_width = (len(str(total_lines + scroll)) * self.char_w + 32 + ln_gap) if self.show_line_numbers else 0
        x0, y_acc = cr.left() + ln_width, cr.top()

        focus_block_start, focus_block_end = -1, -1
        if (self.config and self.config.mode == StudioMode.CODE_YT and self.config.yt_focus
                and self.language in ("python", "javascript", "typescript", "go", "rust", "ruby")):
            for i, line in enumerate(lines):
                line_str = "".join(v for v, _c, _ts in line)
                if re.match(r"^\s*(def|class|func|fn)\s", line_str):
                    if i <= cursor_line:
                        focus_block_start = i
                    elif i > cursor_line and focus_block_start != -1:
                        focus_block_end = i
                        break
            if focus_block_start != -1 and focus_block_end == -1:
                focus_block_end = total_lines

        p.setClipRect(cr)
        p.setFont(self.font)

        for si in range(max_vis):
            li = scroll + si
            if li >= total_lines:
                break
            y = y_acc
            y_acc += self.line_h

            if self.config and self.config.mode == StudioMode.TEXT_EMOJI and self.config.txt_bubbles:
                line_str = "".join(v for v, _c, _ts in lines[li])
                line_w = 0
                for v, _c, _ts in lines[li]:
                    for ch in v:
                        line_w += self._tab_adv if ch == "\t" else self.fm.horizontalAdvance(ch)
                bubble_w = min(cr.width() - 30, line_w + 30)
                bubble_rect = QRect(x0, y + 5, bubble_w, self.line_h - 10)
                if line_str.startswith("Me:"):
                    bubble_rect.moveRight(cr.right() - 10)
                    p.setBrush(QColor("#007AFF")); p.setPen(Qt.PenStyle.NoPen)
                else:
                    p.setBrush(QColor("#333333")); p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(bubble_rect, 10, 10)
                x0_bubble = bubble_rect.left() + 10
            else:
                x0_bubble = x0

            bg_color = None
            if li == cursor_line:
                bg_color = self._qc_current_line
            if self.line_diffs.get(li) == "added":
                bg_color = QColor(50, 200, 50, 40)
            elif self.line_diffs.get(li) == "removed":
                bg_color = QColor(255, 50, 50, 40)
            if bg_color and not (self.config and self.config.mode == StudioMode.TEXT_EMOJI and self.config.txt_bubbles):
                p.fillRect(cr.left(), y, cr.width(), self.line_h, bg_color)

            if self.show_line_numbers and ln_width > 0:
                p.setPen(self._qc_ln)
                p.drawText(QRect(cr.left(), y, ln_width - ln_gap, self.line_h), Qt.AlignRight | Qt.AlignVCenter, str(li + 1))

            line_tokens = lines[li]
            if not line_tokens:
                if cursor_visible and li == cursor_line:
                    self._draw_caret(p, int(x0), int(y + self.line_h * 0.15), max(4, self.line_h - 10))
                continue

            line_w = 0
            for v, _c, _ts in line_tokens:
                for ch in v:
                    line_w += self._tab_adv if ch == "\t" else self.fm.horizontalAdvance(ch)

            if self.ascii_art_mode:
                x = x0 + (cr.width() - ln_width - line_w) // 2
            else:
                x = x0_bubble

            opacity = 1.0
            if focus_block_start != -1 and not (focus_block_start <= li < focus_block_end):
                opacity = 0.3

            dim_cache: Dict[str, QColor] = {}
            if is_bold or is_italic:
                f = QFont(self.font)
                f.setBold(is_bold); f.setItalic(is_italic)
                p.setFont(f)
            else:
                p.setFont(self.font)

            for ch, color, cts in line_tokens:
                if opacity < 1.0:
                    key = color.name()
                    dim = dim_cache.get(key)
                    if dim is None:
                        dim = QColor(color)
                        dim.setAlpha(int(255 * opacity))
                        dim_cache[key] = dim
                    p.setPen(dim)
                else:
                    p.setPen(color)

                if ch == "\t":
                    x += self._tab_adv
                    continue

                ch_w = self.fm.horizontalAdvance(ch)
                # pop tracks THIS char's own typing moment, so an emoji typed
                # earlier does not re-pop when further chars arrive quickly
                is_pop_char = is_emoji(ch) and 0 <= t - cts < 0.15
                if is_pop_char:
                    p.save()
                    progress = max(0, 1.0 - (t - cts) / 0.15)
                    pop_scale = 1.0 + 0.5 * progress
                    cx = x + ch_w / 2
                    cy = y + self.line_h * 0.5
                    p.translate(cx, cy); p.scale(pop_scale, pop_scale); p.translate(-cx, -cy)
                    p.drawText(QRect(int(x), int(y), int(ch_w), int(self.line_h)), Qt.AlignLeft | Qt.AlignVCenter, ch)
                    p.restore()
                else:
                    p.drawText(QRect(int(x), int(y), int(ch_w), int(self.line_h)), Qt.AlignLeft | Qt.AlignVCenter, ch)
                x += ch_w
            if cursor_visible and li == cursor_line:
                self._draw_caret(p, int(x), int(y))

        p.setClipping(False)

        # The keyboard plate is drawn on EVERY typing frame (it used to be
        # gated on the 0.18s key-flash window, which made the whole keyboard
        # flicker in and out of existence during pauses > 0.18s — word gaps,
        # punctuation, newlines, or any slow WPM).  Only the key highlight
        # depends on the flash.
        if self.kb_overlay:
            ak = self.kb_overlay.resolve_key(active_char) \
                if (active_char and key_flash > 0) else None
            # t is only forwarded for the sequential preview (kb_trail=True);
            # export workers keep the stateless call so concurrent frames
            # stay deterministic.
            self.kb_overlay.draw(p, active_key=ak,
                                 flash=key_flash if ak is not None else 0.0,
                                 t=(t if kb_trail else None))

        if draw_guides:
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor(255, 0, 0, 150), 2, Qt.PenStyle.DashLine)); p.setBrush(Qt.NoBrush)
            p.drawRect(24, 24, self.width - 48, self.height - 48)
            if self.show_window_chrome:
                p.setPen(QPen(QColor(0, 255, 0, 150), 2, Qt.PenStyle.DashLine)); p.setBrush(Qt.NoBrush)
                p.drawRect(self._code_rect.left() - 4, self._code_rect.top() - 42, self._code_rect.width() + 8, 42)
            p.setPen(QPen(QColor(0, 150, 255, 150), 2, Qt.PenStyle.DashLine)); p.setBrush(Qt.NoBrush)
            p.drawRect(self._code_rect)

        p.end()
        return img

    def _draw_caret(self, p, x, y, h=None):
        """Draw the text cursor. Style configurable via config.cursor_style."""
        style = getattr(self.config, "cursor_style", "Beam") if self.config else "Beam"
        w = max(2, self.font_size // 10)
        pad = (self.line_h - self.fm.height()) // 2
        caret_y = y + pad + 1
        caret_h = (h - 4) if h else (self.fm.height() - 2)
        cw = self.char_w
        gc = QColor(self._qc_cursor)

        if style == "Block":
            gc.setAlpha(110)
            p.fillRect(x, caret_y - 1, cw, caret_h + 2, gc)
            p.fillRect(x, caret_y - 1, max(2, w), caret_h + 2, self._qc_cursor)
        elif style == "Underline":
            p.fillRect(x, caret_y + caret_h - 1, max(6, cw), 3, self._qc_cursor)
        elif style == "Outline":
            p.setPen(QPen(self._qc_cursor, max(1, w // 2)))
            p.setBrush(Qt.NoBrush)
            p.drawRect(x, caret_y, max(4, cw - 1), caret_h)
        else:  # Beam (default)
            gc.setAlpha(60); p.fillRect(x - w, caret_y - 2, w * 3, caret_h + 4, gc)
            gc.setAlpha(100); p.fillRect(x - 1, caret_y - 1, w * 2, caret_h + 2, gc)
            p.fillRect(x, caret_y, w, caret_h, self._qc_cursor)


# =====================================================================
# MULTI-PANE COMPOSITOR (+ progress bar overlay)
# =====================================================================
class MultiPaneRenderer:
    @staticmethod
    def compute_pane_rects(frame_w, frame_h, num_panes, layout, gap=20, config=None):
        W, H, g, n = frame_w, frame_h, gap, num_panes
        if n == 1:
            return [QRect(0, 0, W, H)]
        if n == 2:
            if config and config.mode == StudioMode.MULTI_WINDOW:
                ratio = config.mw_ratio / 100.0
                if W < H:
                    ph = int((H - g) * ratio)
                    return [QRect(0, 0, W, ph), QRect(0, ph + g, W, H - ph - g)]
                else:
                    pw = int((W - g) * ratio)
                    return [QRect(0, 0, pw, H), QRect(pw + g, 0, W - g - pw, H)]
            if "Stacked" in layout:
                ph = (H - g) // 2
                return [QRect(0, (H - (2 * ph + g)) // 2, W, ph), QRect(0, (H - (2 * ph + g)) // 2 + ph + g, W, ph)]
            if "Junior Big" in layout:
                pw = int((W - g) * 0.7)
                return [QRect(0, 0, pw, H), QRect(pw + g, 0, W - g - pw, H)]
            if "Senior Big" in layout:
                pw = int((W - g) * 0.3)
                return [QRect(0, 0, pw, H), QRect(pw + g, 0, W - g - pw, H)]
            pw = (W - g) // 2
            return [QRect(0, 0, pw, H), QRect(pw + g, 0, W - pw - g, H)]
        if n == 3:
            if W < H:
                ph = (H - 2 * g) // 3
                return [QRect(0, 0, W, ph), QRect(0, ph + g, W, ph), QRect(0, 2 * (ph + g), W, H - 2 * (ph + g))]
            pw = (W - 2 * g) // 3
            return [QRect(0, 0, pw, H), QRect(pw + g, 0, pw, H), QRect(2 * (pw + g), 0, W - 2 * (pw + g), H)]
        pw, ph = (W - g) // 2, (H - g) // 2
        return [QRect(0, 0, pw, ph), QRect(pw + g, 0, W - pw - g, ph),
                QRect(0, ph + g, pw, H - ph - g), QRect(pw + g, ph + g, W - pw - g, H - ph - g)]

    def __init__(self, panes, frame_w, frame_h, num_panes, layout, gap=20,
                 bg_color="#0d0d12", config=None):
        self.panes = panes
        self.frame_w, self.frame_h = frame_w, frame_h
        self.num_panes, self.layout, self.gap = num_panes, layout, gap
        self.bg_color = bg_color
        self.config = config
        self.pane_rects = self.compute_pane_rects(frame_w, frame_h, num_panes, layout, gap, config)

        # ---- branding timeline (v2.3): [intro card][typing][outro card] ----
        lead, tail = 0.0, 0.0
        intro_title = ""
        if config is not None:
            if getattr(config, "intro_enabled", False):
                lead = INTRO_DURATION
                intro_title = (getattr(config, "intro_text", "") or "").strip()
            if getattr(config, "outro_enabled", False):
                tail = OUTRO_DURATION
        if not intro_title and panes:
            intro_title = panes[0][2] or "Watch Me Code"
        self.lead_in = lead
        self.tail = tail
        self._intro_title = intro_title or "Watch Me Code"
        self._intro_handle = ""
        if config is not None:
            self._intro_handle = (getattr(config, "intro_handle", "") or
                                  getattr(config, "wm_text", "") or "").strip()

    def _compute_pane_rects(self):
        return self.compute_pane_rects(self.frame_w, self.frame_h, self.num_panes, self.layout, self.gap, self.config)

    def typing_duration(self):
        """Duration of the typing segment (excludes intro/outro cards)."""
        return max(a.duration() for _, a, _ in self.panes) if self.panes else 0.0

    def duration(self):
        return self.lead_in + self.typing_duration() + self.tail

    def char_timestamps_all(self):
        """(time, char) tuples across all panes, shifted past the intro card."""
        lead = self.lead_in
        ts = []
        for _, a, _ in self.panes:
            if lead:
                ts.extend((t + lead, ch) for t, ch in a.char_timestamps())
            else:
                ts.extend(a.char_timestamps())
        return ts

    # ---- overlays ------------------------------------------------------
    def _progress_bar_height(self):
        return max(3, self.frame_h // 220)

    def _draw_progress_bar(self, p: QPainter, frac: float):
        bar_h = self._progress_bar_height()
        y = self.frame_h - bar_h
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillRect(0, y, self.frame_w, bar_h, QColor(255, 255, 255, 30))
        color_hex = getattr(self.config, "progress_bar_color", "accent") if self.config else "accent"
        if isinstance(color_hex, str) and color_hex.startswith("#"):
            fill = QColor(color_hex)
        else:
            th = THEMES.get(getattr(self.config, "theme", ""), THEMES["Dracula"]) if self.config else THEMES["Dracula"]
            fill = QColor(th.get("junior_accent", "#8be9fd"))
        p.fillRect(0, y, int(self.frame_w * max(0.0, min(1.0, frac))), bar_h, fill)

    # ---- main ----------------------------------------------------------
    def render_frame(self, t, target=None, draw_guides=False, kb_trail=False):
        img = target if target is not None else QImage(self.frame_w, self.frame_h, QImage.Format_RGB32)
        typing_dur = self.typing_duration()

        # ---- phase 1: intro title card ---------------------------------
        if self.lead_in > 0 and t < self.lead_in:
            img.fill(QColor(self.bg_color))
            p = QPainter(img)
            draw_intro_card(p, self.frame_w, self.frame_h, self.config,
                            t / self.lead_in if self.lead_in else 1.0)
            p.end()
            return img

        # ---- phase 3: outro card ---------------------------------------
        typing_end = self.lead_in + typing_dur
        if self.tail > 0 and t >= typing_end:
            img.fill(QColor(self.bg_color))
            p = QPainter(img)
            frac = (t - typing_end) / self.tail if self.tail else 1.0
            draw_outro_card(p, self.frame_w, self.frame_h, self.config,
                            max(0.0, min(1.0, frac)))
            p.end()
            return img

        # ---- phase 2: typing segment ------------------------------------
        tt = t - self.lead_in          # time relative to the typing segment
        img.fill(QColor(self.bg_color))
        p = QPainter(img)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        blink_on = True
        if self.config is not None and getattr(self.config, "cursor_blink", False) and tt > 0.2:
            period = self._panes_blink_period()
            blink_on = (tt % period) < (period / 2.0)

        # subtle Ken Burns punch-in for vertical (Shorts) exports
        punch_scale = 1.0
        if (self.config is not None and getattr(self.config, "punch_zoom", False)
                and self.frame_h > self.frame_w and typing_dur > 0):
            punch_scale = 1.0 + 0.05 * max(0.0, min(1.0, tt / typing_dur))

        for i, (renderer, animator, title) in enumerate(self.panes):
            if i >= len(self.pane_rects):
                break
            rect = self.pane_rects[i]
            nv = animator.visible_at(tt)
            cv = blink_on
            ac, kf = animator.active_key_at(tt)

            scale = punch_scale
            if self.config and self.config.mode == StudioMode.CODE_YT and self.config.yt_zoom and tt < animator.duration():
                progress = tt / animator.duration()
                scale = max(scale, 1.0 + 0.1 * progress)

            pane_img = renderer.render_frame(
                animator.display_chars, nv, cv, active_char=ac, key_flash=kf,
                title_text=title,
                target=QImage(rect.width(), rect.height(), QImage.Format_RGB32),
                t=tt, duration=animator.duration(), animator=animator, draw_guides=draw_guides,
                kb_trail=kb_trail
            )

            # Clip every pane to its own rect: the punch/yt zoom expands the
            # pane image beyond the rect and used to bleed over the gap and
            # into the neighbouring pane.
            p.save()
            p.setClipRect(rect)
            if scale > 1.0:
                pw, ph = rect.width(), rect.height()
                sw, sh = int(pw * scale), int(ph * scale)
                scaled_img = pane_img.scaled(sw, sh, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                             Qt.TransformationMode.SmoothTransformation)
                x = rect.left() - (sw - pw) // 2
                y = rect.top() - (sh - ph) // 2
                p.drawImage(x, y, scaled_img)
            else:
                p.drawImage(rect.topLeft(), pane_img)
            p.restore()

        if self.config is not None:
            if getattr(self.config, "progress_bar_enabled", False) and typing_dur > 0:
                self._draw_progress_bar(p, tt / typing_dur)
            draw_watermark(p, self.frame_w, self.frame_h, self.config)

        p.end()
        return img

    @staticmethod
    def _panes_blink_period():
        return 1.06

##############
#                            ══ 4 - ANIMATION ══                            
# rhythm engine + auto-fit solver + 4 mode strategies
# (was: animation.py in the ten-file edition)
##############

"""Timing layer: the TypingAnimator rhythm engine (Classic / Natural /
Cinematic), the auto-fit WPM solver (exact duration targeting), and
the four per-mode render strategies."""


#==============================================================================
# ── ANIMATION — TypingAnimator (Classic/Natural/Cinematic)
#    (merged from studio/animation.py in the v2.5 ten-file edition)
#==============================================================================

"""Typing simulation: produces per-character timestamps with humanised
delays, punctuation pauses and optional typo/backspace events.

v2.4 rhythm styles
------------------
* ``Classic``   — the original v1 behaviour, reproduced exactly (same RNG
  call order), kept for backwards-compatible renders.
* ``Natural``   — human typing: acceleration bursts of 5-11 characters
  followed by a micro-pause, slightly longer word gaps, tightened
  punctuation pauses and extra hesitation on blank lines.
* ``Cinematic`` — like Natural but more dramatic: heavier sentence/paragraph
  pauses, occasional "thinking" hesitations after block openers (``:``,
  ``{``), and a slow warm-up over the first characters.

``TypingProfile.intensity`` (0..2, default 1) scales how pronounced the
style's personality is: 0 = robotic metronome, 2 = very expressive.

All delays are ``base_delay * multiplier`` with ``base_delay = 1/(wpm*5/60)``,
so the total duration is exactly ``A / wpm + B`` for a fixed seed — the
property :mod:`studio.timing.fit_wpm` relies on to hit target durations.
"""

import bisect
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple


STYLES = ("Classic", "Natural", "Cinematic")


@dataclass
class TypingProfile:
    name: str = "Default"
    wpm: int = 100
    start_pause: float = 0.5
    end_pause: float = 1.5
    typo_rate: float = 0.0
    is_text: bool = False
    style: str = "Natural"      # Classic | Natural | Cinematic
    intensity: float = 1.0      # 0 = metronome, 1 = default, 2 = expressive


class TypingAnimator:
    def __init__(self, code: str, profile: TypingProfile, seed: int = 42):
        self.code, self.profile = code, profile
        self.error_count = 0
        rng = random.Random(seed)
        chars = split_graphemes(code) if profile.is_text else list(code)
        base_delay = 1.0 / ((profile.wpm * 5) / 60)
        style = profile.style if profile.style in STYLES else "Natural"
        k = max(0.0, float(profile.intensity))

        def rng_range(lo: float, hi: float) -> float:
            """Uniform in [lo, hi] with the personality scaled by intensity."""
            if k == 0.0:
                return 1.0
            return rng.uniform(1.0 + (lo - 1.0) * k, 1.0 + (hi - 1.0) * k)

        t = profile.start_pause
        self.display_chars, self._timestamps, self.timeline = [], [], []

        # --- per-style state ------------------------------------------------
        streak = 0                       # chars typed since the last break
        burst_len = self._new_burst(rng, style)
        warmup_chars = 26                # Cinematic warm-up window
        prev_char = ""

        for idx, char in enumerate(chars):
            # ---- typos (identical RNG order in every style) ----------------
            if char != "\n" and char != " " and rng.random() < profile.typo_rate:
                self.error_count += 1
                t += base_delay * rng.uniform(0.5, 1.0)
                self.timeline.append((t, rng.choice("abcdefghijklmnopqrstuvwxyz")))
                self.display_chars.append(self.timeline[-1][1]); self._timestamps.append(t)
                t += base_delay * rng.uniform(0.5, 1.0)
                self.timeline.append((t, "\b"))
                self.display_chars.append("\b"); self._timestamps.append(t)

            self.timeline.append((t, char))
            self.display_chars.append(char); self._timestamps.append(t)

            # ---- delay for this character ----------------------------------
            if style == "Classic":
                t += base_delay * self._classic_delay(char, rng)
            else:
                mult, burst_reset = self._human_delay(
                    char, prev_char, style, rng, rng_range,
                    streak, burst_len, k)
                if burst_reset:
                    streak = 0
                    burst_len = self._new_burst(rng, style)
                else:
                    streak += 1 if not char.isspace() else 0
                # Cinematic slow warm-up over the first characters
                if style == "Cinematic" and idx < warmup_chars:
                    mult *= 1.0 + k * 0.45 * (1.0 - idx / warmup_chars)
                t += base_delay * mult
            prev_char = char

        self._duration = t + profile.end_pause

    # ------------------------------------------------------------------
    @staticmethod
    def _new_burst(rng: random.Random, style: str) -> int:
        if style == "Cinematic":
            return rng.randint(4, 9)
        if style == "Natural":
            return rng.randint(5, 11)
        return 1 << 30  # Classic never bursts

    @staticmethod
    def _classic_delay(char: str, rng: random.Random) -> float:
        """The exact v1 delay table (same ranges, same RNG call order)."""
        if char in ".!?":
            return rng.uniform(4.0, 6.0)
        if char in ",;:":
            return rng.uniform(2.0, 3.5)
        if char == "\n":
            return rng.uniform(3.0, 5.0)
        return rng.uniform(0.7, 1.3)

    def _human_delay(self, char, prev_char, style, rng, rr, streak, burst_len, k=1.0):
        """Return (multiplier, burst_ended) for Natural/Cinematic styles."""
        cine = style == "Cinematic"
        if char in ".!?":
            return rr(4.5, 6.5) if cine else rr(3.5, 5.5), False
        if char in ",;:":
            return rr(2.2, 3.4) if cine else rr(1.8, 3.0), False
        if char == "\n":
            extra = 0.0
            if prev_char in ":{" and rng.random() < (0.4 if cine else 0.25):
                extra = rng.uniform(0.35, 0.9) * k   # thinking after a block opener
            if prev_char == "\n":                    # paragraph break
                base = rr(6.0, 9.0) if cine else rr(4.5, 7.0)
            else:
                base = rr(3.5, 5.5) if cine else rr(2.8, 4.6)
            return base + extra, True
        if char == " ":
            return rr(0.95, 1.35) if cine else rr(0.9, 1.3), False
        # regular character: bursts of speed with a micro-pause between them
        if streak + 1 >= burst_len:
            return rr(1.6, 2.6) if cine else rr(1.4, 2.4), True
        return rr(0.7, 1.15) if cine else rr(0.62, 1.05), False

    # ------------------------------------------------------------------
    def duration(self) -> float:
        return self._duration

    def visible_at(self, t: float) -> int:
        return bisect.bisect_right(self._timestamps, t) if t > 0 else 0

    def char_timestamps(self) -> List[Tuple[float, str]]:
        return self.timeline

    def active_key_at(self, t: float, fd: float = 0.18) -> Tuple[Optional[str], float]:
        if not self._timestamps or t < self._timestamps[0]:
            return None, 0.0
        idx = bisect.bisect_right(self._timestamps, t)
        if idx == 0:
            return None, 0.0
        last_ts, last_char = self.timeline[idx - 1]
        elapsed = t - last_ts
        return (last_char, max(0.0, (1.0 - elapsed / fd) ** 1.5)) if elapsed < fd else (None, 0.0)

    @staticmethod
    def find_wpm_for_target(text: str, target_dur: float, sp: float = 0.5, ep: float = 1.5) -> int:
        """Legacy heuristic (kept for compatibility); prefer studio.timing.fit_wpm."""
        available = target_dur - sp - ep
        if available <= 0:
            return 300
        count = len(split_graphemes(text))
        return max(30, min(300, int(60.0 / max(0.01, available / max(1, count * 1.2)) / 5.0)))

#==============================================================================
# ── TIMING — auto-fit WPM solver, audio probing, targets
#    (merged from studio/timing.py in the v2.5 ten-file edition)
#==============================================================================

"""Smart timing (v2.4): auto-fit solvers and audio-length probing.

This module is the brain behind "Auto-Adjust Timings":

* :func:`audio_duration`   — probe an audio file's length via ffprobe (cached).
* :func:`resolve_fit_target` — decide what "auto-fit" should aim for
  (explicit target seconds, or the length of the loaded BGM / ambience file).
* :func:`fit_wpm`          — solve the per-pane WPM values so the finished
  video hits the target duration exactly, while *preserving the relative
  speeds between panes* (e.g. Junior still types slower than Senior).

The solver exploits a property of :class:`studio.animation.TypingAnimator`:
with a fixed seed every delay is ``base_delay * multiplier``, so the total
duration is exactly ``A / wpm + B`` (B = start/end pauses).  One fixed-point
iteration therefore lands almost on target; a few more polish it.  Because
the fit builds real animators with the same seed & profile as the render,
the prediction matches the exported video to the frame.

Qt-free and import-light: safe to use from batch planning and the CLI.
"""

import os
import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, Tuple


# WPM bounds used by the solvers (wider than the UI spinboxes so the fit can
# slow down far more than it can speed up — that is what creators usually want).
FIT_WPM_MIN = 15.0
FIT_WPM_MAX = 300.0

# Acceptance: within 0.4% of the target or 0.08s, whichever is larger.
# The fixed-point iteration converges ~5x per step, so this costs nothing.
_FIT_EPS_REL = 0.004
_FIT_EPS_ABS = 0.08

_DURATION_CACHE: dict = {}


# ------------------------------------------------------------------ probing
def audio_duration(path: str) -> Optional[float]:
    """Length of an audio/video file in seconds via ffprobe (None on failure).

    Results are cached per (path, mtime) so previews can call this on every
    rebuild without spawning a process each time.
    """
    if not path or not os.path.isfile(path):
        return None
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return None
    key = (os.path.abspath(path), mtime)
    if key in _DURATION_CACHE:
        return _DURATION_CACHE[key]
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        dur = float(out)
        if dur <= 0:
            raise ValueError(out)
    except Exception as e:
        logger.warning(f"Could not probe audio duration of {path}: {e}")
        return None
    if len(_DURATION_CACHE) > 64:
        _DURATION_CACHE.clear()
    _DURATION_CACHE[key] = dur
    return dur


def branding_offsets(config: StudioConfig) -> Tuple[float, float]:
    """(lead_in, tail) seconds added by the intro/outro cards (0 when off)."""
    lead = INTRO_DURATION if getattr(config, "intro_enabled", False) else 0.0
    tail = OUTRO_DURATION if getattr(config, "outro_enabled", False) else 0.0
    return lead, tail


def resolve_fit_target(config: StudioConfig) -> Tuple[float, str]:
    """Return ``(target_total_seconds, note)`` for the current fit mode.

    * ``Target Duration`` -> config.timing_target
    * ``Audio Length``    -> the BGM file's duration; if none is loadable the
      custom ambience file; if that fails too we fall back to timing_target
      and say so in ``note`` (the caller can surface it in the UI).
    """
    mode = getattr(config, "timing_fit", "Off")
    fallback = float(getattr(config, "timing_target", 60.0) or 60.0)
    if mode == "Audio Length":
        for path, what in ((getattr(config, "bgm_path", ""), "BGM"),
                           (getattr(config, "amb_path", ""), "ambience file")):
            dur = audio_duration(path)
            if dur and dur > 1.0:
                return dur, f"fit to {what}: {os.path.basename(path)} ({dur:.1f}s)"
        return fallback, "no audio file found - falling back to target duration"
    return fallback, ""


# ------------------------------------------------------------------ solver
@dataclass
class FitResult:
    """Outcome of an auto-fit run."""
    wpms: List[float] = field(default_factory=list)
    durations: List[float] = field(default_factory=list)   # typing seg per pane
    target_typing: float = 0.0
    clamped: bool = False        # hit the WPM bounds; target unreachable
    note: str = ""

    @property
    def total(self) -> float:
        return max(self.durations) if self.durations else 0.0


def fit_wpm(codes: Sequence[str], base_wpms: Sequence[float],
            target_typing: float, make_profile: Callable[..., object],
            seed: int = 42, iters: int = 8,
            per_pane: bool = False) -> FitResult:
    """Solve WPM values so the longest pane finishes at ``target_typing``.

    ``make_profile(wpm, pane_idx)`` must build the same :class:`TypingProfile`
    the render will use (typo rate, rhythm style, intensity, is_text...), so
    the prediction is exact.

    * ``per_pane=False`` — every pane is scaled by one common factor, which
      preserves their relative speeds (Jr vs Sr, manual multi-window...).
      Only the longest pane lands on the target; shorter panes finish early.
    * ``per_pane=True``  — each pane is solved individually so *all* panes
      finish together on the target (used by the multi-window sync mode).
    """
    n = len(codes)
    if n == 0 or target_typing <= 0:
        return FitResult(wpms=list(base_wpms), durations=[0.0] * n,
                         target_typing=max(0.0, target_typing),
                         clamped=bool(target_typing > 0), note="nothing to fit")

    def durations_for(wpms: Sequence[float]) -> List[float]:
        out = []
        for i, (code, w) in enumerate(zip(codes, wpms)):
            anim = TypingAnimator(code, make_profile(w, i), seed=seed)
            out.append(anim.duration())
        return out

    wpms = [min(FIT_WPM_MAX, max(FIT_WPM_MIN, float(w))) for w in base_wpms]
    clamped = False
    note = ""

    if per_pane:
        # Solve each pane independently: every pane ends exactly on target.
        durs = []
        for i, (code, w0) in enumerate(zip(codes, wpms)):
            w = w0
            anim = TypingAnimator(code, make_profile(w, i), seed=seed)
            d = anim.duration()
            for _ in range(iters):
                if abs(d - target_typing) <= max(_FIT_EPS_ABS, target_typing * _FIT_EPS_REL):
                    break
                if d <= 0:
                    break
                nw = min(FIT_WPM_MAX, max(FIT_WPM_MIN, w * d / target_typing))
                if abs(nw - w) < 1e-9:
                    break
                w = nw
                d = TypingAnimator(code, make_profile(w, i), seed=seed).duration()
            wpms[i] = w
            durs.append(d)
        dmax = max(durs) if durs else 0.0
        if dmax > target_typing * (1 + _FIT_EPS_REL) + _FIT_EPS_ABS:
            clamped = True
            note = (f"content needs {dmax:.1f}s even at {int(FIT_WPM_MAX)} WPM "
                    f"(target {target_typing:.1f}s)")
        elif dmax < target_typing * (1 - _FIT_EPS_REL) - _FIT_EPS_ABS:
            clamped = True
            note = f"content too short to stretch to {target_typing:.1f}s"
        return FitResult(wpms=wpms, durations=durs, target_typing=target_typing,
                         clamped=clamped, note=note)

    durs = durations_for(wpms)
    dmax = max(durs)
    clamped = False
    note = ""

    if dmax <= 0.0:
        return FitResult(wpms=wpms, durations=durs,
                         target_typing=target_typing, clamped=True,
                         note="empty content")

    # Already at/below target with all panes at their floor?  Nothing to do.
    for _ in range(iters):
        err = dmax - target_typing
        if abs(err) <= max(_FIT_EPS_ABS, target_typing * _FIT_EPS_REL):
            break
        scale = dmax / target_typing
        new_wpms = [min(FIT_WPM_MAX, max(FIT_WPM_MIN, w * scale)) for w in wpms]
        if all(abs(nw - w) < 1e-9 for nw, w in zip(new_wpms, wpms)):
            clamped = True
            break
        wpms = new_wpms
        durs = durations_for(wpms)
        dmax = max(durs)

    if dmax > target_typing * (1 + _FIT_EPS_REL) + _FIT_EPS_ABS \
            and all(w >= FIT_WPM_MAX - 1e-6 for w in wpms):
        clamped = True
        note = (f"content needs {dmax:.1f}s even at {int(FIT_WPM_MAX)} WPM "
                f"(target {target_typing:.1f}s)")
    elif dmax < target_typing * (1 - _FIT_EPS_REL) - _FIT_EPS_ABS \
            and all(w <= FIT_WPM_MIN + 1e-6 for w in wpms):
        clamped = True
        note = f"content too short to stretch to {target_typing:.1f}s"

    return FitResult(wpms=wpms, durations=durs, target_typing=target_typing,
                     clamped=clamped, note=note)


def fit_target_for(config: StudioConfig) -> Tuple[Optional[float], str]:
    """(target_typing_seconds, note) — None when auto-fit is off."""
    mode = getattr(config, "timing_fit", "Off")
    if mode == "Off":
        return None, ""
    target_total, note = resolve_fit_target(config)
    lead, tail = branding_offsets(config)
    return max(0.5, target_total - lead - tail), note


def describe_fit(config: StudioConfig, result: FitResult) -> str:
    """Human-readable one-liner for the UI / dry runs."""
    lead, tail = branding_offsets(config)
    total = result.total + lead + tail
    wpm_txt = ", ".join(f"{w:.0f}" for w in result.wpms)
    s = f"auto-fit -> {total:.1f}s total (typing {result.total:.1f}s, WPM {wpm_txt})"
    if result.clamped:
        s += " [clamped]"
    if result.note:
        s += f" — {result.note}"
    return s

#==============================================================================
# ── STRATEGIES — per-mode render strategies + make_strategies
#    (merged from studio/strategies.py in the v2.5 ten-file edition)
#==============================================================================

"""Render strategies (Strategy pattern): turn config + files into a
MultiPaneRenderer.

All build_panes() methods accept a `scale` parameter (0 < scale <= 1) that
renders at a reduced resolution — used by the live preview for a ~4x speedup
while exports always render at full scale.
"""

import difflib
import json
import os
from abc import ABC, abstractmethod
from typing import List, Optional

from PySide6.QtCore import QRect



def get_line_diffs(code1, code2):
    lines1 = code1.splitlines()
    lines2 = code2.splitlines()
    sm = difflib.SequenceMatcher(None, lines1, lines2)
    diffs1, diffs2 = {}, {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            for i in range(i1, i2):
                diffs1[i] = "removed"
        if tag in ("replace", "insert"):
            for j in range(j1, j2):
                diffs2[j] = "added"
    return diffs1, diffs2


def scaledWH(config, scale: float):
    w, h = RESOLUTIONS.get(config.resolution, (1920, 1080))
    w = max(2, int(w * scale) // 2 * 2)
    h = max(2, int(h * scale) // 2 * 2)
    return w, h


class BaseRenderStrategy(ABC):
    @abstractmethod
    def build_panes(self, config: StudioConfig, files, custom_code: str,
                    scale: float = 1.0) -> Optional[MultiPaneRenderer]:
        ...

    def _get_code(self, config, files, custom_code):
        if config.use_custom:
            code = convert_shortcodes(custom_code)
            return (code if code.strip() else "# Custom code empty", "python", "custom_code.py")
        checked = [f for f in files if f.checked]
        if not checked:
            return ("import numpy as np\n\ndef hello():\n    print('Add files to begin!')", "python", "preview.py")
        it = checked[0]
        return (read_text_file(it.path, config.txt_clean),
                EXT_TO_LANGUAGE.get(os.path.splitext(it.path)[1].lower(), "text"),
                os.path.basename(it.path))

    def _make_renderer(self, config, w, h, code, title, lang, pane_idx=0, line_diffs=None,
                       is_text=False):
        if config.mode == StudioMode.MULTI_WINDOW:
            suffix = "" if pane_idx == 0 else f"_{pane_idx + 1}"
            font_fam = getattr(config, f"font_mw{suffix}")
            f_auto = getattr(config, f"font_sz_auto_mw{suffix}")
            f_sz = getattr(config, f"font_sz_mw{suffix}")
        elif config.mode == StudioMode.JR_VS_SR:
            if pane_idx == 0:
                font_fam = config.font_jr; f_auto = config.font_sz_auto_jr; f_sz = config.font_sz_jr
            else:
                font_fam = config.font_sr; f_auto = config.font_sz_auto_sr; f_sz = config.font_sz_sr
        elif config.mode == StudioMode.CODE_YT:
            font_fam = config.font_yt; f_auto = config.font_sz_auto_yt; f_sz = config.font_sz_yt
        elif config.mode == StudioMode.TEXT_EMOJI:
            font_fam = config.font_txt; f_auto = config.font_sz_auto_txt; f_sz = config.font_sz_txt
        else:
            font_fam = "Consolas"; f_auto = True; f_sz = 22

        kb_h = 0
        if config.kb_enabled:
            kb_h = int(w * 0.65 / 15 * 0.82) * 5 + 20

        if f_auto:
            fsz = StudioRenderer.auto_font_size(code.count("\n") + 1, w, h, text=code,
                                                font_family=font_fam, keyboard_h=kb_h,
                                                ascii_art_mode=config.ascii_art)
        else:
            fsz = max(8, round(f_sz * (w / RESOLUTIONS.get(config.resolution, (1920, 1080))[0])))

        kb = None
        if config.kb_enabled:
            pos_str = config.kb_position.lower().replace(" ", "_")
            kb = KeyboardOverlay(w, h, config.kb_layout, THEMES.get(config.theme, THEMES["Dracula"]),
                                 config.kb_opacity, (h - 2 * 24) // 3, pos_str)
        renderer = StudioRenderer(
            w, h, config.theme, font_fam, fsz,
            language=EXT_TO_LANGUAGE.get(os.path.splitext(title)[1].lower(), lang),
            ascii_art_mode=config.ascii_art, config=config, pane_idx=pane_idx,
            line_diffs=line_diffs, kb_overlay=kb)
        renderer.prepare_code(code, is_text=is_text)
        return renderer

    def _make_animator(self, code, wpm, tr=0.0, is_text=False, config=None):
        # ANSI terminal art: escape sequences must never enter the typing
        # timeline (they would render as glitch glyphs and desync the
        # keyboard overlay). Strip them so the animator's characters match
        # exactly the renderer's visible units.
        if "\x1b[" in code:
            code = strip_ansi(code)
        style = getattr(config, "rhythm_style", "Natural") if config else "Natural"
        intensity = (getattr(config, "rhythm_intensity", 100) or 100) / 100.0 if config else 1.0
        return TypingAnimator(code, TypingProfile(wpm=wpm, typo_rate=tr, is_text=is_text,
                                                  style=style, intensity=intensity))

    # ---- v2.4 auto-fit: solve WPMs so the video hits the target --------
    def _profile_factory(self, config, specs):
        """Build the same TypingProfile the render will use (exact fit)."""
        style = getattr(config, "rhythm_style", "Natural")
        intensity = (getattr(config, "rhythm_intensity", 100) or 100) / 100.0

        def make_profile(wpm, pane_idx):
            _, _, tr, is_text = specs[pane_idx]
            return TypingProfile(wpm=wpm, typo_rate=tr, is_text=is_text,
                                 style=style, intensity=intensity)
        return make_profile

    def _run_fit(self, config, specs, target, per_pane=False):
        """Solve specs -> wpms for the given typing-segment target (seconds)."""
        codes = [s[0] for s in specs]
        base = [s[1] for s in specs]
        result = fit_wpm(codes, base, max(0.5, target),
                         self._profile_factory(config, specs), per_pane=per_pane)
        if result.clamped:
            logger.warning(f"Auto-fit clamped: {result.note}")
        return result.wpms

    def _apply_auto_fit(self, config, specs):
        """specs: [(code, base_wpm, typo_rate, is_text), ...] -> solved wpms.

        Returns base wpms unchanged when config.timing_fit is Off.  The fit
        builds animators with the same seed/profile as the render, so the
        prediction matches the export exactly.
        """
        target, note = fit_target_for(config)
        if target is None:
            return [s[1] for s in specs]
        if note:
            logger.info(f"Auto-fit: {note}")
        return self._run_fit(config, specs, target, per_pane=False)


class MultiWindowStrategy(BaseRenderStrategy):
    def build_panes(self, config, files, custom_code, scale=1.0):
        w, h = scaledWH(config, scale)
        n_panes = MULTI_WINDOW_LAYOUTS[config.layout_mw]
        gap = 20
        pane_rects = MultiPaneRenderer.compute_pane_rects(w, h, n_panes, "Grid", gap, config)

        codes = []
        if config.use_custom:
            c, l, t = self._get_code(config, files, custom_code)
            for _ in range(n_panes):
                codes.append((c, l, t))
        else:
            checked = [f for f in files if f.checked]
            if not checked:
                c, l, t = self._get_code(config, files, custom_code)
                for _ in range(n_panes):
                    codes.append((c, l, t))
            else:
                for i in range(n_panes):
                    if i < len(checked):
                        it = checked[i]
                        codes.append((read_text_file(it.path, config.txt_clean),
                                      EXT_TO_LANGUAGE.get(os.path.splitext(it.path)[1].lower(), "text"),
                                      os.path.basename(it.path)))
                    else:
                        codes.append(codes[0])

        if config.sync_mw:
            # v2.4: panes are synced with the exact per-pane solver (was a
            # rough heuristic), so they all finish within milliseconds.  When
            # auto-fit is also on, the sync lands on the fit target instead.
            specs = [(c, config.wpm_mw, config.typo_mw, False) for c, _, _ in codes]
            style = getattr(config, "rhythm_style", "Natural")
            intensity = (getattr(config, "rhythm_intensity", 100) or 100) / 100.0
            base_dur = max(
                TypingAnimator(c, TypingProfile(wpm=config.wpm_mw,
                                                typo_rate=config.typo_mw,
                                                style=style,
                                                intensity=intensity)).duration()
                for c, _, _ in codes)
            fit_t, _note = fit_target_for(config)
            wpms = self._run_fit(config, specs,
                                 fit_t if fit_t is not None else base_dur,
                                 per_pane=True)
        else:
            specs = [(codes[i][0], config.wpm_mw, config.typo_mw, False)
                     for i in range(n_panes)]
            wpms = self._apply_auto_fit(config, specs)

        diffs = [None] * n_panes
        if config.diff_highlight_mw and n_panes >= 2:
            d01_0, d01_1 = get_line_diffs(codes[0][0], codes[1][0])
            diffs[0] = d01_0; diffs[1] = d01_1
            if n_panes >= 3:
                d12_1, d12_2 = get_line_diffs(codes[1][0], codes[2][0])
                merged_1 = {}
                for k, v in d01_1.items():
                    merged_1[k] = v
                for k, v in d12_1.items():
                    merged_1[k] = v
                diffs[1] = merged_1; diffs[2] = d12_2
            if n_panes >= 4:
                d23_2, d23_3 = get_line_diffs(codes[2][0], codes[3][0])
                merged_2 = {}
                for k, v in (diffs[2] or {}).items():
                    merged_2[k] = v
                for k, v in d23_2.items():
                    merged_2[k] = v
                diffs[2] = merged_2; diffs[3] = d23_3

        git_titles = ["Base", "Incoming", "Resolved"]
        panes = []
        for i in range(n_panes):
            code, lang, title = codes[i]
            animator = self._make_animator(code, wpms[i], tr=config.typo_mw, config=config)
            if n_panes == 3 and config.layout_mw == "Git Conflict (3-Pane)":
                title_text = f"{git_titles[i]} - {title}"
            else:
                title_text = title
            rect = pane_rects[i]
            renderer = self._make_renderer(config, rect.width(), rect.height(), code, title, lang, i, diffs[i])
            panes.append((renderer, animator, title_text))
        return MultiPaneRenderer(panes, w, h, n_panes, "Grid", gap=gap, config=config)


class JrVsSrStrategy(BaseRenderStrategy):
    def build_panes(self, config, files, custom_code, scale=1.0):
        w, h = scaledWH(config, scale)
        gap = 20
        pane_rects = MultiPaneRenderer.compute_pane_rects(w, h, 2, config.layout_jr, gap, config)

        if config.use_custom or (config.jr_custom_code and config.sr_custom_code):
            code1 = convert_shortcodes(config.jr_custom_code) if config.jr_custom_code else "def junior():\n    pass"
            code2 = convert_shortcodes(config.sr_custom_code) if config.sr_custom_code else "def senior():\n    pass"
            lang, t1, t2 = "python", "junior.py", "senior.py"
        else:
            checked = [f for f in files if f.checked]
            if not checked:
                c, l, t = self._get_code(config, files, custom_code)
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
                        c, l, t = self._get_code(config, files, custom_code)
                        code1, code2, lang, t1, t2 = c, c, l, t, t
                else:
                    c, l, t = self._get_code(config, files, custom_code)
                    code1, code2, lang, t1, t2 = c, c, l, t, t

        # v2.4 auto-fit: a common scale factor keeps Junior slower than Senior
        wpms = self._apply_auto_fit(config, [(code1, config.jr_wpm, config.typo_jr, False),
                                             (code2, config.sr_wpm, 0.0, False)])
        a1 = self._make_animator(code1, wpms[0], tr=config.typo_jr, config=config)
        a2 = self._make_animator(code2, wpms[1], tr=0.0, config=config)
        r1 = self._make_renderer(config, pane_rects[0].width(), pane_rects[0].height(), code1, t1, lang, 0)
        r2 = self._make_renderer(config, pane_rects[1].width(), pane_rects[1].height(), code2, t2, lang, 1)
        return MultiPaneRenderer([(r1, a1, f"\U0001F476 Junior - {t1}"), (r2, a2, f"\U0001F9D3 Senior - {t2}")],
                                 w, h, 2, config.layout_jr, gap=gap, config=config)


class CodeYTStrategy(BaseRenderStrategy):
    def build_panes(self, config, files, custom_code, scale=1.0):
        w, h = scaledWH(config, scale)
        code, lang, title = self._get_code(config, files, custom_code)
        wpm = self._apply_auto_fit(config, [(code, config.wpm_yt, config.typo_yt, False)])[0]
        a = self._make_animator(code, wpm, tr=config.typo_yt, config=config)
        return MultiPaneRenderer([(self._make_renderer(config, w, h, code, title, lang), a, title)],
                                 w, h, 1, "Single", config=config)


class TextEmojiStrategy(BaseRenderStrategy):
    def build_panes(self, config, files, custom_code, scale=1.0):
        w, h = scaledWH(config, scale)
        code, lang, title = self._get_code(config, files, custom_code)
        if config.shorts_txt:
            # legacy behaviour: squeeze into just under the 3-minute Shorts
            # window (v2.4 uses the exact solver instead of the heuristic)
            wpm = self._run_fit(config, [(code, config.wpm_txt, 0.0, True)],
                                177.0)[0]
        else:
            wpm = self._apply_auto_fit(
                config, [(code, config.wpm_txt, config.typo_txt, True)])[0]
        a = self._make_animator(code, wpm, is_text=True, config=config)
        return MultiPaneRenderer([(self._make_renderer(config, w, h, code, title, lang, is_text=True), a, title)],
                                 w, h, 1, "Single", config=config)


def make_strategies():
    return {
        StudioMode.MULTI_WINDOW: MultiWindowStrategy(),
        StudioMode.JR_VS_SR: JrVsSrStrategy(),
        StudioMode.CODE_YT: CodeYTStrategy(),
        StudioMode.TEXT_EMOJI: TextEmojiStrategy(),
    }

##############
#                              ══ 5 - AUDIO ══                              
# key-click DSP engine + 34 ambience soundscapes (patterns + v3.3 sound design)
# (was: audio.py in the ten-file edition)
##############

"""Audio layer: professional keypress-SFX engine (layered physical key model)
with custom WAV loading, plus 34 procedural ambience soundscapes, custom-file
looping and mixing.

Architecture — the design patterns this module uses, and where to find them:

  * Strategy            every ambience soundscape is an interchangeable
                        ``(n, sr, rng) -> ndarray`` strategy (see
                        :class:`SoundscapeFn`); wave shapes and filter shapes
                        in :class:`ModularSoundEngine` are resolved through
                        dispatch tables instead of ``if/elif`` chains, so new
                        oscillators plug in without touching the engine
                        (Open/Closed principle).
  * Registry            the ``@soundscape("Rain")`` decorator registers
                        strategies into ``AMBIENCE_PRESETS`` — adding a
                        soundscape is one decorated function, there is no
                        hand-maintained dict to forget to update.
  * Facade              :class:`SimpleSoundGen` hides pool building, pitch
                        mapping, mastering and custom-WAV import behind one
                        small class (the only class the rest of the app needs).
  * Factory Method      :class:`VariantPoolFactory` builds the detuned
                        round-robin sample families, from either a procedural
                        :class:`SoundSpec` or user-supplied WAV samples.
  * Builder             :class:`SoundSpecBuilder` composes layered key sounds
                        fluently and safely.
  * Chain of Resp.      mastering is a pipeline of ``AudioStage`` objects
                        (``RoomTailStage → LoudnessStage → PeakGuard``); the
                        engine composes its per-spec chain
                        (``ResonanceBankStage → HighPass → LowPass``) the same
                        way.
  * Flyweight           the 32/16/8 detuned click/space/enter variants are
                        pre-rendered once and reused across every event.
  * Adapter             ``_pcm_bytes_to_float`` adapts every PCM width
                        (8/16/24/32-bit) to float64 for both WAV loaders —
                        the width logic exists exactly once.
  * Value Objects       ``VoiceSpec`` / ``SoundSpec`` are plain dataclasses;
                        presets are declared as data, not built by code.
  * Memoization         FIR low-pass kernels are ``lru_cache``d — the same
                        windowed-sinc kernel used to be rebuilt for every
                        layer of every variant of every export.

Sound design, v3.3 upgrades:

  * organic variants     every round-robin variant now also carries its own
                        level (±1.5 dB), attack time (±22%), brightness
                        (±10%) and micro-delay (≤0.6 ms) — the pool no longer
                        differs only in pitch, which was still audible as a
                        subtle machine-gun pattern on fast passages.
  * physical stereo      clicks are panned by QWERTY geometry (a key on the
                        left of the board sounds left) with a small human
                        spread, instead of pure random panning.
  * real room tail       the reverb impulse gains discrete early reflections
                        (wall taps at 5-32 ms) under the diffusive tail.
  * living beds          rain, wind, café, ocean, forest, stream, space and
                        server ambience drift on multi-period "wander"
                        envelopes instead of a single sine LFO — slow
                        natural breathing instead of an audible wobble.
  * bug fix              ``_hp`` used to return ``impulse − lowpass(x)``
                        (a latent click in the middle of every steam/foam
                        bed); it is a true high-pass now.

Everything here is Qt-free (numpy + stdlib only) and fully deterministic:
identical inputs and seeds always produce bit-identical audio.
"""


import random
import shutil
import subprocess
import wave
from dataclasses import dataclass, field, replace
from functools import lru_cache
from typing import (Callable, ClassVar, Dict, Final, List, Optional, Protocol,
                    Sequence, Tuple, runtime_checkable)

import numpy as np


try:
    from numba import njit
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False


__all__ = [
    "AUDIO_SAMPLE_RATE", "DSP", "SoundSpec", "VoiceSpec", "SoundSpecBuilder",
    "ModularSoundEngine", "SimpleSoundGen", "MODULAR_SOUND_PRESETS",
    "AMBIENCE_PRESETS", "list_ambience_presets", "render_ambience",
    "load_ambience_file", "load_wav_sample", "load_wav_samples",
    "extend_wav_procedural", "render_ambience_from_wav", "mix_ambience",
    "build_ambience_bed", "KeyLayout", "VariantPoolFactory", "VariantFamily",
    "HighPassStage", "LowPassStage", "ResonanceBankStage", "RoomTailStage",
    "LoudnessStage", "SoftClipStage", "TruePeakLimiterStage", "TruePeakStage",
    "run_stages", "SoundscapeFn", "AudioStage",
]

# ── round-robin pool geometry (Flyweight): rendered once, reused everywhere
CLICK_VARIANTS: Final[int] = 32
SPACE_VARIANTS: Final[int] = 16
ENTER_VARIANTS: Final[int] = 8
MAX_CUSTOM_SOURCES: Final[int] = 4
CUSTOM_DETUNE_SEMITONES: Final[Tuple[float, ...]] = (0.0, 0.4, -0.4, 0.9, -0.9)
MAX_CUSTOM_CLICK_SECONDS: Final[float] = 0.35

# ── mastering targets
LUFS_TARGET: Final[float] = -14.0
MASTER_CEILING: Final[float] = 0.98
CLICK_HEADROOM_DB: Final[float] = -1.0
ROOM_TAIL_SEED: Final[int] = 4242
# v1.0.3: the room-tail IR is energy-normalised to a FIXED sum(ir^2).
# v1.0.2 peak-normalised it instead, which made the tail's loudness depend
# on the seed's peak factor (±2 dB, i.e. the two decorrelated stereo seeds
# pulled the image off centre) AND set the accidental wet level to ~half
# the dry signal (sum(ir^2) ≈ 74) — a 110 ms noise tail at -6 dB behind
# every keystroke, which read as the "static" the user reported.  Energy
# 8.0 puts the tail at a tasteful -15 dB room, identical for every seed,
# with the decorrelated stereo pair contributing no image shift.
ROOM_TAIL_IR_ENERGY: Final[float] = 8.0
# v1.0.3: the true-peak limiter's ceiling sits exactly at the scale-only
# backstop level, so the backstop only ever trims limiter reconstruction
# overshoot (~0.0-0.1 dB) instead of re-scaling every heavily-limited track.
LIMITER_CEILING_DBTP: Final[float] = -1.05
TP_BACKSTOP_DBTP: Final[float] = -1.05
# loudness->limit iterations to convergence (limiting reduces integrated
# loudness, so one anchor pass lands below target on extreme-crest presets)
LOUDNESS_PASSES: Final[int] = 3

# ── ambience bed mastering: every procedural bed is loudness-anchored so the
#    "Ambience volume" slider means the same thing for Rain and Wind (before
#    the fix the two differed by ~10 dB of loudness at the same slider value)
BED_TARGET_LUFS: Final[float] = -16.0
BED_PEAK_CEILING: Final[float] = 0.85
# v1.0.3: impulse beds (Vinyl Crackle pops, thunder cracks) carry strong
# intersample peaks — the *sample* cap above left their 4x true peak above
# full scale (measured +0.26 dBTP on Vinyl Crackle), which then shoved the
# whole keystroke mix into the soft ceiling at mix time.  Beds are now also
# capped in the oversampled (true-peak) domain.
BED_TP_CEILING: Final[float] = 0.866      # -1.2 dBTP, ~1.5 dB under the mix ceiling
BED_TP_CEILING_DBTP: Final[float] = -1.2  # limiter ceiling for the bed anchor
BED_ANCHOR_PASSES: Final[int] = 4         # gain->limit iterations to converge
BED_FADE_IN_S: Final[float] = 0.8
BED_FADE_OUT_S: Final[float] = 0.5

# ── per-variant organic variation (fraction of the maximum humanisation)
DEFAULT_VARIATION: Final[float] = 0.55


# ==========================================================================
# Protocols — the two contracts every pluggable piece implements
# ==========================================================================
@runtime_checkable
class SoundscapeFn(Protocol):
    """Strategy contract: render one ambience bed.

    ``n`` is the sample count, ``sr`` the sample rate, ``rng`` a seeded
    ``numpy`` random state (strategies must draw deterministically from it
    and never seed their own).
    """

    def __call__(self, n: int, sr: int, rng: np.random.RandomState) -> np.ndarray:
        ...


@runtime_checkable
class AudioStage(Protocol):
    """One link of a mastering chain: signal in, signal out (same length)."""

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        ...


# ==========================================================================
# Loudness (ITU-R BS.1770 K-weighting) — numba-accelerated when available
# ==========================================================================
if _HAS_NUMBA:
    @njit(cache=True)
    def _nb_k_weight(x, sr):
        n = len(x); y = np.empty(n, dtype=np.float64)
        if sr == 48000:
            # canonical ITU-R BS.1770-4 coefficients for 48 kHz — the same
            # set libebur128 / ffmpeg loudnorm / YouTube use.  (v1.0.3: the
            # previous "fix" had swapped-in values for the stage-1 b2 / a1
            # taps (b2 1.4397 instead of 1.1984) which read a 440 Hz tone
            # +16 dB hot and 4 kHz 9 dB cold — every track was silently
            # normalised ~13 dB too quiet at true BS.1770 loudness.  These
            # are the reference coefficients; a 997 Hz sine at -20 dBFS
            # must measure -20.7 LUFS, which the regression test checks.)
            s1_b0 = 1.53512485958697; s1_b1 = -2.69169618940638; s1_b2 = 1.19839281085285
            s1_a1 = -1.69065929318241; s1_a2 = 0.73248077421585
            s2_b0 = 1.0; s2_b1 = -2.0; s2_b2 = 1.0
            s2_a1 = -1.99004745483398; s2_a2 = 0.99007225036621
        else:
            for i in range(n):
                y[i] = x[i]
            return y
        z1 = z2 = 0.0
        for i in range(n):
            xn = x[i]; yn = s1_b0 * xn + z1
            z1 = s1_b1 * xn - s1_a1 * yn + z2; z2 = s1_b2 * xn - s1_a2 * yn; y[i] = yn
        z1 = z2 = 0.0
        for i in range(n):
            xn = y[i]; yn = s2_b0 * xn + z1
            z1 = s2_b1 * xn - s2_a1 * yn + z2; z2 = s2_b2 * xn - s2_a2 * yn; y[i] = yn
        return y

    @njit(cache=True)
    def _nb_gated_loudness(x_k):
        """BS.1770-4 *gated* integrated loudness of a K-weighted signal.

        400 ms blocks / 100 ms hop, then the standard two-stage gating:
        blocks below -70 LUFS absolute are dropped, blocks below
        (ungated level - 10 LU) relative are dropped.  Gating is what makes
        the measurement agree with how loud a sparse, percussive track
        *feels* — an ungated whole-file mean under-reads a keystroke track
        by several dB because silence between keys drags the average down.
        """
        n = len(x_k)
        blk = int(0.4 * 48000)
        hop = int(0.1 * 48000)
        if n < blk:
            if n == 0:
                return -70.0
            s = 0.0
            for i in range(n):
                s += x_k[i] * x_k[i]
            ms = s / n
            if ms < 1e-20:
                return -70.0
            return -0.691 + 10.0 * np.log10(ms)
        nb = 1 + (n - blk) // hop
        # pass 1: block energies + absolute gate.  Full-sum energies (no
        # stride subsampling): K-weighted tonal/hf-dense content has strong
        # difference-frequency cross-terms in |x|^2, and sampling those at
        # 12 kHz aliases into the block mean and biased the estimate by
        # several dB on bright presets.
        total_e = 0.0
        n_abs = 0
        for b in range(nb):
            s = 0.0
            base = b * hop
            for i in range(base, base + blk):
                v = x_k[i]
                s += v * v
            e = s / blk
            j = -0.691 + 10.0 * np.log10(max(e, 1e-20))
            if j > -70.0:
                total_e += e
                n_abs += 1
        if n_abs == 0:
            return -70.0
        rel = -0.691 + 10.0 * np.log10(total_e / n_abs) - 10.0
        # pass 2: relative gate
        s2 = 0.0
        n_rel = 0
        for b in range(nb):
            s = 0.0
            base = b * hop
            for i in range(base, base + blk):
                v = x_k[i]
                s += v * v
            e = s / blk
            j = -0.691 + 10.0 * np.log10(max(e, 1e-20))
            if j > rel and j > -70.0:
                s2 += e
                n_rel += 1
        if n_rel == 0:
            return -70.0
        return -0.691 + 10.0 * np.log10(s2 / n_rel)

    @njit(cache=True)
    def _nb_apply_gain(x, gain):
        n = len(x); out = np.empty(n, dtype=np.float64)
        for i in range(n):
            out[i] = x[i] * gain
        return out


def _lufs_numpy(x, sr):
    """Pure-numpy BS.1770-4 gated loudness — the no-numba fallback.

    The canonical K-weighting stage is an IIR pair (shelving pre-filter +
    RLB high-pass).  Without numba we use a *linear-phase FIR* equivalent:
    a brickwall split at 1.5 kHz with a +4 dB shelf above it, then a steep
    FIR high-pass at 38 Hz, both FFT-convoled.  The magnitude response
    matches the IIR K-weight curve within a fraction of a dB in the energy
    band that matters, so the gated loudness lands within ~0.5 LU of the
    numba path on speech/music/keystroke content.  Block processing
    (400 ms / 100 ms hop, two-stage gating) mirrors :func:`_nb_gated_loudness`
    exactly, fully vectorised.
    """
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n == 0:
        return -70.0
    # --- FIR K-weight approximation (low + shaped-high keeps phase linear) ---
    # Both branches of the split carry the FIR's group delay ((255-1)/2
    # samples) — ``high`` must be computed against the *delayed* input or
    # the low band leaks into it (x(t) - x(t-d) ≠ HF content) and the
    # measurement loses most of its energy below the split.
    d = (255 - 1) // 2
    xd = np.zeros(n, dtype=np.float64)
    xd[d:] = x[:n - d]
    low = DSP.filt_lp(x, 1500, sr, 255)
    high = xd - low
    xk = low + high * 10.0 ** (4.0 / 20.0)
    xk = DSP.filt_hp(xk, 38.0, sr, 511)
    # --- gated blocks (vectorised: 400 ms windows on a 100 ms hop) ---
    blk = int(0.4 * sr)
    hop = int(0.1 * sr)
    if n < blk:
        ms = float(np.mean(xk * xk))
        return -70.0 if ms < 1e-20 else -0.691 + 10.0 * np.log10(ms)
    nb = 1 + (n - blk) // hop
    idx = np.arange(blk)[None, :] + hop * np.arange(nb)[:, None]
    e = np.mean(xk[idx] * xk[idx], axis=1)
    j = -0.691 + 10.0 * np.log10(np.maximum(e, 1e-20))
    abs_ok = j > -70.0
    if not abs_ok.any():
        return -70.0
    rel = -0.691 + 10.0 * np.log10(float(np.mean(e[abs_ok]))) - 10.0
    ok = abs_ok & (j > rel)
    if not ok.any():
        return -70.0
    return -0.691 + 10.0 * np.log10(float(np.mean(e[ok])))


def _normalize_to_lufs(x, sr, target_lufs=LUFS_TARGET):
    if len(x) < sr // 2:
        return x
    x = np.asarray(x, dtype=np.float64)
    if _HAS_NUMBA:
        xk = _nb_k_weight(x.astype(np.float64), sr)
        cl = _nb_gated_loudness(xk)
    else:
        # v1.0.3: machines without numba used to silently skip mastering
        # (the function returned the input untouched and the -14 LUFS target
        # was a no-op).  The pure-numpy measurement keeps the chain honest.
        cl = _lufs_numpy(x, sr)
    if not np.isfinite(cl) or cl <= -70.0:
        return x
    gdb = target_lufs - cl
    gl = 10.0 ** (gdb / 20.0)
    if _HAS_NUMBA:
        return _nb_apply_gain(x.astype(np.float64), gl).astype(np.float32)
    return (x * gl).astype(np.float32)


def _fft_convolve_chunked(x: np.ndarray, h: np.ndarray, chunk: int = 1 << 18) -> np.ndarray:
    """Overlap-add FFT convolution with bounded memory (long beds + short IR)."""
    n, nh = len(x), len(h)
    if n == 0:
        return x.astype(np.float64)
    if nh <= 1:
        return x.astype(np.float64) * (h[0] if nh == 1 else 1.0)
    n_fft = 1 << ((chunk + nh - 1).bit_length())
    H = np.fft.rfft(h, n_fft)
    out = np.zeros(n + nh - 1, dtype=np.float64)
    for start in range(0, n, chunk):
        blk = x[start:start + chunk]
        conv = np.fft.irfft(np.fft.rfft(blk, n_fft) * H, n_fft)
        end = min(start + len(conv), len(out))
        out[start:end] += conv[:end - start]
    return out[:n]


# ==========================================================================
# Small shared helpers (used by both the SFX and the ambience halves)
# ==========================================================================
def _normalize(x: np.ndarray, peak: float = 0.9) -> np.ndarray:
    """Peak-normalise ``x`` to ``peak`` (no-op on silence)."""
    mx = np.max(np.abs(x))
    if mx > 1e-9:
        x = x / mx * peak
    return x


def _fade_edges(x: np.ndarray, sr: int, fade_in: float = 0.05,
                fade_out: float = 0.5) -> np.ndarray:
    """Quadratic fade-in / fade-out so beds never click at the seams.

    The squared ramps reach zero *fast* at the very end (a linear fade-out
    still carries 10 % of the level 50 ms before the last sample, which
    reads as an audible cut-off edge on stationary noise beds) while
    starting gently — the standard shape for ambience beds.
    """
    n_in = min(len(x), int(fade_in * sr))
    n_out = min(len(x), int(fade_out * sr))
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in) ** 2
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out) ** 2
    return x


# ==========================================================================
# DSP toolkit — static kernels shared by the engine and the soundscapes
# ==========================================================================
class DSP:
    """Stateless DSP primitives (windowed-sinc FIRs, oscillators, modal synthesis)."""

    @staticmethod
    def env_exp(n, sr, attack=0.001, decay_rate=30.0, attack_curve=2.0):
        t = np.arange(n, dtype=np.float64) / sr
        env = np.exp(-t * decay_rate)
        a_samp = max(1, int(attack * sr))
        if a_samp < n:
            a_env = np.linspace(0, 1, a_samp) ** attack_curve
            env[:a_samp] = a_env * np.exp(-np.arange(a_samp, dtype=np.float64) / sr * decay_rate)
        return env

    @staticmethod
    @lru_cache(maxsize=512)  # memoization: kernels are tiny, calls are many
    def fir_lowpass(cutoff, sr=AUDIO_SAMPLE_RATE, n_taps=127):
        """Windowed-sinc low-pass kernel.

        Callers quantise cutoffs to whole Hz, so repeated renders hit the
        cache instead of rebuilding the same kernel.
        """
        if n_taps % 2 == 0:
            n_taps += 1
        fc = min(max(1.0, cutoff), sr / 2.0 - 1.0) / sr
        n = np.arange(n_taps, dtype=np.float64); center = (n_taps - 1) / 2.0
        h = np.sinc(2 * fc * (n - center))
        w = 0.42 - 0.5 * np.cos(2 * np.pi * n / (n_taps - 1)) + 0.08 * np.cos(4 * np.pi * n / (n_taps - 1))
        h *= w
        s = np.sum(h)
        if s > 0:
            h /= s
        return h

    @staticmethod
    def convolve(x, h):
        n, nh = len(x), len(h)
        if nh <= 1:
            return x * h[0] if nh == 1 else x
        n_fft = 1 << ((n + nh - 1).bit_length())
        return np.fft.irfft(np.fft.rfft(x, n_fft) * np.fft.rfft(h, n_fft), n_fft)[:n]

    @staticmethod
    def filt_lp(x, c, sr=AUDIO_SAMPLE_RATE, n_taps=127):
        return DSP.convolve(x, DSP.fir_lowpass(c, sr, n_taps))

    @staticmethod
    def filt_hp(x, c, sr=AUDIO_SAMPLE_RATE, n_taps=63):
        hlp = DSP.fir_lowpass(c, sr, n_taps); h = -hlp; h[len(h) // 2] += 1.0
        return DSP.convolve(x, h)

    @staticmethod
    def filt_bp(x, l, h, sr=AUDIO_SAMPLE_RATE):
        return DSP.filt_lp(x, h, sr) - DSP.filt_lp(x, l, sr)

    @staticmethod
    def filt_resonator(x, freq, q, sr=AUDIO_SAMPLE_RATE, gain=1.0):
        """Decaying sine IR at ``freq`` — turns a click into a body/housing mode."""
        w0 = 2 * np.pi * freq / sr; r = np.exp(-w0 / (2 * max(0.5, q)))
        wd = w0 * np.sqrt(max(0.0, 1.0 - 1.0 / (4 * q * q))) if q > 0.5 else w0
        n_ir = min(len(x), max(16, int(sr * max(0.005, 6.0 * q / max(1.0, freq)))))
        t = np.arange(n_ir, dtype=np.float64); ir = (r ** t) * np.sin(wd * t)
        pk = np.max(np.abs(ir))
        if pk > 1e-10:
            ir = ir / pk * gain
        return DSP.convolve(x, ir)

    @staticmethod
    def osc_sine(f, n, sr):
        return np.sin(2 * np.pi * f * (np.arange(n, dtype=np.float64) / sr))

    @staticmethod
    def osc_fm(c, mr, mi, n, sr):
        t = np.arange(n, dtype=np.float64) / sr
        return np.sin(2 * np.pi * c * t + mi * np.sin(2 * np.pi * c * mr * t))

    @staticmethod
    def osc_saw(f, n, sr):
        t = np.arange(n, dtype=np.float64) / sr; sig = np.zeros(n)
        for h in range(1, 17):
            fh = f * h
            if fh >= sr * 0.45:
                break
            sig += np.sin(2 * np.pi * fh * t) / h
        return sig * 0.5

    @staticmethod
    def osc_triangle(f, n, sr):
        """Band-limited triangle (odd harmonics, 1/h² roll-off) — softer than saw."""
        t = np.arange(n, dtype=np.float64) / sr
        sig = np.zeros(n)
        for h in range(1, 17, 2):
            fh = f * h
            if fh >= sr * 0.45:
                break
            sig += (1.0 if h % 4 == 1 else -1.0) * np.sin(2 * np.pi * fh * t) / (h * h)
        return sig * (8.0 / (np.pi * np.pi))

    @staticmethod
    def noise_white(n, rng):
        return rng.randn(n).astype(np.float64)

    @staticmethod
    def noise_pink(n, rng):
        white = rng.randn(n).astype(np.float64)
        fft = np.fft.rfft(white)
        freqs = np.fft.rfftfreq(n, 1.0 / AUDIO_SAMPLE_RATE)
        freqs[0] = max(freqs[1] if len(freqs) > 1 else 1.0, 1.0)
        fft[1:] /= np.sqrt(np.abs(freqs[1:])); fft[0] = 0
        return np.fft.irfft(fft, n=n)

    @staticmethod
    def noise_brown(n, rng):
        white = rng.randn(n).astype(np.float64); brown = np.cumsum(white); brown -= np.mean(brown)
        pk = np.max(np.abs(brown))
        if pk > 0:
            brown = brown / pk
        return brown * 0.5

    @staticmethod
    def modal(modes, n, sr, inharmonicity=0.0):
        """Sum of decaying sine modes with optional inharmonicity (bars, plates)."""
        t = np.arange(n, dtype=np.float64) / sr; out = np.zeros(n, dtype=np.float64)
        f0 = modes[0][0] if modes else 440.0
        for freq, decay, amp in modes:
            af = freq
            if inharmonicity > 0:
                nh = freq / f0; af = freq * np.sqrt(1 + inharmonicity * nh * nh)
            out += np.sin(2 * np.pi * af * t) * np.exp(-decay * t) * amp
        return out

    @staticmethod
    def sat_tanh(x, drive=1.0):
        if drive <= 0:
            return x
        return np.tanh(x * drive) / max(0.001, np.tanh(drive))

    @staticmethod
    def to_int16(x, target_db=CLICK_HEADROOM_DB):
        pk = np.max(np.abs(x)) if len(x) > 0 else 0.0
        if pk < 1e-10:
            return np.zeros_like(x, dtype=np.int16)
        return np.clip(x * (10 ** (target_db / 20) / pk) * 32767, -32768, 32767).astype(np.int16)


# ==========================================================================
# Mastering stages — Chain of Responsibility
# ==========================================================================
@dataclass(frozen=True, slots=True)
class HighPassStage:
    """Remove rumble below ``cutoff`` Hz (windowed-sinc FIR)."""

    cutoff: float
    n_taps: int = 63

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        return DSP.filt_hp(x, self.cutoff, sr, self.n_taps)


@dataclass(frozen=True, slots=True)
class LowPassStage:
    """Tame brightness above ``cutoff`` Hz (windowed-sinc FIR)."""

    cutoff: float
    n_taps: int = 127

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        return DSP.filt_lp(x, self.cutoff, sr, self.n_taps)


@dataclass(frozen=True, slots=True)
class ResonanceBankStage:
    """Housing / plate modal resonances — 'the case answers the impact'.

    This layer is what separates a real board from a raw noise burst: each
    ``(freq, q, gain)`` mode rings at the impact and is mixed back in wet.
    """

    modes: Tuple[Tuple[float, float, float], ...]

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        out = x
        for rf, rq, rgn in self.modes:
            out = out + DSP.filt_resonator(out, rf, rq, sr, gain=rgn)
        return out


@dataclass(frozen=True, slots=True)
class RoomTailStage:
    """Deterministic small-room reverb: early reflections + diffusive tail.

    The early taps (5-32 ms) give clicks a sense of physical space; the dense
    low-passed tail glues them together.  Fixed seed → bit-identical runs.

    ``reverse`` flips the diffuse noise tail in time.  With the *same* seed
    and ``reverse=True`` the two stereo channels get tails with an identical
    magnitude response (time reversal preserves |IR(f)|, so the wet level
    and spectral balance match exactly — independent noise seeds differ by
    ±1-2 dB of spectral gain and pulled the stereo image off centre) while
    the flipped phase decorrelates the tail, which is what gives the reverb
    its width.  The early taps stay at their true (non-reversed) positions
    in both channels: they are the room's walls, not its diffusion.
    """

    amount: float
    seed: int = ROOM_TAIL_SEED
    reverse: bool = False

    _EARLY_TAPS: ClassVar[Tuple[Tuple[float, float], ...]] = (
        (0.0053, 0.50), (0.0109, 0.34), (0.0161, 0.24),
        (0.0217, 0.16), (0.0263, 0.11), (0.0319, 0.08),
    )

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        amt = float(self.amount)
        if amt <= 0.0 or len(x) < 256:
            return x
        n_ir = max(64, int(sr * 0.11))
        rng = np.random.RandomState(self.seed)
        ir = rng.randn(n_ir) * np.exp(-np.arange(n_ir, dtype=np.float64) / (sr * 0.020))
        ir = DSP.filt_lp(ir, 5200, sr)[:n_ir]
        if self.reverse:
            ir = ir[::-1].copy()
        for d_s, g in self._EARLY_TAPS:            # discrete wall reflections
            k = int(d_s * sr)
            if 0 < k < n_ir:
                ir[k] += g * (1.0 if k % 2 == 0 else -0.7)
        ir -= np.mean(ir)
        # v1.0.3: energy-normalise to a FIXED sum(ir^2) — seed-independent
        # tail loudness (the old peak normalisation made it swing ±2 dB,
        # dragging the decorrelated stereo pair off centre) and a room at a
        # deliberate -15 dB instead of the accidental ~-6 dB noise wash
        # (see ROOM_TAIL_IR_ENERGY).
        e = float(np.sqrt(np.sum(ir * ir)))
        if e < 1e-9:
            return x
        ir = ir / e * np.sqrt(ROOM_TAIL_IR_ENERGY)
        wet = _fft_convolve_chunked(np.asarray(x, dtype=np.float64), ir)[:len(x)]
        k = min(0.45, amt)
        out = np.asarray(x, dtype=np.float64) * (1.0 - k) + wet * (k * 0.6)
        return out


@dataclass(frozen=True, slots=True)
class LoudnessStage:
    """ITU-R BS.1770 loudness normalisation to ``target_lufs``."""

    target_lufs: float = LUFS_TARGET

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        return _normalize_to_lufs(np.asarray(x, dtype=np.float64), sr, self.target_lufs)


def _oversample4(x: np.ndarray, sr: int = AUDIO_SAMPLE_RATE,
                 chunk_s: float = 1.0) -> np.ndarray:
    """4x band-limited oversampling of ``x`` (sinc interpolation, chunked).

    The zero-padding happens in the *frequency* domain: the rfft of each
    chunk is placed on a 4x-long spectrum with stride 4 (old bin k lands on
    new bin 4k) and amplitude-scaled by 4, then inverse-transformed at the
    4x length.  That is what makes ``up[4*i] == x[i]`` while the in-between
    sub-samples carry the true band-limited interpolation — zero-padding in
    the time domain would just concatenate silence and ``[::4]`` would
    decimate the signal.  Chunk pads are trimmed in the 4x domain so the
    result is exactly ``4 * len(x)`` long.  Both the true-peak measurement
    and the limiter share this function, keeping their chunk seams
    identical.
    """
    n = len(x)
    if n == 0:
        return np.zeros(0)
    pad = 512
    # chunk + 2*pad -> next power of two keeps the big FFTs fast (the rare
    # track-edge chunks may be arbitrary lengths; numpy handles those too)
    want = max(1 << 13, int(chunk_s * sr)) + 2 * pad
    L = 1 << int(np.ceil(np.log2(want)))
    chunk = L - 2 * pad
    out = np.empty(n * 4, dtype=np.float64)
    pos = 0
    for s in range(0, n, chunk):
        lo, hi = max(0, s - pad), min(n, s + chunk + pad)
        blk = np.asarray(x[lo:hi], dtype=np.float64)
        lb = len(blk)
        N = 4 * lb
        Y = np.zeros(N // 2 + 1, dtype=np.complex128)
        # same duration, 4x the samples -> bin spacing in Hz is unchanged,
        # so the spectrum copies contiguously with 4x amplitude (the
        # scipy.signal.resample convention).  Stride-4 placement would
        # instead wrap the signal around periodically.
        Y[:lb // 2 + 1] = np.fft.rfft(blk) * 4.0
        up = np.fft.irfft(Y, N)
        lo4 = (s - lo) * 4
        seg_len = (min(n, s + chunk) - s) * 4
        out[pos:pos + seg_len] = up[lo4:lo4 + seg_len]
        pos += seg_len
    return out


if _HAS_NUMBA:
    @njit(cache=True)
    def _nb_limiter_gain(g_needed, step):
        """Instant attack / linear release gain smoothing (limiter envelope).

        ``g_needed`` is the raw per-subsample gain the ceiling demands
        (lookahead-preprocessed — its leading edge is already a smooth
        ramp, see :func:`_nb_lookahead_min`, so the instant attack does
        NOT put a corner into the gain curve; the old v1.0.3 draft instead
        rate-limited the attack itself, which on dense over-ceiling
        content lagged the demand by the whole attack time and let the
        true peak overshoot by up to 2 dB).  The gain climbs back toward
        1.0 at ``step`` per sample (release), which keeps the gain
        reduction musical instead of fluttering at transient rate.
        """
        m = len(g_needed)
        g = np.empty(m, dtype=np.float64)
        prev = 1.0
        for i in range(m):
            need = g_needed[i]
            if need < prev:
                prev = need
            else:
                prev = prev + step
                if prev > 1.0:
                    prev = 1.0
            g[i] = prev
        return g

    @njit(cache=True)
    def _nb_lookahead_min(g_needed, la):
        """Sliding-window minimum over a ``la``-subsample lookahead, with a
        raised leading edge.

        A gain reduction must *begin* before the transient it is limiting:
        ``g[i] = min(g_needed[i : i+la])`` makes the envelope engage up to
        ``la`` subsamples early.  Only neighbourhoods of samples that
        actually demand gain reduction are scanned (g_needed == 1.0
        elsewhere), so the cost stays proportional to the transient duty
        cycle instead of the track length.

        The raw window-min has an instant leading edge (1.0 -> dip in one
        sub-sample, ``la`` before the transient) — a corner that, modulated
        onto the signal, splatters and re-overshoots after band-limited
        reconstruction.  The pre-transient segment [s-la, s) is therefore
        rewritten as a linear ramp from 1.0 down to the dip value, so the
        envelope arrives at full reduction exactly when the transient
        starts, without any corner.  Overlapping transients take the
        minimum, so a ramp can never raise an earlier dip.
        """
        m = len(g_needed)
        g = g_needed.copy()
        i = 0
        while i < m:
            if g_needed[i] >= 1.0:
                i += 1
                continue
            s = i
            while i < m and g_needed[i] < 1.0:
                i += 1
            e = i
            lo = s - la
            if lo < 0:
                lo = 0
            hi = e + la
            if hi > m:
                hi = m
            for j in range(lo, hi):
                k1 = j + la
                if k1 > hi:
                    k1 = hi
                mn = 1e30
                for k in range(j, k1):
                    if g_needed[k] < mn:
                        mn = g_needed[k]
                if mn < g[j]:
                    g[j] = mn
            # smooth the leading edge: linear ramp 1.0 -> g[s] across [s-la, s)
            if s > lo:
                g_at_s = g[s] if s < m else 1.0
                span = s - lo
                for j in range(lo, s):
                    frac = (j - lo + 1) / span
                    ramp = 1.0 + (g_at_s - 1.0) * frac
                    if ramp < g[j]:
                        g[j] = ramp
        return g


@dataclass(frozen=True, slots=True)
class TruePeakLimiterStage:
    """Lookahead true-peak limiter (exact ceiling in the 4x domain).

    A scale-only ceiling has to drag the *whole* track down whenever one
    bright transient overshoots — on intersample-peak-heavy presets
    (Cherry MX Blue, Kailh Box Navy, Optical Speed) that cost 7-11 dB of
    loudness.  This stage instead works in the 4x-oversampled domain:
    the raw gain the ceiling demands is computed per sub-sample, looked
    ahead by ``lookahead_ms`` (the reduction starts *before* the peak —
    a real mastering limiter's behaviour, and what keeps extreme-crest
    presets like Nail Taps ASMR off the scale-only backstop), smoothed
    with an instant attack / linear release envelope, applied to the
    oversampled signal, and decimated back.  The reconstruction of the
    limited signal *is* band-limited by construction, so the output's true
    peak never exceeds the ceiling while average loudness stays at the
    target — the classic mastering-limiter behaviour.
    """

    ceiling_dbtp: float = -1.0
    release_ms: float = 60.0
    lookahead_ms: float = 1.5

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        n = len(x)
        if n == 0:
            return x
        ceil_lin = 10.0 ** (self.ceiling_dbtp / 20.0)
        up = _oversample4(x, sr)                      # 4x domain, up[4i] == x[i]
        g_needed = np.minimum(1.0, ceil_lin / np.maximum(np.abs(up), 1e-12))
        la = int(self.lookahead_ms / 1000.0 * 4.0 * sr)
        if la > 0 and _HAS_NUMBA and float(g_needed.min()) < 1.0:
            g_needed = _nb_lookahead_min(g_needed, la)
        step = (1.0 - ceil_lin) / max(1.0, (self.release_ms / 1000.0) * 4.0 * sr)
        if _HAS_NUMBA:
            g = _nb_limiter_gain(g_needed, step)
        else:
            g = g_needed                     # no release smoothing: fine for sparse clicks
        limited = up * g
        return limited[::4][:n].copy()


@dataclass(frozen=True, slots=True)
class TruePeakStage:
    """Scale-only true-peak ceiling (dBTP) — final safety after the limiter.

    The loudness stage makes a dense keystroke track genuinely -14 LUFS, but
    with nothing after it, extreme-crest presets used to land wherever the
    crest put their peaks (up to -0.2 dBFS on IBM Model M / Typewriter) —
    over YouTube's -1.5 dBTP recommendation and into intersample-clip
    territory on consumer DACs.  This stage measures the band-limited true
    peak at 4x oversampling and scales the *whole track down* when needed;
    it never boosts, so loudness is preserved whenever headroom exists.
    """

    ceiling_dbtp: float = -1.05

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        ceil_lin = 10.0 ** (self.ceiling_dbtp / 20.0)
        tp = float(np.max(_oversample4(np.asarray(x, dtype=np.float64), sr), initial=0.0)) if len(x) else 0.0
        if tp > ceil_lin > 0:
            x = x * (ceil_lin / tp)
        return x


def _measure_lufs(x: np.ndarray, sr: int) -> float:
    """Gated integrated loudness with the canonical K-weight kernels."""
    if _HAS_NUMBA:
        return _nb_gated_loudness(_nb_k_weight(np.asarray(x, dtype=np.float64), sr))
    return _lufs_numpy(np.asarray(x, dtype=np.float64), sr)


def _loudness_gain(x: np.ndarray, sr: int,
                   target_lufs: float = LUFS_TARGET) -> float:
    """Scalar gain that would pull ``x`` to ``target_lufs`` (1.0 on silence)."""
    cl = _measure_lufs(x, sr)
    if not np.isfinite(cl) or cl <= -70.0:
        return 1.0
    return 10.0 ** ((target_lufs - cl) / 20.0)


def _finalize_loudness(x: np.ndarray, sr: int) -> np.ndarray:
    """Iterated loudness anchor + true-peak limiting (mono/stereo shared).

    One anchor pass lands a heavy-crest track BELOW target: the loudness
    stage measures the pre-limiter signal, the limiter then shaves the
    peaks and with them ~1 dB of integrated loudness.  Mastering engineers
    iterate gain-then-limit until the *limited* signal measures on target;
    here the loop converges in <= ``LOUDNESS_PASSES`` passes (measured gap
    < 0.3 LU stops early).  The scale-only backstop runs last and, with
    the limiter ceiling at the same level, only trims reconstruction
    overshoot.
    """
    lim = TruePeakLimiterStage(ceiling_dbtp=LIMITER_CEILING_DBTP,
                               release_ms=60.0, lookahead_ms=1.5)
    for _ in range(LOUDNESS_PASSES):
        g = _loudness_gain(x, sr)
        if g == 1.0:
            break
        x = x * g
        x = lim.process(x, sr)
        # convergence: the limited signal now measures within 0.3 LU?
        cl = _measure_lufs(x, sr)
        if np.isfinite(cl) and abs(cl - LUFS_TARGET) < 0.3:
            break
    return TruePeakStage(ceiling_dbtp=TP_BACKSTOP_DBTP).process(x, sr)


def _finalize_loudness_pair(l: np.ndarray, r: np.ndarray,
                            sr: int) -> Tuple[np.ndarray, np.ndarray]:
    """Stereo variant of :func:`_finalize_loudness`.

    The loudness gain is measured on the mono sum and applied to BOTH
    channels, so the stereo image cannot drift; limiting runs per channel
    (peak domain), the backstop per channel, and a final joint scale keeps
    the pair peak-safe exactly like the old code path.
    """
    lim = TruePeakLimiterStage(ceiling_dbtp=LIMITER_CEILING_DBTP,
                               release_ms=60.0, lookahead_ms=1.5)
    backstop = TruePeakStage(ceiling_dbtp=TP_BACKSTOP_DBTP)
    for _ in range(LOUDNESS_PASSES):
        g = _loudness_gain((l + r) / 1.4142135623730951, sr)
        if g == 1.0:
            break
        l = lim.process(l * g, sr)
        r = lim.process(r * g, sr)
        cl = _measure_lufs((l + r) / 1.4142135623730951, sr)
        if np.isfinite(cl) and abs(cl - LUFS_TARGET) < 0.3:
            break
    l = backstop.process(l, sr)
    r = backstop.process(r, sr)
    mx = max(float(np.max(np.abs(l))) if len(l) else 0.0,
             float(np.max(np.abs(r))) if len(r) else 0.0)
    if mx > 1.0:
        l = l * (MASTER_CEILING / mx)
        r = r * (MASTER_CEILING / mx)
    return l, r


@dataclass(frozen=True, slots=True)
class SoftClipStage:
    """Gentle mastering clipper (classic 'clipper before the limiter').

    Everything below ``knee_dbfs`` passes untouched; the top
    ``ceil_dbfs - knee_dbfs`` is curved down by a C1-continuous cubic
    (value *and* slope match at both ends), and nothing above the ceiling
    survives.  The knee is deliberately narrow (~2 dB): the point is to
    shave only the very top of the highest keystroke peaks — extreme-crest
    presets (IBM Model M's 4.4/5.9 kHz contact pings) gain a couple of dB
    of loudness headroom without any audible flat-topping of the clicks.
    """

    knee_dbfs: float = -2.5
    ceil_dbfs: float = -0.6

    @staticmethod
    def _knee_curve(u: np.ndarray) -> np.ndarray:
        # f(0)=0, f(1)=1, f'(0)=1, f'(1)=0  ->  f(u) = u + u^2 - u^3
        return u + u * u - u * u * u

    def process(self, x: np.ndarray, sr: int) -> np.ndarray:
        knee = 10.0 ** (self.knee_dbfs / 20.0)
        ceil = 10.0 ** (self.ceil_dbfs / 20.0)
        a = np.abs(x)
        if a.size == 0 or float(np.max(a)) <= knee:
            return x
        out = np.array(x, dtype=np.float64, copy=True)
        zone = (a > knee) & (a < ceil)
        if zone.any():
            u = (a[zone] - knee) / (ceil - knee)
            out[zone] = np.sign(x[zone]) * (knee + (ceil - knee) * self._knee_curve(u))
        over = a >= ceil
        if over.any():
            out[over] = np.sign(x[over]) * ceil
        return out


def run_stages(x: np.ndarray, sr: int, stages: Sequence[AudioStage]) -> np.ndarray:
    """Push ``x`` through a stage chain (Chain of Responsibility runner)."""
    for stage in stages:
        x = stage.process(x, sr)
    return x


# ==========================================================================
# Value objects — one synth layer (VoiceSpec) and one whole click (SoundSpec)
# ==========================================================================
@dataclass
class VoiceSpec:
    """One synthesis layer of a key click.

    ``osc`` selects a generator from ``_WAVE_GENERATORS`` (sine / fm / saw /
    triangle / noise_white / noise_pink / noise_brown / modal); ``filt``
    selects one from ``_FILTERS`` (none / lp / hp / bp / resonator).
    A positive ``sweep`` makes tonal layers glide exponentially from ``freq``
    toward ``freq * sweep`` — the physical 'thump' of a slider bottoming out.
    """

    osc: str = "sine"; freq: float = 440.0; fm_ratio: float = 1.0; fm_index: float = 0.0
    attack: float = 0.001; decay_rate: float = 30.0; attack_curve: float = 2.0
    filt: str = "none"; f_cutoff: float = 8000.0; f_high: float = 12000.0; f_q: float = 1.0
    drive: float = 0.0; gain: float = 0.5; delay: float = 0.0
    modes: Optional[List[Tuple[float, float, float]]] = None; inharmonicity: float = 0.0
    sweep: float = 0.0    # exponential pitch glide: end freq = freq * sweep (sine only; 0/1 = off)


@dataclass
class SoundSpec:
    """A complete key sound: layer stack + housing resonances + shaping.

    ``variation`` (0..1) controls how much organic humanisation the engine
    applies per rendered variant (level / attack / brightness / micro-delay);
    the default gives every preset a natural, hand-played feel while staying
    fully deterministic per seed.
    """

    duration: float = 0.12
    layers: List[VoiceSpec] = field(default_factory=list)
    # optional per-pool overrides (Enter / Space keys get their own timbre)
    enter_spec: Optional["SoundSpec"] = None
    space_spec: Optional["SoundSpec"] = None
    # housing / plate modal resonances applied to the summed mix:
    # list of (freq_hz, q, wet_gain) — this is what turns a click into a
    # "thock" (500-900 Hz), a "clack" (1.5-3 kHz) or a marble "tick"
    resonance: Optional[List[Tuple[float, float, float]]] = None
    post_hp: float = 0.0   # final high-pass shaping (Hz; 0 = off)
    post_lp: float = 0.0   # final low-pass shaping (Hz; 0 = off)
    variation: float = DEFAULT_VARIATION


class SoundSpecBuilder:
    """Builder for :class:`SoundSpec` — fluent, validated composition.

    Example::

        spec = (SoundSpecBuilder(duration=0.13)
                .layer("noise_white", attack=0.0001, decay_rate=420.0,
                       filt="bp", f_cutoff=2800, f_high=7000, gain=0.42)
                .layer("sine", freq=130, sweep=0.55, gain=0.5, delay=0.002)
                .resonance((820.0, 9.0, 0.30))
                .post(lp=8500.0)
                .build())
    """

    __slots__ = ("_duration", "_layers", "_enter", "_space",
                 "_resonance", "_post_hp", "_post_lp", "_variation")

    def __init__(self, duration: float = 0.12,
                 variation: float = DEFAULT_VARIATION) -> None:
        self._duration = float(duration)
        self._variation = float(variation)
        self._layers: List[VoiceSpec] = []
        self._enter: Optional[SoundSpec] = None
        self._space: Optional[SoundSpec] = None
        self._resonance: List[Tuple[float, float, float]] = []
        self._post_hp = 0.0
        self._post_lp = 0.0

    def layer(self, osc: str = "sine", **kwargs) -> "SoundSpecBuilder":
        """Append one :class:`VoiceSpec` layer (any VoiceSpec field as kwarg)."""
        self._layers.append(VoiceSpec(osc=osc, **kwargs))
        return self

    def enter(self, spec: SoundSpec) -> "SoundSpecBuilder":
        self._enter = spec
        return self

    def space(self, spec: SoundSpec) -> "SoundSpecBuilder":
        self._space = spec
        return self

    def resonance(self, *modes: Tuple[float, float, float]) -> "SoundSpecBuilder":
        self._resonance.extend(modes)
        return self

    def post(self, hp: float = 0.0, lp: float = 0.0) -> "SoundSpecBuilder":
        self._post_hp, self._post_lp = float(hp), float(lp)
        return self

    def build(self) -> SoundSpec:
        return SoundSpec(duration=self._duration, layers=self._layers,
                         enter_spec=self._enter, space_spec=self._space,
                         resonance=self._resonance or None,
                         post_hp=self._post_hp, post_lp=self._post_lp,
                         variation=self._variation)


# ==========================================================================
# Presets — declarative data: every click is built from the physical event
# chain of a real keypress (cap-contact snap → travel → delayed bottom-out
# → housing/plate modes → sub-bass weight, + spring ping / return tick where
# the switch has one)
# ==========================================================================
MODULAR_SOUND_PRESETS: Dict[str, SoundSpec] = {
    "Mechanical": SoundSpec(duration=0.13, layers=[
        VoiceSpec(osc="noise_white", attack=0.0001, decay_rate=420.0, filt="bp", f_cutoff=2800, f_high=7000, drive=1.4, gain=0.42),
        VoiceSpec(osc="fm", freq=900, fm_ratio=2.4, fm_index=0.8, attack=0.0004, decay_rate=90.0, filt="lp", f_cutoff=3000, gain=0.28, delay=0.0025),
        VoiceSpec(osc="sine", freq=130, sweep=0.55, attack=0.0015, decay_rate=55.0, filt="lp", f_cutoff=500, gain=0.5, delay=0.002)
    ], resonance=[(820.0, 9.0, 0.30), (1350.0, 12.0, 0.18)], post_lp=8500.0),
    "Cherry MX Red": SoundSpec(duration=0.11, layers=[
        # balanced for small speakers: contact noise + 640/1480 Hz housing
        # body carry the identity; the sub layer sits at 95 Hz (not 68) so
        # the click still reads as a keypress on laptop/phone playback
        VoiceSpec(osc="noise_white", attack=0.0004, decay_rate=300.0, filt="bp", f_cutoff=1800, f_high=4500, gain=0.34),
        VoiceSpec(osc="sine", freq=130, sweep=0.6, attack=0.002, decay_rate=45.0, filt="lp", f_cutoff=450, gain=0.5),
        VoiceSpec(osc="sine", freq=95, attack=0.003, decay_rate=28.0, filt="lp", f_cutoff=240, gain=0.38, delay=0.0015)
    ], resonance=[(640.0, 8.0, 0.22), (1480.0, 10.0, 0.12)], post_lp=7000.0),
    "IBM Model M": SoundSpec(duration=0.28, layers=[
        VoiceSpec(osc="sine", freq=4400, attack=0.0002, decay_rate=22.0, filt="lp", f_cutoff=9000, gain=0.35),
        VoiceSpec(osc="sine", freq=5900, attack=0.0003, decay_rate=18.0, filt="lp", f_cutoff=10000, gain=0.15),
        VoiceSpec(osc="noise_white", attack=0.0003, decay_rate=260.0, filt="bp", f_cutoff=1500, f_high=5000, drive=1.3, gain=0.38, delay=0.0005),
        VoiceSpec(osc="sine", freq=170, sweep=0.6, attack=0.001, decay_rate=40.0, filt="lp", f_cutoff=600, gain=0.4, delay=0.003),
        VoiceSpec(osc="sine", freq=3600, attack=0.0005, decay_rate=60.0, filt="lp", f_cutoff=6500, gain=0.10, delay=0.055)
    ], resonance=[(2400.0, 14.0, 0.20)], post_lp=11000.0),
    "ASMR Deep Thock": SoundSpec(duration=0.17, layers=[
        VoiceSpec(osc="sine", freq=92, sweep=0.5, attack=0.004, decay_rate=30.0, filt="lp", f_cutoff=300, gain=0.85),
        VoiceSpec(osc="sine", freq=620, attack=0.002, decay_rate=35.0, filt="lp", f_cutoff=1200, gain=0.28, delay=0.001),
        VoiceSpec(osc="noise_pink", attack=0.006, decay_rate=60.0, filt="lp", f_cutoff=800, gain=0.3)
    ], resonance=[(540.0, 10.0, 0.25)], post_lp=2600.0),
    "Studio ASMR": SoundSpec(duration=0.13, layers=[
        VoiceSpec(osc="noise_white", attack=0.0003, decay_rate=320.0, filt="bp", f_cutoff=2200, f_high=5200, gain=0.2),
        VoiceSpec(osc="sine", freq=480, attack=0.0012, decay_rate=55.0, filt="lp", f_cutoff=1600, gain=0.35, delay=0.002),
        VoiceSpec(osc="sine", freq=130, sweep=0.65, attack=0.002, decay_rate=50.0, filt="lp", f_cutoff=500, gain=0.5, delay=0.002)
    ], resonance=[(760.0, 9.0, 0.22)], post_lp=8000.0),
    "Typewriter": SoundSpec(duration=0.20, layers=[
        VoiceSpec(osc="noise_white", attack=0.0004, decay_rate=140.0, filt="bp", f_cutoff=900, f_high=3800, drive=1.6, gain=0.5),
        VoiceSpec(osc="sine", freq=190, sweep=0.5, attack=0.001, decay_rate=38.0, filt="lp", f_cutoff=800, gain=0.55, delay=0.002),
        VoiceSpec(osc="sine", freq=2350, attack=0.001, decay_rate=9.0, filt="lp", f_cutoff=4000, gain=0.10)
    ], post_lp=9000.0,
        enter_spec=SoundSpec(duration=0.85, layers=[
            VoiceSpec(osc="noise_white", attack=0.0004, decay_rate=140.0, filt="bp", f_cutoff=900, f_high=3800, drive=1.6, gain=0.4),
            VoiceSpec(osc="modal", modes=[(2350.0, 3.2, 1.0), (3520.0, 2.0, 0.5), (4700.0, 1.4, 0.3)],
                      attack=0.0008, decay_rate=6.0, filt="lp", f_cutoff=9000, gain=0.5)
        ], post_lp=11000.0)),
    "Cyberpunk Hacker": SoundSpec(duration=0.12, layers=[
        VoiceSpec(osc="fm", freq=640, fm_ratio=3.2, fm_index=2.2, attack=0.0006, decay_rate=55.0, filt="lp", f_cutoff=5000, gain=0.42),
        VoiceSpec(osc="noise_white", attack=0.0002, decay_rate=500.0, filt="bp", f_cutoff=4000, f_high=9500, gain=0.18),
        VoiceSpec(osc="sine", freq=75, sweep=0.5, attack=0.002, decay_rate=40.0, filt="lp", f_cutoff=250, gain=0.55, delay=0.001)
    ], resonance=[(1150.0, 16.0, 0.15)], post_lp=9000.0),
    "Heavenly ASMR": SoundSpec(duration=0.45, layers=[
        VoiceSpec(osc="modal", modes=[(1250.0, 5.0, 1.0), (2500.0, 3.0, 0.45), (3750.0, 2.2, 0.22), (5250.0, 1.6, 0.12)],
                  inharmonicity=0.0006, attack=0.002, decay_rate=8.0, filt="lp", f_cutoff=12000, gain=0.5),
        VoiceSpec(osc="sine", freq=210, sweep=0.7, attack=0.003, decay_rate=24.0, filt="lp", f_cutoff=500, gain=0.35, delay=0.001)
    ], post_lp=12000.0),
    "Lo-Fi Chill": SoundSpec(duration=0.16, layers=[
        VoiceSpec(osc="sine", freq=140, sweep=0.55, attack=0.004, decay_rate=32.0, filt="lp", f_cutoff=420, gain=0.65),
        VoiceSpec(osc="noise_pink", attack=0.008, decay_rate=26.0, filt="lp", f_cutoff=700, gain=0.3, delay=0.002),
        VoiceSpec(osc="sine", freq=480, attack=0.002, decay_rate=40.0, filt="lp", f_cutoff=900, gain=0.18, delay=0.001)
    ], post_lp=3200.0),
    "Crystal Chime": SoundSpec(duration=0.45, layers=[
        VoiceSpec(osc="modal", modes=[(1650.0, 6.5, 1.0), (3450.0, 4.5, 0.5), (5400.0, 3.0, 0.28), (7600.0, 2.2, 0.18), (10200.0, 1.5, 0.1)],
                  inharmonicity=0.0004, attack=0.0002, decay_rate=7.0, filt="lp", f_cutoff=15000, gain=0.5),
        VoiceSpec(osc="sine", freq=240, attack=0.002, decay_rate=30.0, filt="lp", f_cutoff=400, gain=0.15)
    ], post_lp=15000.0),
    # ── professional line
    "Creamy Thock": SoundSpec(duration=0.16, layers=[
        VoiceSpec(osc="noise_white", attack=0.0035, decay_rate=190.0, filt="lp", f_cutoff=1600, gain=0.4),
        VoiceSpec(osc="sine", freq=150, sweep=0.45, attack=0.003, decay_rate=42.0, filt="lp", f_cutoff=380, gain=0.75, delay=0.002),
        VoiceSpec(osc="sine", freq=82, attack=0.004, decay_rate=26.0, filt="lp", f_cutoff=200, gain=0.5, delay=0.003)
    ], resonance=[(720.0, 8.0, 0.24)], post_lp=3200.0),
    "Marble Clack": SoundSpec(duration=0.11, layers=[
        VoiceSpec(osc="noise_white", attack=0.0001, decay_rate=600.0, filt="bp", f_cutoff=3500, f_high=9000, drive=1.2, gain=0.5),
        VoiceSpec(osc="sine", freq=950, attack=0.0008, decay_rate=90.0, filt="lp", f_cutoff=2600, gain=0.35, delay=0.0015),
        VoiceSpec(osc="sine", freq=145, sweep=0.6, attack=0.0015, decay_rate=70.0, filt="lp", f_cutoff=600, gain=0.4, delay=0.0015)
    ], resonance=[(1900.0, 13.0, 0.30), (2900.0, 15.0, 0.20)], post_lp=12000.0),
    "Cherry MX Blue": SoundSpec(duration=0.14, layers=[
        # click tempered + body raised: an all-HF spike has a ~19 dB
        # true-peak-to-loudness distance, which both under-translates on
        # small speakers and costs 5 dB of loudness at the TP ceiling
        VoiceSpec(osc="noise_white", attack=0.0001, decay_rate=900.0, filt="bp", f_cutoff=5000, f_high=9500, gain=0.32),
        VoiceSpec(osc="sine", freq=3350, attack=0.0004, decay_rate=30.0, filt="lp", f_cutoff=8000, gain=0.18, delay=0.001),
        VoiceSpec(osc="noise_white", attack=0.0003, decay_rate=320.0, filt="bp", f_cutoff=1500, f_high=4200, gain=0.30, delay=0.0022),
        VoiceSpec(osc="sine", freq=125, sweep=0.55, attack=0.002, decay_rate=48.0, filt="lp", f_cutoff=480, gain=0.55, delay=0.0025)
    ], resonance=[(1000.0, 11.0, 0.20)], post_lp=10000.0),
    "Holy Panda": SoundSpec(duration=0.15, layers=[
        VoiceSpec(osc="sine", freq=640, sweep=0.5, attack=0.0012, decay_rate=70.0, filt="lp", f_cutoff=1500, gain=0.5, delay=0.0018),
        VoiceSpec(osc="noise_white", attack=0.0003, decay_rate=350.0, filt="bp", f_cutoff=2200, f_high=5200, gain=0.22),
        VoiceSpec(osc="sine", freq=135, sweep=0.6, attack=0.003, decay_rate=45.0, filt="lp", f_cutoff=450, gain=0.55, delay=0.002)
    ], resonance=[(860.0, 9.0, 0.25)], post_lp=6000.0),
    "Topre Plonk": SoundSpec(duration=0.17, layers=[
        VoiceSpec(osc="sine", freq=320, sweep=0.35, attack=0.0018, decay_rate=34.0, filt="lp", f_cutoff=900, gain=0.6, delay=0.001),
        VoiceSpec(osc="sine", freq=4100, attack=0.0004, decay_rate=26.0, filt="lp", f_cutoff=8000, gain=0.10, delay=0.004),
        VoiceSpec(osc="sine", freq=105, sweep=0.6, attack=0.003, decay_rate=36.0, filt="lp", f_cutoff=350, gain=0.5, delay=0.002),
        VoiceSpec(osc="sine", freq=3300, attack=0.0005, decay_rate=40.0, filt="lp", f_cutoff=6000, gain=0.08, delay=0.05)
    ], resonance=[(620.0, 8.0, 0.20)], post_lp=5000.0),
    "Silent Velvet": SoundSpec(duration=0.13, layers=[
        VoiceSpec(osc="noise_pink", attack=0.005, decay_rate=120.0, filt="lp", f_cutoff=950, gain=0.5),
        VoiceSpec(osc="sine", freq=110, sweep=0.55, attack=0.004, decay_rate=30.0, filt="lp", f_cutoff=300, gain=0.6, delay=0.002)
    ], resonance=[(480.0, 7.0, 0.18)], post_lp=1800.0),
    "Wooden Desk Thock": SoundSpec(duration=0.16, layers=[
        VoiceSpec(osc="noise_white", attack=0.0008, decay_rate=200.0, filt="bp", f_cutoff=900, f_high=2600, drive=1.2, gain=0.35),
        VoiceSpec(osc="sine", freq=260, sweep=0.5, attack=0.002, decay_rate=40.0, filt="lp", f_cutoff=700, gain=0.6, delay=0.0018),
        VoiceSpec(osc="sine", freq=98, attack=0.003, decay_rate=26.0, filt="lp", f_cutoff=280, gain=0.5, delay=0.0025)
    ], resonance=[(420.0, 9.0, 0.28), (980.0, 11.0, 0.20)], post_lp=4200.0),
    "Ink Clack": SoundSpec(duration=0.13, layers=[
        VoiceSpec(osc="noise_white", attack=0.0002, decay_rate=420.0, filt="bp", f_cutoff=2800, f_high=7500, drive=1.3, gain=0.46),
        VoiceSpec(osc="sine", freq=1100, sweep=0.55, attack=0.001, decay_rate=60.0, filt="lp", f_cutoff=2400, gain=0.38, delay=0.0016),
        VoiceSpec(osc="sine", freq=130, sweep=0.6, attack=0.0025, decay_rate=42.0, filt="lp", f_cutoff=480, gain=0.42, delay=0.002)
    ], resonance=[(1250.0, 11.0, 0.30), (2100.0, 13.0, 0.22)], post_lp=11000.0),
    # ── ASMR expansion: soft-touch variants spread across the spectrum
    "Pillow Fort ASMR": SoundSpec(duration=0.16, layers=[
        VoiceSpec(osc="noise_pink", attack=0.009, decay_rate=90.0, filt="lp", f_cutoff=650, gain=0.55),
        VoiceSpec(osc="sine", freq=84, sweep=0.5, attack=0.006, decay_rate=24.0, filt="lp", f_cutoff=240, gain=0.6, delay=0.002)
    ], resonance=[(300.0, 6.0, 0.15)], post_lp=950.0),
    "Fuzzy Felt ASMR": SoundSpec(duration=0.14, layers=[
        VoiceSpec(osc="noise_pink", attack=0.006, decay_rate=130.0, filt="bp", f_cutoff=380, f_high=1150, gain=0.55),
        VoiceSpec(osc="sine", freq=165, sweep=0.55, attack=0.005, decay_rate=38.0, filt="lp", f_cutoff=400, gain=0.55, delay=0.002)
    ], resonance=[(520.0, 7.0, 0.18)], post_lp=1900.0),
    "Whisper Breeze": SoundSpec(duration=0.15, layers=[
        VoiceSpec(osc="noise_pink", attack=0.008, decay_rate=70.0, filt="bp", f_cutoff=750, f_high=2600, gain=0.6),
        VoiceSpec(osc="sine", freq=210, attack=0.006, decay_rate=30.0, filt="lp", f_cutoff=500, gain=0.18, delay=0.003)
    ], post_lp=3400.0),
    "Bamboo Tap": SoundSpec(duration=0.13, layers=[
        VoiceSpec(osc="modal", modes=[(470.0, 22.0, 1.0), (940.0, 26.0, 0.45), (1490.0, 30.0, 0.22)],
                  attack=0.0008, decay_rate=60.0, filt="lp", f_cutoff=2400, gain=0.5),
        VoiceSpec(osc="noise_white", attack=0.0004, decay_rate=300.0, filt="bp", f_cutoff=1000, f_high=2400, gain=0.22, delay=0.0005),
        VoiceSpec(osc="sine", freq=120, sweep=0.6, attack=0.003, decay_rate=40.0, filt="lp", f_cutoff=300, gain=0.3, delay=0.0015)
    ], post_lp=4200.0),
    "Rain Drop Taps": SoundSpec(duration=0.19, layers=[
        VoiceSpec(osc="sine", freq=1350, sweep=0.55, attack=0.0008, decay_rate=26.0, filt="lp", f_cutoff=2600, gain=0.5),
        VoiceSpec(osc="sine", freq=640, sweep=0.6, attack=0.0012, decay_rate=24.0, filt="lp", f_cutoff=1300, gain=0.3, delay=0.004),
        VoiceSpec(osc="noise_white", attack=0.0004, decay_rate=350.0, filt="bp", f_cutoff=2400, f_high=5200, gain=0.16)
    ], resonance=[(1150.0, 10.0, 0.22)], post_lp=6500.0),
    "Glass Taps ASMR": SoundSpec(duration=0.30, layers=[
        VoiceSpec(osc="modal", modes=[(2350.0, 16.0, 1.0), (4800.0, 12.0, 0.4), (7150.0, 9.0, 0.18)],
                  inharmonicity=0.0005, attack=0.0005, decay_rate=15.0, filt="lp", f_cutoff=12000, gain=0.45),
        VoiceSpec(osc="noise_white", attack=0.0002, decay_rate=500.0, filt="bp", f_cutoff=5200, f_high=9000, gain=0.12),
        VoiceSpec(osc="sine", freq=310, attack=0.002, decay_rate=40.0, filt="lp", f_cutoff=700, gain=0.1)
    ], post_lp=13000.0),
    # ── professional expansion (v1.0): more real-switch models ────────────
    "Gateron Ink Linear": SoundSpec(duration=0.15, layers=[
        VoiceSpec(osc="noise_white", attack=0.0028, decay_rate=170.0, filt="lp", f_cutoff=1400, gain=0.38),
        VoiceSpec(osc="sine", freq=138, sweep=0.5, attack=0.0025, decay_rate=38.0, filt="lp", f_cutoff=400, gain=0.78, delay=0.002),
        VoiceSpec(osc="sine", freq=74, attack=0.004, decay_rate=22.0, filt="lp", f_cutoff=180, gain=0.52, delay=0.003),
        VoiceSpec(osc="sine", freq=2450, attack=0.0008, decay_rate=20.0, filt="lp", f_cutoff=5200, gain=0.07, delay=0.045)
    ], resonance=[(610.0, 8.0, 0.22), (980.0, 10.0, 0.14)], post_lp=3000.0),
    "Cherry MX Brown": SoundSpec(duration=0.12, layers=[
        VoiceSpec(osc="noise_white", attack=0.0006, decay_rate=260.0, filt="bp", f_cutoff=1400, f_high=3800, drive=1.1, gain=0.30),
        VoiceSpec(osc="noise_pink", attack=0.0035, decay_rate=95.0, filt="bp", f_cutoff=600, f_high=1700, gain=0.30, delay=0.001),
        VoiceSpec(osc="sine", freq=122, sweep=0.55, attack=0.0018, decay_rate=46.0, filt="lp", f_cutoff=460, gain=0.55, delay=0.002),
        VoiceSpec(osc="sine", freq=62, attack=0.003, decay_rate=26.0, filt="lp", f_cutoff=170, gain=0.40, delay=0.002)
    ], resonance=[(700.0, 8.0, 0.20)], post_lp=6000.0),
    "Kailh Box Navy": SoundSpec(duration=0.16, layers=[
        VoiceSpec(osc="sine", freq=2700, attack=0.0002, decay_rate=34.0, filt="lp", f_cutoff=7000, gain=0.42),
        VoiceSpec(osc="noise_white", attack=0.0002, decay_rate=480.0, filt="bp", f_cutoff=2400, f_high=7600, drive=1.4, gain=0.40, delay=0.0012),
        VoiceSpec(osc="sine", freq=150, sweep=0.5, attack=0.002, decay_rate=52.0, filt="lp", f_cutoff=520, gain=0.55, delay=0.0024),
        VoiceSpec(osc="sine", freq=3050, attack=0.0006, decay_rate=26.0, filt="lp", f_cutoff=7600, gain=0.10, delay=0.05)
    ], resonance=[(1150.0, 12.0, 0.24)], post_lp=10000.0),
    "Optical Speed": SoundSpec(duration=0.09, layers=[
        VoiceSpec(osc="noise_white", attack=0.0003, decay_rate=420.0, filt="bp", f_cutoff=2400, f_high=6200, gain=0.22),
        VoiceSpec(osc="sine", freq=180, sweep=0.6, attack=0.0012, decay_rate=70.0, filt="lp", f_cutoff=620, gain=0.55, delay=0.0012),
        VoiceSpec(osc="sine", freq=3200, attack=0.0004, decay_rate=34.0, filt="lp", f_cutoff=8000, gain=0.06, delay=0.03)
    ], post_lp=8000.0),
    "Alu Plate Clack": SoundSpec(duration=0.12, layers=[
        VoiceSpec(osc="noise_white", attack=0.0002, decay_rate=520.0, filt="bp", f_cutoff=3000, f_high=8200, drive=1.25, gain=0.42),
        VoiceSpec(osc="modal", modes=[(1980.0, 18.0, 1.0), (3120.0, 14.0, 0.5), (4650.0, 11.0, 0.26)],
                  inharmonicity=0.0008, attack=0.0003, decay_rate=26.0, filt="lp", f_cutoff=11000, gain=0.30),
        VoiceSpec(osc="sine", freq=160, sweep=0.55, attack=0.0016, decay_rate=58.0, filt="lp", f_cutoff=560, gain=0.45, delay=0.0016)
    ], resonance=[(2050.0, 15.0, 0.32), (3400.0, 16.0, 0.20)], post_lp=12500.0),
    # ── ASMR wave 2: tactile object foley ─────────────────────────────
    "Nail Taps ASMR": SoundSpec(duration=0.12, layers=[
        # same principle: a touch of low-mid body under the nail-click modal
        VoiceSpec(osc="modal", modes=[(3050.0, 14.0, 1.0), (5300.0, 12.0, 0.35), (7900.0, 9.0, 0.15)],
                  inharmonicity=0.0007, attack=0.0004, decay_rate=30.0, filt="lp", f_cutoff=12000, gain=0.36),
        VoiceSpec(osc="sine", freq=380, sweep=0.6, attack=0.001, decay_rate=40.0, filt="lp", f_cutoff=900, gain=0.22, delay=0.0008),
        VoiceSpec(osc="noise_white", attack=0.0003, decay_rate=260.0, filt="bp", f_cutoff=3400, f_high=7800, gain=0.12),
        VoiceSpec(osc="sine", freq=290, attack=0.0022, decay_rate=44.0, filt="lp", f_cutoff=760, gain=0.16, delay=0.001)
    ], post_lp=13000.0),
    "Bubble Wrap Pop": SoundSpec(duration=0.14, layers=[
        VoiceSpec(osc="sine", freq=1150, sweep=0.35, attack=0.0003, decay_rate=75.0, filt="lp", f_cutoff=3000, gain=0.55),
        VoiceSpec(osc="noise_white", attack=0.0002, decay_rate=300.0, filt="bp", f_cutoff=1200, f_high=4600, drive=1.2, gain=0.34),
        VoiceSpec(osc="sine", freq=200, sweep=0.5, attack=0.002, decay_rate=30.0, filt="lp", f_cutoff=420, gain=0.18, delay=0.001)
    ], resonance=[(1350.0, 10.0, 0.18)], post_lp=8000.0),
    "Ping Pong Bounce": SoundSpec(duration=0.16, layers=[
        VoiceSpec(osc="sine", freq=980, sweep=0.4, attack=0.0005, decay_rate=60.0, filt="lp", f_cutoff=2400, gain=0.50),
        VoiceSpec(osc="modal", modes=[(1750.0, 14.0, 0.8), (3480.0, 9.0, 0.3)],
                  inharmonicity=0.0004, attack=0.0004, decay_rate=22.0, filt="lp", f_cutoff=8000, gain=0.22),
        VoiceSpec(osc="noise_pink", attack=0.0015, decay_rate=90.0, filt="lp", f_cutoff=1200, gain=0.12)
    ], resonance=[(900.0, 9.0, 0.20)], post_lp=7000.0),
}


# ==========================================================================
# ModularSoundEngine — Factory Method: SoundSpec (+ seed) -> int16 variant
# ==========================================================================
# Wave-shape generators share one signature: (spec, n, sr, rng) -> float64.
# Adding a new oscillator = one function + one table entry (Open/Closed).
def _w_sine(spec: VoiceSpec, n: int, sr: int, rng) -> np.ndarray:
    if spec.sweep and 0.02 < spec.sweep < 0.999:
        # exponential pitch glide freq -> freq*sweep (phase-integrated,
        # no discontinuity): the physical "thump" of the slider bottoming out
        t = np.arange(n, dtype=np.float64) / sr
        dur = max(1e-6, n / sr)
        f_t = spec.freq * (spec.sweep ** (t / dur))
        return np.sin(2.0 * np.pi * np.cumsum(f_t) / sr)
    return DSP.osc_sine(spec.freq, n, sr)


def _w_fm(spec: VoiceSpec, n: int, sr: int, rng) -> np.ndarray:
    return DSP.osc_fm(spec.freq, spec.fm_ratio, spec.fm_index, n, sr)


def _w_saw(spec: VoiceSpec, n: int, sr: int, rng) -> np.ndarray:
    return DSP.osc_saw(spec.freq, n, sr)


def _w_triangle(spec: VoiceSpec, n: int, sr: int, rng) -> np.ndarray:
    return DSP.osc_triangle(spec.freq, n, sr)


def _w_noise_white(spec: VoiceSpec, n: int, sr: int, rng) -> np.ndarray:
    return DSP.noise_white(n, rng)


def _w_noise_pink(spec: VoiceSpec, n: int, sr: int, rng) -> np.ndarray:
    return DSP.noise_pink(n, rng)


def _w_noise_brown(spec: VoiceSpec, n: int, sr: int, rng) -> np.ndarray:
    return DSP.noise_brown(n, rng)


def _w_modal(spec: VoiceSpec, n: int, sr: int, rng) -> np.ndarray:
    if not spec.modes:
        return np.zeros(n, dtype=np.float64)
    return DSP.modal(spec.modes, n, sr, spec.inharmonicity)


_WAVE_GENERATORS: Dict[str, Callable[[VoiceSpec, int, int, "np.random.RandomState"], np.ndarray]] = {
    "sine": _w_sine,
    "fm": _w_fm,
    "saw": _w_saw,
    "triangle": _w_triangle,
    "noise_white": _w_noise_white,
    "noise_pink": _w_noise_pink,
    "noise_brown": _w_noise_brown,
    "modal": _w_modal,
}

# layers whose pitch tracks the per-variant detune factor
_TONAL_WAVES: Final[Tuple[str, ...]] = ("sine", "fm", "modal")

# per-layer shaping filters share one signature: (sig, spec, sr) -> float64
_FILTERS: Dict[str, Callable[[np.ndarray, VoiceSpec, int], np.ndarray]] = {
    "lp": lambda sig, sp, sr: DSP.filt_lp(sig, sp.f_cutoff, sr),
    "hp": lambda sig, sp, sr: DSP.filt_hp(sig, sp.f_cutoff, sr),
    "bp": lambda sig, sp, sr: DSP.filt_bp(sig, sp.f_cutoff, sp.f_high, sr),
    "resonator": lambda sig, sp, sr: DSP.filt_resonator(sig, sp.f_cutoff, sp.f_q, sr),
}


class ModularSoundEngine:
    """Factory Method: renders one :class:`SoundSpec` into an int16 variant.

    Deterministic per ``(spec, seed)``.  Each seed draws its own organic
    humanisation (detune / level / attack / brightness / micro-delay), so a
    pool of seeds sounds like 32 slightly different physical keypresses
    instead of 32 clones.
    """

    def __init__(self, sr: int = AUDIO_SAMPLE_RATE):
        self.sr = sr

    # ------------------------------------------------------------- layers
    def _synthesize(self, spec: VoiceSpec, n: int, rng) -> np.ndarray:
        gen = _WAVE_GENERATORS.get(spec.osc)
        if gen is None:                       # unknown shape → silence layer
            return np.zeros(n, dtype=np.float64)
        return gen(spec, n, self.sr, rng)

    def _render_voice(self, spec: VoiceSpec, n: int, rng) -> np.ndarray:
        sig = self._synthesize(spec, n, rng)
        sig = sig * DSP.env_exp(n, self.sr, attack=spec.attack,
                                decay_rate=spec.decay_rate,
                                attack_curve=spec.attack_curve)
        filt = _FILTERS.get(spec.filt)
        if filt is not None:
            sig = filt(sig, spec, self.sr)
        if spec.drive > 0:
            sig = DSP.sat_tanh(sig, spec.drive)
        d = int(spec.delay * self.sr)
        if 0 < d < n:
            sig = np.concatenate([np.zeros(d, dtype=np.float64), sig[:n - d]])
        return sig * spec.gain

    # ------------------------------------------------------------- chain
    @staticmethod
    def _spec_chain(spec: SoundSpec) -> List[AudioStage]:
        """Compose the post-processing chain described by ``spec``."""
        chain: List[AudioStage] = []
        if spec.resonance:
            chain.append(ResonanceBankStage(tuple(spec.resonance)))
        if spec.post_hp > 0:
            chain.append(HighPassStage(spec.post_hp))
        if spec.post_lp > 0:
            chain.append(LowPassStage(spec.post_lp))
        return chain

    # ------------------------------------------------------------- render
    def render(self, spec: SoundSpec, seed: int) -> np.ndarray:
        rng = np.random.RandomState(int(seed))
        n = int(self.sr * spec.duration)
        mix = np.zeros(n, dtype=np.float64)

        # organic humanisation for this variant (all drawn from the seed →
        # bit-identical re-renders, but 32 seeds ≠ 32 clones)
        variation = min(max(float(getattr(spec, "variation", DEFAULT_VARIATION)), 0.0), 1.0)
        detune = 2.0 ** (rng.uniform(-0.35, 0.35) / 12.0)          # ±0.35 st
        level_lin = 10.0 ** (rng.uniform(-1.5, 0.0) * variation / 20.0)
        attack_mul = 2.0 ** (rng.uniform(-0.22, 0.22) * variation)
        bright_mul = 2.0 ** (rng.uniform(-0.10, 0.10) * variation)
        micro_delay = rng.uniform(0.0, 0.0006) * variation

        nyq_lp, nyq_bp = int(0.45 * self.sr), int(0.47 * self.sr)
        for v in spec.layers:
            v2 = v
            if v2.osc in _TONAL_WAVES:
                v2 = replace(v2, freq=v2.freq * detune)
                if v2.osc == "modal" and v2.modes:
                    v2 = replace(v2, modes=[(f * detune, d, a)
                                            for (f, d, a) in v2.modes])
            if variation > 0.0:
                v2 = replace(v2,
                             attack=max(1e-6, v2.attack * attack_mul),
                             gain=max(0.0, v2.gain * level_lin),
                             delay=max(0.0, v2.delay + micro_delay))
                if v2.filt in ("lp", "hp", "bp", "resonator"):
                    v2 = replace(v2,
                                 f_cutoff=float(round(min(v2.f_cutoff * bright_mul, nyq_lp))),
                                 f_high=float(round(min(v2.f_high * bright_mul, nyq_bp))))
            mix += self._render_voice(v2, n, rng)

        for stage in self._spec_chain(spec):
            mix = stage.process(mix, self.sr)
        # DC/rumble guard + peak-normalise to -1 dBFS
        return DSP.to_int16(DSP.filt_hp(mix, 20.0, self.sr, n_taps=63))


# ==========================================================================
# Pitch shifting (kept domain-exact: int16 pool samples, float custom samples)
# ==========================================================================
def _pitch_shift_int16(sound: np.ndarray, semitones: float) -> np.ndarray:
    """Linear-interpolated resampling pitch shift on an int16 click sample."""
    if semitones == 0 or len(sound) < 8:
        return sound
    factor = 2 ** (semitones / 12)
    n_orig = len(sound); n_new = max(1, int(n_orig / factor))
    if n_new == n_orig:
        return sound
    indices = np.linspace(0, n_orig - 1, n_new)
    i0 = indices.astype(np.int32); frac = indices - i0
    i1 = np.minimum(i0 + 1, n_orig - 1)
    s = sound.astype(np.float64)
    shifted = s[i0] * (1 - frac) + s[i1] * frac
    return shifted.astype(np.int16)


def _pitch_shift_float(sound: np.ndarray, semitones: float) -> np.ndarray:
    """Pitch shift keeping the float domain (for custom WAV samples)."""
    shifted = _pitch_shift_int16(
        np.clip(sound * 32767, -32768, 32767).astype(np.int16), semitones)
    return shifted.astype(np.float64) / 32767.0


# ==========================================================================
# WAV import — Adapter: every PCM width decoded through one function
# ==========================================================================
def _pcm_bytes_to_float(raw: bytes, sampwidth: int) -> np.ndarray:
    """Adapt raw little-endian PCM bytes to mono-ready float64 in [-1, 1)."""
    if sampwidth == 2:
        return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    if sampwidth == 1:
        return (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    if sampwidth == 4:
        return np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    if sampwidth == 3:
        b = np.frombuffer(raw, dtype=np.uint8)
        usable = (len(b) // 3) * 3
        b = b[:usable].reshape(-1, 3)
        vals = (b[:, 0].astype(np.int32)
                | (b[:, 1].astype(np.int32) << 8)
                | (b[:, 2].astype(np.int32) << 16))
        vals = np.where(vals & 0x800000, vals - 0x1000000, vals)
        return vals.astype(np.float64) / 8388608.0
    raise ValueError(f"Unsupported sample width: {sampwidth * 8}-bit")


def load_wav_sample(path: str, target_sr: int = AUDIO_SAMPLE_RATE) -> np.ndarray:
    """Load a WAV file as mono float64 at target_sr, peak-normalised to 0.9.

    Supports 8/16/24/32-bit PCM; multi-channel audio is down-mixed and any
    sample rate is linearly resampled. Raises on unreadable files.
    """
    with wave.open(path, "rb") as w:
        nch, sampwidth, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)

    data = _pcm_bytes_to_float(raw, sampwidth)

    if nch > 1:
        data = data[: (len(data) // nch) * nch].reshape(-1, nch).mean(axis=1)

    if rate != target_sr and len(data) > 1:
        new_len = max(1, int(len(data) * target_sr / rate))
        idx = np.linspace(0, len(data) - 1, new_len)
        i0 = idx.astype(np.int64)
        frac = idx - i0
        i1 = np.minimum(i0 + 1, len(data) - 1)
        data = data[i0] * (1 - frac) + data[i1] * frac

    peak = float(np.max(np.abs(data))) if len(data) else 0.0
    if peak > 1e-9:
        data = data / peak * 0.9

    max_len = int(target_sr * MAX_CUSTOM_CLICK_SECONDS)  # key clicks stay short
    if len(data) > max_len:
        data = data[:max_len]
    return np.ascontiguousarray(data, dtype=np.float64)


def load_wav_samples(paths: List[str]) -> List[np.ndarray]:
    """Load every readable WAV; failures are logged, never raised."""
    out = []
    for p in paths:
        try:
            sample = load_wav_sample(p)
            if len(sample) > 16:
                out.append(sample)
        except Exception as e:
            logger.error(f"Failed to load custom WAV '{p}': {e}")
    return out


# ==========================================================================
# KeyLayout — QWERTY geometry → row timbre + stereo placement
# ==========================================================================
class KeyLayout:
    """Maps characters onto the physical keyboard.

    Row gives the timbre offset (number row bright, bottom row deep);
    column gives the stereo position, so in stereo mode a key on the left
    of the board also *sounds* left — with a modest human spread applied by
    the caller.
    """

    ROWS: Final[Tuple[str, ...]] = ("`1234567890-=", "qwertyuiop[]\\", "asdfghjkl;'", "zxcvbnm,./")
    ROW_PITCH: Final[Tuple[float, ...]] = (1.5, 0.5, -0.5, -2.0)
    ROW_STAGGER: Final[Tuple[float, ...]] = (0.10, 0.05, 0.0, -0.05)
    PAN_LIMIT: Final[float] = 0.55

    # shifted symbols inherit the timbre/pan of the key that types them
    # (mirrors KeyboardOverlay.base_shift; "+" used to fall through to the
    # home-row default because it is not an unshifted label anywhere)
    SHIFT_BASE: Final[Dict[str, str]] = {
        "~": "`", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6",
        "&": "7", "*": "8", "(": "9", ")": "0", "_": "-", "+": "=",
        "{": "[", "}": "]", "|": "\\", ":": ";", '"': "'", "<": ",",
        ">": ".", "?": "/",
    }

    def __init__(self) -> None:
        self._pitch: Dict[str, float] = {}
        self._pan: Dict[str, float] = {}
        for r, row in enumerate(self.ROWS):
            n = len(row)
            for i, c in enumerate(row):
                self._pitch[c] = self.ROW_PITCH[r]
                center = i / max(1, n - 1) + self.ROW_STAGGER[r] - 0.5
                self._pan[c] = max(-self.PAN_LIMIT, min(self.PAN_LIMIT, center))
        for s, b in self.SHIFT_BASE.items():
            if b in self._pitch:
                self._pitch[s] = self._pitch[b]
                self._pan[s] = self._pan[b]

    def pitch_for(self, ch: str) -> float:
        if ch in (" ", "\n", "\t"):
            return -3.0
        low = ch.lower()
        if low in self._pitch:
            return self._pitch[low]
        # accented letters keep the timbre of their base letter
        nfd = unicodedata.normalize("NFD", low)
        base = nfd[0] if nfd else ""
        return self._pitch.get(base, 0.0)

    def pan_for(self, ch: str) -> float:
        low = ch.lower()
        if low in self._pan:
            return self._pan[low]
        nfd = unicodedata.normalize("NFD", low)
        base = nfd[0] if nfd else ""
        return self._pan.get(base, 0.0)


_KEY_LAYOUT = KeyLayout()


# ==========================================================================
# VariantPoolFactory — Factory Method for the round-robin sample families
# ==========================================================================
@dataclass(frozen=True, slots=True)
class VariantFamily:
    """Flyweight: pre-rendered click / space / enter variant pools."""

    clicks: Tuple[np.ndarray, ...]
    spaces: Tuple[np.ndarray, ...]
    enters: Tuple[np.ndarray, ...]


class VariantPoolFactory:
    """Builds detuned round-robin families from a preset or user WAVs.

    The detune ladder (0 / ±0.4 / ±0.9 st) guarantees the round-robin never
    plays the exact same waveform twice in a row — for procedural presets the
    per-seed organic variation of :class:`ModularSoundEngine` adds the rest.
    """

    def from_preset(self, spec: SoundSpec,
                    engine: Optional[ModularSoundEngine] = None) -> VariantFamily:
        eng = engine or ModularSoundEngine()
        enter_spec = spec.enter_spec or spec
        space_spec = spec.space_spec or spec
        return VariantFamily(
            tuple(eng.render(spec, i) for i in range(CLICK_VARIANTS)),
            tuple(eng.render(space_spec, 100 + i) for i in range(SPACE_VARIANTS)),
            tuple(eng.render(enter_spec, 200 + i) for i in range(ENTER_VARIANTS)),
        )

    def from_custom_samples(
            self, custom_samples: Sequence[np.ndarray]) -> Optional[VariantFamily]:
        """Build a variant pool from user WAV samples (≤ 4 sources × 5 detunes).

        Returns ``None`` when no sample is usable, so the caller can fall
        back to the procedural preset (Null-Object style decision).
        """
        base = [np.asarray(s, dtype=np.float64) for s in custom_samples
                if len(np.asarray(s)) > 16]
        if not base:
            return None
        pool: List[np.ndarray] = []
        for s in base[:MAX_CUSTOM_SOURCES]:
            s = _normalize(s.copy(), 0.9)
            for st in CUSTOM_DETUNE_SEMITONES:
                pool.append(s if st == 0.0 else _pitch_shift_float(s, st))
        pool = pool[:CLICK_VARIANTS]
        clicks = tuple(pool)
        spaces = tuple(_pitch_shift_float(s, -3.0) for s in pool[:8]) or clicks
        enters = tuple(_pitch_shift_float(s, -5.0) for s in pool[:4]) or clicks
        return VariantFamily(clicks, spaces, enters)


# ==========================================================================
# SimpleSoundGen — Facade: timestamps in, mastered PCM out
# ==========================================================================
class SimpleSoundGen:
    """Turns character timestamps into mastered keyboard PCM.

    Attributes:
        clicks:  ``CLICK_VARIANTS`` letter variants (round-robin pool)
        spaces:  spacebar variants (deepened)
        enters:  Enter variants (deepest)
    """

    # legacy aliases kept for code that poked at the old class attributes
    _QWERTY_ROWS = KeyLayout.ROWS
    _ROW_PITCH_SHIFT = KeyLayout.ROW_PITCH

    def __init__(self, sr: int = AUDIO_SAMPLE_RATE, preset: str = "Mechanical",
                 stereo: bool = False, reverb_amt: float = 0.1,
                 custom_samples: Optional[List[np.ndarray]] = None):
        self.sr = sr
        self.preset = preset
        self.stereo = stereo
        self.reverb_amt = reverb_amt
        self.engine = ModularSoundEngine(sr)
        self.layout = _KEY_LAYOUT

        factory = VariantPoolFactory()
        family = None
        if custom_samples:
            # same treatment the procedural presets get: a detuned variant
            # pool built from each user sample
            family = factory.from_custom_samples(custom_samples)
        if family is None:
            spec = MODULAR_SOUND_PRESETS.get(preset, MODULAR_SOUND_PRESETS["Mechanical"])
            family = factory.from_preset(spec, self.engine)

        self.clicks: List[np.ndarray] = list(family.clicks)
        self.spaces: List[np.ndarray] = list(family.spaces)
        self.enters: List[np.ndarray] = list(family.enters)

    # ------------------------------------------------------------- mapping
    def _get_pitch_shift(self, char: str) -> float:
        return self.layout.pitch_for(char)

    def _pan_hint(self, char: str) -> float:
        return self.layout.pan_for(char)

    # ------------------------------------------------------- pitch helpers
    @staticmethod
    def _pitch_shift(sound: np.ndarray, semitones: float) -> np.ndarray:
        return _pitch_shift_int16(sound, semitones)

    @classmethod
    def _pitch_shift_f(cls, sound: np.ndarray, semitones: float) -> np.ndarray:
        return _pitch_shift_float(sound, semitones)

    def _shift_sample(self, snd: np.ndarray, shift: float) -> np.ndarray:
        """Pitch shift samples of either int16 (presets) or float (custom WAV)."""
        if snd.dtype == np.int16:
            return self._pitch_shift(snd, shift)
        shifted = self._pitch_shift(
            np.clip(snd * 32767, -32768, 32767).astype(np.int16), shift)
        return shifted.astype(np.float64) / 32767.0

    # ------------------------------------------------------------- master
    def _pre_master_chain(self) -> Tuple[AudioStage, ...]:
        """Room tail → soft-clip (crest control), the pre-loudness stages.

        The loudness anchor + true-peak limiting live in
        :func:`_finalize_loudness` — they must run *iteratively* (limit,
        re-measure, re-gain) to land heavy-crest presets on the -14 LUFS
        target, which a static stage chain cannot express.
        """
        return (RoomTailStage(self.reverb_amt), SoftClipStage())

    def _master_chain(self) -> Tuple[AudioStage, ...]:
        """Legacy single-pass chain (Room tail → clip → -14 LUFS → limiter →
        backstop), kept for compatibility with code/tests that inspect the
        stage order.  The render paths use :meth:`_pre_master_chain` +
        :func:`_finalize_loudness` (iterated to convergence) instead.
        """
        return (RoomTailStage(self.reverb_amt), SoftClipStage(),
                LoudnessStage(), TruePeakLimiterStage(), TruePeakStage())

    def _stereo_master(self, ml: np.ndarray, mr: np.ndarray,
                       sr: int) -> Tuple[np.ndarray, np.ndarray]:
        """Master a stereo pair *as one image* (v1.0.3).

        The old path ran the full mono chain on each channel separately.
        Two professional defects follow from that:

        1. **Image drift.**  The loudness stage normalises each channel to
           -14 LUFS *individually* — on QWERTY most letters sit right of
           centre, so the left channel (quieter) was boosted more than the
           right, dragging solos and panned content back toward the centre
           (and worse, by a different amount on every render).
        2. **Mono-ish reverb.**  Both channels convolved the *same* seeded
           IR, so the "room" collapsed to a point source behind the clicks.

        The fix: decorrelated room tails (two seeds, same statistics), a
        soft-clip crest pass per channel, then ONE iterated loudness gain
        measured on the mono sum and applied to both channels with the
        true-peak limiter running per channel — they are scale-safe per
        channel and preserve the image.  Silence and sub-block tracks pass
        through untouched.
        """
        # 1) shared room, decorrelated tails: SAME seed, right channel's
        # diffuse tail time-reversed — identical magnitude response (no
        # level/spectral skew) with flipped phase (real width)
        ml = RoomTailStage(self.reverb_amt, seed=ROOM_TAIL_SEED).process(ml, sr)
        mr = RoomTailStage(self.reverb_amt, seed=ROOM_TAIL_SEED,
                           reverse=True).process(mr, sr)
        # 2) crest control, then the shared loudness/limit loop
        ml = SoftClipStage().process(np.asarray(ml, dtype=np.float64), sr)
        mr = SoftClipStage().process(np.asarray(mr, dtype=np.float64), sr)
        return _finalize_loudness_pair(ml, mr, sr)


    def _room_tail(self, x: np.ndarray) -> np.ndarray:
        """Compat wrapper around :class:`RoomTailStage`."""
        return RoomTailStage(self.reverb_amt).process(x, self.sr)

    # -------------------------------------------------------------- render
    def generate_pcm(self, timestamps, volume: float = 0.5) -> np.ndarray:
        """Mix one click per ``(time, char)`` event into int16 PCM.

        Mono output is a plain int16 stream; stereo output is interleaved
        L/R.  Deterministic: the same timestamps always produce the same
        audio, so re-renders stay in sync.

        All mixing happens in the true float domain [-1, 1): int16 pool
        samples are divided by 32768 on the way in (custom WAV samples are
        already float).  The master chain — soft clip, gated -14 LUFS,
        -1 dBTP ceiling — is a float-scale processor and only does the
        right thing when its input actually lives in [-1, 1]; feeding it
        int16-scale units (the old behaviour) made the loudness stage a
        no-op and left the output level to chance.
        """
        if not timestamps:
            return np.zeros(0, dtype=np.int16)
        sr = self.sr
        total = max(ts for ts, _ in timestamps) + 0.3
        n = int(sr * total)
        rng = random.Random(98765)
        raw, starts_i, pans = [], [], []
        for ts, ch in timestamps:
            if ch == "\n":
                # Enter: heavier strike, sits slightly left of centre
                snd, vm, pan = rng.choice(self.enters), rng.uniform(1.05, 1.20), 0.2
            elif ch == " ":
                # Spacebar: stabiliser thunk, dead centre
                snd, vm, pan = rng.choice(self.spaces), rng.uniform(1.00, 1.15), 0.0
            else:
                base_snd = rng.choice(self.clicks)
                shift = self._get_pitch_shift(ch)
                snd = self._shift_sample(base_snd, shift) if shift else base_snd
                # velocity varies per press; position follows the real layout
                vm = rng.uniform(0.90, 1.12)
                pan = max(-KeyLayout.PAN_LIMIT,
                          min(KeyLayout.PAN_LIMIT,
                              self._pan_hint(ch) + rng.uniform(-0.06, 0.06)))
            s = int(ts * sr); e = min(s + len(snd), n)
            if s < n:
                # int16 pool variants -> true float; custom WAV samples are
                # already float in [-1, 1) — one domain for every source
                if snd.dtype == np.int16:
                    snd_f = snd[:e - s].astype(np.float32) / 32768.0
                else:
                    snd_f = snd[:e - s].astype(np.float32)
                raw.append(snd_f * volume * vm)
                starts_i.append(s)
                if self.stereo:
                    pans.append(pan)
        if not raw:
            return np.zeros(n, dtype=np.int16)

        if self.stereo:
            ml = np.zeros(n, dtype=np.float32); mr = np.zeros(n, dtype=np.float32)
            for i, snd in enumerate(raw):
                s = starts_i[i]; pan = pans[i]
                lg = np.cos((pan + 1.0) * np.pi / 4.0); rg = np.sin((pan + 1.0) * np.pi / 4.0)
                e = min(s + len(snd), n)
                ml[s:e] += snd[:e - s] * lg; mr[s:e] += snd[:e - s] * rg
            # v1.0.3: master the pair as ONE image — a single loudness gain
            # measured on the mono sum (per-channel normalisation used to
            # drag panned content off its position) and decorrelated room
            # tails for a real stereo room.
            ml, mr = self._stereo_master(ml.astype(np.float64), mr.astype(np.float64), sr)
            mx = max(float(np.max(np.abs(ml))) if len(ml) else 0.0,
                     float(np.max(np.abs(mr))) if len(mr) else 0.0)
            if mx > 1.0:
                # joint peak-safe mastering: one scale keeps the stereo image
                ml = ml * (MASTER_CEILING / mx); mr = mr * (MASTER_CEILING / mx)
            out = np.empty(n * 2, dtype=np.int16)
            out[0::2] = np.clip(ml * 32767, -32768, 32767).astype(np.int16)
            out[1::2] = np.clip(mr * 32767, -32768, 32767).astype(np.int16)
            return out

        # mono: vectorised additive mixing via flat buffer + offsets
        starts = np.array(starts_i, dtype=np.int64)
        lengths = np.array([len(s) for s in raw], dtype=np.int64)
        flat = np.concatenate(raw)
        offsets = np.zeros(len(raw), dtype=np.int64)
        for i in range(1, len(raw)):
            offsets[i] = offsets[i - 1] + lengths[i - 1]
        mix = np.zeros(n, dtype=np.float32)
        for i in range(len(starts)):
            mix[int(starts[i]):int(starts[i] + lengths[i])] += flat[int(offsets[i]):int(offsets[i] + lengths[i])]
        # v1.0.3: room tail → crest clip → iterated loudness/limit-to-target
        # (a single anchor pass landed heavy-crest presets ~1 dB below
        # -14 LUFS because limiting itself removes loudness)
        mix = run_stages(mix.astype(np.float64), sr, self._pre_master_chain())
        mix = _finalize_loudness(mix, sr)
        mx = float(np.max(np.abs(mix))) if len(mix) else 0.0
        if mx > 1.0:  # peak-safe backstop after the true-peak stage
            mix = mix * (MASTER_CEILING / mx)
        return np.clip(mix * 32767, -32768, 32767).astype(np.int16)


# ==========================================================================
# ── AMBIENCE — 34 soundscapes via the Registry pattern
#    Each soundscape is a Strategy (SoundscapeFn) registered by the
#    @soundscape decorator; adding one = adding one decorated function.
#    Every preset is deterministic for a given seed and rendered fully
#    vectorised with numpy (FFT filtering), so a 60-second bed renders in
#    well under a second.  Custom files are handled by the loaders below.
# ==========================================================================

AMBIENCE_PRESETS: Dict[str, SoundscapeFn] = {}


def soundscape(name: str) -> Callable[[SoundscapeFn], SoundscapeFn]:
    """Registry decorator: publish ``fn`` as an ambience preset."""
    def register(fn):
        if name in AMBIENCE_PRESETS:
            raise ValueError(f"duplicate soundscape registered: {name!r}")
        AMBIENCE_PRESETS[name] = fn
        fn.soundscape_name = name      # metadata for tooling / introspection
        return fn
    return register


# ------------------------------------------------------------------ helpers
_xlp = DSP.filt_lp   # shared windowed-sinc low-pass (was a duplicated kernel)


def _hp(x, cutoff, sr, n_taps=63):
    """True high-pass: signal minus its low-passed copy."""
    return x - _xlp(x, cutoff, sr, n_taps)


def _bp(x, lo, hi, sr):
    return _xlp(x, hi, sr) - _xlp(x, lo, sr)


def _noise(n, rng):
    return rng.randn(n)


def _pink(n, rng):
    white = rng.randn(n)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, 1.0 / AUDIO_SAMPLE_RATE)
    freqs[0] = max(freqs[1] if len(freqs) > 1 else 1.0, 1.0)
    fft[1:] /= np.sqrt(np.abs(freqs[1:])); fft[0] = 0
    out = np.fft.irfft(fft, n=n)
    pk = np.max(np.abs(out)) or 1.0
    return out / pk


def _brown(n, rng):
    white = rng.randn(n)
    brown = np.cumsum(white)
    brown -= np.linspace(brown[0], brown[-1], n)  # remove drift
    # v1.0.3: subtract the sub-audible wander (cumsum residuals below ~15 Hz
    # still carry most of the energy — the fireplace bed spent 9.7 dB of its
    # peak headroom on rumble the render path then DC-blocked away anyway;
    # removing it at the source lets the anchor reach the loudness target
    # without crushing the crackle detail).
    brown = brown - _xlp(brown, 15.0, AUDIO_SAMPLE_RATE)
    pk = np.max(np.abs(brown)) or 1.0
    return brown / pk


def _lfo(n, sr, freq, phase=0.0, lo=0.0, hi=1.0):
    t = np.arange(n, dtype=np.float64) / sr
    return lo + (hi - lo) * (0.5 + 0.5 * np.sin(2 * np.pi * freq * t + phase))


def _wander(n, sr, rng, lo=0.0, hi=1.0, periods=(40.0, 90.0, 200.0)):
    """Multi-period drift envelope in ``[lo, hi]``.

    Three slow sines of unequal period and weight superpose into a wander
    that never exactly repeats — the natural 'breathing' a single LFO lacks.
    Deterministic: every random draw comes from the bed's ``rng``.
    """
    t = np.arange(n, dtype=np.float64) / sr
    w = np.zeros(n, dtype=np.float64)
    for p in periods:
        w += np.sin(2 * np.pi * t / p + rng.uniform(0.0, 6.2831853)) * rng.uniform(0.6, 1.0)
    pk = np.max(np.abs(w))
    if pk > 1e-9:
        w /= pk
    return lo + (hi - lo) * (0.5 + 0.5 * w)


def _impulses(n, sr, rng, density, amp=1.0):
    """Random impulse train with tiny exponential decays (crackles/droplets)."""
    out = np.zeros(n)
    n_events = int(density * n / sr)
    if n_events <= 0:
        return out
    pos = (rng.random(n_events) * n).astype(np.int64)
    a = 0.3 + 0.7 * rng.random(n_events)
    decay = np.exp(-rng.uniform(80, 400, n_events))
    tail = 64
    for p, ai, d in zip(pos, a, decay):
        ln = min(tail, n - p)
        if ln <= 0:
            continue
        out[p:p + ln] += ai * d * rng.randn(ln)
    pk = np.max(np.abs(out)) or 1.0
    return out / pk * amp


# ------------------------------------------------------------------ beds
# v1.0.3: high-shelf damping per bed — the "static" complaint.  Several
# textures are built from bright noise bands; on laptop speakers that top
# octave reads as radio hiss rather than air.  A gentle FIR shelf (-2 to
# -4 dB above ~4-6 kHz) keeps the texture's identity (surf still hisses,
# vinyl still crackles) while pulling the fizz out of the mix.  Only beds
# whose measured 5 kHz+ energy share was unusually high are listed.
_BED_TILT: Final[Dict[str, Tuple[float, float]]] = {
    # bed name:            (shelf cutoff Hz, shelf gain dB)
    "Café Murmur":         (4200.0, -3.5),
    "Blizzard":            (5000.0, -3.0),
    "Ocean Waves":         (5200.0, -2.5),
    "Hot Spring":          (5200.0, -2.5),
    "Vinyl Crackle":       (5200.0, -3.0),
    "Server Room":         (6000.0, -2.0),
    "Airplane Cabin":      (5000.0, -2.0),
    "Underwater":          (4200.0, -2.0),
}


def _shelf_tilt(x: np.ndarray, sr: int, cutoff: float,
                gain_db: float) -> np.ndarray:
    """First-order high-shelf: damp everything above ``cutoff`` by ``gain_db``.

    Linear-phase FIR split (reuses the memoised windowed-sinc low-pass):
    ``out = low + high * gain`` — no phase smear, no resonant ripple, and
    the shelf is mild enough that it never audibly "EQs" the texture.
    """
    if gain_db >= 0.0:
        return x
    low = DSP.filt_lp(x, float(cutoff), sr, 127)
    high = x - low
    return low + high * (10.0 ** (gain_db / 20.0))


@soundscape("Rain")
def _p_rain(n, sr, rng):
    """Steady rainfall: dark gusting wash + dense droplet patter.

    The old bed was one wide band of stationary white noise (400-9000 Hz) —
    literally the spectrum of radio static.  Real rain has a pink-ish
    spectrum living between ~300 Hz and ~6 kHz, breathes with the shower's
    intensity and is articulated by thousands of droplet impacts.  So the
    wash is now two independently modulated layers (dark body + bright
    sheen) over a droplet train.
    """
    intensity = _wander(n, sr, rng, lo=0.45, hi=1.0, periods=(21.0, 47.0, 113.0))
    # dark body of the shower (pink-ish, 200-2600 Hz) — carries the wash
    body = _bp(_pink(n, rng), 200, 2600, sr)
    body *= intensity * 1.9
    # brighter sheen (2.0-5.2 kHz): quieter, gusting on its own phase
    sheen = _bp(_noise(n, rng), 2000, 5200, sr)
    x = body + sheen * 0.30 * _wander(n, sr, rng, lo=0.25, hi=0.9,
                                      periods=(13.0, 29.0, 67.0))
    # dense droplet patter — the articulation that reads as "rain", not hiss
    # (low-passed so the impacts stay wet, not sparky)
    x += 0.26 * _xlp(_impulses(n, sr, rng, density=34.0, amp=1.0), 4200, sr)
    x += 0.22 * _xlp(_impulses(n, sr, rng, density=16.0, amp=1.0), 2800, sr)
    # occasional heavy drops: lower, fuller splats under the patter
    x += 0.40 * _xlp(_impulses(n, sr, rng, density=1.6, amp=1.0), 1600, sr)
    return _normalize(x, 0.75)


@soundscape("Rain & Thunder")
def _p_rain_thunder(n, sr, rng):
    x = _p_rain(n, sr, rng) * 0.85
    rumble = _xlp(_brown(n, rng), 120, sr)
    swell_t = 0.0
    while swell_t < n / sr:
        c = int(swell_t * sr)
        ln = min(int((2.5 + rng.random() * 2.5) * sr), n - c)
        if ln <= 0:
            break
        env = np.sin(np.linspace(0, np.pi, ln)) ** 2
        x[c:c + ln] += 1.5 * rumble[c:c + ln] * env
        swell_t += 8 + rng.random() * 18
    return _normalize(x, 0.85)


@soundscape("Rain on Window")
def _p_rain_window(n, sr, rng):
    """Rain heard through glass: muffled patter + tonal droplet plinks."""
    x = _xlp(_p_rain(n, sr, rng), 1400, sr)
    n_ping = min(int(0.09 * sr), max(2, n - 2))
    tp = np.arange(n_ping) / sr
    for _ in range(int(n / sr * 2.2)):          # ~2 droplets per second
        f = (700 + rng.random() * 1600) * (1.0 - 0.15 * tp / tp[-1])
        ph = 2 * np.pi * np.cumsum(f) / sr
        ping = np.sin(ph) * np.exp(-tp * 55) * (0.25 + 0.5 * rng.random())
        c = int(rng.random() * max(1, n - n_ping))
        e = min(c + n_ping, n)
        x[c:e] += ping[:e - c]
    return _normalize(x, 0.7)


@soundscape("Ocean Waves")
def _p_ocean(n, sr, rng):
    """Ocean waves: overlapping swells with foam hiss cresting at the peak."""
    bed = _xlp(_brown(n, rng), 240, sr) * 0.55
    bed *= _wander(n, sr, rng, lo=0.8, hi=1.0, periods=(50.0, 110.0, 230.0))
    surf = _bp(_noise(n, rng), 300, 2400, sr)
    foam = _hp(_noise(n, rng), 3500, sr) * 0.35
    x = bed
    wt = 0.0
    while wt < n / sr:
        c = int(wt * sr)
        ln = min(int((4.5 + rng.random() * 4.0) * sr), n - c)
        if ln <= 0:
            break
        env = np.sin(np.linspace(0, np.pi, ln)) ** 2 * (0.55 + rng.random() * 0.45)
        x[c:c + ln] += surf[c:c + ln] * env * 1.1
        x[c:c + ln] += foam[c:c + ln] * env * env * 0.9
        wt += ln / sr * (0.55 + rng.random() * 0.35)   # waves overlap
    return _normalize(x, 0.75)


@soundscape("Forest Dawn")
def _p_forest(n, sr, rng):
    """Forest dawn: soft breeze, leaf rustle and distant birdsong."""
    breeze = _bp(_noise(n, rng), 150, 900, sr)
    breeze *= _wander(n, sr, rng, lo=0.2, hi=0.7, periods=(35.0, 80.0, 160.0))
    x = breeze * 0.8
    x += 0.06 * _impulses(n, sr, rng, density=3.0, amp=1.0)   # leaves
    nd = int(0.14 * sr)                                        # one bird note
    td = np.arange(nd) / sr
    for _ in range(int(n / sr * 0.5)):          # ~0.5 trill groups per second
        if rng.random() < 0.45:
            continue
        c = int(rng.random() * max(1, n - nd * 5))
        f0 = 2200 + rng.random() * 2600
        for k in range(2 + int(rng.random() * 3)):
            s = c + int(k * (0.07 + rng.random() * 0.05) * sr)
            if s + nd >= n:
                break
            f = f0 * (1.0 + 0.25 * rng.random()) * (1.0 - 0.3 * td / td[-1])
            note = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-td * 34)
            x[s:s + nd] += note * (0.05 + rng.random() * 0.09)
    return _normalize(x, 0.6)


@soundscape("Night Crickets")
def _p_crickets(n, sr, rng):
    out = np.zeros(n)
    chirp_carrier = 3800 + rng.random() * 900
    chirp_dur = int(0.035 * sr)
    t = np.arange(chirp_dur) / sr
    unit = np.sin(2 * np.pi * chirp_carrier * t) * np.exp(-t * 60)
    pos = 0.0
    while pos < n / sr:
        c = int(pos * sr)
        for k in range(3 + int(rng.random() * 3)):
            s = c + int(k * 0.07 * sr)
            if s + chirp_dur >= n:
                break
            out[s:s + chirp_dur] += unit * (0.5 + rng.random() * 0.5)
        pos += 0.45 + rng.random() * 0.8
    # quiet night air
    out += 0.06 * _xlp(_pink(n, rng), 1500, sr)
    return _normalize(out, 0.65)


@soundscape("Wind")
def _p_wind(n, sr, rng):
    base = _brown(n, rng)
    band1 = _bp(base, 180, 700, sr)
    band2 = _bp(base, 500, 1800, sr)
    gust = _wander(n, sr, rng, lo=0.18, hi=1.0, periods=(22.0, 55.0, 120.0))
    gust = _xlp(gust, 3.0, sr, n_taps=255)
    x = band1 * gust + band2 * (gust ** 2) * 0.7
    # whistle rides the gusts
    x += 0.08 * np.sin(2 * np.pi * (700 + 300 * _lfo(n, sr, 0.03)) * np.arange(n) / sr) * (gust ** 3)
    return _normalize(x, 0.7)


@soundscape("Fireplace")
def _p_fire(n, sr, rng):
    bed = _xlp(_brown(n, rng), 220, sr) * 0.9
    crackle = _impulses(n, sr, rng, density=6.0, amp=1.0)
    crackle = _xlp(crackle, 4500, sr)
    whoosh = _bp(_noise(n, rng), 80, 400, sr) * _lfo(n, sr, 0.23, lo=0.1, hi=0.6)
    return _normalize(bed + crackle + whoosh, 0.7)


@soundscape("Café Murmur")
def _p_cafe(n, sr, rng):
    # three shared formant bands, each murmur blob gets its own LFO pair
    # (9 FFT filters instead of 27 — a 60 s bed renders in ~2 s)
    src = _noise(n, rng)
    bands = ((_bp(src, 120, 440, sr), 0.9),    # chest / room
             (_bp(src, 440, 900, sr), 1.0),    # speech body
             (_bp(src, 900, 1500, sr), 0.35))  # sibilance
    x = np.zeros(n)
    for band, base in bands:
        for _ in range(3):
            m = _lfo(n, sr, 0.15 + rng.random() * 0.5, phase=rng.random() * 6.28, lo=0.1, hi=1.0)
            m *= _lfo(n, sr, 0.6 + rng.random() * 1.2, phase=rng.random() * 6.28, lo=0.55, hi=1.0)
            x += band * m * base / 9.0
    # the whole room ebbs and flows between lunch rush and lull
    x *= _wander(n, sr, rng, lo=0.85, hi=1.0, periods=(45.0, 95.0, 180.0))
    # light cup/cutlery clicks
    x += 0.12 * _impulses(n, sr, rng, density=1.6, amp=1.0)
    # a few tonal porcelain clinks
    nd = min(int(0.5 * sr), max(2, n - 2))
    td = np.arange(nd) / sr
    for _ in range(int(n / sr / 6.0)):
        f = 1150 + rng.random() * 900
        clink = (np.sin(2 * np.pi * f * td) * np.exp(-td * 18)
                 + 0.4 * np.sin(2 * np.pi * f * 2.42 * td) * np.exp(-td * 30))
        s = int(rng.random() * max(1, n - nd))
        x[s:s + nd] += clink * (0.05 + rng.random() * 0.05)
    # occasional espresso-machine steam burst (skipped on very short beds)
    if n >= 3 * sr:
        for _ in range(max(1, int(n / sr / 25.0))):
            ln = int((2.0 + rng.random() * 2.0) * sr)
            ln = min(ln, n - 2)
            s = int(rng.random() * max(1, n - ln))
            steam = _hp(_noise(ln, rng), 2200, sr) * np.sin(np.linspace(0, np.pi, ln)) ** 2
            x[s:s + ln] += steam * 0.12
    return _normalize(x, 0.7)


@soundscape("Library")
def _p_library(n, sr, rng):
    """Reading room: hushed tone, page turns, a distant chair scrape."""
    x = _xlp(_pink(n, rng), 1200, sr) * 0.30
    x += np.sin(2 * np.pi * 55 * np.arange(n) / sr) * 0.03
    for _ in range(max(1, int(n / sr / 7.0))):   # page turns
        c = int(rng.random() * max(1, n - int(1.0 * sr)))
        for k in range(2):
            ln = int((0.16 + rng.random() * 0.1) * sr)
            s = c + int(k * (0.12 + rng.random() * 0.05) * sr)
            if s + ln >= n:
                break
            sw = _bp(_noise(ln, rng), 1200, 5200, sr)
            x[s:s + ln] += sw * np.sin(np.linspace(0, np.pi, ln)) ** 2 * (0.2 + rng.random() * 0.15)
    return _normalize(x, 0.5)


@soundscape("Zen Garden")
def _p_zen(n, sr, rng):
    """Zen garden: trickling water with pentatonic wind-chime plinks."""
    stream = _bp(_noise(n, rng), 350, 2600, sr)
    stream *= _lfo(n, sr, 0.08, phase=rng.random() * 6.28, lo=0.55, hi=1.0)
    x = stream * 0.55
    x += _xlp(_brown(n, rng), 180, sr) * 0.15   # basin depth
    scale = [523.25, 587.33, 698.46, 783.99, 880.0, 1046.5]
    nd = int(2.2 * sr)
    if n > nd:
        td = np.arange(nd) / sr
        for _ in range(max(1, int(n / sr / 5.0))):   # one plink every ~5 s
            f = scale[rng.randint(len(scale))]
            plink = np.zeros(nd)
            for mul, amp in ((1.0, 1.0), (2.76, 0.35), (5.4, 0.12)):   # inharmonic
                plink += np.sin(2 * np.pi * f * mul * td) * amp
            s = int(rng.random() * (n - nd))
            x[s:s + nd] += plink * np.exp(-td * 2.4) * (0.10 + rng.random() * 0.08)
    return _normalize(x, 0.6)


@soundscape("City Traffic")
def _p_city(n, sr, rng):
    """City street: distant traffic wash with passing-vehicle whooshes."""
    x = _xlp(_brown(n, rng), 200, sr) * 0.5
    x += _bp(_noise(n, rng), 90, 420, sr) * _lfo(n, sr, 0.043, phase=rng.random() * 6.28,
                                                 lo=0.3, hi=0.8) * 0.5
    nw = int(3.0 * sr)
    for _ in range(max(1, int(n / sr / 9.0))):   # one pass every ~9 s
        nw_eff = min(nw, max(2, n - 2))          # never longer than the bed
        whoosh = _bp(_noise(nw_eff, rng), 250, 1600, sr)
        env = np.sin(np.linspace(0, np.pi, nw_eff)) ** 1.5
        seg = whoosh * env * (0.25 + rng.random() * 0.2)
        s = int(rng.random() * max(1, n - nw_eff))
        e = min(s + nw_eff, n)
        x[s:e] += seg[:e - s]
        if rng.random() < 0.3:                   # rare distant horn
            hl = min(int(0.45 * sr), max(2, n - 2))
            th = np.arange(hl) / sr
            h = (np.sin(2 * np.pi * 440 * th) + np.sin(2 * np.pi * 554 * th)) * 0.5
            hs = s + int(rng.random() * max(1, nw_eff - hl))
            he = min(hs + hl, n)
            if he > hs:
                x[hs:he] += h[:he - hs] * np.hanning(hl)[:he - hs] * 0.04
    return _normalize(x, 0.7)


@soundscape("Midnight City")
def _p_night_city(n, sr, rng):
    """Midnight city: deep drone, airy wash and one far-off siren."""
    x = _xlp(_brown(n, rng), 150, sr) * 0.6
    x += _bp(_noise(n, rng), 200, 800, sr) * _lfo(n, sr, 0.05, phase=rng.random() * 6.28,
                                                  lo=0.15, hi=0.4) * 0.5
    if n > 20 * sr:                              # distant wail, very quiet
        wl = int((6 + rng.random() * 4) * sr)
        s = int(n * (0.25 + rng.random() * 0.4))
        e = min(s + wl, n)
        tw = np.arange(e - s) / sr
        f = 620 + 240 * np.sin(2 * np.pi * 0.22 * tw)
        ph = 2 * np.pi * np.cumsum(f) / sr
        env = np.minimum(1.0, tw / 1.2) * np.minimum(1.0, ((e - s) / sr - tw) / 1.2)
        x[s:e] += np.sin(ph) * np.maximum(env, 0.0) * 0.035
    return _normalize(x, 0.6)


@soundscape("Night Train")
def _p_train(n, sr, rng):
    """Night train: rail-joint rhythm, bogie rumble and cabin hiss."""
    sway = _lfo(n, sr, 0.12, phase=rng.random() * 6.28, lo=0.8, hi=1.0)
    x = (_xlp(_brown(n, rng), 160, sr) * 0.7 + _xlp(_pink(n, rng), 3500, sr) * 0.10) * sway
    tl = min(int(0.16 * sr), max(2, n - 2))
    tt = np.arange(tl) / sr
    thump = _xlp(np.exp(-tt * 28) * _noise(tl, rng), 300, sr)
    speed = 0.62 + rng.random() * 0.12           # rail joints per second
    pos = 0.3
    while pos < n / sr - 0.4:
        c = int(pos * sr)
        g = 0.5 + rng.random() * 0.5
        for off, amp in ((0.0, g), (0.14, g * 0.82)):    # bogie pair
            s = c + int(off * sr)
            e = min(s + tl, n)
            if s < n:
                x[s:e] += thump[:e - s] * amp * 1.6
        pos += speed
    return _normalize(x, 0.72)


@soundscape("Airplane Cabin")
def _p_cabin(n, sr, rng):
    """Airplane cabin: layered jet thrust, engine beat and air hiss."""
    t = np.arange(n) / sr
    thrust = _xlp(_brown(n, rng), 130, sr) * 1.1
    thrust += _bp(_noise(n, rng), 70, 240, sr) * 0.5
    # cabin air hiss: band-limited and slowly drifting, never a flat
    # white-noise bed (the old 900-6500 Hz band read as radio static)
    hiss = _bp(_noise(n, rng), 900, 4600, sr) * 0.13
    hiss *= _wander(n, sr, rng, lo=0.70, hi=1.0, periods=(25.0, 55.0, 130.0))
    beat = 1.0 + 0.06 * np.sin(2 * np.pi * 11.5 * t) + 0.04 * np.sin(2 * np.pi * 3.7 * t + 1.3)
    return _normalize(thrust * beat + hiss, 0.7)


@soundscape("Lo-Fi Study")
def _p_lofi(n, sr, rng):
    """Lo-fi study loop: warm chord pads floating over soft vinyl crackle."""
    x = _impulses(n, sr, rng, density=7.0, amp=1.0) * 0.16
    x += _xlp(_noise(n, rng), 5000, sr) * 0.02
    chords = [(220.00, 261.63, 329.63, 392.00),   # Am7
              (174.61, 220.00, 261.63, 329.63),   # Fmaj7
              (196.00, 246.94, 293.66, 349.23),   # Gm7
              (164.81, 220.00, 246.94, 329.63)]   # Cmaj7/E
    step = 8.0
    pos, i = 0.0, 0
    while pos < n / sr:
        c = int(pos * sr)
        ln = min(int(step * sr), n - c)
        if ln <= 0:
            break
        tc = np.arange(ln) / sr
        env = np.minimum(1.0, tc / 1.5) * np.minimum(1.0, (ln / sr - tc) / 2.0)
        pad = np.zeros(ln)
        for f in chords[i % len(chords)]:
            vib = 1.0 + 0.004 * np.sin(2 * np.pi * 0.7 * tc + rng.random() * 6.28)
            pad += np.sin(2 * np.pi * f * vib * tc + rng.random() * 6.28)
        x[c:c + ln] += pad / 4.0 * np.maximum(env, 0.0) * 0.16
        pos += step
        i += 1
    return _normalize(x, 0.55)


@soundscape("Space Drone")
def _p_space(n, sr, rng):
    t = np.arange(n) / sr
    drone = (np.sin(2 * np.pi * 55 * t) * 0.5
             + np.sin(2 * np.pi * (55 * 1.007) * t) * 0.5   # slow beat
             + np.sin(2 * np.pi * 110.3 * t) * 0.3
             + np.sin(2 * np.pi * 220.7 * t) * 0.12)
    drone *= _lfo(n, sr, 0.02, phase=1.0, lo=0.55, hi=1.0)
    air = _xlp(_pink(n, rng), 900, sr) * 0.18
    air *= _wander(n, sr, rng, lo=0.55, hi=1.0, periods=(60.0, 130.0, 240.0))
    sparkle = _bp(_noise(n, rng), 3000, 8000, sr) * _lfo(n, sr, 0.11, lo=0.0, hi=0.05)
    return _normalize(drone + air + sparkle, 0.6)


@soundscape("Vinyl Crackle")
def _p_vinyl(n, sr, rng):
    hiss = _xlp(_noise(n, rng), 6000, sr) * 0.05
    crackle = _impulses(n, sr, rng, density=9.0, amp=1.0) * 0.5
    pops = _impulses(n, sr, rng, density=0.35, amp=2.0)
    rumble = _xlp(_brown(n, rng), 90, sr) * 0.25
    return _normalize(hiss + crackle + pops + rumble, 0.55)


@soundscape("Server Room")
def _p_server(n, sr, rng):
    t = np.arange(n) / sr
    hum = (np.sin(2 * np.pi * 120 * t) * 0.4 + np.sin(2 * np.pi * 240 * t) * 0.15)
    fan = _xlp(_brown(n, rng), 350, sr) * 0.9
    hiss = _xlp(_noise(n, rng), 10000, sr) * 0.05
    # faint fan-blade whine drifting with the airflow
    whine = (np.sin(2 * np.pi * 198.0 * t) + 0.5 * np.sin(2 * np.pi * 397.0 * t)) * 0.015
    whine *= _wander(n, sr, rng, lo=0.4, hi=1.0, periods=(30.0, 75.0, 150.0))
    return _normalize(hum + fan + hiss + whine, 0.7)


@soundscape("Brown Noise")
def _p_brown(n, sr, rng):
    x = _xlp(_brown(n, rng), 500, sr)
    return _normalize(x, 0.8)


@soundscape("Quiet Room")
def _p_keyboard_room(n, sr, rng):
    """Lightly reverberant 'empty office' bed: airy noise + distant hum."""
    air = _xlp(_pink(n, rng), 2500, sr) * 0.5
    hum = np.sin(2 * np.pi * 60 * np.arange(n) / sr) * 0.08
    hvac = _bp(_noise(n, rng), 100, 300, sr) * 0.25
    return _normalize(air + hum + hvac, 0.55)


# ------------------------------------------------- zen & pleasant expansion
@soundscape("Bamboo Fountain")
def _p_bamboo_fountain(n, sr, rng):
    """Suikinkutsu: water drips into a buried pot — deep hollow resonant
    dongs under a soft trickle."""
    trickle = _bp(_noise(n, rng), 900, 4200, sr)
    trickle *= _lfo(n, sr, 0.11, phase=rng.random() * 6.28, lo=0.4, hi=0.85)
    x = trickle * 0.30
    x += _xlp(_brown(n, rng), 200, sr) * 0.12          # soil / stone body
    nd = int(1.8 * sr)
    if n > nd * 2:
        td = np.arange(nd) / sr
        for _ in range(max(1, int(n / sr / 4.0))):     # one drip every ~4 s
            f = 196.0 * (1.0 + rng.random() * 0.5)     # pot resonance, low
            dong = np.zeros(nd)
            for mul, amp in ((1.0, 1.0), (2.14, 0.42), (3.01, 0.18), (4.16, 0.08)):
                dong += np.sin(2 * np.pi * f * mul * td) * amp
            s = int(rng.random() * (n - nd))
            x[s:s + nd] += dong * np.exp(-td * 3.2) * (0.16 + rng.random() * 0.10)
    return _normalize(x, 0.6)


@soundscape("Mountain Stream")
def _p_stream(n, sr, rng):
    """Mountain stream: lively babbling brook — chattery bubbles over a
    constant water bed."""
    bed = _bp(_noise(n, rng), 300, 5200, sr)
    x = bed * 0.5 * _wander(n, sr, rng, lo=0.6, hi=1.0, periods=(40.0, 90.0, 180.0))
    x += _xlp(_brown(n, rng), 160, sr) * 0.18
    nb = min(int(0.05 * sr), max(2, n - 2))            # bubble-release chirps
    tb = np.arange(nb) / sr
    for _ in range(int(n / sr * 4.0)):                 # ~4 burbles / s
        f = (500 + rng.random() * 700) * (1.0 + 1.8 * tb / tb[-1])
        ph = 2 * np.pi * np.cumsum(f) / sr
        bl = np.sin(ph) * np.exp(-tb * 45) * (0.10 + rng.random() * 0.16)
        c = int(rng.random() * max(1, n - nb))
        e = min(c + nb, n)
        x[c:e] += bl[:e - c]
    return _normalize(x, 0.68)


@soundscape("Morning Birds")
def _p_morning_birds(n, sr, rng):
    """Morning birdsong over a soft meadow breeze, with a distant cuckoo."""
    breeze = _bp(_noise(n, rng), 200, 1100, sr)
    breeze *= _lfo(n, sr, 0.05, phase=rng.random() * 6.28, lo=0.25, hi=0.6)
    x = breeze * 0.7
    x += 0.05 * _impulses(n, sr, rng, density=2.0, amp=1.0)   # leaves
    nd = int(0.16 * sr)
    td = np.arange(nd) / sr
    for _ in range(int(n / sr * 1.2)):                 # ~1.2 trill groups / s
        if rng.random() < 0.35 or n <= nd * 4:
            continue
        c = int(rng.random() * (n - nd * 4))
        f0 = 2400 + rng.random() * 2900
        for k in range(2 + int(rng.random() * 4)):
            s = c + int(k * (0.06 + rng.random() * 0.06) * sr)
            if s + nd >= n:
                break
            f = f0 * (1.0 + 0.22 * rng.random()) * (1.0 - 0.25 * td / td[-1])
            note = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-td * 30)
            x[s:s + nd] += note * (0.08 + rng.random() * 0.12)
    if n > 8 * sr:                                     # distant cuckoo
        for _ in range(2):
            s = int(n * rng.random() * 0.7)
            for k, ff in ((0, 660.0), (1, 528.0)):     # cu-coo (falling 3rd)
                cs = s + int(k * 0.30 * sr)
                cl = min(int(0.18 * sr), max(2, n - cs - 2))
                if cl <= 2 or cs < 0:
                    continue
                tc = np.arange(cl) / sr
                x[cs:cs + cl] += (np.sin(2 * np.pi * ff * tc)
                                  * np.exp(-tc * 14) * 0.05)
    return _normalize(x, 0.62)


@soundscape("Garden Wind Chimes")
def _p_wind_chimes(n, sr, rng):
    """Garden wind chimes: a carillon of pentatonic chimes drifting on a soft
    breeze."""
    breeze = _bp(_noise(n, rng), 300, 1600, sr)
    breeze *= _lfo(n, sr, 0.07, phase=rng.random() * 6.28, lo=0.2, hi=0.55)
    x = breeze * 0.4
    scale = [659.26, 783.99, 880.0, 1046.5, 1174.7, 1318.5]
    nd = int(3.0 * sr)
    if n > nd * 2:
        td = np.arange(nd) / sr
        for _ in range(max(1, int(n / sr / 3.5))):     # one chime every ~3.5 s
            f = scale[rng.randint(len(scale))]
            chime = np.zeros(nd)
            for mul, amp, dec in ((1.0, 1.0, 1.6), (2.0, 0.28, 2.2),
                                  (2.92, 0.14, 3.0), (4.5, 0.06, 4.0)):
                chime += np.sin(2 * np.pi * f * mul * td + rng.random() * 6.28) * amp * np.exp(-td * dec)
            s = int(rng.random() * (n - nd))
            x[s:s + nd] += chime * (0.10 + rng.random() * 0.09)
            if rng.random() < 0.35:                    # a second clapper, close by
                s2 = min(n - nd, s + int((0.12 + rng.random() * 0.2) * sr))
                f2 = scale[rng.randint(len(scale))]
                x[s2:s2 + nd] += np.sin(2 * np.pi * f2 * td) * np.exp(-td * 1.9) * 0.07
    return _normalize(x, 0.58)


@soundscape("Singing Bowls")
def _p_singing_bowls(n, sr, rng):
    """Singing bowls: slowly swelling metal harmonics over a warm drone."""
    t = np.arange(n) / sr
    drone = (np.sin(2 * np.pi * 98 * t) * 0.35
             + np.sin(2 * np.pi * 147.2 * t) * 0.18)
    drone *= _lfo(n, sr, 0.018, phase=rng.random() * 6.28, lo=0.5, hi=1.0)
    x = drone
    bowl_len = int(7.0 * sr)
    if n > bowl_len * 2:
        tb = np.arange(bowl_len) / sr
        for _ in range(max(1, int(n / sr / 11.0))):    # one bowl every ~11 s
            f = 214.0 * (1.0 + rng.choice([-1, 1]) * rng.random() * 0.06)
            bowl = np.zeros(bowl_len)
            for mul, amp in ((1.0, 1.0), (2.71, 0.35), (4.83, 0.14), (7.6, 0.05)):
                bowl += np.sin(2 * np.pi * f * mul * tb + rng.random() * 6.28) * amp
            bowl *= np.minimum(1.0, tb / 2.5) * np.exp(-tb * 0.35)   # slow swell
            s = int(rng.random() * (n - bowl_len))
            x[s:s + bowl_len] += bowl * 0.22
    air = _xlp(_pink(n, rng), 800, sr) * 0.06
    return _normalize(x + air, 0.6)


@soundscape("Hot Spring")
def _p_hot_spring(n, sr, rng):
    """Onsen: soft bubbling water, gentle steam hiss, rare wooden bucket knock."""
    water = _bp(_noise(n, rng), 250, 1800, sr)
    x = water * 0.45 * _lfo(n, sr, 0.08, phase=rng.random() * 6.28, lo=0.5, hi=0.9)
    x += _xlp(_brown(n, rng), 180, sr) * 0.2           # pool depth
    x += _hp(_noise(n, rng), 4000, sr) * _lfo(n, sr, 0.05, phase=rng.random() * 6.28,
                                              lo=0.0, hi=0.06)
    nb = min(int(0.035 * sr), max(2, n - 2))           # water blups
    tb = np.arange(nb) / sr
    for _ in range(int(n / sr * 6.0)):                 # ~6 blups / s
        f = (300 + rng.random() * 500) * (1.0 + 1.4 * tb / tb[-1])
        ph = 2 * np.pi * np.cumsum(f) / sr
        bl = np.sin(ph) * np.exp(-tb * 60) * (0.06 + rng.random() * 0.10)
        c = int(rng.random() * max(1, n - nb))
        e = min(c + nb, n)
        x[c:e] += bl[:e - c]
    if n > 10 * sr:                                    # rare bucket knock
        for _ in range(max(1, int(n / sr / 22.0))):
            kl = min(int(0.09 * sr), max(2, n - 2))
            tk = np.arange(kl) / sr
            knock = (np.sin(2 * np.pi * 820 * tk) * np.exp(-tk * 55)
                     + 0.4 * np.sin(2 * np.pi * 1380 * tk) * np.exp(-tk * 80))
            s = int(rng.random() * max(1, n - kl))
            x[s:s + kl] += knock * 0.08
    return _normalize(x, 0.65)


@soundscape("Rice Field Dusk")
def _p_frog_pond(n, sr, rng):
    """Rice field dusk: gentle frog chorus and crickets in warm evening air."""
    x = _xlp(_pink(n, rng), 1000, sr) * 0.10 + _bp(_noise(n, rng), 200, 900, sr) * 0.10
    for _ in range(max(1, int(n / sr / 2.5))):         # one croak every ~2.5 s
        cl = min(int((0.35 + rng.random() * 0.2) * sr), max(2, n - 2))
        tc = np.arange(cl) / sr
        f0 = 380 + rng.random() * 240
        rate = 18 + rng.random() * 12
        pulse = np.maximum(0.0, np.sin(2 * np.pi * rate * tc))    # smooth AM croak
        croak = np.sin(2 * np.pi * f0 * tc) * (0.45 + 0.55 * pulse)
        croak *= np.minimum(1.0, tc / 0.05) * np.minimum(1.0, (cl / sr - tc) / 0.08)
        s = int(rng.random() * max(1, n - cl))
        e = min(s + cl, n)
        x[s:e] += croak[:e - s] * (0.14 + rng.random() * 0.10)
    carrier = 4200 + rng.random() * 600                # crickets, quieter
    cd = min(int(0.03 * sr), max(2, n - 2))
    tcr = np.arange(cd) / sr
    unit = np.sin(2 * np.pi * carrier * tcr) * np.exp(-tcr * 70)
    pos = 0.0
    while pos < n / sr:
        c = int(pos * sr)
        for k in range(2 + int(rng.random() * 2)):
            s = c + int(k * 0.075 * sr)
            if s + cd >= n:
                break
            x[s:s + cd] += unit * (0.10 + rng.random() * 0.08)
        pos += 0.6 + rng.random() * 1.1
    return _normalize(x, 0.6)


# ------------------------------------------------------------------ wave 3
# v1.0 expansion: storm / immersion / season beds requested for the
# professional pack.  Same rules as above: deterministic per seed, fully
# vectorised, built from the shared helper vocabulary.
@soundscape("Blizzard")
def _p_blizzard(n, sr, rng):
    """Blizzard: howling layered wind, gusts that come and go, snow hiss."""
    # core wind: stacked band-passed layers with drifting centres
    x = _bp(_noise(n, rng), 120, 700, sr) * 0.55
    x += (_bp(_noise(n, rng), 400, 1800, sr)
          * _wander(n, sr, rng, 0.30, 1.0, (22.0, 57.0, 131.0)) * 0.30)
    howl = _bp(_noise(n, rng), 300, 900, sr)
    howl *= _lfo(n, sr, 0.09, phase=rng.random() * 6.28, lo=0.0, hi=0.5)
    x += howl * 0.35
    # violent gusts sweeping through
    gust_t = rng.uniform(1.0, 4.0)
    while gust_t < n / sr:
        c = int(gust_t * sr)
        ln = min(int((1.5 + rng.random() * 2.5) * sr), n - c)
        if ln <= 0:
            break
        env = np.sin(np.linspace(0, np.pi, ln)) ** 2
        x[c:c + ln] += env * _bp(_noise(ln, rng), 200, 2200, sr) * 0.9
        gust_t += 4 + rng.random() * 9
    # fine snow hiss riding on top
    x += (_hp(_noise(n, rng), 5500, sr)
          * _lfo(n, sr, 0.06, phase=rng.random() * 6.28, lo=0.02, hi=0.10))
    return _normalize(x, 0.78)


@soundscape("Underwater")
def _p_underwater(n, sr, rng):
    """Underwater: deep pressure hum, muffled current, streams of bubbles."""
    t = np.arange(n) / sr
    x = (np.sin(2 * np.pi * 46 * t + rng.random() * 6.28) * 0.30
         + np.sin(2 * np.pi * 61.7 * t) * 0.16)
    x *= _lfo(n, sr, 0.05, phase=rng.random() * 6.28, lo=0.6, hi=1.0)
    x += (_xlp(_noise(n, rng), 240, sr)
          * _wander(n, sr, rng, 0.40, 0.90, (30.0, 77.0, 168.0)) * 0.28)
    # bubble streams: short bursts of rising pitch blips
    bl = min(int(0.06 * sr), max(2, n - 2))
    tb = np.arange(bl) / sr
    tpos = 0.0
    while tpos < n / sr:
        stream_len = 0.4 + rng.random() * 1.2
        rate = 10 + rng.random() * 14
        base = 380 + rng.random() * 420
        c0 = int(tpos * sr)
        for k in range(int(stream_len * rate)):
            c = c0 + int(k / rate * sr)
            if c + bl >= n:
                break
            f = (base + rng.random() * 500) * (1.0 + 2.2 * tb / tb[-1])
            ph = 2 * np.pi * np.cumsum(f) / sr
            x[c:c + bl] += np.sin(ph) * np.exp(-tb * 40) * (0.05 + rng.random() * 0.09)
        tpos += stream_len + 1.0 + rng.random() * 3.0
    return _normalize(x, 0.62)


@soundscape("Cathedral Hall")
def _p_cathedral(n, sr, rng):
    """Cathedral: vast airy hall drone with slow organ swells and stone echoes."""
    t = np.arange(n) / sr
    drone = (np.sin(2 * np.pi * 65.4 * t) * 0.30
             + np.sin(2 * np.pi * 98.0 * t) * 0.18
             + np.sin(2 * np.pi * 130.8 * t) * 0.10)
    drone *= _lfo(n, sr, 0.015, phase=rng.random() * 6.28, lo=0.45, hi=0.9)
    x = drone * 0.8
    x += (_xlp(_pink(n, rng), 900, sr)
          * _lfo(n, sr, 0.03, phase=rng.random() * 6.28, lo=0.10, hi=0.30))
    # distant organ chords: additive partials with very slow attack/release
    organ_len = int(9.0 * sr)
    if n > organ_len * 2:
        to = np.arange(organ_len) / sr
        for _ in range(max(1, int(n / sr / 14.0))):
            root = 130.8 * (1.0 + rng.choice([-1, 1]) * rng.random() * 0.02)
            chord = np.zeros(organ_len)
            for f in (root, root * 1.26, root * 1.5, root * 2.0):
                chord += np.sin(2 * np.pi * f * to + rng.random() * 6.28)
            env = (np.minimum(1.0, to / 4.5)
                   * np.minimum(1.0, (organ_len / sr - to) / 4.5))
            s = int(rng.random() * (n - organ_len))
            x[s:s + organ_len] += chord * env * 0.08
    # sparse stone echoes: soft taps with long cathedral decays
    el = min(int(1.8 * sr), max(2, n - 2))
    te = np.arange(el) / sr
    for _ in range(max(1, int(n / sr / 9.0))):
        s = int(rng.random() * max(1, n - el))
        x[s:s + el] += (np.sin(2 * np.pi * (180 + rng.random() * 80) * te)
                        * np.exp(-te * 3.2) * 0.05)
    return _normalize(x, 0.55)


@soundscape("Car Ride Rain")
def _p_car_rain(n, sr, rng):
    """Car ride in the rain: roof patter through the glass, tyre hum, wipers."""
    x = _xlp(_p_rain(n, sr, rng), 2600, sr) * 0.9
    x += (_xlp(_brown(n, rng), 140, sr)
          * _lfo(n, sr, 0.04, phase=rng.random() * 6.28, lo=0.7, hi=1.0) * 0.4)
    # wiper swish every few seconds: a broad band noise arc
    wl = min(int(0.9 * sr), max(2, n - 2))
    tw = np.arange(wl) / sr
    pos = rng.uniform(0.5, 2.0)
    while pos < n / sr:
        s = int(pos * sr)
        e = min(s + wl, n)
        seg = e - s
        if seg <= 2:
            break
        swish = (_bp(_noise(seg, rng), 500, 3400, sr)
                 * np.sin(np.pi * tw[:seg] / max(wl / sr, 1e-6)) ** 2)
        x[s:e] += swish * 0.30
        pos += 3.0 + rng.random() * 1.2
    return _normalize(x, 0.72)


@soundscape("Cicada Swarm")
def _p_cicada(n, sr, rng):
    """Summer noon: dense cicada buzz swelling over warm, dry air."""
    # 3.4-4.2 kHz carriers sit in the natural cicada range; the old
    # 5.2-6.1 kHz carriers (band-limited up to 8.6 kHz) were ear-piercing
    carrier = 3400 + rng.random() * 800
    t = np.arange(n) / sr
    buzz = (np.sin(2 * np.pi * carrier * t)
            * (0.5 + 0.5 * np.sin(2 * np.pi * 86 * t + rng.random() * 6.28)))
    x = _bp(buzz, 2200, 6400, sr) * _wander(n, sr, rng, 0.15, 0.75, (9.0, 23.0, 61.0))
    b2 = (np.sin(2 * np.pi * carrier * 1.07 * t)
          * (0.5 + 0.5 * np.sin(2 * np.pi * 63 * t + rng.random() * 6.28)))
    x += _bp(b2, 2500, 6800, sr) * _wander(n, sr, rng, 0.05, 0.45, (13.0, 31.0, 83.0))
    x += _bp(_noise(n, rng), 200, 900, sr) * 0.12          # hot still air
    for _ in range(max(1, int(n / sr / 6.0))):             # dry leaf rustles
        rl = min(int(0.35 * sr), max(2, n - 2))
        tr = np.arange(rl) / sr
        rustle = _bp(_noise(rl, rng), 1200, 5200, sr) * np.exp(-tr * 9)
        s = int(rng.random() * max(1, n - rl))
        x[s:s + rl] += rustle * (0.10 + rng.random() * 0.08)
    return _normalize(x, 0.62)


@soundscape("Autumn Leaves")
def _p_autumn_leaves(n, sr, rng):
    """Autumn park: dry leaves crunching and drifting on a cool breeze."""
    breeze = _bp(_noise(n, rng), 150, 800, sr) * _lfo(n, sr, 0.06,
                                                      phase=rng.random() * 6.28,
                                                      lo=0.15, hi=0.4)
    x = breeze * 0.55
    # dense dry crackle: crisp impulses in a woody band
    crack = _impulses(n, sr, rng, density=26.0, amp=1.0)
    x += _bp(crack, 800, 5200, sr) * _wander(n, sr, rng, 0.25, 1.0,
                                             (17.0, 43.0, 97.0)) * 0.5
    # leaf flurries: short rustle clouds
    pos = 0.5 + rng.random()
    while pos < n / sr:
        rl = min(int((0.5 + rng.random() * 0.8) * sr), max(2, n - 2))
        tr = np.arange(rl) / sr
        cloud = (_bp(_noise(rl, rng), 700, 4200, sr)
                 * np.sin(np.pi * tr / max(tr[-1], 1e-6)) ** 2)
        s = int(pos * sr)
        e = min(s + rl, n)
        x[s:e] += cloud[:e - s] * (0.30 + rng.random() * 0.25)
        pos += 2.5 + rng.random() * 5.0
    return _normalize(x, 0.68)



def _anchor_bed_loudness(x: np.ndarray, sr: int) -> np.ndarray:
    """Loudness-anchor a bed to :data:`BED_TARGET_LUFS` with *dynamic* peak
    control.  Deterministic.

    The DC block is *not* done here: it must run before the edge fades, or
    subtracting the mean after the fade turns the faded-to-zero tail back
    into a constant pedestal.

    v1.0.3: peak control is a lookahead true-peak limiter iterated with the
    loudness gain, exactly like the keystroke master chain.  The old order
    (anchor gain, then scale-only peak caps) was self-defeating on
    impulsive beds: Fireplace's crackle bed has ~36 dB of crest, the +24 dB
    anchor pushed pops to +12 dBFS, the scale cap pulled everything back
    down and the bed landed at -29 LUFS — 13 dB under the slider's promise
    (v1.0.2 could not see this: the corrupted K-weight filter read every
    bed as if it were on target).  Limiting the pops instead keeps the
    anchored loudness AND the peaks safe; the crackle character survives
    (its room tone comes up, its pops are shaved, as any broadcast bed is).
    """
    if len(x) < int(0.5 * sr):
        return x
    x = np.asarray(x, dtype=np.float64)
    lim = TruePeakLimiterStage(ceiling_dbtp=BED_TP_CEILING_DBTP,
                               release_ms=60.0, lookahead_ms=1.5)
    for _ in range(BED_ANCHOR_PASSES):
        cl = _measure_lufs(x, sr)
        if not np.isfinite(cl) or cl <= -60.0:
            break
        x = x * (10.0 ** ((BED_TARGET_LUFS - cl) / 20.0))
        x = lim.process(x, sr)
        cl2 = _measure_lufs(x, sr)
        if np.isfinite(cl2) and abs(cl2 - BED_TARGET_LUFS) < 0.5:
            break
    # backstop: the limiter's rate-limited attack can leave ~0.2 dB of
    # reconstruction overshoot — trim it scale-only so beds are guaranteed
    # <= -1.05 dBTP no matter how impulsive they are
    x = TruePeakStage(ceiling_dbtp=TP_BACKSTOP_DBTP).process(x, sr)
    return x


# ==========================================================================
# ── MUSIC — a procedural music layer under EVERY background bed
#
#    Every soundscape can now carry a generated soundtrack: a Registry of
#    :class:`MusicProfile` objects (one per preset, keyed by soundscape
#    name) describes key, chord progression, tempo, voices and tone; five
#    synthesised voices (pad / keys / pluck / bell / bass) are scheduled on
#    a humanised grid and glued by a multi-tap delay.  Everything is
#    deterministic, 100% generated and royalty-free — safe for YouTube —
#    and the whole bus is loudness-anchored to a fixed internal level so
#    every preset mixes at the same perceived loudness.
#
#    Patterns: block | sparse | poly | arp | arp_ud | sway | chimes
# ==========================================================================

_MUSIC_RMS: Final[float] = 0.05        # internal music RMS at volume=1.0
MUSIC_SEED_OFFSET: Final[int] = 1013   # music rng derives from bed seed

_CHORD_TYPES: Final[Dict[str, Tuple[int, ...]]] = {
    "M": (0, 4, 7), "m": (0, 3, 7),
    "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11),
    "9": (0, 4, 7, 10, 14), "m9": (0, 3, 7, 10, 14), "maj9": (0, 4, 7, 11, 14),
    "add9": (0, 4, 7, 14), "madd9": (0, 3, 7, 14),
    "sus2": (0, 2, 7), "sus4": (0, 5, 7),
    "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9),
    "5": (0, 7),
}


@dataclass(frozen=True)
class MusicProfile:
    """Musical identity of one soundscape (Strategy pattern, like the
    soundscape beds themselves).  ``root`` is a note name (e.g. ``"A2"``);
    ``prog`` is a tuple of ``(semitone offset from root, chord type)``;
    voice weights (pad/keys/pluck/bell/bass) are 0 = silent."""
    root: str = "A2"
    prog: Tuple[Tuple[int, str], ...] = ((0, "madd9"), (8, "maj7"),
                                         (3, "maj7"), (10, "sus2"))
    bpm: float = 50.0
    chord_bars: int = 2
    pattern: str = "sparse"
    pad: float = 0.45
    pad_cut: float = 1400.0
    keys: float = 0.40
    pluck: float = 0.0
    bell: float = 0.0
    bass: float = 0.18
    tone: float = 3000.0            # master bus low-pass (tape/air control)
    arp_oct: int = 1                # octaves the arpeggio may climb
    swing: float = 0.0              # 0..0.35: off-8th delay (lo-fi feel)
    reverb: float = 0.55            # multi-tap glue send


def _note_hz(name: str) -> float:
    """``"A2"`` -> 110 Hz (12-TET, A4 = 440).  No regex: fixed shape."""
    s = name.strip()
    semi = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    i = 1
    if len(s) > 1 and s[1] in "#b":
        semi[s[0]] += 1 if s[1] == "#" else -1
        i = 2
    octave = int(s[i:])
    midi = (octave + 1) * 12 + semi[s[0]]
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


# ------------------------------------------------------------------ voices
def _note_tail_fade(env: np.ndarray, sr: int, frac: float = 0.30,
                    max_s: float = 0.06) -> np.ndarray:
    """Smooth a scheduled note's hard truncation to zero (raised cosine).

    Notes are cut at ``n = min(dur, k*decay)`` samples while their natural
    exponential decay is still audible (a 2 s felt-piano note with a 4 s
    decay is chopped at ~60 % amplitude) — that hard cut adds a tick on
    every note, which stacked across the music bus reads as crackle.
    """
    m = int(min(max_s, len(env) / sr * frac) * sr)
    if m <= 0:
        return env
    m = min(m, len(env))
    env[-m:] *= 0.5 * (1.0 + np.cos(np.linspace(0.0, np.pi, m)))
    return env


def _nv_pad(buf, sr, t0, f, dur, amp, rng):
    """Slow swelling pad: two detuned layers x 3 partials, sine envelope."""
    s0 = max(0, int(t0 * sr))
    s1 = min(len(buf), s0 + int(dur * sr))
    if s1 <= s0:
        return
    t = np.arange(s1 - s0) / sr
    sig = np.zeros(s1 - s0)
    for det, g in ((0.9985 + rng.random() * 0.0012, 1.0),
                   (1.0015 + rng.random() * 0.0012, 0.85)):
        for k, kg in ((1, 1.0), (2, 0.40), (3, 0.14)):
            fk = f * det * k
            if fk > 0.45 * sr:
                continue
            sig += g * kg * np.sin(2 * np.pi * fk * t + rng.random() * 6.28318)
    buf[s0:s1] += sig * np.sin(np.pi * t / dur) ** 0.8 * amp * 0.30


def _nv_keys(buf, sr, t0, f, dur, amp, rng):
    """Felt-piano: 5 slightly inharmonic partials, soft 8 ms attack."""
    decay = float(np.clip(2.8 * (220.0 / f) ** 0.35, 0.7, 4.2))
    n = int(min(dur, 3.6 * decay) * sr)
    s0 = max(0, int(t0 * sr))
    s1 = min(len(buf), s0 + n)
    if s1 <= s0:
        return
    t = np.arange(s1 - s0) / sr
    sig = np.zeros(s1 - s0)
    for k, kg in ((1, 1.0), (2, 0.50), (3, 0.26), (4, 0.13), (5, 0.06)):
        fk = f * k * np.sqrt(1.0 + 1.2e-4 * k * k)   # real-string stretch
        sig += kg * np.sin(2 * np.pi * fk * t + rng.random() * 6.28318)
    att = min(0.008, dur)
    env = _note_tail_fade(np.exp(-t / decay) * np.minimum(t / att, 1.0), sr)
    buf[s0:s1] += sig * env * amp * 0.28


def _nv_pluck(buf, sr, t0, f, dur, amp, rng):
    """Nylon/marimba pluck: bright transient, fast harmonic decay."""
    decay = float(np.clip(0.55 * (220.0 / f) ** 0.40, 0.16, 1.2))
    n = int(min(dur, 2.5 * decay) * sr)
    s0 = max(0, int(t0 * sr))
    s1 = min(len(buf), s0 + n)
    if s1 <= s0:
        return
    t = np.arange(s1 - s0) / sr
    sig = np.zeros(s1 - s0)
    for k, kg in ((1, 1.0), (2, 0.42), (3, 0.15), (4, 0.05)):
        sig += kg * np.sin(2 * np.pi * f * k * t + rng.random() * 6.28318)
    att = max(0.002, 0.012 * (220.0 / f))
    env = _note_tail_fade(
        np.exp(-t / decay) * np.sin(np.pi * np.minimum(t / att, 1.0) / 2), sr)
    buf[s0:s1] += sig * env * amp * 0.30


def _nv_bell(buf, sr, t0, f, dur, amp, rng):
    """Bell/music-box: inharmonic partial 2.76f, long shimmer decay."""
    decay = float(np.clip(1.9 * (220.0 / f) ** 0.35, 0.45, 3.8))
    n = int(min(dur, 3.0 * decay) * sr)
    s0 = max(0, int(t0 * sr))
    s1 = min(len(buf), s0 + n)
    if s1 <= s0:
        return
    t = np.arange(s1 - s0) / sr
    sig = (np.sin(2 * np.pi * f * t + rng.random() * 6.28318)
           + 0.32 * np.sin(2 * np.pi * f * 2.76 * t + rng.random() * 6.28318)
           + 0.10 * np.sin(2 * np.pi * f * 5.40 * t + rng.random() * 6.28318))
    env = _note_tail_fade(np.exp(-t / decay) * np.minimum(t / 0.003, 1.0), sr)
    buf[s0:s1] += sig * env * amp * 0.30


def _nv_bass(buf, sr, t0, f, dur, amp, rng):
    """Sub bass: sine + a whisper of 2nd partial, gentle release."""
    s0 = max(0, int(t0 * sr))
    s1 = min(len(buf), s0 + int(dur * sr))
    if s1 <= s0:
        return
    t = np.arange(s1 - s0) / sr
    rel = 0.30 * dur
    env = (np.minimum(t / 0.04, 1.0)
           * (1.0 - np.clip((t - (dur - rel)) / rel, 0.0, 1.0)) ** 1.5)
    sig = (np.sin(2 * np.pi * f * t + rng.random() * 6.28318)
           + 0.18 * np.sin(2 * np.pi * f * 2 * t + rng.random() * 6.28318))
    buf[s0:s1] += sig * env * amp * 0.34


# ------------------------------------------------------------------ patterns
# All patterns share one signature: (buf, pad, prof, freqs, t0, slot, sr,
# rng, beat) — the last parameter is unused by the a-metrical ones (block,
# chimes) but keeps the dispatcher uniform.
def _pattern_block(buf, pad, prof, freqs, t0, slot, sr, rng, beat=0.0):
    """Sustained chords: pad swells, soft bass, optional rolled keys hit."""
    for fi, f in enumerate(freqs[:4]):
        _nv_pad(pad, sr, t0, f, slot * 1.05, prof.pad, rng)
        if prof.keys > 0:                        # gentle roll at chord start
            _nv_keys(buf, sr, t0 + fi * 0.045, f * 2, slot * 0.62,
                     prof.keys * 0.55, rng)
    if prof.bass > 0:
        fb = freqs[0] * 0.5
        _nv_bass(buf, sr, t0, fb if fb >= 45 else fb * 2, slot * 0.95,
                 prof.bass, rng)
    if prof.bell > 0 and rng.random() < 0.55:
        f = rng.choice(freqs) * 2
        _nv_bell(buf, sr, t0 + rng.random() * slot * 0.7, f, slot, prof.bell * 0.5, rng)


def _pattern_sparse(buf, pad, prof, freqs, t0, slot, sr, rng, beat):
    """Random chord-tone notes on a quarter grid; calm, breathing."""
    for fi, f in enumerate(freqs[:4]):
        _nv_pad(pad, sr, t0, f, slot * 1.02, prof.pad * 0.8, rng)
    lead = prof.keys if prof.keys >= prof.pluck else prof.pluck
    _vf = _nv_keys if prof.keys >= prof.pluck else _nv_pluck
    b = 0.0
    while b < slot - 0.1:
        if rng.random() < 0.42:
            f = rng.choice(freqs) * (2 if rng.random() < 0.35 else 1)
            _vf(buf, sr, t0 + b + rng.uniform(-0.02, 0.02), f, beat * 1.7,
                lead * (0.7 + 0.3 * rng.random()), rng)
        b += beat
    if prof.bass > 0:
        fb = freqs[0] * 0.5
        _nv_bass(buf, sr, t0, fb if fb >= 45 else fb * 2, slot * 0.9,
                 prof.bass, rng)


def _pattern_poly(buf, pad, prof, freqs, t0, slot, sr, rng, beat):
    """Interlocking 8th-note ostinato (koto / gamelan / synth feel)."""
    seq = (0, 2, 1, 3, 0, 2, 3, 2)
    nf = len(freqs)
    for fi, f in enumerate(freqs[: max(2, nf - 1)]):
        _nv_pad(pad, sr, t0, f, slot * 1.02, prof.pad * 0.6, rng)
    i = 0
    while i * 0.5 * beat < slot - 0.05:
        idx = seq[i % len(seq)]
        f = freqs[idx % nf] * (2 if idx >= nf else 1)
        swing = prof.swing * 0.5 * beat if i % 2 else 0.0
        _nv_pluck(buf, sr, t0 + i * 0.5 * beat + swing + rng.uniform(-0.012, 0.012),
                  f, beat * 1.4, prof.pluck * (0.7 + 0.3 * rng.random()), rng)
        i += 1
    if prof.bell > 0 and rng.random() < 0.4:
        _nv_bell(buf, sr, t0 + rng.random() * slot * 0.8, freqs[-1] * 4,
                 slot * 0.8, prof.bell * 0.45, rng)
    if prof.bass > 0:
        fb = freqs[0] * 0.5
        for b in (0.0, 2.0 * beat):
            if b < slot - 0.1:
                _nv_bass(buf, sr, t0 + b, fb if fb >= 45 else fb * 2,
                         beat * 1.6, prof.bass, rng)


def _pattern_arp(buf, pad, prof, freqs, t0, slot, sr, rng, beat, updown=False):
    """8th-note arpeggio climbing (or up-down) through the chord."""
    seq = list(freqs) + [f * 2 for f in freqs[: max(1, prof.arp_oct)]]
    if updown:
        seq = seq + seq[-2:0:-1]
    pad_f = freqs[0]
    _nv_pad(pad, sr, t0, pad_f, slot * 1.05, prof.pad, rng)
    lead = max(prof.pluck, prof.keys * 0.8)
    _vf = _nv_pluck if prof.pluck >= prof.keys else _nv_keys
    i = 0
    while i * 0.5 * beat < slot - 0.05:
        swing = prof.swing * 0.5 * beat if i % 2 else 0.0
        _vf(buf, sr, t0 + i * 0.5 * beat + swing + rng.uniform(-0.012, 0.012),
            seq[i % len(seq)], beat * 1.5,
            lead * (0.68 + 0.32 * rng.random()), rng)
        i += 1
    if prof.bass > 0:
        fb = freqs[0] * 0.5
        for b, f in ((0.0, fb), (0.5 * slot, freqs[-1] * 0.5 if len(freqs) > 1 else fb)):
            if b < slot - 0.1:
                _nv_bass(buf, sr, t0 + b, f * 2 if f < 45 else f,
                         beat * 1.7, prof.bass, rng)


def _pattern_sway(buf, pad, prof, freqs, t0, slot, sr, rng, beat):
    """Lo-fi jazz sway: rolled chord on 1, swung pickup before beat 3."""
    for fi, f in enumerate(freqs[:4]):
        _nv_pad(pad, sr, t0, f, slot * 1.02, prof.pad * 0.5, rng)
        if prof.keys > 0:
            _nv_keys(buf, sr, t0 + fi * 0.05, f * 2, beat * 2.4,
                     prof.keys * 0.6, rng)
    pick_t = t0 + (3.0 + prof.swing) * 0.5 * beat      # last 8th before 3
    if prof.keys > 0 and pick_t < t0 + slot - 0.05:
        _nv_keys(buf, sr, pick_t, freqs[-1] * 4, beat * 1.2,
                 prof.keys * 0.35, rng)
    if prof.bass > 0:
        fb = freqs[0] * 0.5
        for b, f in ((0.0, fb), (2.0 * beat, freqs[1] * 0.5 if len(freqs) > 1 else fb)):
            _nv_bass(buf, sr, t0 + b, f * 2 if f < 45 else f,
                     beat * 1.8, prof.bass, rng)
    if prof.bell > 0 and rng.random() < 0.25:
        _nv_bell(buf, sr, t0 + rng.random() * slot * 0.6, rng.choice(freqs) * 4,
                 slot * 0.7, prof.bell * 0.4, rng)


def _pattern_chimes(buf, pad, prof, freqs, t0, slot, sr, rng, beat=0.0):
    """Wind-chime clusters: pad wash + randomised bell clusters."""
    for fi, f in enumerate(freqs[:4]):
        _nv_pad(pad, sr, t0, f, slot * 1.02, prof.pad * 0.7, rng)
    if prof.bell <= 0:
        return
    n_ev = max(1, int(slot * rng.uniform(0.9, 1.6)))
    for _ in range(n_ev):
        tc = t0 + rng.random() * slot
        for k in range(rng.integers(1, 4) if hasattr(rng, "integers") else int(1 + rng.random() * 3)):
            f = rng.choice(freqs) * (4 if rng.random() < 0.5 else 2)
            _nv_bell(buf, sr, tc + k * rng.uniform(0.05, 0.16), f,
                     rng.uniform(1.4, 2.8), prof.bell * (0.4 + 0.6 * rng.random()), rng)


_PATTERNS: Final[Dict[str, Callable]] = {
    "block": _pattern_block,
    "sparse": _pattern_sparse,
    "poly": _pattern_poly,
    "arp": partial(_pattern_arp, updown=False),
    "arp_ud": partial(_pattern_arp, updown=True),
    "sway": _pattern_sway,
    "chimes": _pattern_chimes,
}


def _music_glue(x: np.ndarray, sr: int, send: float) -> np.ndarray:
    """Multi-tap echo glue: three decaying, low-passed taps behind the dry
    signal — a room around the notes without a real reverb's cost."""
    if send <= 0:
        return x
    n = len(x)
    out = x.copy()
    for k, tp in enumerate((0.287, 0.431, 0.613)):
        d = int(tp * sr)
        if d >= n - 8:
            break
        tap = np.zeros(n)
        tap[d:] = x[:n - d]
        out += _xlp(tap, 4200.0, sr, 63) * (0.30 * send * (0.72 ** k))
    return out


def _voice_chord(freqs: List[float], low_hz: float = 130.8,
                 blend_hz: float = 300.0) -> List[float]:
    """Open-voicing pass for one chord (v1.0.3).

    Pads built straight from the chord offsets stack 3rds right on top of a
    low root: a D-rooted sus2 puts D3/E3 within 100 Hz of each other, and
    two tones that close beat against each other for the whole chord — the
    muddy, detuned "organ in a tunnel" sound.  Real arrangers voice a pad
    *above* the root: fold every tone into [C3, ~C6], then lift upper tones
    an octave whenever a low pair sits closer than ~3 semitones inside the
    blend region (below ``blend_hz``), where detuned pads beat hardest.
    The bass voice keeps the un-voiced root (see :func:`build_music_bed`),
    so the harmonic foundation is unchanged.
    """
    v = []
    for f in freqs:
        f2 = float(f)
        while f2 < low_hz:
            f2 *= 2.0
        while f2 > 8.0 * low_hz:                 # ceiling ≈ C6
            f2 *= 0.5
        v.append(f2)
    v.sort()
    # build upward: a tone may only move UP an octave — either because it
    # sits too close below 300 Hz to the previous kept tone (beating) or
    # because an earlier lift pushed the running voice above it (ordering) —
    # so the output is non-decreasing AND de-clustered by construction
    out: List[float] = []
    for f in v:
        while out and (f < out[-1]
                       or (out[-1] < blend_hz and f / out[-1] < 1.20)):
            f *= 2.0
        out.append(f)
    return out


def build_music_bed(preset: str, duration: float, sr: int = AUDIO_SAMPLE_RATE,
                    seed: int = 7, volume: float = 1.0) -> np.ndarray:
    """Render the procedural music layer for one soundscape.

    Mono float64, length ``duration * sr``, loudness anchored to
    :data:`_MUSIC_RMS` * ``volume``.  Deterministic for
    ``(preset, duration, sr, seed)``; every preset in
    :data:`AMBIENCE_PRESETS` has a profile in :data:`MUSIC_PROFILES`.
    """
    n = max(1, int(duration * sr))
    prof = MUSIC_PROFILES.get(preset, MusicProfile())
    rng = np.random.RandomState((int(seed) + MUSIC_SEED_OFFSET) % (2 ** 31))
    buf = np.zeros(n)
    pad_buf = np.zeros(n)
    beat = 60.0 / max(1.0, prof.bpm)
    slot = max(1, prof.chord_bars) * 4.0 * beat
    root_f = _note_hz(prof.root)
    pat_fn = _PATTERNS.get(prof.pattern, _pattern_sparse)
    t = 0.0
    ci = 0
    while t < duration - 0.05:
        off, ctype = prof.prog[ci % len(prof.prog)]
        tones = _CHORD_TYPES.get(ctype, _CHORD_TYPES["m7"])
        raw_freqs = [root_f * 2.0 ** ((off + st) / 12.0) for st in tones]
        # v1.0.3: open voicing for the pad/lead voices — folds the chord
        # into [C3, C6] and de-clusters low pairs so the detuned pad stops
        # beating; the bass stays on the raw root one octave down.
        freqs = _voice_chord(raw_freqs)
        slot_n = min(slot, duration - t)
        pat_fn(buf, pad_buf, prof, freqs, t, slot_n, sr, rng, beat)
        ci += 1
        t += slot
    # bus colour: dark pad bus + master tone, then echo glue
    x = _xlp(buf + _xlp(pad_buf, prof.pad_cut, sr, 63), prof.tone, sr, 63)
    # v1.0.3: infrasonic block — slow pad/bass envelope shapes leak a DC-ish
    # drift that stacks under the texture bed's own low end; 40 Hz keeps the
    # foundation and only removes the drift.
    x = DSP.filt_hp(x, 40.0, sr, 511)
    x = _music_glue(x, sr, prof.reverb)
    _fade_edges(x, sr,
                fade_in=min(1.5, max(0.05, duration * 0.2)),
                fade_out=min(1.0, max(0.05, duration * 0.15)))
    rms = float(np.sqrt(np.mean(x * x))) if len(x) else 0.0
    if rms > 1e-9:
        x *= (_MUSIC_RMS * float(np.clip(volume, 0.0, 4.0))) / rms
    pk = float(np.max(np.abs(x))) if len(x) else 0.0
    if pk > 0.95:
        x *= 0.95 / pk
    return x


def mix_music_into_bed(bed: np.ndarray, preset: str, duration: float, sr: int,
                       seed: int = 7, volume: float = 1.0) -> np.ndarray:
    """Add the music layer to a texture bed, keeping the fixed bed loudness.

    The combined bed is re-anchored to :data:`BED_TARGET_LUFS`, so the
    ``Ambience Vol`` slider means the same thing with music on or off —
    the music simply trades a little texture headroom for itself, which
    is exactly how a broadcast bed is mastered.
    """
    music = build_music_bed(preset, duration, sr, seed=seed, volume=volume)
    if len(music) < len(bed):
        music = np.pad(music, (0, len(bed) - len(music)))
    mixed = _soft_ceiling(bed + music[:len(bed)])
    return _anchor_bed_loudness(mixed, sr)


MUSIC_PROFILES: Final[Dict[str, MusicProfile]] = {
    # -- rain family -------------------------------------------------
    "Rain": MusicProfile(
        root="A2", prog=((0, "madd9"), (8, "maj7"), (3, "maj7"), (10, "sus2")),
        bpm=48, chord_bars=2, pattern="sparse",
        pad=0.50, pad_cut=1500, keys=0.50, bass=0.18, tone=3000, reverb=0.60),
    "Rain & Thunder": MusicProfile(
        root="A2", prog=((0, "madd9"), (7, "m"), (8, "maj7"), (5, "m7")),
        bpm=42, chord_bars=2, pattern="block",
        pad=0.70, pad_cut=1100, keys=0.22, bass=0.20, tone=2300, reverb=0.65),
    "Rain on Window": MusicProfile(
        root="C3", prog=((0, "add9"), (9, "m7"), (5, "maj7"), (7, "sus2")),
        bpm=54, chord_bars=2, pattern="sparse",
        pad=0.40, pad_cut=2000, keys=0.20, bell=0.45, tone=3400, reverb=0.60),
    "Car Ride Rain": MusicProfile(
        root="C3", prog=((0, "maj9"), (9, "m7"), (5, "maj7"), (7, "M")),
        bpm=64, chord_bars=1, pattern="sway",
        pad=0.25, pad_cut=1600, keys=0.50, bass=0.30,
        tone=2600, swing=0.15, reverb=0.50),
    "Blizzard": MusicProfile(
        root="A2", prog=((0, "madd9"), (8, "maj7"), (5, "m7"), (7, "m")),
        bpm=36, chord_bars=2, pattern="block",
        pad=0.90, pad_cut=800, tone=1900, reverb=0.70),
    # -- water -------------------------------------------------------
    "Ocean Waves": MusicProfile(
        root="D3", prog=((0, "m9"), (8, "maj7"), (3, "maj7"), (10, "add9")),
        bpm=40, chord_bars=2, pattern="block",
        pad=0.85, pad_cut=1000, keys=0.15, bass=0.22, tone=2400, reverb=0.70),
    "Mountain Stream": MusicProfile(
        root="C4", prog=((0, "add9"), (7, "M"), (10, "M"), (5, "sus2")),
        bpm=54, chord_bars=2, pattern="sparse",
        pad=0.25, pad_cut=2600, pluck=0.30, bell=0.55, tone=4600, reverb=0.65),
    "Bamboo Fountain": MusicProfile(
        root="G3", prog=((0, "sus2"), (7, "sus2"), (5, "sus2"), (2, "madd9")),
        bpm=50, chord_bars=1, pattern="poly",
        pad=0.20, pad_cut=1800, pluck=0.50, bell=0.20, tone=3200, reverb=0.55),
    "Underwater": MusicProfile(
        root="D3", prog=((0, "madd9"), (10, "maj7"), (5, "madd9"), (0, "sus2")),
        bpm=40, chord_bars=2, pattern="block",
        pad=0.85, pad_cut=750, bell=0.15, bass=0.20, tone=1500, reverb=0.75),
    "Hot Spring": MusicProfile(
        root="C3", prog=((0, "M"), (7, "m7"), (0, "M"), (5, "maj7")),
        bpm=52, chord_bars=1, pattern="poly",
        pad=0.30, pad_cut=1800, pluck=0.50, tone=3000, reverb=0.50),
    # -- nature ------------------------------------------------------
    "Forest Dawn": MusicProfile(
        root="C3", prog=((0, "M"), (9, "m7"), (5, "maj7"), (7, "M")),
        bpm=64, chord_bars=1, pattern="poly",
        pad=0.22, pad_cut=2400, pluck=0.50, bell=0.22, tone=4600, reverb=0.50),
    "Morning Birds": MusicProfile(
        root="C4", prog=((0, "add9"), (5, "maj7"), (9, "m7"), (7, "M")),
        bpm=60, chord_bars=1, pattern="poly",
        pad=0.20, pad_cut=2600, pluck=0.35, bell=0.50, tone=5200, reverb=0.55),
    "Night Crickets": MusicProfile(
        root="A2", prog=((0, "madd9"), (5, "m7"), (7, "sus2"), (3, "maj7")),
        bpm=44, chord_bars=2, pattern="sparse",
        pad=0.65, pad_cut=900, bell=0.18, tone=2100, reverb=0.60),
    "Garden Wind Chimes": MusicProfile(
        root="D4", prog=((0, "sus2"), (9, "m"), (5, "M"), (7, "sus2")),
        bpm=48, chord_bars=1, pattern="chimes",
        pad=0.28, pad_cut=2400, bell=0.60, tone=5000, reverb=0.70),
    "Wind": MusicProfile(
        root="D3", prog=((0, "m9"), (5, "7"), (10, "maj7"), (3, "maj7")),
        bpm=40, chord_bars=2, pattern="block",
        pad=0.80, pad_cut=1200, bass=0.18, tone=2400, reverb=0.65),
    "Autumn Leaves": MusicProfile(
        root="D3", prog=((0, "m7"), (5, "7"), (10, "maj7"), (8, "maj7")),
        bpm=56, chord_bars=2, pattern="sparse",
        pad=0.20, pad_cut=1700, keys=0.50, bass=0.30, tone=2900, reverb=0.60),
    "Cicada Swarm": MusicProfile(
        root="A2", prog=((0, "madd9"), (7, "madd9"), (0, "sus2"), (5, "m7")),
        bpm=42, chord_bars=2, pattern="block",
        pad=0.70, pad_cut=1600, bell=0.22, tone=3000, reverb=0.65),
    "Rice Field Dusk": MusicProfile(
        root="D3", prog=((0, "sus2"), (5, "sus2"), (7, "sus2"), (0, "sus2")),
        bpm=52, chord_bars=1, pattern="poly",
        pad=0.25, pad_cut=1900, pluck=0.50, bell=0.25, tone=3400, reverb=0.60),
    # -- indoor / urban ----------------------------------------------
    "Fireplace": MusicProfile(
        root="D3", prog=((0, "m7"), (5, "7"), (10, "maj7"), (3, "maj7")),
        bpm=60, chord_bars=1, pattern="poly",
        pad=0.20, pad_cut=1600, pluck=0.50, bass=0.28, tone=2800, reverb=0.50),
    "Café Murmur": MusicProfile(
        root="D3", prog=((0, "m7"), (5, "7"), (10, "maj7"), (7, "m7")),
        bpm=72, chord_bars=1, pattern="sway",
        pad=0.15, pad_cut=1800, keys=0.55, bass=0.35,
        tone=2600, swing=0.18, reverb=0.50),
    "Library": MusicProfile(
        root="C3", prog=((0, "maj9"), (4, "m7"), (9, "m7"), (5, "maj7")),
        bpm=50, chord_bars=2, pattern="sparse",
        pad=0.30, pad_cut=1600, keys=0.40, tone=2600, reverb=0.60),
    "Quiet Room": MusicProfile(
        root="C3", prog=((0, "maj9"), (9, "m7"), (5, "maj7"), (7, "sus2")),
        bpm=46, chord_bars=2, pattern="sparse",
        pad=0.25, pad_cut=1400, keys=0.32, tone=2400, reverb=0.60),
    "City Traffic": MusicProfile(
        root="E3", prog=((0, "m9"), (8, "maj7"), (5, "m9"), (7, "sus4")),
        bpm=46, chord_bars=2, pattern="block",
        pad=0.85, pad_cut=1000, bass=0.22, tone=2200, reverb=0.60),
    "Midnight City": MusicProfile(
        root="A2", prog=((0, "madd9"), (8, "M"), (3, "M"), (10, "M")),
        bpm=78, chord_bars=1, pattern="arp_ud",
        pad=0.50, pad_cut=1600, pluck=0.45, bass=0.40, tone=3200, reverb=0.50),
    "Night Train": MusicProfile(
        root="A2", prog=((0, "m7"), (5, "7"), (8, "maj7"), (3, "maj7")),
        bpm=64, chord_bars=1, pattern="sway",
        pad=0.25, pad_cut=1600, keys=0.50, bass=0.35,
        tone=2800, swing=0.15, reverb=0.55),
    "Airplane Cabin": MusicProfile(
        root="C3", prog=((0, "maj9"), (7, "sus2"), (9, "m7"), (5, "maj7")),
        bpm=36, chord_bars=2, pattern="block",
        pad=0.90, pad_cut=1400, bell=0.12, tone=2800, reverb=0.70),
    "Lo-Fi Study": MusicProfile(
        root="D3", prog=((0, "m7"), (5, "7"), (10, "maj7"), (8, "maj7")),
        bpm=68, chord_bars=1, pattern="sway",
        pad=0.20, pad_cut=1500, keys=0.55, bass=0.40,
        tone=2200, swing=0.20, reverb=0.50),
    "Vinyl Crackle": MusicProfile(
        root="C3", prog=((0, "maj9"), (9, "m7"), (5, "maj7"), (4, "m7")),
        bpm=62, chord_bars=1, pattern="sparse",
        pad=0.20, pad_cut=1600, keys=0.50, bass=0.30, tone=2400, reverb=0.55),
    "Server Room": MusicProfile(
        root="E3", prog=((0, "madd9"), (8, "maj7"), (0, "sus2"), (5, "m7")),
        bpm=40, chord_bars=2, pattern="block",
        pad=0.80, pad_cut=900, bell=0.12, tone=2000, reverb=0.70),
    "Brown Noise": MusicProfile(
        root="D2", prog=((0, "madd9"), (0, "sus2"), (0, "madd9"), (7, "madd9")),
        bpm=30, chord_bars=4, pattern="block",
        pad=0.75, pad_cut=800, bass=0.30, tone=1500, reverb=0.60),
    # -- special atmospheres ------------------------------------------
    "Zen Garden": MusicProfile(
        root="D3", prog=((0, "sus2"), (7, "sus2"), (5, "sus2"), (7, "sus2")),
        bpm=52, chord_bars=1, pattern="poly",
        pad=0.22, pad_cut=1800, pluck=0.55, bell=0.15, tone=3200, reverb=0.55),
    "Space Drone": MusicProfile(
        root="A2", prog=((0, "madd9"), (0, "sus4"), (0, "madd9"), (7, "madd9")),
        bpm=30, chord_bars=4, pattern="block",
        pad=1.00, pad_cut=700, bass=0.25, tone=1700, reverb=0.80),
    "Singing Bowls": MusicProfile(
        root="C3", prog=((0, "5"), (7, "5"), (0, "5"), (5, "5")),
        bpm=30, chord_bars=4, pattern="block",
        pad=0.90, pad_cut=1200, bell=0.30, bass=0.15, tone=2000, reverb=0.80),
    "Cathedral Hall": MusicProfile(
        root="D3", prog=((0, "m"), (8, "M"), (5, "m"), (7, "sus4")),
        bpm=36, chord_bars=2, pattern="block",
        pad=0.95, pad_cut=1600, bell=0.15, bass=0.25, tone=2600, reverb=0.85),
}


# ------------------------------------------------------------------ facade
def list_ambience_presets() -> List[str]:
    """All registered soundscape names, in registration order."""
    return list(AMBIENCE_PRESETS.keys())


def render_ambience(preset: str, duration: float, sr: int = AUDIO_SAMPLE_RATE,
                    seed: int = 7, with_music: bool = False,
                    music_volume: float = 0.5) -> np.ndarray:
    """Render an ambience bed: mono float64 in [-1, 1], length = duration*sr.

    The bed is DC-blocked, loudness-anchored (:data:`BED_TARGET_LUFS`) and
    given a gentle 0.8 s fade-in / 0.5 s fade-out so it never clicks at the
    track seams and never overwhelms the keystrokes at the same slider
    setting.

    With ``with_music`` the preset's procedural music layer
    (:func:`build_music_bed`, level ``music_volume`` 0..1) is mixed in and
    the combined bed is re-anchored, so music trades texture headroom at a
    constant total loudness — the recommended way to call it for exports.
    """
    n = max(1, int(duration * sr))
    fn = AMBIENCE_PRESETS.get(preset)
    if fn is None:
        fn = AMBIENCE_PRESETS["Rain"]
    rng = np.random.RandomState(seed)
    x = fn(n, sr, rng)
    # v1.0.3: per-bed high-shelf damping — pulls radio-static fizz out of
    # the bright textures while leaving their identity intact (see
    # :data:`_BED_TILT`).
    tilt = _BED_TILT.get(preset)
    if tilt:
        x = _shelf_tilt(x, sr, tilt[0], tilt[1])
    # DC/LF block BEFORE the fades: one-sided textures (fireplace crackle)
    # carry a true DC offset, and mean-subtraction alone cannot fix it once
    # the fades have zeroed the tail (the removed tail's mean would
    # re-appear as a constant pedestal).  A 20 Hz high-pass removes DC and
    # slow drift alike, and the short kernel does not smear the fade.
    x = x - _xlp(x, 20.0, sr)
    fade_in = min(BED_FADE_IN_S, max(0.05, duration * 0.25))
    x = _fade_edges(x, sr, fade_in=fade_in, fade_out=BED_FADE_OUT_S)
    x = _anchor_bed_loudness(x, sr)
    if with_music and music_volume > 0:
        x = mix_music_into_bed(x, preset, duration, sr, seed=seed,
                               volume=music_volume)
    return x




# ==========================================================================
# Custom files — decode (native WAV or ffmpeg pipe), loop, evolve
# ==========================================================================
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def _decode_with_ffmpeg(path: str, sr: int) -> Optional[np.ndarray]:
    """Decode any ffmpeg-supported audio file to mono float64 at sr."""
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-i", path,
           "-f", "f32le", "-ac", "1", "-ar", str(sr), "pipe:1"]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=120)
        if proc.returncode != 0 or not proc.stdout:
            logger.error(f"ffmpeg could not decode ambience file {path}: "
                         f"{proc.stderr.decode('utf-8', 'ignore')[:200]}")
            return None
        return np.frombuffer(proc.stdout, dtype=np.float32).astype(np.float64)
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.error(f"Failed to decode ambience file {path}: {e}")
        return None


def _load_wav_mono(path: str, sr: int) -> Optional[np.ndarray]:
    """Decode any supported audio file to mono float64 at ``sr`` (no looping)."""
    try:
        if path.lower().endswith(".wav"):
            with wave.open(path, "rb") as w:
                nch, sw, rate, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
                raw = w.readframes(nf)
            try:
                data = _pcm_bytes_to_float(raw, sw)
            except ValueError:
                logger.error(f"Unsupported audio WAV width: {sw * 8}-bit")
                return None
        else:
            # ffmpeg path already returns mono float64 at the target rate
            return _decode_with_ffmpeg(path, sr)
        if nch > 1:
            data = data[: (len(data) // nch) * nch].reshape(-1, nch).mean(axis=1)
        if rate != sr and len(data) > 1:
            data = _resample_linear(data, sr, rate)
        return data
    except Exception as e:
        logger.error(f"Cannot load audio file {path}: {e}")
        return None


def _resample_linear(data: np.ndarray, sr: int, rate: int) -> np.ndarray:
    new_len = max(1, int(len(data) * sr / rate))
    idx = np.linspace(0, len(data) - 1, new_len)
    i0 = idx.astype(np.int64)
    frac = idx - i0
    i1 = np.minimum(i0 + 1, len(data) - 1)
    return data[i0] * (1 - frac) + data[i1] * frac


def load_ambience_file(path: str, duration: float, sr: int = AUDIO_SAMPLE_RATE) -> Optional[np.ndarray]:
    """Load an audio file tiled into a plain loop of the requested duration.

    Returns mono float64 in [-1, 1] with crossfaded loop seams and a fade-out,
    or ``None`` if the file cannot be decoded.  For long beds prefer
    :func:`render_ambience_from_wav` / :func:`extend_wav_procedural`, which
    keep a short recording from obviously repeating.
    """
    data = _load_wav_mono(path, sr)
    if data is None:
        return None
    return _loop_to_duration(data, duration, sr)


def _loop_to_duration(data: np.ndarray, duration: float, sr: int,
                      xfade: float = 1.5) -> np.ndarray:
    """Tile data to cover duration, crossfading the seams, fade-out at end."""
    n = max(1, int(duration * sr))
    if len(data) == 0:
        return np.zeros(n)
    data = _normalize(data.copy(), 0.85)
    out = _tile_seamless(data, n, min(len(data) // 2, max(4, int(xfade * sr))))
    _fade_edges(out, sr, fade_in=0.02, fade_out=0.6)
    return out


def _tile_seamless(unit: np.ndarray, n: int, xn: int) -> np.ndarray:
    """Tile ``unit`` to ``n`` samples, crossfading ``xn`` samples at each seam."""
    if len(unit) == 0:
        return np.zeros(n)
    if len(unit) >= n:
        return unit[:n].copy()
    xn = max(4, min(int(xn), len(unit) // 2))
    out = np.zeros(n)
    pos = 0
    while pos < n:
        end = min(pos + len(unit), n)
        seg = unit[: end - pos]
        if pos == 0:
            out[pos:end] = seg
        elif xn > 4 and (end - pos) > xn:
            ramp = np.linspace(0.0, 1.0, xn)
            # crossfade: fade existing out, fade the new copy in
            out[pos:pos + xn] = out[pos:pos + xn] * (1 - ramp) + seg[:xn] * ramp
            out[pos + xn:end] = seg[xn:]
        else:
            out[pos:end] = seg
        if end >= n:
            break
        pos = end - xn if end - xn > pos else end
    return out


# ---------------------------------------------- procedural long-form (WAV extender)
def _trim_silence(x: np.ndarray, sr: int, thresh_db: float = -46.0,
                  margin_s: float = 0.01) -> np.ndarray:
    """Trim leading/trailing near-silence, keeping a tiny margin."""
    if len(x) < 64:
        return x
    pk = float(np.max(np.abs(x)))
    if pk < 1e-9:
        return x
    idx = np.flatnonzero(np.abs(x) > pk * (10.0 ** (thresh_db / 20.0)))
    if len(idx) == 0:
        return x
    m = max(1, int(margin_s * sr))
    a = max(0, int(idx[0]) - m)
    b = min(len(x), int(idx[-1]) + m)
    return x[a:b]


def _best_loop_unit(x: np.ndarray, sr: int) -> np.ndarray:
    """Cut the most self-similar loop out of ``x``.

    An FFT autocorrelation finds the lag at which the recording re-enters
    itself with the least discontinuity; the end of that loop unit is then
    crossfaded toward its own head so tiling it is seamless by construction.
    """
    n = len(x)
    xf = min(n // 4, max(8, int(0.05 * sr)))
    min_len = max(int(0.2 * n), 4 * xf, 64)
    hi = n - xf - 1
    if hi - min_len < 64:
        # too short to search: crossfade the tail straight into the head
        unit = x.copy()
        ramp = np.linspace(0.0, 1.0, xf)
        unit[:xf] = unit[:xf] * ramp + unit[n - xf:] * (1.0 - ramp)
        return unit
    L = 1 << int(np.ceil(np.log2(2 * n)))
    X = np.fft.rfft(x - np.mean(x), L)
    ac = np.fft.irfft(X * np.conj(X), L)[:n]
    ac = ac / (float(ac[0]) + 1e-12)
    lags = np.arange(min_len, hi)
    k = int(lags[int(np.argmax(ac[min_len:hi]))])
    unit = x[:k].copy()
    ramp = np.linspace(0.0, 1.0, xf)
    unit[k - xf:k] = unit[k - xf:k] * (1.0 - ramp) + x[0:xf] * ramp
    return unit


def extend_wav_procedural(src: np.ndarray, duration: float,
                          sr: int = AUDIO_SAMPLE_RATE, seed: int = 7,
                          evolve: bool = True) -> np.ndarray:
    """Procedurally extend a short recording into a long ambient bed.

    Naive tiling repeats the source verbatim on every pass — instantly
    audible after a minute.  This extender instead:

      1. trims silence and normalizes;
      2. finds the most self-similar re-entry point (FFT autocorrelation)
         and cuts a seamless loop unit;
      3. tiles it with short equal-power seam crossfades;
      4. with ``evolve`` on, the base itself is read at a slowly drifting
         playback rate (seamless + varispeed = no two passes identical) and
         three slow, seed-driven movements are layered on top:
           * a varispeed ghost — a copy played a few percent faster/slower
             that slowly beats against the base layer;
           * a half-speed, low-passed "deep" copy for slow sub-movement;
           * independent gain LFOs (periods 40-160 s) on every layer;
      5. normalizes and fades the edges.

    Deterministic for a given (source, seed, sr).  Mono float64 in [-1, 1].
    """
    n = max(1, int(duration * sr))
    src = np.asarray(src, dtype=np.float64)
    if len(src) < 32 or n <= 1:
        return np.zeros(n)
    rng = np.random.RandomState(seed)

    unit = _best_loop_unit(_normalize(_trim_silence(src, sr), 0.85), sr)
    xf = max(8, int(0.04 * sr))
    if not evolve:
        base = _tile_seamless(unit, n, xf)
        _fade_edges(base, sr, fade_in=0.05, fade_out=0.6)
        return _normalize(base, 0.85)

    def _speed_copy(u: np.ndarray, factor: float) -> np.ndarray:
        if abs(factor - 1.0) < 1e-6 or len(u) < 8:
            return u
        m = max(8, int(len(u) / factor))
        idx = np.linspace(0, len(u) - 1, m)
        i0 = idx.astype(np.int64)
        frac = idx - i0
        i1 = np.minimum(i0 + 1, len(u) - 1)
        return u[i0] * (1.0 - frac) + u[i1] * frac

    t = np.arange(n, dtype=np.float64) / sr

    # 1) base at slowly drifting speed: the loop unit is seamless, so
    #    variable-rate reading stays continuous while no two passes of the
    #    loop are ever identical (kills audible repetition entirely)
    r_per = float(rng.uniform(70.0, 140.0))
    rate = 1.0 + float(rng.uniform(0.004, 0.010)) * np.sin(2 * np.pi * t / r_per
                                                           + rng.uniform(0, 6.283))
    idx = np.cumsum(rate) % len(unit)
    i0 = idx.astype(np.int64)
    frac = idx - i0
    i1 = np.minimum(i0 + 1, len(unit) - 1)
    base = unit[i0] * (1.0 - frac) + unit[i1] * frac
    b_gain = 1.0 + 0.10 * np.sin(2 * np.pi * t / float(rng.uniform(55.0, 130.0))
                                 + rng.uniform(0, 6.283))

    # 2) varispeed ghost at a fixed offset rate: slowly beats against the
    #    drifting base layer
    drift = float(rng.uniform(0.025, 0.05)) * (1.0 if rng.rand() < 0.5 else -1.0)
    ghost = _tile_seamless(_speed_copy(unit, 1.0 + drift), n, xf)
    g_gain = 0.30 * (1.0 + 0.55 * np.sin(2 * np.pi * t / float(rng.uniform(40.0, 90.0))
                                         + rng.uniform(0, 6.283)))
    # 3) half-speed deep layer (low-passed: adds weight, not a second melody)
    deep = DSP.filt_lp(_tile_seamless(_speed_copy(unit, 0.5), n, xf), 700.0, sr)
    d_gain = 0.22 * (1.0 + 0.60 * np.sin(2 * np.pi * t / float(rng.uniform(80.0, 160.0))
                                         + rng.uniform(0, 6.283)))

    out = base * b_gain + ghost * g_gain + deep * d_gain
    out = _normalize(out, 0.85)
    _fade_edges(out, sr, fade_in=0.05, fade_out=0.6)
    return out


def render_ambience_from_wav(path: str, duration: float, sr: int = AUDIO_SAMPLE_RATE,
                             seed: int = 7, evolve: bool = True) -> Optional[np.ndarray]:
    """Load an audio file and procedurally extend it to ``duration``.

    Returns mono float64 in [-1, 1], or ``None`` if the file cannot be
    decoded.  This is the long-form path behind :func:`build_ambience_bed`.
    """
    data = _load_wav_mono(path, sr)
    if data is None:
        return None
    return extend_wav_procedural(data, duration, sr, seed=seed, evolve=evolve)


# ==========================================================================
# Mixing — keyboard PCM + ambience bed -> final PCM
# ==========================================================================
def _soft_ceiling(x: np.ndarray, ceiling: float = MASTER_CEILING,
                  knee: float = 0.90) -> np.ndarray:
    """Soft-knee peak ceiling for the bed mix.

    Below ``knee`` the signal is untouched; between knee and ceiling it is
    curved down by the same C1 cubic the SoftClipStage uses; above the
    ceiling it flattens.  Replaces the old hard ``np.clip(x, -1, 1)``: a
    loud keystroke plus a loud bed no longer shears off at the rails (which
    audibly crackled) — the top few tenths of a dB are rounded instead.
    """
    a = np.abs(x)
    if a.size == 0 or float(np.max(a)) <= knee:
        return x
    out = np.array(x, dtype=np.float64, copy=True)
    zone = (a > knee) & (a < ceiling)
    if zone.any():
        u = (a[zone] - knee) / (ceiling - knee)
        fu = u + u * u - u * u * u
        out[zone] = np.sign(x[zone]) * (knee + (ceiling - knee) * fu)
    over = a >= ceiling
    if over.any():
        out[over] = np.sign(x[over]) * ceiling
    return out


def mix_ambience(kb_pcm: np.ndarray, sr: int, channels: int,
                 amb: Optional[np.ndarray], amb_volume: float) -> np.ndarray:
    """Mix an ambience bed (mono float) into the keyboard PCM (int16).

    Returns int16 PCM of the same shape as the input.  If ``amb`` is None or
    the volume is zero the input is returned unchanged (as int16).
    """
    if kb_pcm.dtype == np.int16 and channels == 2:
        mono_len = len(kb_pcm) // 2
    else:
        mono_len = len(kb_pcm)
    if amb is None or amb_volume <= 0 or mono_len == 0:
        if kb_pcm.dtype == np.int16:
            return kb_pcm
        return np.clip(kb_pcm * 32767, -32768, 32767).astype(np.int16)

    gain = float(np.clip(amb_volume, 0, 100)) / 100.0
    bed = amb[:mono_len]
    if len(bed) < mono_len:
        bed = np.pad(bed, (0, mono_len - len(bed)))

    if channels == 2 and kb_pcm.dtype == np.int16:
        left = kb_pcm[0::2].astype(np.float64) / 32768.0
        right = kb_pcm[1::2].astype(np.float64) / 32768.0
        # gentle Haas widening: the bed is no longer dead-centre — the right
        # ear gets an 8 ms-delayed copy, which reads as a real room
        d = min(len(bed) - 1, max(1, int(0.008 * sr)))
        bed_r = np.empty_like(bed)
        bed_r[:d] = bed[:d] * 0.5
        bed_r[d:] = bed[:-d]
        bed_r *= 0.96
        left = _soft_ceiling(left + bed * gain)
        right = _soft_ceiling(right + bed_r * gain)
        out = np.empty(len(kb_pcm), dtype=np.int16)
        out[0::2] = (left * 32767).astype(np.int16)
        out[1::2] = (right * 32767).astype(np.int16)
        return out

    if kb_pcm.dtype == np.int16:
        mono = kb_pcm.astype(np.float64) / 32768.0
    else:
        mono = kb_pcm.astype(np.float64)
    mono = _soft_ceiling(mono + bed * gain)
    return np.clip(mono * 32767, -32768, 32767).astype(np.int16)


def build_ambience_bed(config, duration: float, sr: int = AUDIO_SAMPLE_RATE) -> Optional[np.ndarray]:
    """Resolve the configured ambience (custom file first, then preset) and
    overlay the procedural music layer when enabled.

    A custom file is procedurally extended to ``duration`` (see
    :func:`extend_wav_procedural`); set ``config.amb_evolve = False`` for the
    plain verbatim loop of the old behaviour.  ``config.amb_music`` (on by
    default) adds the soundscape's generated soundtrack at
    ``config.amb_music_volume`` (0-100) — every background bed ships with
    music so the result is YouTube-ready without a separate BGM file.
    """
    if not getattr(config, "amb_enabled", False):
        return None
    if duration <= 0:
        return None
    mv = float(np.clip(getattr(config, "amb_music_volume", 45), 0, 100)) / 100.0
    music_on = bool(getattr(config, "amb_music", True)) and mv > 0
    preset = getattr(config, "amb_preset", "Rain")
    path = getattr(config, "amb_path", "") or ""
    if path:
        src = _load_wav_mono(path, sr)
        if src is not None:
            evolve = bool(getattr(config, "amb_evolve", True))
            bed = extend_wav_procedural(src, duration, sr, evolve=evolve)
            if music_on:
                bed = mix_music_into_bed(bed, preset, duration, sr,
                                         seed=7, volume=mv)
            return bed
        logger.warning(f"Ambience file '{path}' failed; using preset "
                       f"'{preset}' instead")
    return render_ambience(preset, duration, sr,
                           with_music=music_on, music_volume=mv)

##############
#                             ══ 6 - ENCODERS ══                            
# hardware encoder auto-detection + quality maps
# (was: encoders.py in the ten-file edition)
##############

"""Hardware video-encoder auto-detection (NVENC/QSV/AMF/VideoToolbox/
VAAPI with libx264 fallback) and quality-preset codec arguments."""


#==============================================================================
# ── ENCODERS — hardware detection + quality codec args
#    (merged from studio/encoders.py in the v2.5 ten-file edition)
#==============================================================================

"""Hardware video-encoder auto-detection (Qt-free, subprocess only).

Two-stage detection:
  1. *Fast stage*: parse ``ffmpeg -encoders`` to see which encoders the build
     knows about. Cheap, but a build can list e.g. ``h264_nvenc`` on a machine
     without an NVIDIA GPU.
  2. *Deep probe*: run a real 0.2 s ``testsrc2`` encode through each hardware
     encoder into the null muxer. Only encoders that actually produce frames
     are offered as working.

Results are cached in memory (per process) and on disk in the temp dir keyed
by the ffmpeg binary path + version, so the GUI can restore the last known
state instantly and re-probe only on demand.

The GUI shows "Auto (Hardware)": at export time :func:`resolve_encoder_choice`
picks the first working hardware encoder in preference order, or falls back to
the software encoder when nothing hardware-accelerated works.
"""

import json
import os
import platform
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Protocol, Tuple


FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

# ------------------------------------------------------------------ registry
# id -> (display label, ffmpeg encoder name).  Order = auto-selection priority.
HARDWARE_ENCODERS: List[Tuple[str, str, str]] = [
    ("nvenc", "NVENC (NVIDIA)", "h264_nvenc"),
    ("qsv", "QSV (Intel)", "h264_qsv"),
    ("amf", "AMF (AMD)", "h264_amf"),
    ("videotoolbox", "VideoToolbox (macOS)", "h264_videotoolbox"),
    ("vaapi", "VAAPI (Linux)", "h264_vaapi"),
]

SOFTWARE_ID = "software"
SOFTWARE_LABEL = "YouTube Optimised (H.264/AAC)"
AUTO_LABEL = "Auto (Hardware)"

# Map legacy display names (stored in old settings.json / project files) to ids.
_LABEL_TO_ID = {label: enc_id for enc_id, label, _ in HARDWARE_ENCODERS}
_LABEL_TO_ID[SOFTWARE_LABEL] = SOFTWARE_ID
_LABEL_TO_ID[AUTO_LABEL] = "auto"
# v2.0 aliases that were the first entry of ENCODERS
_LABEL_TO_ID["YouTube Optimised (H.264/AAC)"] = SOFTWARE_ID

PROBE_TIMEOUT = 25          # seconds for a deep probe encode
_CACHE_VERSION = 1


@dataclass
class EncoderInfo:
    """Detection result for one encoder backend."""
    id: str
    label: str
    ffmpeg_name: str = ""
    listed: bool = False                 # present in `ffmpeg -encoders`
    probed_ok: Optional[bool] = None     # None = not deep-probed yet
    detail: str = ""

    @property
    def working(self) -> bool:
        if not self.listed:
            return False
        return self.probed_ok is not False

    def as_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "ffmpeg_name": self.ffmpeg_name,
                "listed": self.listed, "probed_ok": self.probed_ok, "detail": self.detail}


@dataclass
class EncoderScanResult:
    """Full detection snapshot for a machine."""
    ffmpeg_path: str = ""
    ffmpeg_version: str = ""
    encoders: Dict[str, EncoderInfo] = field(default_factory=dict)
    scanned_at: float = 0.0

    def working_hw(self) -> List[EncoderInfo]:
        """All hardware encoders that passed the deep probe."""
        out = []
        for enc_id, _label, _name in HARDWARE_ENCODERS:
            info = self.encoders.get(enc_id)
            if info is not None and info.listed and info.probed_ok:
                out.append(info)
        return out

    def best(self) -> Optional[EncoderInfo]:
        """First *deep-probe-verified* hardware encoder, in preference order."""
        for enc_id, _label, _name in HARDWARE_ENCODERS:
            info = self.encoders.get(enc_id)
            if info and info.listed and info.probed_ok:
                return info
        return None

    def summary_lines(self) -> List[str]:
        out = [f"ffmpeg: {self.ffmpeg_path} ({self.ffmpeg_version})"]
        for enc_id, label, name in HARDWARE_ENCODERS:
            info = self.encoders.get(enc_id)
            if info is None:
                continue
            if not info.listed:
                state = "not in this ffmpeg build"
            elif info.probed_ok is None:
                state = "listed (not probed)"
            elif info.probed_ok:
                state = "WORKING"
            else:
                state = f"listed but probe failed ({info.detail[:60]})"
            out.append(f"  {label:<24} [{name}] {state}")
        return out


# ------------------------------------------------------------------ probing
def _run(cmd: List[str], timeout: float) -> Tuple[int, str]:
    """Run a command, capture combined stdout+stderr text; never raises."""
    try:
        if platform.system() == "Windows":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs = {"startupinfo": si, "creationflags": subprocess.CREATE_NO_WINDOW}
        else:
            kwargs = {}
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, **kwargs)
        out = proc.stdout.decode("utf-8", errors="ignore")
        err = proc.stderr.decode("utf-8", errors="ignore")
        return proc.returncode, out + "\n" + err
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except FileNotFoundError:
        return -1, "ffmpeg not found"
    except OSError as e:
        return -1, str(e)


def ffmpeg_version() -> str:
    rc, out = _run([FFMPEG, "-hide_banner", "-version"], timeout=10)
    if rc == 0:
        m = re.search(r"ffmpeg version (\S+)", out)
        return m.group(1) if m else "unknown"
    return "unavailable"


def list_ffmpeg_encoders() -> set:
    """Return the set of encoder names this ffmpeg build knows about."""
    rc, out = _run([FFMPEG, "-hide_banner", "-encoders"], timeout=15)
    names = set()
    if rc == 0:
        for line in out.splitlines():
            # layout: " V....D h264_nvenc    NVIDIA NVENC ..." (6 flag chars)
            m = re.match(r"^\s*[A-Za-z.]{6}\s+(\S+)", line)
            if m:
                names.add(m.group(1))
    return names


def probe_encoder(enc_id: str, width: int = 256, height: int = 256,
                  duration: float = 0.2, fps: int = 30) -> Tuple[bool, str]:
    """Deep probe: actually encode a tiny test clip with this encoder."""
    src = ["-f", "lavfi", "-i", f"testsrc2=size={width}x{height}:rate={fps}:duration={duration}"]
    if enc_id == "nvenc":
        cmd = [FFMPEG, "-hide_banner", "-loglevel", "error"] + src + \
              ["-c:v", "h264_nvenc", "-f", "null", "-"]
    elif enc_id == "qsv":
        cmd = [FFMPEG, "-hide_banner", "-loglevel", "error"] + src + \
              ["-c:v", "h264_qsv", "-f", "null", "-"]
    elif enc_id == "amf":
        cmd = [FFMPEG, "-hide_banner", "-loglevel", "error"] + src + \
              ["-c:v", "h264_amf", "-f", "null", "-"]
    elif enc_id == "videotoolbox":
        cmd = [FFMPEG, "-hide_banner", "-loglevel", "error"] + src + \
              ["-c:v", "h264_videotoolbox", "-f", "null", "-"]
    elif enc_id == "vaapi":
        cmd = [FFMPEG, "-hide_banner", "-loglevel", "error",
               "-init_hw_device", "vaapi=va:", "-filter_hw_device", "va"] + src + \
              ["-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi", "-f", "null", "-"]
    elif enc_id == SOFTWARE_ID:
        cmd = [FFMPEG, "-hide_banner", "-loglevel", "error"] + src + \
              ["-c:v", "libx264", "-preset", "ultrafast", "-f", "null", "-"]
    else:
        return False, f"unknown encoder id: {enc_id}"

    rc, err = _run(cmd, timeout=PROBE_TIMEOUT)
    if rc == 0:
        return True, "probe encode ok"
    tail = " | ".join(l.strip() for l in err.strip().splitlines()[-2:] if l.strip())
    return False, tail or f"exit code {rc}"


# ------------------------------------------------------------------ caching
_disk_cache_lock = threading.Lock()
_CACHE_FILE = TEMP_DIR / "encoder_cache.json"
_mem_cache: Optional[EncoderScanResult] = None


def _cache_key(version: str) -> dict:
    return {"ffmpeg": FFMPEG, "version": version, "cache_version": _CACHE_VERSION}


def _load_disk_cache(version: str) -> Optional[EncoderScanResult]:
    try:
        if not _CACHE_FILE.exists():
            return None
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("key") != _cache_key(version):
            return None
        result = EncoderScanResult(
            ffmpeg_path=data.get("ffmpeg_path", FFMPEG),
            ffmpeg_version=version,
            encoders={k: EncoderInfo(**v) for k, v in data.get("encoders", {}).items()},
            scanned_at=data.get("scanned_at", 0.0),
        )
        return result
    except Exception:
        return None


def _save_disk_cache(result: EncoderScanResult) -> None:
    with _disk_cache_lock:
        try:
            payload = {
                "key": _cache_key(result.ffmpeg_version),
                "ffmpeg_path": result.ffmpeg_path,
                "scanned_at": result.scanned_at,
                "encoders": {k: v.as_dict() for k, v in result.encoders.items()},
            }
            tmp = str(_CACHE_FILE) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=1)
            os.replace(tmp, _CACHE_FILE)
        except Exception:
            logger.debug("Could not write encoder cache", exc_info=True)


def clear_cache() -> None:
    """Forget in-memory and on-disk detection results."""
    global _mem_cache
    with _disk_cache_lock:
        _mem_cache = None
        try:
            if _CACHE_FILE.exists():
                os.remove(_CACHE_FILE)
        except OSError:
            pass


def detect_encoders(deep: bool = True, use_cache: bool = True,
                    hw_only_probe: bool = True) -> EncoderScanResult:
    """Detect encoder availability.

    Parameters
    ----------
    deep:
        Also run a real test encode for every *listed* hardware encoder.
    use_cache:
        Reuse the previous detection result when the ffmpeg binary/version
        has not changed (disk cache shared between GUI runs).
    hw_only_probe:
        Only deep-probe hardware encoders (software is assumed working).
    """
    global _mem_cache
    if use_cache and _mem_cache is not None:
        return _mem_cache

    version = ffmpeg_version()
    if use_cache and version not in ("unavailable",):
        cached = _load_disk_cache(version)
        if cached is not None:
            _mem_cache = cached
            return _mem_cache

    result = EncoderScanResult(ffmpeg_path=FFMPEG, ffmpeg_version=version,
                               scanned_at=time.time())
    listed = list_ffmpeg_encoders()
    hw_by_ffmpeg_name = {name: (eid, label) for eid, label, name in HARDWARE_ENCODERS}

    for enc_id, label, name in HARDWARE_ENCODERS:
        info = EncoderInfo(id=enc_id, label=label, ffmpeg_name=name, listed=name in listed)
        if info.listed and deep:
            ok, detail = probe_encoder(enc_id)
            info.probed_ok = ok
            info.detail = detail
        result.encoders[enc_id] = info

    sw = EncoderInfo(id=SOFTWARE_ID, label=SOFTWARE_LABEL, ffmpeg_name="libx264",
                     listed="libx264" in listed)
    if sw.listed and not hw_only_probe:
        ok, detail = probe_encoder(SOFTWARE_ID)
        sw.probed_ok = ok
        sw.detail = detail
    result.encoders[SOFTWARE_ID] = sw

    if use_cache and version not in ("unavailable",):
        _save_disk_cache(result)
    _mem_cache = result
    return result


def resolve_encoder_choice(encoder_setting: str, deep: bool = True,
                           use_cache: bool = True) -> Tuple[str, EncoderScanResult]:
    """Turn the user-facing encoder setting into a concrete backend id.

    Returns ``(encoder_id, scan_result)``.  ``encoder_id`` is one of
    ``"auto"`` (nothing hardware works -> use software), or a hardware id,
    or ``"software"``.
    """
    enc_id = _LABEL_TO_ID.get(encoder_setting, SOFTWARE_ID)
    if enc_id == SOFTWARE_ID:
        return SOFTWARE_ID, detect_encoders(deep=False, use_cache=use_cache)
    scan = detect_encoders(deep=deep, use_cache=use_cache)
    if enc_id == "auto":
        best = scan.best()
        if best:
            return best.id, scan
        return SOFTWARE_ID, scan
    info = scan.encoders.get(enc_id)
    if info and info.listed and (info.probed_ok is not False):
        return enc_id, scan
    logger.warning(f"Encoder '{encoder_setting}' unavailable ({info.detail if info else 'not found'}); "
                   f"falling back to software encoder")
    return SOFTWARE_ID, scan


# ------------------------------------------------------------------ args
# Strategy pattern: every backend (hardware or software) owns the knowledge
# of how its ffmpeg argument list is built.  ``build_video_codec_args`` is a
# thin facade over the ``ENCODER_STRATEGIES`` registry, so supporting a new
# backend means adding one class + one registry entry instead of growing an
# if/elif chain.


class EncoderStrategy(Protocol):
    """Contract every encoder backend strategy implements."""

    encoder_id: str
    ffmpeg_name: str

    def global_args(self, w: int, h: int, fps: int, quality: str) -> List[str]:
        """Args placed BEFORE the inputs (hardware device initialisation)."""
        ...

    def codec_args(self, w: int, h: int, fps: int, quality: str) -> List[str]:
        """Args placed right BEFORE the output path."""
        ...


# Quality tokens accepted inside a codec-args template.  They are replaced
# with the value from QUALITY_MAP (and its +2 offset) at build time.
_Q_TOKENS: Dict[str, Callable[[int], int]] = {
    "{q}": lambda v: v,
    "{q+2}": lambda v: v + 2,
}

_COLOR_TAGS = ("-color_primaries", "bt709", "-color_trc", "bt709",
               "-colorspace", "bt709", "-color_range", "tv")

# Quality preset -> per-encoder rate-control values (YouTube-oriented).
# libx264 uses CRF (+x264 preset); hardware encoders use their own quality
# knobs (CQ / global_quality / QP / q:v).  Lower value == better quality.
QUALITY_MAP: Dict[str, dict] = {
    "High":     {"crf": 16, "hw": 17, "vt": 75, "x264_preset": "slow"},
    "Balanced": {"crf": 20, "hw": 21, "vt": 60, "x264_preset": "slow"},
    "Small":    {"crf": 26, "hw": 28, "vt": 42, "x264_preset": "medium"},
}


def normalize_quality(quality: Optional[str]) -> str:
    """Clamp any quality setting to a known preset name."""
    q = (quality or "Balanced").strip().capitalize()
    return q if q in QUALITY_MAP else "Balanced"


@dataclass(frozen=True, slots=True)
class HardwareEncoderStrategy:
    """Strategy for hardware encoders driven by a static argument template.

    ``codec`` is the argument tail; the ``{q}`` / ``{q+2}`` tokens are
    substituted with the quality-map value (and its +2 offset) at build time.
    """

    encoder_id: str
    ffmpeg_name: str
    quality_key: str                      # key into QUALITY_MAP ("hw" | "vt")
    codec: Tuple[str, ...]
    pre: Tuple[str, ...] = ()             # global args (device init)

    def global_args(self, w: int, h: int, fps: int, quality: str) -> List[str]:
        return list(self.pre)

    def codec_args(self, w: int, h: int, fps: int, quality: str) -> List[str]:
        q = QUALITY_MAP[normalize_quality(quality)][self.quality_key]
        return [str(_Q_TOKENS[a](q)) if a in _Q_TOKENS else a
                for a in self.codec]


@dataclass(frozen=True, slots=True)
class SoftwareEncoderStrategy:
    """Strategy for the YouTube-optimised libx264 backend (CRF + a bitrate
    ceiling derived from the frame size)."""

    encoder_id: str = SOFTWARE_ID
    ffmpeg_name: str = "libx264"

    def global_args(self, w: int, h: int, fps: int, quality: str) -> List[str]:
        return []

    def codec_args(self, w: int, h: int, fps: int, quality: str) -> List[str]:
        q = QUALITY_MAP[normalize_quality(quality)]
        maxrate = int((w * h / 2073600.0) * 12000000)
        return ["-c:v", "libx264", "-preset", q["x264_preset"], "-crf", str(q["crf"]),
                "-maxrate", str(maxrate), "-bufsize", str(maxrate * 2),
                "-pix_fmt", "yuv420p", "-profile:v", "high",
                "-g", str(fps * 2), "-keyint_min", str(fps * 2), "-sc_threshold", "0"] \
            + list(_COLOR_TAGS)


def _hw(enc_id: str, ffmpeg_name: str, quality_key: str, codec: Tuple[str, ...],
        pre: Tuple[str, ...] = ()) -> HardwareEncoderStrategy:
    """Small helper so the registry below stays a readable table."""
    return HardwareEncoderStrategy(enc_id, ffmpeg_name, quality_key, codec, pre)


# id -> strategy.  Registration order mirrors HARDWARE_ENCODERS priority.
ENCODER_STRATEGIES: Dict[str, EncoderStrategy] = {
    s.encoder_id: s
    for s in (
        _hw("nvenc", "h264_nvenc", "hw",
            ("-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr",
             "-cq", "{q}", "-b:v", "0",
             "-pix_fmt", "yuv420p", "-profile:v", "high") + _COLOR_TAGS),
        _hw("qsv", "h264_qsv", "hw",
            ("-c:v", "h264_qsv", "-preset", "slow", "-global_quality", "{q}",
             "-pix_fmt", "yuv420p", "-profile:v", "high") + _COLOR_TAGS),
        _hw("amf", "h264_amf", "hw",
            ("-c:v", "h264_amf", "-preset", "quality", "-rc", "cqp",
             "-qp_i", "{q}", "-qp_p", "{q+2}",
             "-pix_fmt", "yuv420p", "-profile:v", "high") + _COLOR_TAGS),
        _hw("videotoolbox", "h264_videotoolbox", "vt",
            ("-c:v", "h264_videotoolbox", "-q:v", "{q}",
             "-pix_fmt", "yuv420p", "-profile:v", "high") + _COLOR_TAGS),
        # VAAPI encodes surfaces uploaded to the GPU: device init + hwupload.
        _hw("vaapi", "h264_vaapi", "hw",
            ("-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi",
             "-rc_mode", "VBR", "-global_quality", "{q}", "-profile:v", "high") + _COLOR_TAGS,
            pre=("-init_hw_device", "vaapi=va:", "-filter_hw_device", "va")),
        SoftwareEncoderStrategy(),
    )
}


def get_encoder_strategy(encoder_id: str) -> EncoderStrategy:
    """Factory: resolve the Strategy for ``encoder_id`` (unknown -> software)."""
    return ENCODER_STRATEGIES.get(encoder_id, ENCODER_STRATEGIES[SOFTWARE_ID])


def build_video_codec_args(encoder_id: str, w: int, h: int, fps: int,
                           quality: str = "Balanced") -> Tuple[List[str], List[str]]:
    """Build ffmpeg args for the chosen backend (facade over the Strategy).

    Returns ``(global_args, codec_args)``: ``global_args`` must be placed
    before the inputs (hw device init), ``codec_args`` right before the
    output path.  GIF output is handled by the caller (not a hw concern).
    ``quality`` is one of "High" / "Balanced" / "Small" (see QUALITY_MAP).
    """
    strategy = get_encoder_strategy(encoder_id)
    return (strategy.global_args(w, h, fps, quality),
            strategy.codec_args(w, h, fps, quality))


def describe_choice(encoder_id: str, scan: EncoderScanResult) -> str:
    """Human-readable one-liner about the encoder chosen for an export."""
    info = scan.encoders.get(encoder_id)
    if encoder_id == SOFTWARE_ID:
        return "Software (libx264, YouTube-optimised)"
    if info:
        return f"{info.label} [{info.ffmpeg_name}]"
    return encoder_id

##############
#                             ══ 7 - EXPORTER ══                            
# ExportEngine (mp4/gif/png) + batch planning / dual render
# (was: exporter.py in the ten-file edition)
##############

"""Output layer: the ExportEngine (mp4/gif/png, ordered frame piping,
-14 LUFS loudnorm) plus batch planning and dual YouTube/Shorts
variants."""


#==============================================================================
# ── EXPORTER — ExportEngine + VideoExporter (mp4/gif/png)
#    (merged from studio/exporter.py in the v2.5 ten-file edition)
#==============================================================================

"""Video export pipeline (Producer-Consumer pattern).

v2.1 changes:
  * ExportEngine: the whole export logic now lives in a plain synchronous
    class so the GUI thread wrapper (VideoExporter) and the headless CLI
    share exactly the same code path.
  * Hardware-encoder auto-detection: "Auto (Hardware)" probes NVENC/QSV/AMF/
    VideoToolbox/VAAPI at export time and falls back to libx264.
  * Background ambience: procedural beds or custom audio files are mixed
    into the key-click track (audio.py, ambience section).

v2.0 fixes kept:
  * Cross-platform subprocess (no Windows-only STARTUPINFO on POSIX).
  * Frames written to ffmpeg strictly in order (ordered buffer).
  * ffmpeg stderr drained continuously (no pipe deadlock) + error tail.
  * Output formats: mp4 (H.264), gif (two-pass palette), png sequence.
"""

import os
import platform
import queue
import shutil
import subprocess
import tempfile
import threading
import wave
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, List, Optional, Protocol, Sequence, Union

import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage


#==============================================================================
# ── OBSERVER — thread-safe progress/status fan-out for exports
#==============================================================================

# Observer pattern: anything that wants live export updates (GUI progress bar,
# log panel, CLI spinner, batch report collector, tests) implements the
# ProgressObserver protocol and attaches itself to a ProgressSubject.
# ExportEngine notifies exactly one subject; the subject fans out to every
# attached observer.  The legacy plain-callable ``progress_cb`` / ``status_cb``
# parameters keep working through the CallbackObserver adapter.

class ProgressObserver(Protocol):
    """Contract for anything that receives live export progress."""

    def on_progress(self, percent: int) -> None:
        """0-100 completion percentage."""
        ...

    def on_status(self, message: str) -> None:
        """Human-readable status line."""
        ...


@dataclass
class CallbackObserver:
    """Adapter: plain callables -> ProgressObserver (legacy API bridge)."""

    on_progress: Callable[[int], None] = lambda percent: None
    on_status: Callable[[str], None] = lambda message: None


class ProgressSubject:
    """Thread-safe fan-out point (the Observer pattern subject).

    Exports run on worker threads (a QThread in the GUI, the CLI thread in
    headless mode), so attach/detach/notify are all lock-guarded.  A raising
    observer is contained: it is logged and detached instead of aborting the
    export — one broken listener must never fail a render.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._observers: List[ProgressObserver] = []

    # ------------------------------------------------------------ wiring
    def attach(self, observer: ProgressObserver) -> None:
        """Start delivering events to ``observer`` (idempotent)."""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def detach(self, observer: ProgressObserver) -> None:
        """Stop delivering events to ``observer`` (silently ignores unknown)."""
        with self._lock:
            try:
                self._observers.remove(observer)
            except ValueError:
                pass

    # ---------------------------------------------------------- emission
    def notify_progress(self, percent: int) -> None:
        self._notify("on_progress", percent)

    def notify_status(self, message: str) -> None:
        self._notify("on_status", message)

    # ----------------------------------------------------------- helpers
    def _notify(self, method: str, value: Union[int, str]) -> None:
        with self._lock:
            targets = list(self._observers)   # snapshot -> no callback under lock
        for observer in targets:
            try:
                getattr(observer, method)(value)
            except Exception as exc:          # one broken listener != failed export
                logger.warning(f"{type(observer).__name__}.{method} failed: {exc}")
                self.detach(observer)


@dataclass(eq=False)
class ExportCommand:
    """One queued export job.  ``eq=False`` keeps identity semantics so a
    running command can be used as a dict key (parallel-batch tracking)."""
    item: object
    output_path: str
    config: object
    mp: Optional[MultiPaneRenderer] = None
    status: str = "Pending"


@dataclass
class ExportResult:
    success: bool
    message: str = ""
    output_path: str = ""
    frames: int = 0
    encoder: str = ""
    cancelled: bool = False


def _popen(cmd):
    """Cross-platform quiet subprocess (fixes the v1 Windows-only crash)."""
    kwargs = dict(stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if platform.system() == "Windows":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.Popen(cmd, **kwargs)


def _build_audio(config, mp: MultiPaneRenderer, audio_path: str):
    """Render the full soundscape (key clicks + optional ambience) to a wav
    file.  Key-sound synthesis and the ambience bed are independent DSP
    stages, so they run on parallel threads (numpy releases the GIL, so
    this actually overlaps on multi-core machines — the Jr/Sr pane sounds
    are synthesized concurrently for the same reason).  The ambience bed
    also works standalone when key sounds are off.  Returns the sample
    rate, or None when nothing was generated."""
    custom = None
    if config.use_custom_wav and config.custom_wav_paths:
        custom = load_wav_samples([p for p in config.custom_wav_paths.split("|") if p])

    lead = getattr(mp, "lead_in", 0.0)   # intro card shifts all key times
    video_dur = mp.duration()
    is_jr = (config.mode == StudioMode.JR_VS_SR and len(mp.panes) >= 2)

    with ThreadPoolExecutor(max_workers=3) as pool:
        # All three DSP stages are submitted before any result is awaited,
        # so key synthesis (both panes) and the ambience bed overlap.
        if is_jr:
            sg1 = SimpleSoundGen(preset=config.jr_sound, stereo=config.stereo, custom_samples=custom)
            ts1 = [(t + lead, ch) for t, ch in mp.panes[0][1].char_timestamps()] if lead \
                else mp.panes[0][1].char_timestamps()
            sg2 = SimpleSoundGen(preset=config.sr_sound, stereo=config.stereo, custom_samples=custom)
            ts2 = [(t + lead, ch) for t, ch in mp.panes[1][1].char_timestamps()] if lead \
                else mp.panes[1][1].char_timestamps()
            f1 = pool.submit(sg1.generate_pcm, ts1, 1.0)
            f2 = pool.submit(sg2.generate_pcm, ts2, 1.0)
            sr = sg1.sr
            channels = 2 if config.stereo else 1
        else:
            sg = SimpleSoundGen(preset=config.sound_preset, stereo=config.stereo, custom_samples=custom)
            fkeys = pool.submit(sg.generate_pcm, mp.char_timestamps_all(), 1.0)
            sr = sg.sr
            channels = 2 if sg.stereo else 1

        # The bed is independent of the key PCM: render it concurrently.  Its
        # length must cover max(video, key-pcm) — we optimistically build it
        # for the video duration (the normal case) and only rebuild the rare
        # longer one afterwards, keeping the output identical.
        bed_future = pool.submit(build_ambience_bed, config, video_dur, sr)

        if is_jr:
            pcm1, pcm2 = f1.result(), f2.result()
            max_len = max(len(pcm1), len(pcm2))
            mix = np.zeros(max_len, dtype=np.int32)
            mix[:len(pcm1)] += pcm1
            mix[:len(pcm2)] += pcm2
            pcm = np.clip(mix, -32768, 32767).astype(np.int16)
        else:
            pcm = fkeys.result()

        pcm_dur = len(pcm) / (channels * sr) if len(pcm) else 0.0
        total_dur = max(video_dur, pcm_dur)
        bed = bed_future.result()
        if total_dur > video_dur + 1e-9:
            bed = build_ambience_bed(config, total_dur, sr)

    if len(pcm) == 0 and bed is None:
        return None
    if len(pcm) == 0:
        pcm = np.zeros(int(total_dur * sr), dtype=np.int16)
    pcm = mix_ambience(pcm, sr, channels, bed,
                       getattr(config, "amb_volume", 35))

    with wave.open(audio_path, "w") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return sr


def _image_to_rgb24(img: QImage) -> bytes:
    """Convert a QImage (RGB32) to packed rgb24 bytes.

    Works across PySide6 versions: newer builds return a memoryview from
    constBits() (no setsize), older ones a QByteArray.
    """
    w, h = img.width(), img.height()
    bpl = img.bytesPerLine()
    ptr = img.constBits()
    if hasattr(ptr, "setsize"):
        ptr.setsize(bpl * h)
    arr = np.frombuffer(ptr, dtype=np.uint8, count=bpl * h).reshape((h, bpl // 4, 4))
    if bpl == w * 4:
        arr = arr[:, :w, :]
    return np.ascontiguousarray(arr[:, :, 2::-1]).tobytes()


class ExportEngine:
    """Synchronous export: render frames -> ffmpeg (mp4/gif) or PNG folder.

    The GUI wraps this in a QThread; the headless CLI and the tests call
    :meth:`run` directly.  All progress is reported through callbacks, so no
    Qt signals are required.
    """

    def __init__(self, mp: MultiPaneRenderer, config, output_path: str,
                 source_names: Optional[list] = None):
        self.mp = mp
        self.config = config
        self.output = output_path
        self.source_names = list(source_names) if source_names else None
        self.fps = config.fps
        self.w, self.h = mp.frame_w, mp.frame_h

    # ------------------------------------------------------------------
    def _make_crt(self):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor, QPainter
        w, h = self.w, self.h

        def crt(img):
            p = QPainter(img)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 80))
            for y in range(0, h, 3):
                p.drawRect(0, y, w, 1)
            p.setBrush(QColor(0, 255, 0, 20))
            p.drawRect(0, 0, w, h)
            p.end()
        return crt

    # ------------------------------------------------------------------
    def run(self, progress_cb: Optional[Callable[[int], None]] = None,
            status_cb: Optional[Callable[[str], None]] = None,
            cancel_event: Optional[threading.Event] = None,
            observers: Optional[Sequence[ProgressObserver]] = None,
            max_workers: Optional[int] = None) -> ExportResult:
        """Render and encode one export.

        ``max_workers`` caps the frame-render thread pool so several
        parallel exports (GUI batch or CLI ``--jobs``) can share the
        machine's cores instead of oversubscribing them.  ``None`` uses
        cpu_count-1 (the full machine for a single export).
        """
        cancel = cancel_event or threading.Event()
        workers = max(1, int(max_workers) if max_workers
                      else (os.cpu_count() or 4) - 1)
        # Observer wiring: the legacy callback pair is adapted into observers,
        # extra observers are attached, and the body below goes through the one
        # thread-safe subject — so progress can be fanned out to any number of
        # listeners without changing a single call site in the export logic.
        subject = ProgressSubject()
        subject.attach(CallbackObserver(
            on_progress=progress_cb or (lambda p: None),
            on_status=status_cb or (lambda s: None)))
        for observer in observers or ():
            subject.attach(observer)
        progress_cb = subject.notify_progress
        status_cb = subject.notify_status

        tmp = tempfile.mkdtemp(dir=str(TEMP_DIR), prefix="export_")
        stderr_tail = deque(maxlen=30)
        proc = None
        try:
            fmt = getattr(self.config, "output_format", "mp4")
            total_dur = self.mp.duration()
            n_frames = max(1, int(total_dur * self.fps))
            audio_path = os.path.join(tmp, "audio.wav")
            crt = self._make_crt()

            # Make sure the destination directory exists (headless --output can
            # point anywhere; the GUI always uses the pre-created OUTPUT_DIR).
            try:
                parent = os.path.dirname(os.path.abspath(self.output))
                if parent:
                    os.makedirs(parent, exist_ok=True)
            except OSError as e:
                return ExportResult(False, f"Cannot create output directory: {e}",
                                    self.output)

            has_audio = False
            # GIF containers cannot carry audio — skip the (parallel but
            # not free) soundscape synthesis entirely for gif exports.
            if fmt != "gif" and (self.config.sound_enabled
                                 or getattr(self.config, "amb_enabled", False)):
                if _build_audio(self.config, self.mp, audio_path) is not None:
                    has_audio = True
                else:
                    logger.warning("Sound enabled but no PCM generated; exporting silent video")

            loud = (fmt == "mp4" and has_audio
                    and getattr(self.config, "yt_loudnorm", True))

            # Cancel may have been pressed during the (slow) audio render.
            if cancel.is_set():
                return ExportResult(False, "Cancelled", self.output, 0, cancelled=True)

            # ---------------- PNG sequence ----------------
            if fmt == "png":
                outdir = self.output
                os.makedirs(outdir, exist_ok=True)
                written = self._render_loop_png(outdir, n_frames, crt, progress_cb, status_cb, cancel,
                                                workers)
                if cancel.is_set():
                    return ExportResult(False, "Cancelled", outdir, written, cancelled=True)
                progress_cb(100)
                return ExportResult(True, "ok", outdir, written,
                                    encoder="png-sequence")

            # ---------------- build ffmpeg command (mp4/gif) ------------
            cmd = ["ffmpeg", "-y", "-nostats", "-loglevel", "error",
                   "-f", "rawvideo", "-pix_fmt", "rgb24",
                   "-s", f"{self.w}x{self.h}", "-r", str(self.fps), "-i", "pipe:0"]
            if has_audio:
                cmd += ["-i", audio_path]
            has_bgm = False
            if self.config.bgm_path and os.path.exists(self.config.bgm_path):
                cmd += ["-i", self.config.bgm_path]
                has_bgm = True

            if has_audio and has_bgm:
                loud_tail = f",{LOUDNORM_FILTER}" if loud else ""
                if self.config.bgm_duck:
                    cmd += ["-filter_complex",
                            f"[2:a]volume={self.config.bgm_volume / 100.0}[bgm];"
                            f"[bgm][1:a]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=200[bgm_duck];"
                            f"[1:a][bgm_duck]amix=inputs=2:duration=longest{loud_tail}[aout]"]
                else:
                    cmd += ["-filter_complex",
                            f"[2:a]volume={self.config.bgm_volume / 100.0}[bgm];"
                            f"[1:a][bgm]amix=inputs=2:duration=longest{loud_tail}[aout]"]
                cmd += ["-map", "0:v", "-map", "[aout]"]
            elif has_audio:
                if loud:
                    cmd += ["-af", LOUDNORM_FILTER]
                cmd += ["-map", "0:v", "-map", "1:a"]
            else:
                cmd += ["-map", "0:v"]

            chosen_encoder = ""
            if fmt == "gif":
                cmd += ["-c:v", "gif"]
            else:
                enc_id, scan = resolve_encoder_choice(getattr(self.config, "encoder", ""))
                quality = getattr(self.config, "quality_preset", "Balanced")
                pre, codec_args = build_video_codec_args(enc_id, self.w, self.h, self.fps,
                                                         quality=quality)
                # global args (hw device init) must precede the inputs
                if pre:
                    cmd = cmd[:1] + pre + cmd[1:]
                cmd += codec_args
                chosen_encoder = describe_choice(enc_id, scan)
                status_cb(f"Encoder: {chosen_encoder} | Quality: {quality}")
                if has_audio or has_bgm:
                    cmd += ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
                cmd += ["-movflags", "+faststart"]
            cmd += [self.output]

            proc = _popen(cmd)

            # drain stderr continuously to avoid pipe-buffer deadlock
            def _drain():
                try:
                    for line in iter(proc.stderr.readline, b""):
                        stderr_tail.append(line.decode("utf-8", errors="ignore").rstrip())
                except Exception:
                    pass
            drain_t = threading.Thread(target=_drain, daemon=True)
            drain_t.start()

            frame_queue: "queue.Queue[tuple]" = queue.Queue(maxsize=60)

            def render_worker(fi):
                result = None
                try:
                    if not cancel.is_set():
                        t = fi / self.fps
                        img = QImage(self.w, self.h, QImage.Format_RGB32)
                        img = self.mp.render_frame(t, img)
                        if self.config.txt_crt:
                            crt(img)
                        result = _image_to_rgb24(img)
                except Exception:
                    logger.error(f"Error rendering frame {fi}", exc_info=True)
                    result = None
                finally:
                    # Cancellable put: if the consumer went away (ffmpeg crash,
                    # timeout, cancel) workers must not block forever.  Cancel
                    # is checked FIRST so already-submitted but unstarted
                    # workers drop their frame instantly instead of each
                    # stalling 0.5 s on the full queue.
                    while True:
                        if cancel.is_set():
                            break
                        try:
                            frame_queue.put((fi, result), timeout=0.5)
                            break
                        except queue.Full:
                            pass

            max_workers = workers
            failed = False

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(render_worker, fi) for fi in range(n_frames)]
                thumb_pcts = [0.25, 0.50, 0.75] if (self.config.yt_extras and fmt == "mp4") else []
                thumb_idx = 0

                expected = 0
                buffer = {}
                while expected < n_frames and not cancel.is_set():
                    try:
                        fi, data = frame_queue.get(timeout=15)
                    except queue.Empty:
                        if cancel.is_set():
                            break
                        cancel.set()  # unblock workers before leaving the with
                        return ExportResult(False, "Rendering timed out.", self.output,
                                            expected, encoder=chosen_encoder)
                    buffer[fi] = data
                    while expected in buffer:
                        data = buffer.pop(expected)
                        if data is None:
                            failed = True
                            cancel.set()
                            break
                        try:
                            proc.stdin.write(data)
                        except BrokenPipeError:
                            cancel.set()  # unblock workers before leaving the with
                            tail = "\n".join(list(stderr_tail)[-5:])
                            return ExportResult(False, f"FFmpeg crashed:\n{tail[:800]}",
                                                self.output, expected, encoder=chosen_encoder)
                        if thumb_idx < len(thumb_pcts) and expected == int(n_frames * thumb_pcts[thumb_idx]):
                            thumb_path = os.path.splitext(self.output)[0] + f"_thumb_{thumb_idx + 1}.jpg"
                            self.mp.render_frame(expected / self.fps,
                                                 QImage(self.w, self.h, QImage.Format_RGB32)).save(thumb_path, "JPG", 95)
                            thumb_idx += 1
                        if expected % 30 == 0:
                            progress_cb(int(expected / n_frames * 100))
                            status_cb(f"Rendering frame {expected}/{n_frames}...")
                        expected += 1
                    if failed or cancel.is_set():
                        break

            try:
                proc.stdin.close()
            except Exception:
                pass
            if cancel.is_set() and proc.poll() is None:
                proc.kill()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

            if cancel.is_set():
                self._discard_partial_output()
                return ExportResult(False, "Cancelled", self.output, expected,
                                    encoder=chosen_encoder, cancelled=True)

            if fmt == "gif":
                status_cb("Optimizing GIF palette...")
                self._optimize_gif(tmp)

            rc = proc.poll()
            if rc not in (0, None):
                tail = "\n".join(list(stderr_tail)[-5:])
                return ExportResult(False, f"FFmpeg exited with code {rc}:\n{tail[:800]}",
                                    self.output, expected, encoder=chosen_encoder)

            ok = os.path.exists(self.output) and os.path.getsize(self.output) > 0
            if not ok:
                return ExportResult(False, "Export produced no output file.",
                                    self.output, expected, encoder=chosen_encoder)

            # ---------------- YouTube metadata (v2.3) ----------------
            if fmt == "mp4" and getattr(self.config, "write_metadata", True):
                status_cb("Writing YouTube metadata files...")
                names = self.source_names or [os.path.splitext(os.path.basename(self.output))[0]]
                written = write_metadata_files(
                    self.config, self.output, names,
                    typing_duration=self.mp.typing_duration(),
                    lead=getattr(self.mp, "lead_in", 0.0),
                    tail=getattr(self.mp, "tail", 0.0),
                    frame_size=(self.w, self.h))
                if written:
                    logger.info(f"YouTube metadata written: {written}")

            progress_cb(100)
            return ExportResult(True, "ok", self.output, n_frames, encoder=chosen_encoder)

        except Exception as e:
            logger.error(f"Export failed for {self.output}", exc_info=True)
            return ExportResult(False, str(e), self.output, encoder="")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    def _discard_partial_output(self):
        """Delete the unfinished output file after a cancelled export.

        An ffmpeg process killed mid-write leaves an MP4 without its moov
        atom (unplayable in every player) and a GIF without its optimized
        palette, so keeping the file only litters the output folder.  PNG
        sequences are intentionally kept: the frames written so far are
        valid standalone images the user may still want.
        """
        if getattr(self.config, "output_format", "mp4") == "png":
            return
        try:
            if os.path.exists(self.output):
                os.remove(self.output)
                logger.info(f"Cancelled export: removed partial {self.output}")
        except OSError as e:
            logger.warning(f"Could not remove partial output {self.output}: {e}")

    # ------------------------------------------------------------------
    def _render_loop_png(self, outdir, n_frames, crt, progress_cb, status_cb, cancel,
                         workers: Optional[int] = None):
        """Render the PNG sequence; returns the number of frames written."""
        workers = max(1, int(workers) if workers else (os.cpu_count() or 4) - 1)
        frame_queue: "queue.Queue[tuple]" = queue.Queue(maxsize=60)

        def render_worker(fi):
            result = None
            try:
                if not cancel.is_set():
                    t = fi / self.fps
                    img = self.mp.render_frame(t, QImage(self.w, self.h, QImage.Format_RGB32))
                    if self.config.txt_crt:
                        crt(img)
                    result = img
            except Exception:
                logger.error(f"Error rendering frame {fi}", exc_info=True)
                result = None
            finally:
                # Cancellable put (mirrors the mp4/gif loop): once the
                # consumer left, workers must not block on a full queue.
                # Cancel is checked first -> instant drop, no 0.5 s stall.
                while True:
                    if cancel.is_set():
                        break
                    try:
                        frame_queue.put((fi, result), timeout=0.5)
                        break
                    except queue.Full:
                        pass

        max_workers = workers
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(render_worker, fi) for fi in range(n_frames)]
            expected = 0
            buffer = {}
            while expected < n_frames and not cancel.is_set():
                try:
                    fi, img = frame_queue.get(timeout=15)
                except queue.Empty:
                    if cancel.is_set():
                        break
                    status_cb("Rendering timed out.")
                    cancel.set()                 # unblock the still-running workers
                    return expected
                buffer[fi] = img
                while expected in buffer:
                    img = buffer.pop(expected)
                    if img is None:
                        status_cb("Frame rendering failed.")
                        cancel.set()
                        break
                    img.save(os.path.join(outdir, f"frame_{expected:06d}.png"), "PNG")
                    if expected % 30 == 0:
                        progress_cb(int(expected / n_frames * 100))
                        status_cb(f"Writing frame {expected}/{n_frames}...")
                    expected += 1
            return expected

    def _optimize_gif(self, tmp):
        """Two-pass palette optimization for smaller, better-looking GIFs."""
        palette = os.path.join(tmp, "palette.png")
        p1 = _popen(["ffmpeg", "-y", "-nostats", "-loglevel", "error", "-i", self.output,
                     "-vf", "palettegen=max_colors=128:stats_mode=diff", palette])
        p1.wait()
        if os.path.exists(palette) and os.path.getsize(palette) > 0:
            optimized = os.path.join(tmp, "optimized.gif")
            p2 = _popen(["ffmpeg", "-y", "-nostats", "-loglevel", "error", "-i", self.output,
                         "-i", palette, "-lavfi",
                         "paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle", optimized])
            p2.wait()
            if p2.poll() == 0 and os.path.exists(optimized) and os.path.getsize(optimized) > 0:
                shutil.move(optimized, self.output)
            else:
                logger.warning("GIF palette optimization failed; keeping unoptimized gif")
        else:
            logger.warning("GIF palette generation failed; keeping unoptimized gif")


class VideoExporter(QThread):
    """GUI wrapper around ExportEngine: bridges callbacks to Qt signals.

    The pane renderer is built inside this worker thread as well, so the
    GUI stays responsive the whole time and the Cancel button is effective
    from the instant Export is clicked — including the preparation phase,
    which used to run (and freeze the window) on the GUI thread.
    """

    progress = Signal(int)
    status = Signal(str)
    finished_ok = Signal(str)
    error = Signal(str)

    def __init__(self, command: ExportCommand, strategy=None,
                 max_workers: Optional[int] = None):
        super().__init__()
        self.command = command
        self.strategy = strategy
        self._max_workers = max_workers
        self.mp = command.mp
        self.output = command.output_path
        self.fps = command.config.fps
        self.config = command.config
        self._cancel = threading.Event()
        if self.mp is not None:
            self.w, self.h = self.mp.frame_w, self.mp.frame_h
        else:
            self.w = self.h = 0
        self._engine = None

    def cancel(self):
        self._cancel.set()

    def run(self):
        try:
            if self.mp is None:
                if self._cancel.is_set():
                    self.error.emit("Cancelled")
                    return
                self.status.emit(
                    f"Preparing {os.path.basename(self.output)}...")
                try:
                    self.mp = self.strategy.build_panes(
                        self.config, [self.command.item],
                        self.config.custom_code)
                except Exception as e:
                    logger.error(
                        f"Failed to build panes for {self.output}",
                        exc_info=True)
                    self.error.emit(str(e) or "Pane build failed")
                    return
                self.command.mp = self.mp
                if not self.mp:
                    self.error.emit("Empty renderer")
                    return
                self.w, self.h = self.mp.frame_w, self.mp.frame_h

            if self._cancel.is_set():            # cancelled during pane build
                self.error.emit("Cancelled")
                return

            src = getattr(self.command.item, "path", None)
            self._engine = ExportEngine(
                self.mp, self.config, self.output,
                source_names=[os.path.basename(src)] if src else None)
            result = self._engine.run(
                progress_cb=self.progress.emit,
                status_cb=self.status.emit,
                cancel_event=self._cancel,
                max_workers=self._max_workers,
            )
        except Exception as e:                       # belt & braces: never crash the thread
            logger.error(f"Export thread failed for {self.output}", exc_info=True)
            self.error.emit(str(e) or "Export failed")
            return
        if result.success:
            self.finished_ok.emit(result.output_path)
        elif result.cancelled:
            self.error.emit("Cancelled")
        else:
            self.error.emit(result.message or "Export failed")

#==============================================================================
# ── BATCH — planning, dual variants, frame estimates
#    (merged from studio/batch.py in the v2.5 ten-file edition)
#==============================================================================

"""Batch planning: turn a configuration + list of inputs into a concrete
export queue (shared by the GUI export flow and the headless CLI).

This module is Qt-free.
"""

import copy
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional, Tuple



@dataclass
class BatchItem:
    """One planned export job."""
    input_path: str                 # may be "custom_code.py" for the custom editor
    output_path: str
    config: StudioConfig
    label: str = ""

    @property
    def name(self) -> str:
        return self.label or os.path.basename(self.output_path)


def resolve_output_name(template: str, input_path: str, output_format: str,
                        output_dir: Optional[str] = None,
                        suffix: str = "") -> str:
    """Expand the output-name template for one input file.

    ``suffix`` (e.g. "_yt" / "_shorts") is appended before the extension so
    dual YouTube+Shorts renders never overwrite each other.
    """
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    lang = EXT_TO_LANGUAGE.get(os.path.splitext(input_path)[1].lower(), "text")
    date_str = datetime.now().strftime("%Y%m%d")
    try:
        out_name = template.format(name=base_name, date=date_str, lang=lang)
    except (KeyError, IndexError, ValueError):
        logger.warning(f"Bad output template '{template}'; using default naming")
        out_name = f"{base_name}_{date_str}"
    out_dir = output_dir or str(OUTPUT_DIR)
    if output_format == "png":
        return os.path.join(out_dir, f"{out_name}{suffix}_frames")
    return os.path.join(out_dir, f"{out_name}{suffix}.{output_format}")


YT_RESOLUTION = "1920x1080"
SHORTS_RESOLUTION = "1080x1920 (9:16)"


def make_dual_variants(config: StudioConfig) -> Tuple[StudioConfig, StudioConfig]:
    """Split one config into (YouTube 16:9, Shorts 9:16) variants.

    The Shorts variant keeps every setting but swaps the resolution; the
    metadata generator automatically tags vertical outputs with #shorts.
    """
    yt = copy.deepcopy(config)
    yt.resolution = YT_RESOLUTION
    sh = copy.deepcopy(config)
    sh.resolution = SHORTS_RESOLUTION
    return yt, sh


def plan_batch(config: StudioConfig, input_paths: List[str],
               output_dir: Optional[str] = None,
               dual: bool = False) -> List[BatchItem]:
    """Plan the export queue.

    ``input_paths`` should already be filtered (e.g. checked files only);
    a ``["custom_code.py"]`` sentinel means "use the custom editor content".
    Missing files are skipped with a warning.

    With ``dual=True`` (mp4 only) every input produces TWO items: a 16:9
    YouTube version (``_yt``) and a 9:16 Shorts version (``_shorts``).
    """
    items: List[BatchItem] = []
    dual_active = dual and config.output_format == "mp4"
    for path in input_paths:
        if path != "custom_code.py" and not os.path.isfile(path):
            logger.warning(f"Skipping missing input: {path}")
            continue
        if not dual_active:
            out = resolve_output_name(config.output_template, path,
                                      config.output_format, output_dir)
            items.append(BatchItem(input_path=path, output_path=out,
                                   config=config, label=os.path.basename(path)))
            continue
        yt_cfg, sh_cfg = make_dual_variants(config)
        yt_out = resolve_output_name(config.output_template, path,
                                     config.output_format, output_dir, suffix="_yt")
        sh_out = resolve_output_name(config.output_template, path,
                                     config.output_format, output_dir, suffix="_shorts")
        base = os.path.basename(path)
        items.append(BatchItem(input_path=path, output_path=yt_out,
                               config=yt_cfg, label=f"{base} (YouTube 16:9)"))
        items.append(BatchItem(input_path=path, output_path=sh_out,
                               config=sh_cfg, label=f"{base} (Shorts 9:16)"))
    return items


def estimate_frames(config: StudioConfig, input_paths: List[str],
                    dual: bool = False) -> int:
    """Rough pre-export estimate of total frames (for progress UI / dry runs).

    v2.4: honours the auto-fit solver — when ``timing_fit`` is on, the typing
    duration is predicted with the same solver the render uses.
    """
    try:

        rate = lambda wpm: max(1.0, wpm * 5 / 60.0)
        lead, tail = branding_offsets(config)
        branding = lead + tail
        style = getattr(config, "rhythm_style", "Natural")
        intensity = (getattr(config, "rhythm_intensity", 100) or 100) / 100.0
        fit_target, _note = fit_target_for(config)   # None when fit is Off
        total = 0
        for path in input_paths:
            if path == "custom_code.py":
                code = config.custom_code or "x"
            elif os.path.isfile(path):
                try:
                    code = read_text_file(path, config.txt_clean)
                except OSError:
                    continue
            else:
                continue
            chars = max(1, len(code))
            if config.mode.value.startswith("Junior"):
                specs = [(code, config.jr_wpm, config.typo_jr, False),
                         (code, config.sr_wpm, 0.0, False)]
            elif config.mode.value.startswith("Multi"):
                specs = [(code, config.wpm_mw, config.typo_mw, False)]
            elif config.mode.value.startswith("Single Window Code"):
                specs = [(code, config.wpm_yt, config.typo_yt, False)]
            else:
                specs = [(code, config.wpm_txt, config.typo_txt, True)]

            if fit_target is not None:
                # v2.4: predict with the real solver (same profiles as render)
                def mk(w, i):
                    _, bw, tr, is_text = specs[i]
                    return TypingProfile(wpm=w, typo_rate=tr, is_text=is_text,
                                         style=style, intensity=intensity)
                res = fit_wpm([s[0] for s in specs], [s[1] for s in specs],
                              max(0.5, fit_target - branding), mk)
                dur = res.total
            else:
                base = max(s[1] for s in specs)
                dur = chars / rate(base) + 2.0
            total += int((dur + branding) * config.fps)
        if dual and config.output_format == "mp4":
            total *= 2
        return total
    except Exception:
        return 0


@dataclass
class BatchReport:
    """Outcome of a batch run."""
    ok: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    cancelled: bool = False
    items: List[dict] = field(default_factory=list)  # per-item detail dicts
    duration_sec: float = 0.0

    @property
    def success(self) -> bool:
        return not self.failed and not self.cancelled

    def summary(self) -> str:
        s = f"{len(self.ok)} ok, {len(self.failed)} failed"
        if self.cancelled:
            s += " (cancelled)"
        return s

##############
#                                ══ 8 - UI ══                               
# PySide6 GUI (dark stylesheet included)
# (was: ui.py in the ten-file edition)
##############

"""Presentation layer: the dark stylesheet and the full PySide6 MainWindow
(preview, tabs, presets, export, settings persistence)."""


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

WAV_PRESET = CUSTOM_WAV_PRESET  # was: from config import CUSTOM_WAV_PRESET as WAV_PRESET

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
        self._export_active = False
        self._active_exports = {}     # ExportCommand -> running VideoExporter
        self._item_progress = {}      # ExportCommand -> last per-item percent
        self._threads = []            # strong refs: QThreads until finished
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
        self.select_visible_btn = QPushButton("\u2611 Sel Visible")
        self.select_visible_btn.setToolTip("Check only the files currently visible under the active filters")
        self.select_visible_btn.clicked.connect(self._select_visible)
        sel_row.addWidget(self.select_visible_btn)
        self.deselect_visible_btn = QPushButton("\u2610 Desel Visible")
        self.deselect_visible_btn.setToolTip("Uncheck only the files currently visible under the active filters")
        self.deselect_visible_btn.clicked.connect(self._deselect_visible)
        sel_row.addWidget(self.deselect_visible_btn)
        sel_row.addStretch()
        sel_count_lbl = QLabel("0 selected")
        sel_count_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        sel_row.addWidget(sel_count_lbl)
        self._sel_count_lbl = sel_count_lbl
        ll.addLayout(sel_row)

        # Advanced filter row: name/path text, extension, category, folder,
        # case-sensitivity ("Ultimate UI" batch filtering)
        filter_row = QHBoxLayout(); filter_row.setContentsMargins(0, 0, 0, 0)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("\U0001F50D Filter name or path\u2026")
        self.filter_edit.setClearButtonEnabled(True)
        filter_row.addWidget(self.filter_edit, 1)
        self.ext_filter_cb = QComboBox(); self.ext_filter_cb.setFixedWidth(92)
        self.ext_filter_cb.addItem("\U0001F4C2 All")
        filter_row.addWidget(self.ext_filter_cb)
        self.type_filter_cb = QComboBox(); self.type_filter_cb.setFixedWidth(118)
        self.type_filter_cb.addItems(list(FILE_CATEGORIES.keys()))
        filter_row.addWidget(self.type_filter_cb)
        self.folder_filter_cb = QComboBox(); self.folder_filter_cb.setFixedWidth(132)
        self.folder_filter_cb.addItem("\U0001F4C1 All Folders")
        filter_row.addWidget(self.folder_filter_cb)
        self.case_chk = QCheckBox("Aa")
        self.case_chk.setToolTip("Case-sensitive name/path matching")
        filter_row.addWidget(self.case_chk)
        self.filter_sync_btn = QPushButton("\u21c4 Sync")
        self.filter_sync_btn.setFixedWidth(64)
        self.filter_sync_btn.setToolTip("Restrict the list to the file types the current mode is designed for\n(Text & Emoji \u2192 Text/Art, code modes \u2192 Code)")
        self.filter_sync_btn.clicked.connect(self._sync_filter_to_mode)
        filter_row.addWidget(self.filter_sync_btn)
        self.filter_clear_btn = QPushButton("\u2715 Clear")
        self.filter_clear_btn.setFixedWidth(64)
        self.filter_clear_btn.clicked.connect(self._clear_filter)
        filter_row.addWidget(self.filter_clear_btn)
        ll.addLayout(filter_row)
        self.filter_edit.textChanged.connect(lambda _v: self._apply_filter())
        self.ext_filter_cb.currentTextChanged.connect(lambda _v: self._apply_filter())
        self.type_filter_cb.currentTextChanged.connect(lambda _v: self._apply_filter())
        self.folder_filter_cb.currentTextChanged.connect(lambda _v: self._apply_filter())
        self.case_chk.toggled.connect(lambda _v: self._apply_filter())

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
        self.amb_music_chk = QCheckBox("Procedural music layer (royalty-free, YouTube-safe)")
        self.amb_music_chk.setToolTip(
            "Every background sound now carries its own generated soundtrack: key, chord\n"
            "progression, tempo and voices are chosen per preset (music-box rain, lo-fi jazz\n"
            "cafe, gamelan rice fields \u2026).  Deterministic and 100% generated \u2014 no copyright,\n"
            "no Content-ID claims.  Works with preset AND custom ambience files.")
        self.amb_music_chk.setChecked(True)
        agl.addRow("", self.amb_music_chk)
        self.amb_music_vol_sp = QSpinBox(); self.amb_music_vol_sp.setRange(0, 100)
        self.amb_music_vol_sp.setValue(45)
        self.amb_music_vol_sp.setSuffix("%")
        self.amb_music_vol_sp.setToolTip("Level of the music inside the ambience bed")
        agl.addRow("Music Vol:", self.amb_music_vol_sp)
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
        self.parallel_sp = QSpinBox()
        self.parallel_sp.setRange(1, 4)
        self.parallel_sp.setFixedWidth(58)
        self.parallel_sp.setToolTip(
            "Parallel renders: how many exports run at the same time.\n"
            "2+ overlaps e.g. the YouTube/Shorts variants of dual rendering;\n"
            "frame-worker threads are divided between the running renders")
        self.parallel_sp.valueChanged.connect(self._on_parallel_changed)
        br2b.addWidget(self.parallel_sp)
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
        self.cancel_btn = QPushButton("\u2716 Cancel")
        self.cancel_btn.setFixedWidth(92)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setToolTip(
            "Cancel the running render and clear the rest of the queue (Ctrl+.)")
        self.cancel_btn.setStyleSheet(
            "QPushButton { background: #f38ba8; color: #1e1e2e; font-weight: bold;"
            " border: none; border-radius: 6px; padding: 8px; }"
            "QPushButton:disabled { background: #45475a; color: #7f849c; }")
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
        self.ansi_chk = QCheckBox("ANSI Colors (ESC[…m terminal sequences)")
        self.ansi_chk.setToolTip("Translate ANSI escape sequences from .ans/.nfo terminal art into\n"
                                 "per-character colors. When off, the sequences are stripped so they\n"
                                 "never appear as glitch glyphs.")
        fl.addRow(self.ansi_chk)
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
        QShortcut(QKeySequence("Ctrl+."), self, activated=self._cancel_export)

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
            self._populate_ext_filter()
            self._populate_folder_filter()
            self._apply_filter()
            self._update_sel_count()
            if not self.thumb_headline_edit.text().strip():
                self._autofill_headline()
            self._debounce_timer.start()
            self.statusBar().showMessage(f"Added {added} file(s)", 3000)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Files", "",
            "All Supported Files (*.py *.js *.ts *.java *.c *.cpp *.cs *.go *.rs *.rb *.php *.swift "
            "*.kt *.sh *.sql *.html *.css *.json *.yaml *.yml *.toml *.txt *.md *.csv *.asc *.ans "
            "*.art *.ascii *.nfo *.diz *.emoji *.emo);;"
            "All Files (*)")
        self._add_paths(paths)

    def _clear_list(self):
        self._items.clear()
        self._item_paths.clear()
        self._refresh_table()
        self._populate_ext_filter()
        self._populate_folder_filter()
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
        self._populate_ext_filter()
        self._populate_folder_filter()
        self._apply_filter()
        self._update_sel_count()
        self._debounce_timer.start()

    def _select_all(self):
        for it in self._items:
            it.checked = True
        self._refresh_table_keep_filter(); self._update_sel_count(); self._debounce_timer.start()

    def _deselect_all(self):
        for it in self._items:
            it.checked = False
        self._refresh_table_keep_filter(); self._update_sel_count(); self._debounce_timer.start()

    # ----- advanced batch filtering (name / ext / category / folder) -----
    @staticmethod
    def _rel_folder(path: str) -> str:
        """Folder label of *path* relative to the input dir for the filter combo."""
        rel = os.path.relpath(path, str(INPUT_DIR))
        if rel.startswith(".."):
            return "[External]"
        folder = os.path.dirname(rel)
        return "[Root]" if folder in (".", "") else folder

    def _populate_ext_filter(self):
        if not hasattr(self, "ext_filter_cb"):
            return
        cur = self.ext_filter_cb.currentText()
        exts = sorted({os.path.splitext(it.path)[1].lower() for it in self._items})
        self.ext_filter_cb.blockSignals(True)
        self.ext_filter_cb.clear()
        self.ext_filter_cb.addItem("\U0001F4C2 All")
        for e in exts:
            self.ext_filter_cb.addItem(e)
        idx = self.ext_filter_cb.findText(cur)
        if idx != -1:
            self.ext_filter_cb.setCurrentIndex(idx)
        self.ext_filter_cb.blockSignals(False)

    def _populate_folder_filter(self):
        if not hasattr(self, "folder_filter_cb"):
            return
        cur = self.folder_filter_cb.currentText()
        folders = sorted({self._rel_folder(it.path) for it in self._items})
        self.folder_filter_cb.blockSignals(True)
        self.folder_filter_cb.clear()
        self.folder_filter_cb.addItem("\U0001F4C1 All Folders")
        for f in folders:
            self.folder_filter_cb.addItem(f)
        idx = self.folder_filter_cb.findText(cur)
        if idx != -1:
            self.folder_filter_cb.setCurrentIndex(idx)
        self.folder_filter_cb.blockSignals(False)

    def _sync_filter_to_mode(self):
        self.type_filter_cb.setCurrentText(
            "Text/Art" if self.config.mode == StudioMode.TEXT_EMOJI else "Code")
        self._apply_filter()
        self.statusBar().showMessage(
            f"Filter synced to mode: {self.type_filter_cb.currentText()}", 2000)

    def _apply_filter(self):
        """Hide table rows that don't match all active filter criteria."""
        if not hasattr(self, "filter_edit") or not hasattr(self, "_items"):
            return
        text = self.filter_edit.text().strip()
        ext_filter = self.ext_filter_cb.currentText()
        type_filter = self.type_filter_cb.currentText()
        folder_filter = self.folder_filter_cb.currentText()
        case_sensitive = self.case_chk.isChecked()
        needle = text if case_sensitive else text.lower()
        for i, item in enumerate(self._items):
            name, path = os.path.basename(item.path), item.path
            if not case_sensitive:
                name, path = name.lower(), path.lower()
            match_text = ((needle in name) or (needle in path)) if needle else True
            ext = os.path.splitext(item.path)[1].lower()
            match_ext = (ext_filter == "\U0001F4C2 All") or (ext == ext_filter.lower())
            match_type = True
            if type_filter != "All" and type_filter in FILE_CATEGORIES:
                match_type = ext in FILE_CATEGORIES[type_filter]
            match_folder = True
            if folder_filter != "\U0001F4C1 All Folders":
                match_folder = (self._rel_folder(item.path) == folder_filter)
            if i < self.table.rowCount():
                self.table.setRowHidden(
                    i, not (match_text and match_ext and match_type and match_folder))
        self._update_sel_count()

    def _clear_filter(self):
        self.filter_edit.clear()
        self.ext_filter_cb.setCurrentIndex(0)
        self.type_filter_cb.setCurrentIndex(0)
        self.folder_filter_cb.setCurrentIndex(0)
        self.case_chk.setChecked(False)

    def _select_visible(self):
        for i, it in enumerate(self._items):
            if i < self.table.rowCount() and not self.table.isRowHidden(i):
                it.checked = True
        self._refresh_table_keep_filter(); self._update_sel_count(); self._debounce_timer.start()

    def _deselect_visible(self):
        for i, it in enumerate(self._items):
            if i < self.table.rowCount() and not self.table.isRowHidden(i):
                it.checked = False
        self._refresh_table_keep_filter(); self._update_sel_count(); self._debounce_timer.start()

    def _refresh_table_keep_filter(self):
        self._refresh_table()

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
        # keep the active filter applied so status updates never re-reveal
        # rows the user explicitly filtered out
        self._apply_filter()

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
        self.amb_music_chk.toggled.connect(lambda v: update_config('amb_music', v))
        self.amb_music_vol_sp.valueChanged.connect(lambda v: update_config('amb_music_volume', v))
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
        self.ansi_chk.toggled.connect(lambda v: update_config('ansi_colors', v))
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
        self._export_active = True
        self._active_exports.clear()
        self._item_progress.clear()
        self._threads.clear()
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
        self.statusBar().showMessage(
            "Rendering... click \u2716 Cancel (Ctrl+.) to stop")
        self._process_export_queue()

    def _process_export_queue(self):
        """Launch queued exports while a slot is free (parallel_renders)."""
        if not self.export_commands and not self._active_exports:
            self._export_active = False
            self.export_btn.setEnabled(True)
            self.skip_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.batch_info_lbl.setText("Batch complete! Files are in the output folder.")
            QMessageBox.information(self, "Done", "Batch export complete!")
            return

        parallel = max(1, min(4, int(getattr(self.config, "parallel_renders", 1))))
        while self.export_commands and len(self._active_exports) < parallel:
            self.current_command = self.export_commands.popleft()
            self.current_command.status = "Running"
            self.current_command.item.status = "Running"
            self._launch_exporter(self.current_command)
        self._refresh_table()

    def _workers_per_render(self) -> int:
        """Frame-render threads per export so parallel renders never
        oversubscribe the machine: the total stays around cpu-1."""
        parallel = max(1, min(4, int(getattr(self.config, "parallel_renders", 1))))
        total = max(2, (os.cpu_count() or 4) - 1)
        return max(1, total // parallel)

    def _launch_exporter(self, cmd):
        """Start one VideoExporter for ``cmd`` and register it as active."""
        self.statusBar().showMessage(
            f"Preparing {os.path.basename(cmd.output_path)}...")
        # Panes are built inside the worker thread: the window stays
        # responsive during preparation and Cancel is effective from the
        # first millisecond of the render.
        exporter = VideoExporter(
            cmd, strategy=self.strategies[cmd.config.mode],
            max_workers=self._workers_per_render())
        exporter.progress.connect(lambda p, c=cmd: self._on_export_progress(c, p))
        exporter.status.connect(lambda s: self.statusBar().showMessage(s))
        exporter.finished_ok.connect(lambda p, c=cmd: self._on_item_done(c, p))
        exporter.error.connect(lambda e, c=cmd: self._on_item_failed(c, e))
        self._active_exports[cmd] = exporter
        self._item_progress[cmd] = 0
        self._threads.append(exporter)      # strong ref until QThread.finished
        self._exporter = exporter           # compat alias (closeEvent, tests)
        exporter.finished.connect(
            lambda ex=exporter: self._reap_exporter(ex))
        exporter.start()

    def _reap_exporter(self, exporter):
        """QThread.finished: drop the strong reference.  Popping earlier
        would garbage-collect a QThread whose run() is still unwinding,
        which aborts the process with 'QThread: Destroyed while running'."""
        try:
            self._threads.remove(exporter)
        except ValueError:
            pass

    def _on_parallel_changed(self, value):
        self.config.parallel_renders = int(value)

    def _on_export_progress(self, cmd, p):
        item_name = os.path.basename(cmd.output_path)
        self.statusBar().showMessage(f"Rendering {item_name}: {p}%")
        self._item_progress[cmd] = p

        done = self.batch_done
        running = len(self._active_exports)
        partial = sum(self._item_progress.values()) / 100.0
        total_progress = done + partial
        pct = int((total_progress / self.batch_total) * 100) if self.batch_total > 0 else 0

        elapsed = _time.time() - self.batch_start_time
        if total_progress > 0:
            eta = (elapsed / total_progress) * (self.batch_total - total_progress)
            eta_str = f"{int(eta // 60)}m {int(eta % 60)}s"
        else:
            eta_str = "..."

        self.batch_info_lbl.setText(
            f"{running} running \u00b7 Overall: {pct}% | ETA: {eta_str}")
        self.progress_bar.setValue(int(total_progress))

    def _on_item_done(self, cmd, path):
        cmd.item.status = "Done"
        self.batch_done += 1
        self._active_exports.pop(cmd, None)
        self._item_progress.pop(cmd, None)
        self._refresh_table()
        self.progress_bar.setValue(self.batch_done)
        self._process_export_queue()

    def _on_item_failed(self, cmd, err):
        self._active_exports.pop(cmd, None)
        self._item_progress.pop(cmd, None)
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
        """Skip the oldest still-running render (and let the queue continue)."""
        if self._active_exports:
            cmd = next(iter(self._active_exports))   # first started
            self.statusBar().showMessage(
                f"Skipping {os.path.basename(cmd.output_path)}...")
            self._active_exports[cmd].cancel()

    def _cancel_export(self):
        """Cancel the whole export queue: current render + pending items.

        Safe to call at any time \u2014 when no batch is running it just shows a
        hint and leaves the item table untouched.  The engine kills the
        running ffmpeg process and deletes the partial output file; the
        worker thread wraps up within a few hundred milliseconds.
        """
        if not self._export_active:
            self.statusBar().showMessage("No render is running.", 2000)
            return
        self._batch_cancelled = True
        self._export_active = False
        for exporter in list(self._active_exports.values()):
            exporter.cancel()
        for cmd in self.export_commands:     # still-pending items -> Cancelled
            cmd.status = "Cancelled"
            cmd.item.status = "Cancelled"
        self.export_commands.clear()
        if self.current_command:
            self.current_command.item.status = "Cancelled"
        self._item_progress.clear()
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
        self.parallel_sp.setValue(max(1, min(4, int(getattr(cfg, "parallel_renders", 1)))))
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
        self.amb_music_chk.setChecked(bool(getattr(cfg, "amb_music", True)))
        self.amb_music_vol_sp.setValue(getattr(cfg, "amb_music_volume", 45))

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
        self.ansi_chk.setChecked(cfg.ansi_colors)
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
        # Renders still running? Cancel them all and give the worker threads
        # a moment to kill ffmpeg and wrap up, so we never destroy a live
        # QThread (which would abort the interpreter hard).
        for exporter in list(self._active_exports.values()):
            if exporter.isRunning():
                exporter.cancel()
        for exporter in list(self._threads) + ([self._exporter]
                                               if self._exporter else []):
            try:
                if exporter.isRunning() and not exporter.wait(5000):
                    logger.warning("Export thread did not stop within 5s on close")
            except Exception:
                pass                                 # never block app shutdown
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
def _install_qpa_message_filter() -> None:
    """Silence the benign Qt platform warning ``propagateSizeHints()``.

    The offscreen/minimal platform plugins (and some Wayland sessions) do not
    implement ``QPlatformWindow::propagateSizeHints()``; setting window size
    constraints on an already-visible window then prints one uncategorised
    qWarning per call.  The warning is harmless — window geometry is
    unaffected — so we drop exactly those messages and pass everything else
    through with Qt's default-style formatting.  GUI startup only; the
    headless CLI and the test suite keep their full console output.
    """
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except Exception:                       # Qt-less environments: nothing to do
        return

    _LABELS = {
        QtMsgType.QtDebugMsg: "debug",
        QtMsgType.QtInfoMsg: "info",
        QtMsgType.QtWarningMsg: "warning",
        QtMsgType.QtCriticalMsg: "critical",
        QtMsgType.QtFatalMsg: "fatal",
    }

    def _handler(mode, context, message):   # noqa: ANN001 - Qt C-ABI signature
        if "propagateSizeHints" in message:
            return
        kind = _LABELS.get(mode, "message")
        print(f"qt.{kind}: {message}", file=sys.stderr)

    qInstallMessageHandler(_handler)


def run_app():
    _install_qpa_message_filter()
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

##############
#                               ══ 9 - MAIN ══                              
# headless CLI + batch planning glue (launcher lives at end of file)
# (was: main.py in the ten-file edition)
##############

import sys
from pathlib import Path

# Flat ten-file layout: make this directory importable from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent))

#==============================================================================
# ── HEADLESS — CLI parser, headless runner, JSON report
#    (merged from studio/headless.py in the v2.5 ten-file edition)
#==============================================================================

"""Headless mode: render typing videos from the command line without any
interactive GUI window (Qt runs on the offscreen platform).

Examples
--------
Render one file with defaults::

    python app.py --headless demo.py --output out/demo.mp4

Use a saved project + preset, export GIF::

    python app.py --headless --config myproject.studio --preset "GIF Loop for README" \\
        demo.py --output out/demo.gif

Dry-run (plan the batch and print estimated frames, render nothing)::

    python app.py --headless --dry-run --input demo.py other.py

Machine-readable output::

    python app.py --headless demo.py --output out.mp4 --json-report report.json

Inspect what the machine can do::

    python app.py --headless --list-encoders
    python app.py --headless --list-presets
"""

import argparse
import json
import os
import sys
import threading
import time
from dataclasses import asdict, dataclass
from typing import List, Optional


# ------------------------------------------------------------------ modes
_MODE_ALIASES = {
    "multi-window": StudioMode.MULTI_WINDOW,
    "multi_window": StudioMode.MULTI_WINDOW,
    "mw": StudioMode.MULTI_WINDOW,
    "jr-vs-sr": StudioMode.JR_VS_SR,
    "jr_vs_sr": StudioMode.JR_VS_SR,
    "jrss": StudioMode.JR_VS_SR,
    "code-yt": StudioMode.CODE_YT,
    "code_yt": StudioMode.CODE_YT,
    "yt": StudioMode.CODE_YT,
    "text-emoji": StudioMode.TEXT_EMOJI,
    "text_emoji": StudioMode.TEXT_EMOJI,
    "text": StudioMode.TEXT_EMOJI,
    # exact enum display values also accepted
    **{m.value.lower(): m for m in StudioMode},
}


def parse_mode(value: str) -> StudioMode:
    v = value.strip().lower()
    if v in _MODE_ALIASES:
        return _MODE_ALIASES[v]
    raise ValueError(f"Unknown mode '{value}'. Use one of: "
                     "multi-window, jr-vs-sr, code-yt, text-emoji")


@dataclass
class HeadlessFile:
    """Duck-typed stand-in for the GUI FileItem (strategies only need these)."""
    path: str
    checked: bool = True
    status: str = "Pending"


# "--timing-fit duration" / "audio" shorthand -> canonical config values
_FIT_ALIASES = {
    "off": "Off",
    "duration": "Target Duration",
    "target": "Target Duration",
    "target duration": "Target Duration",
    "audio": "Audio Length",
    "audio length": "Audio Length",
}


# ------------------------------------------------------------------ config
def build_config_from_args(args: argparse.Namespace) -> StudioConfig:
    """Compose the effective configuration: project file -> preset -> CLI flags.

    Pure function of ``args`` (Qt-free) so tests can exercise it directly.
    """
    config = StudioConfig()

    # 1. project file (saved from the GUI or written by hand)
    if getattr(args, "config", None):
        with open(args.config, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "config" in data and isinstance(data["config"], dict):
            data = data["config"]  # accept preset-style files too
        config = safe_config_from_dict(data)

    # 2. workflow preset (applied on top of the project file)
    if getattr(args, "preset", None):
        config = apply_preset(config, args.preset)

    # 3. explicit CLI overrides win over everything
    def set_if(attr, value):
        if value is not None:
            setattr(config, attr, value)

    if getattr(args, "mode", None):
        config.mode = parse_mode(args.mode)
    set_if("theme", args.theme)
    set_if("resolution", args.resolution)
    set_if("fps", args.fps)
    set_if("encoder", args.encoder)
    set_if("wpm_yt", args.wpm)
    set_if("wpm_mw", args.wpm)
    set_if("wpm_txt", args.wpm)
    if args.sound is not None:
        config.sound_enabled = args.sound
    if args.ambience_enabled is not None:
        config.amb_enabled = args.ambience_enabled
    if getattr(args, "key_sound", None):
        if args.key_sound in MODULAR_SOUND_PRESETS or args.key_sound == WAV_PRESET:
            config.sound_preset = args.key_sound
        else:
            logger.warning(f"Unknown key sound '{args.key_sound}'; keeping "
                           f"'{config.sound_preset}'. See --list-sounds.")
    if args.stereo is not None:
        config.stereo = args.stereo
    set_if("amb_preset", args.ambience)
    set_if("amb_path", args.ambience_file or "")
    set_if("amb_volume", args.ambience_volume)
    if getattr(args, "amb_music", None) is not None:
        config.amb_music = args.amb_music
    set_if("amb_music_volume", args.ambience_music_volume)
    if args.progress_bar is not None:
        config.progress_bar_enabled = args.progress_bar
    set_if("output_format", args.format)
    set_if("quality_preset", args.quality)
    if args.loudnorm is not None:
        config.yt_loudnorm = args.loudnorm
    if getattr(args, "dual_render", False):
        config.dual_render = True
    if args.metadata is not None:
        config.write_metadata = args.metadata
    if getattr(args, "watermark", None):
        config.wm_enabled = True
        config.wm_text = args.watermark
    if getattr(args, "intro", None):
        config.intro_enabled = True
        config.intro_text = args.intro
    if getattr(args, "outro", False):
        config.outro_enabled = True
    if getattr(args, "punch_zoom", False):
        config.punch_zoom = True
    if getattr(args, "thumb_text", None):
        config.thumb_headline = args.thumb_text
    # v2.4 smart timing
    if getattr(args, "rhythm", None):
        config.rhythm_style = args.rhythm
    if getattr(args, "rhythm_intensity", None) is not None:
        config.rhythm_intensity = args.rhythm_intensity
    if getattr(args, "timing_fit", None):
        config.timing_fit = _FIT_ALIASES.get(args.timing_fit.lower(), args.timing_fit)
    if getattr(args, "timing_target", None) is not None:
        config.timing_target = float(args.timing_target)
        if config.timing_fit == "Off":
            config.timing_fit = "Target Duration"   # --timing-target implies fit
    if getattr(args, "custom_code_file", None):
        with open(args.custom_code_file, "r", encoding="utf-8") as f:
            config.custom_code = f.read()
        config.use_custom = True
    if getattr(args, "custom_code", None):
        config.custom_code = args.custom_code
        config.use_custom = True
    return config


# ------------------------------------------------------------------ Qt boot
def ensure_qt():
    """Create a QGuiApplication on the offscreen platform (idempotent)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv[:1])
    return app


# ------------------------------------------------------------------ runner
def run_batch_headless(config: StudioConfig, input_paths: List[str],
                       output: Optional[str] = None,
                       progress: bool = True,
                       quiet: bool = False,
                       dual: bool = False,
                       save_thumbs: bool = False,
                       thumb_text: str = "",
                       jobs: int = 1) -> BatchReport:
    """Plan and export a batch without any GUI. Returns a BatchReport.

    ``jobs > 1`` renders up to that many files at the same time on worker
    threads; each export's frame pool is capped so the total thread count
    stays around cpu-1.  The report is always assembled in input order.
    """

    ensure_qt()
    strategies = make_strategies()
    items = plan_batch(config, input_paths, dual=dual)
    report = BatchReport()
    jobs = max(1, int(jobs or 1))

    # honour a single --output for single-item runs
    if output and items:
        if len(items) == 1:
            if not os.path.splitext(output)[1]:
                # extensionless --output: treat it as the output DIRECTORY
                try:
                    os.makedirs(output, exist_ok=True)
                except OSError as e:
                    logger.error(f"Cannot create output directory {output}: {e}")
                items[0].output_path = os.path.join(
                    output, os.path.basename(items[0].output_path))
            else:
                items[0].output_path = output
        else:
            logger.warning("--output ignored for multi-file batches (using output dir)")
            if not os.path.splitext(output)[1]:
                for it in items:
                    it.output_path = os.path.join(
                        output, os.path.basename(it.output_path))

    # divide the frame-render threads between the parallel exports
    per_engine_workers = None
    if jobs > 1:
        per_engine_workers = max(1, (max(2, (os.cpu_count() or 4) - 1)) // jobs)

    def export_one(task):
        """Build + render one planned item; returns its report entry."""
        idx, item = task
        cfg = item.config          # dual variants carry their own resolution
        if not quiet:
            print(f"[{idx}/{len(items)}] {item.name} -> {item.output_path}", flush=True)
        entry = {"input": item.input_path, "output": item.output_path,
                 "ok": False, "message": "", "frames": 0, "encoder": ""}
        try:
            mp = strategies[cfg.mode].build_panes(
                cfg, [HeadlessFile(item.input_path)], cfg.custom_code)
            if mp is None:
                raise RuntimeError("Empty renderer")
        except Exception as e:
            logger.error(f"Build failed for {item.name}", exc_info=True)
            entry["message"] = str(e)
            if not quiet:
                print(f"    FAILED {item.name}: {e}", file=sys.stderr, flush=True)
            return entry

        engine = ExportEngine(mp, cfg, item.output_path,
                              source_names=[os.path.basename(item.input_path)])
        last_pct = {"v": -1}

        def on_progress(pct, _name=item.name, _last=last_pct):
            if quiet or pct == _last["v"]:
                return
            _last["v"] = pct
            print(f"    {_name}: {pct}%", flush=True)

        result = engine.run(progress_cb=on_progress, status_cb=lambda s: None,
                            max_workers=per_engine_workers)
        entry.update(ok=result.success, message=result.message,
                     frames=result.frames, encoder=result.encoder)
        if result.success:
            if save_thumbs:
                head = thumb_text or cfg.thumb_headline or derive_title(item.input_path)
                try:
                    entry["thumbnails"] = save_thumbnails(mp, cfg, item.output_path,
                                                          headline=head)
                except Exception as e:
                    logger.warning(f"Thumbnail generation failed for {item.name}: {e}")
            if not quiet:
                tail = f" ({result.encoder})" if result.encoder else ""
                print(f"    OK {item.name}{tail}", flush=True)
        elif not quiet:
            print(f"    FAILED {item.name}: {result.message}", file=sys.stderr, flush=True)
        return entry

    task_list = list(enumerate(items, 1))
    if jobs > 1:
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            entries = list(ex.map(export_one, task_list))
    else:
        entries = [export_one(t) for t in task_list]

    for entry in entries:                  # input order, always
        report.items.append(entry)
        if entry["ok"]:
            report.ok.append(os.path.basename(entry["output"]))
        else:
            report.failed.append(
                f"{os.path.basename(entry['output'])}: {entry['message']}")
    return report


# ------------------------------------------------------------------ info cmds
def _cmd_list_encoders() -> int:
    scan = detect_encoders(deep=True, use_cache=True)
    print("Hardware encoder detection:")
    print("\n".join(scan.summary_lines()))
    best = scan.best()
    if best:
        print(f"\nAuto (Hardware) will use: {best.label} [{best.ffmpeg_name}]")
    else:
        print("\nNo working hardware encoder detected; Auto (Hardware) will use "
              "the software encoder (libx264).")
    return 0


def _cmd_list_presets() -> int:
    for name in all_preset_names():
        print(f"  {name:<26} {describe_preset(name)}")
    return 0


# ------------------------------------------------------------------ parser
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python app.py",
        description=f"{APP_NAME} v{APP_VERSION} — render typing videos "
                    f"(use --headless for CLI rendering)")
    p.add_argument("--headless", action="store_true", help="run without the GUI")
    p.add_argument("inputs", nargs="*", help="input files (headless mode)")

    p.add_argument("--config", help="project file (.studio JSON) to start from")
    p.add_argument("--preset", help="apply a workflow preset by name")
    p.add_argument("--input", dest="input_flags", action="append", nargs="+", default=[],
                   help="input file(s); repeatable")

    p.add_argument("--output", "-o", help="output file (single item) or directory")
    p.add_argument("--format", choices=["mp4", "gif", "png"], help="output format")
    p.add_argument("--mode", help="multi-window | jr-vs-sr | code-yt | text-emoji")
    p.add_argument("--theme", help="theme name (see --list-themes)")
    p.add_argument("--resolution", help=f"one of {', '.join(RESOLUTIONS)}")
    p.add_argument("--fps", type=int, help="frames per second (15-60)")
    p.add_argument("--wpm", type=int, help="typing speed for the current mode")
    p.add_argument("--encoder", help="encoder display name (see --list-encoders)")
    p.add_argument("--sound", action="store_true", default=None,
                   help="enable key sounds")
    p.add_argument("--no-sound", dest="sound", action="store_false",
                   help="disable key sounds")
    p.add_argument("--ambience", metavar="PRESET", help="background ambience preset")
    p.add_argument("--key-sound", metavar="PRESET",
                   help="key-SFX preset by name (see --list-sounds)")
    p.add_argument("--stereo", action="store_true", default=None,
                   help="stereo key sounds with layout panning")
    p.add_argument("--ambience-file", metavar="PATH", help="custom ambience audio file")
    p.add_argument("--ambience-volume", type=int, help="ambience volume 0-100")
    p.add_argument("--ambience-music-volume", type=int, metavar="0-100",
                   help="procedural music layer volume inside the bed (0 = off)")
    p.add_argument("--no-ambience-music", dest="amb_music", action="store_false",
                   default=None, help="disable the procedural music layer")
    p.add_argument("--enable-ambience", dest="ambience_enabled", action="store_true", default=None)
    p.add_argument("--disable-ambience", dest="ambience_enabled", action="store_false")
    p.add_argument("--progress-bar", action="store_true", default=None,
                   help="burn the animated progress bar")
    p.add_argument("--no-progress-bar", dest="progress_bar", action="store_false")
    p.add_argument("--quality", choices=["High", "Balanced", "Small"],
                   help="encode quality preset (CRF/CQ per encoder)")
    p.add_argument("--loudnorm", action="store_true", default=None,
                   help="normalize audio to YouTube loudness (-14 LUFS)")
    p.add_argument("--no-loudnorm", dest="loudnorm", action="store_false")
    p.add_argument("--dual-render", action="store_true",
                   help="render each input twice: 16:9 YouTube + 9:16 Shorts (mp4)")
    p.add_argument("--watermark", metavar="TEXT",
                   help="persistent watermark text, e.g. '@yourhandle'")
    p.add_argument("--intro", metavar="TEXT",
                   help="show a 1.5s intro title card with TEXT")
    p.add_argument("--outro", action="store_true",
                   help="show a 2.2s outro card with subscribe pill")
    p.add_argument("--punch-zoom", action="store_true",
                   help="subtle Ken Burns punch-in (9:16 outputs only)")
    p.add_argument("--thumbnail", action="store_true",
                   help="save YouTube (1280x720) + Shorts (1080x1920) thumbnails")
    p.add_argument("--jobs", "-J", type=int, default=1, metavar="N",
                   help="render up to N files at the same time in headless batch "
                        "mode (frame threads are divided between them)")
    p.add_argument("--thumb-text", metavar="TEXT", help="thumbnail headline text")
    p.add_argument("--metadata", action="store_true", default=None,
                   help="write .description.txt/.metadata.json next to mp4 exports")
    p.add_argument("--no-metadata", dest="metadata", action="store_false")
    p.add_argument("--custom-code", help="literal code/text to type")
    p.add_argument("--custom-code-file", help="file whose contents should be typed")

    p.add_argument("--rhythm", choices=["Classic", "Natural", "Cinematic"],
                   help="typing rhythm personality (default: Natural)")
    p.add_argument("--rhythm-intensity", type=int, metavar="50-150",
                   help="how expressive the rhythm is (100 = default)")
    p.add_argument("--timing-fit", metavar="MODE",
                   help="auto-adjust timings: 'duration' (fit --timing-target) "
                        "or 'audio' (fit the BGM/ambience file length)")
    p.add_argument("--timing-target", type=float, metavar="SECONDS",
                   help="target total duration for --timing-fit duration "
                        "(implies fit when given)")

    p.add_argument("--dry-run", action="store_true",
                   help="plan the batch, print outputs and estimated frames, exit")
    p.add_argument("--json-report", metavar="PATH", help="write a machine-readable report")
    p.add_argument("--list-encoders", action="store_true", help="probe hardware encoders and exit")
    p.add_argument("--list-presets", action="store_true", help="list workflow presets and exit")
    p.add_argument("--list-themes", action="store_true", help="list themes and exit")
    p.add_argument("--list-sounds", action="store_true",
                   help="list key-SFX presets and ambience soundscapes and exit")
    p.add_argument("--quiet", "-q", action="store_true", help="suppress progress output")
    p.add_argument("--verbose", "-v", action="store_true", help="debug logging to console")
    return p


def _collect_inputs(args) -> List[str]:
    inputs = list(args.inputs)
    for group in args.input_flags:
        inputs.extend(group)
    # de-dup, keep order
    seen, out = set(), []
    for p in inputs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def run_headless(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging = __import__("logging")
        logging.getLogger("TypingVideoApp").addHandler(logging.StreamHandler(sys.stderr))
        logging.getLogger("TypingVideoApp").setLevel(logging.DEBUG)

    # ---- info commands (no Qt needed except list-encoders probes ffmpeg) ----
    if getattr(args, "list_sounds", False):
        print("Key sound presets:")
        for name in MODULAR_SOUND_PRESETS:
            print(f"  {name}")
        print("\nAmbience soundscapes:")
        for name in list_ambience_presets():
            print(f"  {name}")
        return 0
    if args.list_themes:
        print("Themes:")
        for name in THEMES:
            print(f"  {name}")
        return 0
    if args.list_presets:
        return _cmd_list_presets()
    if args.list_encoders:
        return _cmd_list_encoders()

    if not args.headless:
        # not headless -> GUI (also covers `python app.py` with no args)
        if args.inputs or args.config or args.output:
            print("error: rendering inputs require --headless "
                  "(GUI mode takes no file arguments)", file=sys.stderr)
            return 2
        return run_app()

    inputs = _collect_inputs(args)
    if not inputs and not (args.custom_code or args.custom_code_file):
        print("error: no input files (and no --custom-code). "
              "Use --input FILE, positional paths, or --custom-code '...'", file=sys.stderr)
        return 2
    if not inputs:
        inputs = ["custom_code.py"]

    if args.custom_code and "custom_code.py" not in inputs:
        inputs.append("custom_code.py")

    try:
        config = build_config_from_args(args)
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: cannot load --config: {e}", file=sys.stderr)
        return 2
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    # validate resolution early
    if config.resolution not in RESOLUTIONS:
        print(f"error: unknown resolution '{config.resolution}'. "
              f"Valid: {', '.join(RESOLUTIONS)}", file=sys.stderr)
        return 2

    # --output extension wins over preset/--format when they disagree
    # (prevents encoding a GIF into an .mp4 container and vice versa)
    if getattr(args, "output", None):
        ext = os.path.splitext(args.output)[1].lower().lstrip(".")
        if ext in ("mp4", "gif", "png") and ext != config.output_format:
            logger.info(f"--output extension .{ext} overrides the configured "
                        f"format '{config.output_format}'")
            config.output_format = ext

    planned = plan_batch(config, inputs, dual=config.dual_render)
    est = estimate_frames(config, inputs, dual=config.dual_render)
    if not planned:
        print("error: nothing to export (all inputs missing?)", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"Dry run — {len(planned)} item(s), ≈{est} frames total:")
        for it in planned:
            print(f"  {it.input_path}  ->  {it.output_path}")
        fit_note = ""
        if config.timing_fit != "Off":
            _t, _n = fit_target_for(config)
            fit_note = f" | auto-fit: {config.timing_fit}" + (
                f" -> {_t:.1f}s typing" if _t is not None else "") + (
                f" ({_n})" if _n else "")
        print(f"mode={config.mode.value} | {config.resolution} @ {config.fps}fps | "
              f"format={config.output_format} | encoder={config.encoder} | "
              f"quality={config.quality_preset} | loudness={'-14 LUFS' if config.yt_loudnorm else 'raw'} | "
              f"rhythm={config.rhythm_style} ({config.rhythm_intensity}%) | "
              f"sound={'on' if config.sound_enabled else 'off'}"
              + (f" | ambience={config.amb_preset} ({config.amb_volume}%)"
                 if config.amb_enabled else "")
              + (" | dual YouTube+Shorts" if config.dual_render else "")
              + (f" | jobs={args.jobs}" if getattr(args, "jobs", 1) and args.jobs > 1 else "")
              + fit_note)
        return 0

    t0 = time.perf_counter()
    report = run_batch_headless(config, inputs, output=args.output,
                                progress=not args.quiet, quiet=args.quiet,
                                dual=config.dual_render,
                                save_thumbs=args.thumbnail,
                                thumb_text=args.thumb_text or "",
                                jobs=max(1, int(getattr(args, "jobs", 1) or 1)))
    elapsed = time.perf_counter() - t0
    report.duration_sec = elapsed

    if args.json_report:
        try:
            payload = {
                "app": APP_NAME, "version": APP_VERSION,
                "success": report.success,
                "duration_sec": round(elapsed, 2),
                "items": report.items,
            }
            with open(args.json_report, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except OSError as e:
            print(f"warning: could not write JSON report: {e}", file=sys.stderr)

    if not args.quiet:
        print(f"\nBatch finished in {elapsed:.1f}s — {report.summary()}")
    return 0 if report.success else 1

#==============================================================================
# ── LAUNCHER — GUI by default, CLI with flags
#    (merged from main.py + studio/__main__.py in the v2.5 ten-file edition)
#==============================================================================

def main() -> int:
    argv = sys.argv[1:]
    if argv and any(a.startswith("--") for a in argv):
        return run_headless(argv)
    return run_app()

##############
# ══ LAUNCHER ══ — GUI by default, CLI with flags
##############

if __name__ == "__main__":
    sys.exit(main())
