"""Foundation layer: StudioConfig, constants, 12 themes, text/grapheme
utilities and workflow presets (built-in + user JSON presets)."""

from __future__ import annotations

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
APP_VERSION = "1.0.0"

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
    ".csv", ".asc", ".ascii", ".art", ".nfo", ".diz", ".emoji", ".emo"
})

EXT_TO_LANGUAGE = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".c": "c", ".cpp": "cpp",
    ".cs": "csharp", ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".kt": "kotlin", ".sh": "bash", ".sql": "sql", ".html": "html", ".css": "css", ".scss": "scss",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown", ".txt": "text",
    ".csv": "text", ".asc": "text", ".ascii": "text", ".art": "text",
    ".nfo": "text", ".diz": "text", ".emoji": "text", ".emo": "text"
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
from functools import lru_cache
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
    if not char:
        return False
    cat = unicodedata.category(char[0])
    return cat.startswith("So") or cat.startswith("Sk") or cat.startswith("Sm") or ZWJ in char or VS16 in char


def convert_shortcodes(text: str) -> str:
    for code, emoji in EMOJI_SHORTCODES.items():
        text = text.replace(code, emoji)
    return text


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
    if clean and ext not in (".asc", ".ascii", ".art", ".nfo", ".diz", ".emoji", ".emo"):
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
        if getattr(cfg, "timing_fit", "Off") != "Off":
            parts.append(f"auto-fit {cfg.timing_target:.0f}s")
        if getattr(cfg, "rhythm_style", "Natural") != "Natural":
            parts.append(f"{cfg.rhythm_style.lower()} rhythm")
        return " | ".join(parts)
    except Exception:
        return ""
