#!/usr/bin/env python3

r"""# TypingVideoApp v1.0.0 — Ten-File Edition

Create beautiful "typing" videos for YouTube, Shorts, Reels and TikTok: code that
types itself with syntax highlighting, mechanical keyboard sounds, an on-screen
keyboard, and cinematic effects. Refactored from a single 2,500-line script into
exactly ten Python files — with new overlays, more themes, new export formats and
a batch of bug fixes.

## What's new in v1.0.0 — first stable release

- **Version 1.0.0** — same ten files, same complete feature set; window
  title, CLI, JSON reports and the debug log (`typingvideoapp.log`) now
  report 1.0.0.
- **Keyboard overlay fixes**: the on-screen keyboard no longer flickers in
  and out during typing pauses, the pressed key gets an eased sink + flash
  highlight, and the live preview shows a fading afterglow trail on
  recently pressed keys.
- **Glitch-free rendering**: the code view scrolls without sudden jumps and
  the punch-in zoom can no longer bleed across pane borders.

## What's new in v2.4 — Smart Timing (better auto-adjust timings)

### Rhythm engine (three typing personalities)
- **Natural** (new default): human typing bursts of 5-11 characters with
  micro-pauses between them, slightly longer word gaps and tightened
  punctuation pauses — the video no longer sounds like a metronome.
- **Cinematic**: more dramatic — heavier sentence and paragraph pauses,
  occasional "thinking" hesitations after block openers (`:`, `{`) and a slow
  warm-up over the first characters. Great for showcase videos.
- **Classic**: byte-for-byte the v1 timing table, kept for reproducibility.
- **Expressiveness slider** (50-150 %) scales how pronounced the personality
  is; 0 % = robotic metronome. All styles stay deterministic per seed.

### Auto-fit: solve the WPM for you (Video tab → "Timing & Rhythm")
- **Target Duration**: pick a length (or use the 30s/1m/2m/3m/5m quick chips)
  and the studio *solves* the typing speed so the finished video — intro/outro
  cards included — lands on it. The fixed-point solver converges in a few
  iterations and predicts the export to within ~0.1 s (sub-frame at 30 fps).
- **Audio Length**: the video ends *exactly* with your BGM or custom ambience
  file (probed via ffprobe, cached). Perfect for loop-perfect Shorts.
- **Multi-pane aware**: in Junior vs Senior the solver scales a common factor
  so the Junior still types slower than the Senior; Multi-Window sync now uses
  an exact per-pane solver — panes finish within milliseconds of each other
  (the old heuristic drifted by seconds).
- Graceful clamping: content that cannot physically fit the target caps at
  300 WPM and the UI/dry-run tells you so; tiny snippets are stretched down to
  15 WPM.
- **Live estimate label** under the new group shows the current total duration,
  frame count and the solved WPM while you toggle settings.
- The Shorts presets now auto-fit to **55 s** (safe under the 60 s limit), and
  **GIF Loop for README** fits to 10 s — no matter how big the snippet is.
- CLI: `--rhythm Natural|Classic|Cinematic`, `--rhythm-intensity 50-150`,
  `--timing-fit duration|audio`, `--timing-target SECONDS`; `--dry-run` prints
  the resolved fit target.

## What was new in v2.3 — the YouTube & Shorts creator pack

### Upload-ready encoding
- **Quality preset selector** (Video tab): High (CRF 16 archive master),
  Balanced (YouTube-recommended), Small (faster upload) — mapped onto the right
  rate-control knob per encoder (CRF for libx264, CQ for NVENC, global_quality
  for QSV/VAAPI, QP for AMF, q:v for VideoToolbox).
- **YouTube loudness (-14 LUFS)**: audio is normalized to YouTube's target
  loudness (`loudnorm=I=-14:TP=-1.5:LRA=11`) on every mp4 export (toggle in the
  Audio tab, on by default).
- YouTube-friendly containers everywhere: `+faststart` (moov atom first),
  `yuv420p` pixel format, bt709 color tags, AAC 256k @ 48 kHz.

### Batch YouTube + Shorts dual render
- One click (or `--dual-render`) renders **every checked file twice**: a 16:9
  YouTube version (`<name>_yt.mp4`, 1920x1080) and a 9:16 Shorts version
  (`<name>_shorts.mp4`, 1080x1920 that automatically gets `#shorts` in its
  metadata). Also available as the **Shorts Machine (Dual)** preset.

### Thumbnail studio (new YouTube & Shorts tab)
- Renders a thumbnail from the finished code frame: themed background with
  accent glow, floating editor-window card, big wrapped headline with accent
  underline and drop shadow.
- Headline is **auto-filled from the file name** (`sorting_algorithms.py` →
  "Sorting Algorithms") and editable; save 1280x720 (YouTube) or 1080x1920
  (Shorts cover) PNGs, or use `--thumbnail` in headless mode.

### Branding overlays
- **Intro title card** (1.5 s fade) and **outro card with a pulsing YouTube-
  style Subscribe pill** (2.2 s), themed to the active palette.
- **@handle watermark** in any corner with adjustable opacity.
- Cards extend the timeline properly: key-click sounds shift past the intro,
  ambience covers the whole video, progress bar tracks the typing segment.

### Shorts assistant
- **Safe-zone guides** in the preview (title top, action rail right, caption
  bottom) — preview only, never burned into exports.
- **Two-tier duration guard**: yellow above 60 s, red above 180 s.
- **Punch-in zoom**: a subtle 5% Ken Burns push-in for vertical videos.

### SEO metadata generator
- Every mp4 export (on by default) writes `<name>.description.txt` — title,
  hook, **chapters** (0:00 Intro / Coding / Outro when intro+outro are on),
  subscribe CTA and hashtags — plus `<name>.metadata.json` with tags extracted
  from the code itself, ready to paste into YouTube Studio.
- New presets: **Shorts Machine (Dual)** and **Shorts Hook (9:16)**.

## What was new in v2.2

- **Subtitles removed** — the SRT burn-in overlay, the `.srt` parser
  (`config.py`, utils section) and all `subtitle_*` settings were dropped. Old
  `settings.json` / project / preset files that still contain `subtitle_*` keys
  load cleanly (the unknown fields are ignored), so upgrading is a no-op.

## What was new in v2.1

### Hardware-encoder auto-detection
- **"Auto (Hardware)" encoder** (now the default): at export time the app probes
  NVENC (NVIDIA), QSV (Intel), AMF (AMD), VideoToolbox (macOS) and VAAPI (Linux)
  and picks the fastest one that *actually works*, falling back to the
  optimised software encoder (libx264) when no GPU is available.
- Two-stage detection: a fast `ffmpeg -encoders` scan, then a real 0.2 s test
  encode per hardware backend (builds list encoders that fail on machines
  without the GPU). Results are cached on disk keyed by the ffmpeg version, so
  detection runs once.
- **Detect button** in the Video tab shows what was found (hover for details),
  probed off the UI thread.

### Background ambience (new Audio-tab group)
- **11 procedurally generated soundscapes**: Rain, Rain & Thunder, Brown Noise,
  Café Murmur, Night Crickets, Wind, Space Drone, Vinyl Crackle, Server Room,
  Fireplace, Quiet Room — deterministic, royalty-free, rendered with numpy
  (a 60-second bed takes well under a second).
- **Custom ambience file**: any `.wav`/`.mp3`/`.m4a`/`.ogg`/`.flac` can be used
  instead — it is looped with a seamless equal-power crossfade and faded out at
  the end of the video.
- The bed is mixed under the key clicks at its own volume; it also works
  **stand-alone** with key sounds disabled (great for lo-fi aesthetic videos).

### Workflow presets
- **7 built-in one-click presets**: YouTube 1080p Code, Shorts / TikTok 9:16,
  ASMR Lo-Fi, GIF Loop for README, Fast Draft (Silent), Cinematic Code (4K),
  Podcast Room.
- **Save your own presets** (disk icon) — stored as JSON in `presets/`, shared
  between sessions; presets apply on top of the current settings so they stay
  forward-compatible.
- Batch planning is shared between the GUI and the CLI (`exporter.py`, batch
  section):
  template naming, missing-file skipping and frame estimation all behave
  identically in both front-ends.

### Headless mode (CLI)
Render without opening any window (Qt runs on the offscreen platform):

```bash
# render one file (sound + ambience + auto encoder)
python main.py --headless demo.py -o out/demo.mp4 --ambience Rain

# apply a workflow preset; explicit output extension wins over the preset
python main.py --headless demo.py -o out/demo.gif --preset "GIF Loop for README"

# type literal custom code with the progress bar + ambience
python main.py --headless --custom-code 'print("hi")' -o out/hi.mp4 \
    --progress-bar --ambience "Night Crickets"

# batch (all positional inputs), machine-readable report, dry-run
python main.py --headless --dry-run a.py b.py c.py
python main.py --headless a.py b.py -o out_dir/ --json-report report.json

# YouTube & Shorts pack (v2.3)
python main.py --headless --dual-render a.py          # 16:9 YouTube + 9:16 Shorts
python main.py --headless demo.py -o out/demo.mp4 --quality Small --thumbnail \
    --thumb-text "Sorting Explained" --watermark "@mychannel" --intro "Watch This" \
    --outro --punch-zoom

# Smart timing (v2.4): auto-adjust timings to a length
python main.py --headless demo.py -o out/demo.mp4 --timing-fit duration --timing-target 60
python main.py --headless demo.py -o out/demo.mp4 --timing-fit audio \
    --rhythm Cinematic --rhythm-intensity 120     # end with the BGM, dramatic rhythm
python main.py --headless --dry-run demo.py --timing-target 55   # prints the fit plan

# introspection
python main.py --headless --list-encoders
python main.py --headless --list-presets
python main.py --headless --list-themes
```

Exit code is `0` only when every item exported successfully; `--json-report`
writes per-item results (encoder used, frame count, error messages). Every
mp4 export also writes `<name>.description.txt` + `<name>.metadata.json`
(opt out with `--no-metadata`).

### Test suite (177 pytest tests)
```
test_app.py             # the whole suite in one file: offscreen Qt
# bootstrap + shared fixtures, unit (Qt-free), memory, performance
# and e2e layers (filter with -m memory / performance / e2e)
```

Run everything (offscreen, no display needed):

```bash
pip install pytest
python -m pytest test_app.py                 # full suite (~1-2 min)
python -m pytest -m memory              # leak guards only
python -m pytest -m performance         # benchmarks only
python -m pytest -m e2e                 # end-to-end only
```

## What was new in v2.0

### Overlays
- **Animated progress bar** — thin YouTube-style bar at the bottom of the video,
  colored by the active theme accent (or any custom hex color).

### Themes
- **10 new themes** (12 total): Tokyo Night, Nord, Monokai, GitHub Dark,
  Solarized Dark, Catppuccin Mocha, Gruvbox Dark, Rosé Pine, Everforest Dark,
  Kanagawa — alongside Dracula and One Dark.

### Visual effects
- **Ambient glow** behind the code window (toggleable).
- **4 cursor styles**: Beam, Block, Underline, Outline + optional cursor blink.
- **Typos now flash red** using the theme error color (previously they looked
  like normal characters).

### Sound
- **Custom WAV key sounds** — load your own `.wav` recordings (8/16/24/32-bit,
  any sample rate, auto down-mixed, resampled to 48 kHz and normalized) and use
  them as the key-click source for any mode.

### Export
- **New formats**: `mp4` (H.264), `gif` (two-pass palette-optimized animated
  GIF), and `png` (numbered PNG frame-sequence folder).
- **Estimated frame count** shown before exporting; ETA during batch export.
- **"Open Output" button** (Ctrl+Shift+O) to jump straight to rendered files.

### Performance
- Live preview renders at reduced scale (auto-tuned to ~960px wide) — roughly
  **4x faster** interactive previews at 1080p, 16x at 4K.
- **Syntax colors are computed once per clip** (per-character color map) instead
  of re-running pygments on every single frame — the single biggest render
  bottleneck in v1.

### UX polish
- **Drag & drop** files onto the batch table.
- **Keyboard shortcuts**: Ctrl+O add files · Ctrl+R rescan · Ctrl+S save project ·
  Ctrl+L load project · Ctrl+E export · Ctrl+Shift+O open output ·
  **Space** play/pause preview · **Left/Right** step one frame.
- **Preview loop toggle** and frame-count display.
- Full settings **auto-save & restore** (v1 only remembered the mode and theme —
  now every setting, custom code and window geometry survive restarts).
- Context menu on files: Export This File Only / Open File / Open Containing Folder.
- Refined dark UI: styled menus, tooltips, sliders, pressed states.

### Bug fixes
- Export **crashed on Linux/macOS** (called `subprocess.STARTUPINFO()`, a
  Windows-only API, unconditionally). Fixed with a guarded, cross-platform launch.
- Frames were piped to ffmpeg in **thread-completion order**, which could
  corrupt video under load. Frames are now re-ordered through an ordered buffer.
- ffmpeg's stderr pipe was never drained — long renders could **deadlock**.
  Now drained continuously and reported on failure.
- Loading a project/settings file with unknown keys raised `TypeError`; now
  forward/backward compatible.
- Unbounded per-frame token cache could grow to gigabytes on long videos;
  now bounded (and mostly unnecessary thanks to the new color map).
- FPS spinner accepted only 30/60; now 15–60 (great for GIFs).

v2.1 additionally hardens the export engine: worker threads use a cancellable
queue (no deadlock if ffmpeg dies mid-render), the output directory is created
automatically, and `ffmpeg` failures are surfaced with the captured stderr tail.

## Installation

```bash
cd TypingVideoApp
pip install "PySide6>=6.5" "numpy>=1.24" "pygments>=2.15"
pip install pytest                   # to run the test suite
```

Optional extras:
- `pip install numba` — accelerates loudness normalization.
- `ffmpeg` must be on PATH for exporting (GIF/PNG export needs ffmpeg too).

## Usage

```bash
python main.py        # GUI
python main.py --headless demo.py -o out/demo.mp4    # CLI
```

1. Put source files into `./input/` (auto-scanned) or drag & drop / Add files.
2. Pick a mode tab: Multi-Window, Junior vs Senior, Code YT, or Text & Emoji.
3. Configure theme, overlays, sound; press **Space** to preview.
4. Hit **Export**. Outputs land in `./output/`.

### Junior vs Senior JSON format

```json
{
  "title": "sorting.py",
  "language": "python",
  "junior_code": "def sort(x):\n    for i in range(len(x)):\n        for j in range(len(x)-1):\n            if x[j] > x[j+1]:\n                x[j], x[j+1] = x[j+1], x[j]\n    return x",
  "senior_code": "def sort(x):\n    return sorted(x)"
}
```

## Project structure — exactly 10 files

```
TypingVideoApp/
├── main.py        # launcher + full CLI (--headless) + this README
├── config.py      # StudioConfig, constants, 12 themes, presets, helpers
├── encoders.py    # hardware encoder auto-detection + quality maps
├── metadata.py    # SEO title/description/tags/chapters writer
├── audio.py       # key-click DSP engine + 11 ambience soundscapes
├── animation.py   # rhythm engine + auto-fit solver + 4 mode strategies
├── rendering.py   # renderers, keyboard overlay, branding cards, thumbnails
├── exporter.py    # ExportEngine (mp4/gif/png) + batch planning / dual render
├── ui.py          # PySide6 GUI (dark stylesheet included)
└── test_app.py    # 177 pytest tests (unit / memory / performance / e2e)
```

Runtime artifacts (created next to the working directory): `input/`, `output/`,
`temp/`, `presets/` (user workflow presets), `settings.json` (auto-saved
state), `typingvideoapp.log` (debug log).
"""

