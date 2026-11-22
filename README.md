# TypingVideoApp v1.0.0

Create beautiful "typing" videos for YouTube, Shorts, Reels and TikTok: code
that types itself with syntax highlighting, mechanical keyboard sounds, an
on-screen keyboard, and cinematic effects — exported as upload-ready MP4, GIF
or PNG sequences.

| File | Purpose |
| --- | --- |
| `app.py` | The whole application in one self-contained file (GUI + headless CLI) |
| `test_app.py` | pytest suite — `python -m pytest test_app.py` (229 tests) |
| `README.md` | This manual |

Originally grown from a single 2,500-line script through a ten-file edition —
with new overlays, more themes, new export formats and a batch of bug fixes.

## What's new in v1.0.0 — first stable release

- **Version 1.0.0** — same complete feature set; window
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
python app.py --headless demo.py -o out/demo.mp4 --ambience Rain

# apply a workflow preset; explicit output extension wins over the preset
python app.py --headless demo.py -o out/demo.gif --preset "GIF Loop for README"

# type literal custom code with the progress bar + ambience
python app.py --headless --custom-code 'print("hi")' -o out/hi.mp4 \
    --progress-bar --ambience "Night Crickets"

# batch (all positional inputs), machine-readable report, dry-run
python app.py --headless --dry-run a.py b.py c.py
python app.py --headless a.py b.py -o out_dir/ --json-report report.json

# YouTube & Shorts pack (v2.3)
python app.py --headless --dual-render a.py          # 16:9 YouTube + 9:16 Shorts
python app.py --headless demo.py -o out/demo.mp4 --quality Small --thumbnail \
    --thumb-text "Sorting Explained" --watermark "@mychannel" --intro "Watch This" \
    --outro --punch-zoom

# Smart timing (v2.4): auto-adjust timings to a length
python app.py --headless demo.py -o out/demo.mp4 --timing-fit duration --timing-target 60
python app.py --headless demo.py -o out/demo.mp4 --timing-fit audio \
    --rhythm Cinematic --rhythm-intensity 120     # end with the BGM, dramatic rhythm
python app.py --headless --dry-run demo.py --timing-target 55   # prints the fit plan

# introspection
python app.py --headless --list-encoders
python app.py --headless --list-presets
python app.py --headless --list-themes
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
python app.py        # GUI
python app.py --headless demo.py -o out/demo.mp4    # CLI
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

## Project structure

All app code lives in a single `app.py`, merged in dependency order; banner
comments mark where each former module begins. Tests live separately in
`test_app.py`.

```
app.py
├── header         # short docstring + the single `from __future__` import
├── 1 · config     # StudioConfig, constants, 12 themes, presets, helpers
├── 2 · metadata   # SEO title/description/tags/chapters writer
├── 3 · rendering  # renderers, keyboard overlay, branding cards, thumbnails
├── 4 · animation  # rhythm engine + auto-fit solver + 4 mode strategies
├── 5 · audio      # key-click DSP engine + 28 ambience soundscapes
├── 6 · encoders   # hardware encoder auto-detection + quality maps
├── 7 · exporter   # ExportEngine (mp4/gif/png) + batch planning / dual render
├── 8 · ui         # PySide6 GUI (dark stylesheet included)
└── 9 · main       # headless CLI + batch planning glue

test_app.py        # pytest suite:  python -m pytest test_app.py
README.md          # this manual
```

### Design patterns used

| Pattern | Where | What it does |
| --- | --- | --- |
| Strategy | `animation` | `BaseRenderStrategy` + one subclass per video mode |
| Strategy | `encoders` | `EncoderStrategy` protocol + per-backend ffmpeg arg templates |
| Builder | `audio` | `SoundSpecBuilder` composes layered key sounds |
| Factory Method | `audio` | `VariantPoolFactory`, `ModularSoundEngine`, `get_encoder_strategy` |
| Registry | `audio` | `AMBIENCE_PRESETS` + the `@soundscape` decorator |
| Observer | `exporter` | `ProgressObserver` protocol + thread-safe `ProgressSubject` |
| Facade | `audio` | `SimpleSoundGen` (timestamps in, mastered PCM out) |
| Pipeline | `audio` | `AudioStage` protocol + `run_stages` DSP chain |

Runtime artifacts (created next to the working directory): `input/`, `output/`,
`temp/`, `presets/` (user workflow presets), `settings.json` (auto-saved
state), `typingvideoapp.log` (debug log).
