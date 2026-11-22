"""Hardware video-encoder auto-detection (NVENC/QSV/AMF/VideoToolbox/
VAAPI with libx264 fallback) and quality-preset codec arguments."""

from __future__ import annotations

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
from typing import Dict, List, Optional, Tuple

from config import TEMP_DIR
from config import logger

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
_COLOR_TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709",
               "-colorspace", "bt709", "-color_range", "tv"]

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


def build_video_codec_args(encoder_id: str, w: int, h: int, fps: int,
                           quality: str = "Balanced") -> Tuple[List[str], List[str]]:
    """Build ffmpeg args for the chosen backend.

    Returns ``(global_args, codec_args)``: ``global_args`` must be placed
    before the inputs (hw device init), ``codec_args`` right before the
    output path.  GIF output is handled by the caller (not a hw concern).
    ``quality`` is one of "High" / "Balanced" / "Small" (see QUALITY_MAP).
    """
    q = QUALITY_MAP[normalize_quality(quality)]
    pixels = w * h
    maxrate = int((pixels / 2073600.0) * 12000000)
    bufsize = maxrate * 2

    if encoder_id == "nvenc":
        pre = []
        post = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr",
                "-cq", str(q["hw"]), "-b:v", "0",
                "-pix_fmt", "yuv420p", "-profile:v", "high"] + _COLOR_TAGS
    elif encoder_id == "qsv":
        pre = []
        post = ["-c:v", "h264_qsv", "-preset", "slow", "-global_quality", str(q["hw"]),
                "-pix_fmt", "yuv420p", "-profile:v", "high"] + _COLOR_TAGS
    elif encoder_id == "amf":
        pre = []
        post = ["-c:v", "h264_amf", "-preset", "quality", "-rc", "cqp",
                "-qp_i", str(q["hw"]), "-qp_p", str(q["hw"] + 2),
                "-pix_fmt", "yuv420p", "-profile:v", "high"] + _COLOR_TAGS
    elif encoder_id == "videotoolbox":
        pre = []
        post = ["-c:v", "h264_videotoolbox", "-q:v", str(q["vt"]),
                "-pix_fmt", "yuv420p", "-profile:v", "high"] + _COLOR_TAGS
    elif encoder_id == "vaapi":
        # VAAPI encodes surfaces uploaded to the GPU: device init + hwupload.
        pre = ["-init_hw_device", "vaapi=va:", "-filter_hw_device", "va"]
        post = ["-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi",
                "-rc_mode", "VBR", "-global_quality", str(q["hw"]), "-profile:v", "high"] + _COLOR_TAGS
    else:  # software (YouTube-optimised libx264)
        pre = []
        post = ["-c:v", "libx264", "-preset", q["x264_preset"], "-crf", str(q["crf"]),
                "-maxrate", str(maxrate), "-bufsize", str(bufsize),
                "-pix_fmt", "yuv420p", "-profile:v", "high",
                "-g", str(fps * 2), "-keyint_min", str(fps * 2), "-sc_threshold", "0"] + _COLOR_TAGS
    return pre, post


def describe_choice(encoder_id: str, scan: EncoderScanResult) -> str:
    """Human-readable one-liner about the encoder chosen for an export."""
    info = scan.encoders.get(encoder_id)
    if encoder_id == SOFTWARE_ID:
        return "Software (libx264, YouTube-optimised)"
    if info:
        return f"{info.label} [{info.ffmpeg_name}]"
    return encoder_id