from __future__ import annotations

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

    python main.py --headless demo.py --output out/demo.mp4

Use a saved project + preset, export GIF::

    python main.py --headless --config myproject.studio --preset "GIF Loop for README" \\
        demo.py --output out/demo.gif

Dry-run (plan the batch and print estimated frames, render nothing)::

    python main.py --headless --dry-run --input demo.py other.py

Machine-readable output::

    python main.py --headless demo.py --output out.mp4 --json-report report.json

Inspect what the machine can do::

    python main.py --headless --list-encoders
    python main.py --headless --list-presets
"""

import argparse
import json
import os
import sys
import threading
import time
from dataclasses import asdict, dataclass
from typing import List, Optional

from exporter import BatchReport, estimate_frames, plan_batch
from config import APP_NAME, APP_VERSION, RESOLUTIONS, StudioConfig, StudioMode, safe_config_from_dict
from config import logger

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
        from config import apply_preset
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
    set_if("amb_preset", args.ambience)
    set_if("amb_path", args.ambience_file or "")
    set_if("amb_volume", args.ambience_volume)
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
                       thumb_text: str = "") -> BatchReport:
    """Plan and export a batch without any GUI. Returns a BatchReport."""
    from exporter import ExportEngine
    from animation import make_strategies

    ensure_qt()
    strategies = make_strategies()
    items = plan_batch(config, input_paths, dual=dual)
    report = BatchReport()

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

    for idx, item in enumerate(items, 1):
        cfg = item.config          # dual variants carry their own resolution
        if not quiet:
            print(f"[{idx}/{len(items)}] {item.name} -> {item.output_path}", flush=True)
        try:
            mp = strategies[cfg.mode].build_panes(
                cfg, [HeadlessFile(item.input_path)], cfg.custom_code)
            if mp is None:
                raise RuntimeError("Empty renderer")
        except Exception as e:
            logger.error(f"Build failed for {item.name}", exc_info=True)
            report.failed.append(f"{item.name}: {e}")
            continue

        source_names = [os.path.basename(item.input_path)]
        engine = ExportEngine(mp, cfg, item.output_path, source_names=source_names)
        last_pct = {"v": -1}

        def on_progress(pct, _name=item.name, _last=last_pct, _q=quiet):
            if _q or pct == _last["v"]:
                return
            _last["v"] = pct
            print(f"    {_name}: {pct}%", flush=True)

        result = engine.run(progress_cb=on_progress, status_cb=lambda s: None)
        entry = {
            "input": item.input_path, "output": item.output_path,
            "ok": result.success, "message": result.message,
            "frames": result.frames, "encoder": result.encoder,
        }
        report.items.append(entry)
        if result.success:
            report.ok.append(item.name)
            if save_thumbs:
                from metadata import derive_title
                from rendering import save_thumbnails
                head = thumb_text or cfg.thumb_headline or derive_title(item.input_path)
                thumbs = save_thumbnails(mp, cfg, item.output_path, headline=head)
                entry["thumbnails"] = thumbs
            if not quiet:
                tail = f" ({result.encoder})" if result.encoder else ""
                print(f"    OK {item.name}{tail}", flush=True)
        else:
            report.failed.append(f"{item.name}: {result.message}")
            if not quiet:
                print(f"    FAILED {item.name}: {result.message}", file=sys.stderr, flush=True)

    return report


# ------------------------------------------------------------------ info cmds
def _cmd_list_encoders() -> int:
    from encoders import detect_encoders
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
    from config import all_preset_names, describe_preset
    for name in all_preset_names():
        print(f"  {name:<26} {describe_preset(name)}")
    return 0


# ------------------------------------------------------------------ parser
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python main.py",
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
    p.add_argument("--ambience-file", metavar="PATH", help="custom ambience audio file")
    p.add_argument("--ambience-volume", type=int, help="ambience volume 0-100")
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
    if args.list_themes:
        from config import THEMES
        print("Themes:")
        for name in THEMES:
            print(f"  {name}")
        return 0
    if args.list_presets:
        return _cmd_list_presets()
    if args.list_encoders:
        return _cmd_list_encoders()

    if not args.headless:
        # not headless -> GUI (also covers `python main.py` with no args)
        if args.inputs or args.config or args.output:
            print("error: rendering inputs require --headless "
                  "(GUI mode takes no file arguments)", file=sys.stderr)
            return 2
        from ui import run_app
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
            from animation import fit_target_for
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
              + fit_note)
        return 0

    t0 = time.perf_counter()
    report = run_batch_headless(config, inputs, output=args.output,
                                progress=not args.quiet, quiet=args.quiet,
                                dual=config.dual_render,
                                save_thumbs=args.thumbnail,
                                thumb_text=args.thumb_text or "")
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
    from ui import run_app
    return run_app()


if __name__ == "__main__":
    sys.exit(main())
