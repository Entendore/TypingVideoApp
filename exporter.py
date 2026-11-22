"""Output layer: the ExportEngine (mp4/gif/png, ordered frame piping,
-14 LUFS loudnorm) plus batch planning and dual YouTube/Shorts
variants."""

from __future__ import annotations

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
from typing import Callable, Optional

import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from config import LOUDNORM_FILTER, TEMP_DIR, StudioMode
from encoders import (SOFTWARE_ID, build_video_codec_args, describe_choice,
                       resolve_encoder_choice)
from audio import SimpleSoundGen, load_wav_samples
from animation import MultiPaneRenderer
from config import logger
from audio import build_ambience_bed, mix_ambience


@dataclass
class ExportCommand:
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
    file.  The ambience bed also works standalone when key sounds are off.
    Returns the sample rate, or None when nothing was generated."""
    custom = None
    if config.use_custom_wav and config.custom_wav_paths:
        custom = load_wav_samples([p for p in config.custom_wav_paths.split("|") if p])

    lead = getattr(mp, "lead_in", 0.0)   # intro card shifts all key times
    if config.mode == StudioMode.JR_VS_SR and len(mp.panes) >= 2:
        sg1 = SimpleSoundGen(preset=config.jr_sound, stereo=config.stereo, custom_samples=custom)
        ts1 = [(t + lead, ch) for t, ch in mp.panes[0][1].char_timestamps()] if lead \
            else mp.panes[0][1].char_timestamps()
        pcm1 = sg1.generate_pcm(ts1, 1.0)
        sg2 = SimpleSoundGen(preset=config.sr_sound, stereo=config.stereo, custom_samples=custom)
        ts2 = [(t + lead, ch) for t, ch in mp.panes[1][1].char_timestamps()] if lead \
            else mp.panes[1][1].char_timestamps()
        pcm2 = sg2.generate_pcm(ts2, 1.0)

        max_len = max(len(pcm1), len(pcm2))
        mix = np.zeros(max_len, dtype=np.int32)
        mix[:len(pcm1)] += pcm1
        mix[:len(pcm2)] += pcm2
        pcm = np.clip(mix, -32768, 32767).astype(np.int16)
        sr = sg1.sr
        channels = 2 if config.stereo else 1
    else:
        sg = SimpleSoundGen(preset=config.sound_preset, stereo=config.stereo, custom_samples=custom)
        pcm = sg.generate_pcm(mp.char_timestamps_all(), 1.0)
        sr = sg.sr
        channels = 2 if sg.stereo else 1

    # Layer the ambience bed under the key clicks (v2.1).  The bed covers the
    # whole video (and stands alone when key sounds produced no PCM).
    total_dur = max(mp.duration(), len(pcm) / (channels * sr) if len(pcm) else 0.0)
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
            cancel_event: Optional[threading.Event] = None) -> ExportResult:
        cancel = cancel_event or threading.Event()
        progress_cb = progress_cb or (lambda p: None)
        status_cb = status_cb or (lambda s: None)

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
            if self.config.sound_enabled or getattr(self.config, "amb_enabled", False):
                if _build_audio(self.config, self.mp, audio_path) is not None:
                    has_audio = True
                else:
                    logger.warning("Sound enabled but no PCM generated; exporting silent video")

            loud = (fmt == "mp4" and has_audio
                    and getattr(self.config, "yt_loudnorm", True))

            # ---------------- PNG sequence ----------------
            if fmt == "png":
                outdir = self.output
                os.makedirs(outdir, exist_ok=True)
                self._render_loop_png(outdir, n_frames, crt, progress_cb, status_cb, cancel)
                if cancel.is_set():
                    return ExportResult(False, "Cancelled", outdir, n_frames, cancelled=True)
                progress_cb(100)
                return ExportResult(True, "ok", outdir, n_frames,
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
                    # timeout, cancel) workers must not block forever.
                    while True:
                        try:
                            frame_queue.put((fi, result), timeout=0.5)
                            break
                        except queue.Full:
                            if cancel.is_set():
                                break

            max_workers = max(2, (os.cpu_count() or 4) - 1)
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
                from metadata import write_metadata_files
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
    def _render_loop_png(self, outdir, n_frames, crt, progress_cb, status_cb, cancel):
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
                frame_queue.put((fi, result))

        max_workers = max(2, (os.cpu_count() or 4) - 1)
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
                    return
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
    """GUI wrapper around ExportEngine: bridges callbacks to Qt signals."""

    progress = Signal(int)
    status = Signal(str)
    finished_ok = Signal(str)
    error = Signal(str)

    def __init__(self, command: ExportCommand):
        super().__init__()
        self.command = command
        self.mp = command.mp
        self.output = command.output_path
        self.fps = command.config.fps
        self.config = command.config
        self._cancel = threading.Event()
        self.w, self.h = self.mp.frame_w, self.mp.frame_h
        src = getattr(command.item, "path", None)
        self._engine = ExportEngine(self.mp, self.config, self.output,
                                    source_names=[os.path.basename(src)] if src else None)

    def cancel(self):
        self._cancel.set()

    def run(self):
        result = self._engine.run(
            progress_cb=self.progress.emit,
            status_cb=self.status.emit,
            cancel_event=self._cancel,
        )
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

from config import (EXT_TO_LANGUAGE, INTRO_DURATION, OUTRO_DURATION,
                     OUTPUT_DIR, StudioConfig)
from config import logger, read_text_file


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
        from animation import TypingProfile
        from animation import branding_offsets, fit_target_for, fit_wpm

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
