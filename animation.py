"""Timing layer: the TypingAnimator rhythm engine (Classic / Natural /
Cinematic), the auto-fit WPM solver (exact duration targeting), and
the four per-mode render strategies."""

from __future__ import annotations

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

from config import split_graphemes

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

from config import OUTRO_DURATION, INTRO_DURATION, StudioConfig
from config import logger

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

from config import (EXT_TO_LANGUAGE, JR_VS_SR_LAYOUTS, MULTI_WINDOW_LAYOUTS,
                     RESOLUTIONS, StudioConfig, StudioMode)
from rendering import KeyboardOverlay
from rendering import MultiPaneRenderer, StudioRenderer
from config import THEMES
from config import convert_shortcodes, logger, read_text_file


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
