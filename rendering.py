"""Visual layer: keyboard layouts + overlay renderer, branding intro/
outro cards and watermark, the YouTube/Shorts thumbnail studio, and
the Studio/MultiPane renderers with progress bar + punch zoom."""

from __future__ import annotations

#==============================================================================
# ── KEYBOARD — 9 layouts + overlay renderer
#    (merged from studio/keyboard.py in the v2.5 ten-file edition)
#==============================================================================

"""On-screen keyboard overlay: layouts for 9 layouts and the renderer that
draws the keyboard with per-key press flash animations."""

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen

from config import THEMES, get_theme

KEYBOARD_LAYOUTS = {
    "QWERTY": [[("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1), ("]", 1), ("\\", 1.5)], [("Caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("'", 1), ("Enter", 2.25)], [("Shift", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Fn", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "AZERTY": [[("²", 1), ("&", 1), ("é", 1), ("\"", 1), ("'", 1), ("(", 1), ("-", 1), ("è", 1), ("_", 1), ("ç", 1), ("à", 1), (")", 1), ("=", 1), ("Bksp", 2)], [("Tab", 1.5), ("A", 1), ("Z", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("^", 1), ("$", 1), ("Enter", 1.5)], [("Caps", 1.75), ("Q", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), ("M", 1), ("ù", 1), ("*", 1), ("Enter", 2.25)], [("Shift", 1.25), ("<", 1), ("W", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), (",", 1), (";", 1), (":", 1), ("!", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Win", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "QWERTZ": [[("^", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("ß", 1), ("´", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Z", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("Ü", 1), ("+", 1), ("Enter", 1.5)], [("Caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), ("Ö", 1), ("Ä", 1), ("#", 1), ("Enter", 2.25)], [("Shift", 1.25), ("<", 1), ("Y", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), (",", 1), (".", 1), ("-", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Win", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "Dvorak": [[("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("[", 1), ("]", 1), ("Bksp", 2)], [("Tab", 1.5), ("'", 1), (",", 1), (".", 1), ("P", 1), ("Y", 1), ("F", 1), ("G", 1), ("C", 1), ("R", 1), ("L", 1), ("/", 1), ("=", 1), ("\\", 1.5)], [("Caps", 1.75), ("A", 1), ("O", 1), ("E", 1), ("U", 1), ("I", 1), ("D", 1), ("H", 1), ("T", 1), ("N", 1), ("S", 1), ("-", 1), ("Enter", 2.25)], [("Shift", 2.25), (";", 1), ("Q", 1), ("J", 1), ("K", 1), ("X", 1), ("B", 1), ("M", 1), ("W", 1), ("V", 1), ("Z", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Win", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "Colemak": [[("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("F", 1), ("P", 1), ("G", 1), ("J", 1), ("L", 1), ("U", 1), ("Y", 1), (";", 1), ("[", 1), ("]", 1), ("\\", 1.5)], [("Bksp", 1.75), ("A", 1), ("R", 1), ("S", 1), ("T", 1), ("D", 1), ("H", 1), ("N", 1), ("E", 1), ("I", 1), ("O", 1), ("'", 1), ("Enter", 2.25)], [("Shift", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("K", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Win", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "JIS (Japanese)": [[("半", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("^", 1), ("¥", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("@", 1), ("[", 1), ("]", 1), ("\\", 1.5)], [("Caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), (":", 1), ("Enter", 2.25)], [("Shift", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("_", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("無", 1), ("", 4.25), ("変", 1.25), ("Alt", 1.25), ("Fn", 1.25), ("Ctrl", 1.25)]],
    "Pinyin (Chinese)": [[("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1), ("]", 1), ("\\", 1.5)], [("中", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("'", 1), ("Enter", 2.25)], [("Shift", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Fn", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]],
    "Turkish Q": [[("\"", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("*", 1), ("-", 1), ("Bksp", 2)], [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("Ğ", 1), ("Ü", 1), (";", 1.5)], [("Caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), ("Ş", 1), ("İ", 1), ("Enter", 2.25)], [("Shift", 2.25), ("<", 1), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), ("Ö", 1), ("Ç", 1), (".", 1), ("Shift", 2.75)], [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("", 6.25), ("Alt", 1.25), ("Fn", 1.25), ("Menu", 1.25), ("Ctrl", 1.25)]]
}


class KeyboardOverlay:
    def __init__(self, video_w, video_h, layout_name="QWERTY", theme=None, opacity=0.82,
                 max_height=None, position="bottom_center"):
        self.video_w, self.video_h, self.theme, self.opacity = video_w, video_h, theme, opacity
        self.rows = KEYBOARD_LAYOUTS.get(layout_name, KEYBOARD_LAYOUTS["QWERTY"])
        self.char_map = {}
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
        for s, b in {"~":"`", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6", "&": "7",
                     "*": "8", "(": "9", ")": "0", "_": "-", "+=": "=", "{": "[", "}": "]", "|": "\\",
                     ":": ";", '"': "'", "<": ",", ">": ".", "?": "/"}.items():
            if b in self.char_map:
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
        return self.char_map.get(ch)

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

from config import INTRO_DURATION, OUTRO_DURATION, WM_POSITIONS
from config import THEMES

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

from config import THUMB_SHORTS_SIZE, THUMB_YT_SIZE
from metadata import derive_title
from config import THEMES


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
            from config import logger
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

from config import INTRO_DURATION, OUTRO_DURATION, StudioMode
from config import THEMES, get_theme
from config import LexerFactory, is_emoji, logger, split_graphemes

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
        """
        try:
            units = split_graphemes(code) if is_text else list(code)
            if not units:
                self._units_text = None
                self._units_colors = None
                return
            colors = [self._qc_fg] * len(units)
            if _HAS_PYGMENTS and self.language not in ("text", "ascii art", "emoji art"):
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
            self._units_text = units
            self._units_colors = colors
        except Exception:
            logger.error("prepare_code failed; falling back to per-frame lexing", exc_info=True)
            self._units_text = None
            self._units_colors = None

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
        charseq: List[Tuple[str, QColor, bool]] = []  # (char, color, matched_to_source)
        if self._units_colors is not None:
            orig_idx = 0
            units = self._units_text
            colors = self._units_colors
            for ch in display_chars[:num_visible]:
                if ch == "\b":
                    if charseq:
                        popped = charseq.pop()
                        if popped[2] and orig_idx > 0:
                            orig_idx -= 1
                else:
                    if orig_idx < len(units) and ch == units[orig_idx]:
                        charseq.append((ch, colors[orig_idx], True))
                        orig_idx += 1
                    else:
                        # typo or transient char -> theme error color
                        charseq.append((ch, self._qc_error, False))
        else:
            # fallback: no color map -> reconstruct text, lex per frame
            out_fb = []
            for ch in display_chars[:num_visible]:
                if ch == "\b":
                    if out_fb:
                        out_fb.pop()
                else:
                    out_fb.append(ch)
            for ch in out_fb:
                charseq.append((ch, self._qc_fg, False))

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
        lines: List[List[Tuple[str, QColor]]] = []
        current: List[Tuple[str, QColor]] = []
        for ch, color, _m in charseq:
            if ch == "\n":
                lines.append(current)
                current = []
            else:
                current.append((ch, color))
        lines.append(current)

        if self._units_colors is None:
            # fallback path: recolor via pygments on the visible text
            visible_text = "".join(ch for ch, _c, _m in charseq)
            tokens = self._tokenize_pygments(visible_text)
            lines, current = [], []
            for color, val in tokens:
                if "\n" in val:
                    parts = val.split("\n")
                    for i, part in enumerate(parts):
                        if part:
                            current.append((part, color))
                        if i < len(parts) - 1:
                            lines.append(current)
                            current = []
                else:
                    for ch in val:
                        current.append((ch, color))
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
                line_str = "".join(v for v, _c in line)
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

        ts_list = animator._timestamps if animator and hasattr(animator, "_timestamps") else []
        char_ts = ts_list[num_visible - 1] if num_visible > 0 and num_visible <= len(ts_list) else 0

        for si in range(max_vis):
            li = scroll + si
            if li >= total_lines:
                break
            y = y_acc
            y_acc += self.line_h

            if self.config and self.config.mode == StudioMode.TEXT_EMOJI and self.config.txt_bubbles:
                line_str = "".join(v for v, _c in lines[li])
                line_w = 0
                for v, _c in lines[li]:
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
            for v, _c in line_tokens:
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

            for ch, color in line_tokens:
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
                is_pop_char = is_emoji(ch) and 0 <= t - char_ts < 0.15
                if is_pop_char:
                    p.save()
                    progress = max(0, 1.0 - (t - char_ts) / 0.15)
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
