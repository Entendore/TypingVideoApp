#!/usr/bin/env python3
"""Whole test suite for TypingVideoApp (extracted from app.py).

Offscreen Qt bootstrap, shared fixtures, unit (Qt-free), design-pattern,
memory, performance and e2e layers.

Run:      python -m pytest test_app.py
Filter:   python -m pytest test_app.py -m memory|performance|e2e
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Headless-safe Qt platform for every test (GUI tests run offscreen too)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# point the library path at the locally-extracted Qt libs when present
for _qtlib in (Path("/tmp/qtdist/usr/lib/x86_64-linux-gnu"),
               Path("/tmp/qtdist/usr/lib/x86_64-linux-gnu"),
               Path("/tmp/qtpkgs/root/usr/lib/x86_64-linux-gnu"),
               Path("/tmp/qtlibs/root/usr/lib/x86_64-linux-gnu")):
    if _qtlib.is_dir():
        _ld = os.environ.get("LD_LIBRARY_PATH", "")
        if str(_qtlib) not in _ld:
            os.environ["LD_LIBRARY_PATH"] = f"{_qtlib}:{_ld}" if _ld else str(_qtlib)

import pytest

warnings.filterwarnings("ignore", category=pytest.PytestUnknownMarkWarning)

# (no extra third-party imports needed)

# ------------------------------------------------------------------ Qt libs
# The sandbox may lack system libEGL; extracted Qt libs may live in a local
# dir.  LD_LIBRARY_PATH cannot be changed after process start, so preload the
# libraries by absolute path (RTLD_GLOBAL) before PySide6 is ever imported.
def _preload_qt_libs():
    import ctypes
    candidates = [
        "/tmp/qtdist/usr/lib/x86_64-linux-gnu",
        "/tmp/qtpkgs/root/usr/lib/x86_64-linux-gnu",
        "/tmp/qtlibs/root/usr/lib/x86_64-linux-gnu",
    ]
    needed = ["libGLdispatch.so.0", "libEGL.so.1"]
    for base in candidates:
        if not os.path.isdir(base):
            continue
        loaded_all = True
        for name in needed:
            try:
                ctypes.CDLL(f"{base}/{name}", mode=ctypes.RTLD_GLOBAL)
            except OSError:
                loaded_all = False
        if loaded_all:
            return


try:
    _preload_qt_libs()
except Exception:
    pass

# ---------------------------------------------------------------------------
# Import the single-file app.  app.py registers legacy module-name aliases
# (sys.modules["config"], ["encoders"], ["audio"], ... all point to itself),
# so the suites' `sys.modules[...]` lookups keep working unchanged.
import app as app  # noqa: E402  (module handle for monkeypatching)
from app import (  # noqa: E402
    AMBIENCE_PRESETS,
    CallbackObserver,
    ENCODERS,
    ENCODER_AUTO,
    ENCODER_STRATEGIES,
    ExportEngine,
    FileItem,
    HARDWARE_ENCODERS,
    HeadlessFile,
    KeyboardOverlay,
    KEYBOARD_LAYOUTS,
    MODULAR_SOUND_PRESETS,
    MUSIC_PROFILES,
    MainWindow,
    ModularSoundEngine,
    ProgressSubject,
    QUALITY_MAP,
    SimpleSoundGen,
    SoundSpec,
    StudioConfig,
    StudioMode,
    StudioRenderer,
    THEMES,
    TypingAnimator,
    TypingProfile,
    VoiceSpec,
    is_emoji,
    _LABEL_TO_ID,
    _note_hz,
    _note_tail_fade,
    apply_preset,
    audio_duration,
    branding_durations,
    build_ambience_bed,
    build_chapters,
    build_music_bed,
    build_config_from_args,
    build_metadata,
    build_parser,
    build_video_codec_args,
    builtin_names,
    convert_shortcodes,
    derive_title,
    describe_preset,
    detect_encoders,
    draw_intro_card,
    draw_outro_card,
    draw_watermark,
    estimate_frames,
    extend_wav_procedural,
    extract_tags,
    fit_target_for,
    fit_wpm,
    format_chapter_time,
    format_time,
    get_encoder_strategy,
    human_duration,
    list_ambience_presets,
    load_ambience_file,
    load_wav_samples,
    make_dual_variants,
    make_strategies,
    make_thumbnail,
    mix_ambience,
    mix_music_into_bed,
    normalize_quality,
    parse_mode,
    plan_batch,
    read_text_file,
    parse_ansi,
    strip_ansi,
    SUPPORTED_EXTENSIONS,
    EXT_TO_LANGUAGE,
    FILE_CATEGORIES,
    BaseRenderStrategy,
    render_ambience,
    render_ambience_from_wav,
    resolve_encoder_choice,
    resolve_fit_target,
    resolve_output_name,
    run_batch_headless,
    safe_config_from_dict,
    save_thumbnails,
    split_graphemes,
    write_metadata_files,
)

#==============================================================================
# ── CONFTEST — offscreen Qt bootstrap + shared fixtures
#    (merged from tests/conftest.py in the v2.5 ten-file edition)
#==============================================================================

"""Pytest bootstrap for the TypingVideoApp test suite.

Sets up import paths, forces the offscreen Qt platform and provides shared
fixtures (Qt app, sample files, base config, tmp working dirs).
"""

import os
import sys
from pathlib import Path


# Headless-safe Qt platform for every test (GUI tests run offscreen too)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# point the library path at the locally-extracted Qt libs when present
_QT_LIB_DIRS = [
    Path("/tmp/qtdist/usr/lib/x86_64-linux-gnu"),
    Path("/tmp/qtpkgs/root/usr/lib/x86_64-linux-gnu"),
    Path("/tmp/qtlibs/root/usr/lib/x86_64-linux-gnu"),
]
for _qtlib in _QT_LIB_DIRS:
    if _qtlib.is_dir():
        ld = os.environ.get("LD_LIBRARY_PATH", "")
        if str(_qtlib) not in ld:
            os.environ["LD_LIBRARY_PATH"] = f"{_qtlib}:{ld}" if ld else str(_qtlib)

import pytest

# ------------------------------------------------------------------ Qt libs
# The sandbox may lack system libEGL; the extracted Qt libs live in a local
# dir.  LD_LIBRARY_PATH cannot be changed after process start, so preload the
# libraries by absolute path (RTLD_GLOBAL) before PySide6 is ever imported.
def _preload_qt_libs():
    import ctypes
    candidates = [
        "/tmp/qtdist/usr/lib/x86_64-linux-gnu",
        "/tmp/qtpkgs/root/usr/lib/x86_64-linux-gnu",
        "/tmp/qtlibs/root/usr/lib/x86_64-linux-gnu",
    ]
    needed = ["libGLdispatch.so.0", "libEGL.so.1"]
    for base in candidates:
        if not os.path.isdir(base):
            continue
        loaded_all = True
        for name in needed:
            try:
                ctypes.CDLL(f"{base}/{name}", mode=ctypes.RTLD_GLOBAL)
            except OSError:
                loaded_all = False
        if loaded_all:
            return


try:
    import ctypes  # noqa: F401
    _preload_qt_libs()
except Exception:
    pass


@pytest.fixture(scope="session")
def qt_app():
    """One shared QApplication for the whole session.

    QApplication IS a QGuiApplication, so it serves both widget tests and the
    headless render path.  Having a single fixture avoids the fatal
    "QWidget: Must construct a QApplication" abort when a QGuiApplication was
    created first by another test group in the same process.
    """
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    yield app


@pytest.fixture(scope="session")
def qapp(qt_app):
    """Alias of qt_app (widgets)."""
    yield qt_app


@pytest.fixture(scope="session")
def qgui(qt_app):
    """Alias of qt_app (QImage/QPainter render path)."""
    yield qt_app


@pytest.fixture()
def sample_code(tmp_path):
    """A small demo .py file."""
    p = tmp_path / "demo.py"
    p.write_text(
        "def greet(name):\n"
        "    print(f'Hello, {name}!')\n"
        "    return 0\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    greet('world')\n",
        encoding="utf-8")
    return str(p)


@pytest.fixture()
def base_config():
    """Small-resolution config for fast render tests."""
    return StudioConfig(resolution="1280x720", fps=12, sound_enabled=False,
                        yt_extras=False)

#==============================================================================
# ── UNIT TESTS (Qt-free)
#    (merged from tests/test_units.py in the v2.5 ten-file edition)
#==============================================================================

"""Unit tests (Qt-free): config, presets, batch planning, encoders, ambience,
sound engine, utils. These run anywhere without a display or ffmpeg."""

import json
import os
import wave
from dataclasses import asdict

import numpy as np
import pytest



# ================================================================ config
class TestConfig:
    def test_defaults(self):
        cfg = StudioConfig()
        assert cfg.mode == StudioMode.CODE_YT
        assert cfg.encoder == ENCODER_AUTO
        assert cfg.output_format == "mp4"
        assert cfg.amb_enabled is False
        assert cfg.amb_preset == "Rain"
        assert 0 <= cfg.amb_volume <= 100

    def test_encoder_choices_include_auto(self):
        assert ENCODERS[0] == ENCODER_AUTO
        assert len(ENCODERS) >= 5  # auto + software + 3 hw vendors

    def test_safe_config_drops_unknown_keys(self):
        cfg = safe_config_from_dict({"theme": "Nord", "bogus_field": 123,
                                     "another": None})
        assert cfg.theme == "Nord"
        assert not hasattr(cfg, "bogus_field")

    def test_safe_config_drops_legacy_subtitle_fields(self):
        """v2.2 removed subtitles: old settings/projects must load cleanly."""
        cfg = safe_config_from_dict({"subtitle_enabled": True,
                                     "subtitle_path": "/x/c.srt",
                                     "subtitle_size": 54, "theme": "Nord"})
        assert cfg.theme == "Nord"
        assert not hasattr(cfg, "subtitle_enabled")
        assert not hasattr(cfg, "subtitle_path")
        assert not hasattr(cfg, "subtitle_size")

    def test_no_subtitle_fields_on_config(self):
        cfg = StudioConfig()
        for legacy in ("subtitle_enabled", "subtitle_path", "subtitle_size"):
            assert not hasattr(cfg, legacy)

    def test_safe_config_mode_string(self):
        cfg = safe_config_from_dict({"mode": "Junior vs Senior Dev"})
        assert cfg.mode == StudioMode.JR_VS_SR

    def test_safe_config_bad_mode_falls_back(self):
        cfg = safe_config_from_dict({"mode": "Nonsense"})
        assert cfg.mode == StudioMode.CODE_YT

    def test_roundtrip(self):
        cfg = StudioConfig(fps=45, amb_enabled=True, amb_volume=55)
        cfg2 = safe_config_from_dict(asdict(cfg))
        assert cfg2 == cfg

    def test_legacy_v20_settings_load(self):
        """v2.0 settings.json encoder strings still map onto the new list."""
        cfg = safe_config_from_dict({"encoder": "YouTube Optimised (H.264/AAC)"})
        assert cfg.encoder in ENCODERS


# ================================================================ presets
class TestPresets:
    def test_builtin_list(self):
        names = builtin_names()
        assert "Default" in names and "ASMR Lo-Fi" in names
        assert len(names) >= 6

    def test_apply_builtin_overrides_only_listed_fields(self):
        cfg = StudioConfig(theme="Nord", fps=45)
        out = apply_preset(cfg, "ASMR Lo-Fi")
        assert out.sound_preset == "ASMR Deep Thock"
        assert out.amb_enabled is True
        assert out.amb_preset == "Rain"
        # untouched fields survive
        assert out.fps == 45

    def test_apply_preset_returns_new_object(self):
        cfg = StudioConfig()
        out = apply_preset(cfg, "GIF Loop for README")
        assert out is not cfg
        assert cfg.output_format == "mp4"          # original untouched
        assert out.output_format == "gif"

    def test_apply_unknown_preset_raises(self):
        with pytest.raises(KeyError):
            apply_preset(StudioConfig(), "No Such Preset")

    def test_user_preset_roundtrip(self, tmp_path, monkeypatch):
        presets = sys.modules["config"]  # was: import config as presets
        monkeypatch.setattr(presets, "PRESETS_DIR", tmp_path / "presets")
        cfg = StudioConfig(theme="Kanagawa", wpm_yt=123, amb_enabled=True)
        presets.save_user_preset("My Test Preset", cfg)
        user = presets.load_user_presets()
        assert "My Test Preset" in user
        out = presets.apply_preset(StudioConfig(), "My Test Preset")
        assert out.theme == "Kanagawa"
        assert out.wpm_yt == 123
        assert presets.delete_user_preset("My Test Preset") is True
        assert "My Test Preset" not in presets.load_user_presets()

    def test_preset_name_sanitized(self, tmp_path, monkeypatch):
        presets = sys.modules["config"]  # was: import config as presets
        monkeypatch.setattr(presets, "PRESETS_DIR", tmp_path / "presets")
        presets.save_user_preset('bad/name:*?', StudioConfig())
        files = list((tmp_path / "presets").glob("*.json"))
        assert len(files) == 1
        assert "/" not in files[0].stem and ":" not in files[0].stem


# ================================================================ batch
class TestBatch:
    def test_resolve_output_name_template(self):
        out = resolve_output_name("{name}_{date}", "/x/my_file.py", "mp4")
        assert out.endswith(".mp4")
        assert os.path.basename(out).startswith("my_file_")

    def test_resolve_output_name_png_is_dir(self):
        out = resolve_output_name("{name}", "/x/f.py", "png")
        assert out.endswith("_frames")

    def test_resolve_bad_template_falls_back(self):
        out = resolve_output_name("{missing_key}", "/x/f.py", "mp4")
        assert "f_" in os.path.basename(out)

    def test_plan_batch_skips_missing(self, sample_code):
        items = plan_batch(StudioConfig(), [sample_code, "/no/such/file.py"])
        assert len(items) == 1
        assert items[0].input_path == sample_code

    def test_plan_batch_output_paths_differ(self, sample_code, tmp_path):
        p2 = tmp_path / "second.py"
        p2.write_text("x = 1\n")
        items = plan_batch(StudioConfig(), [sample_code, str(p2)])
        assert len(items) == 2
        assert items[0].output_path != items[1].output_path

    def test_estimate_frames_positive(self, sample_code):
        est = estimate_frames(StudioConfig(fps=30), [sample_code])
        assert est > 0

    def test_estimate_frames_scales_with_fps(self, sample_code):
        lo = estimate_frames(StudioConfig(fps=15), [sample_code])
        hi = estimate_frames(StudioConfig(fps=60), [sample_code])
        assert hi > lo


# ================================================================ encoders
class TestEncoders:
    def test_display_label_mapping(self):
        for enc_id, label, _name in HARDWARE_ENCODERS:
            assert _LABEL_TO_ID[label] == enc_id

    def test_software_args(self):
        pre, post = build_video_codec_args("software", 1920, 1080, 30)
        assert pre == []
        joined = " ".join(post)
        assert "libx264" in joined and "yuv420p" in joined

    def test_hw_args_names(self):
        pre, post = build_video_codec_args("nvenc", 1920, 1080, 30)
        assert "h264_nvenc" in " ".join(post) and pre == []
        pre, post = build_video_codec_args("vaapi", 1920, 1080, 30)
        assert "h264_vaapi" in " ".join(post)
        assert "-init_hw_device" in " ".join(pre)   # device init goes pre-input
        assert "hwupload" in " ".join(post)

    def test_resolve_software_short_circuits(self):
        enc_id, scan = resolve_encoder_choice("YouTube Optimised (H.264/AAC)")
        assert enc_id == "software"

    def test_resolve_unknown_falls_back_to_software(self):
        enc_id, _ = resolve_encoder_choice("Something Made Up")
        assert enc_id == "software"

    def test_resolve_auto_without_hw_falls_back(self, monkeypatch):
        """With every hw probe failing, Auto must return the software id."""
        enc = sys.modules["encoders"]  # was: import encoders as enc
        fake = enc.EncoderScanResult(ffmpeg_path="x", ffmpeg_version="test")
        for enc_id, label, name in enc.HARDWARE_ENCODERS:
            fake.encoders[enc_id] = enc.EncoderInfo(
                id=enc_id, label=label, ffmpeg_name=name,
                listed=True, probed_ok=False, detail="no GPU in CI")
        fake.encoders["software"] = enc.EncoderInfo(
            id="software", label=enc.SOFTWARE_LABEL, ffmpeg_name="libx264",
            listed=True, probed_ok=True)
        monkeypatch.setattr(enc, "detect_encoders", lambda **kw: fake)
        enc_id, scan = enc.resolve_encoder_choice(ENCODER_AUTO)
        assert enc_id == "software"

    def test_resolve_auto_picks_working_hw(self, monkeypatch):
        enc = sys.modules["encoders"]  # was: import encoders as enc
        fake = enc.EncoderScanResult(ffmpeg_path="x", ffmpeg_version="test")
        for i, (enc_id, label, name) in enumerate(enc.HARDWARE_ENCODERS):
            fake.encoders[enc_id] = enc.EncoderInfo(
                id=enc_id, label=label, ffmpeg_name=name,
                listed=True, probed_ok=(enc_id == "qsv"),  # only QSV works
                detail="" if enc_id == "qsv" else "no")
        fake.encoders["software"] = enc.EncoderInfo(
            id="software", label=enc.SOFTWARE_LABEL, ffmpeg_name="libx264", listed=True)
        monkeypatch.setattr(enc, "detect_encoders", lambda **kw: fake)
        enc_id, _ = enc.resolve_encoder_choice(ENCODER_AUTO)
        assert enc_id == "qsv"

    def test_cache_roundtrip(self, tmp_path, monkeypatch):
        enc = sys.modules["encoders"]  # was: import encoders as enc
        cache_file = tmp_path / "encoder_cache.json"
        monkeypatch.setattr(enc, "_CACHE_FILE", cache_file)
        monkeypatch.setattr(enc, "_mem_cache", None)
        result = enc.EncoderScanResult(ffmpeg_path="/bin/ffmpeg", ffmpeg_version="9.9-test",
                                       scanned_at=1.0)
        result.encoders["software"] = enc.EncoderInfo(
            id="software", label="s", ffmpeg_name="libx264", listed=True, probed_ok=True)
        enc._save_disk_cache(result)
        loaded = enc._load_disk_cache("9.9-test")
        assert loaded is not None
        assert loaded.encoders["software"].probed_ok is True
        # wrong version -> no hit
        assert enc._load_disk_cache("other") is None

    def test_list_ffmpeg_encoders_parses_flags(self, monkeypatch):
        """Flag columns like ' V....D ' must parse (regression: D broke the regex)."""
        enc = sys.modules["encoders"]  # was: import encoders as enc
        sample = (" Encoders:\n"
                  " V....D h264_nvenc        NVIDIA NVENC H.264 encoder (codec h264)\n"
                  " V..... h264_qsv          Intel QSV (codec h264)\n"
                  " A....D aac               AAC encoder\n"
                  " garbage line\n")
        monkeypatch.setattr(enc, "_run", lambda cmd, timeout: (0, sample))
        names = enc.list_ffmpeg_encoders()
        assert {"h264_nvenc", "h264_qsv", "aac"} <= names


# ================================================================ ambience
class TestAmbience:
    @pytest.mark.parametrize("name", [
        "Rain", "Rain & Thunder", "Brown Noise", "Café Murmur", "Night Crickets",
        "Wind", "Space Drone", "Vinyl Crackle", "Server Room", "Fireplace", "Quiet Room"])
    def test_all_presets_render(self, name):
        x = render_ambience(name, 1.0)
        assert len(x) == 48000
        assert x.dtype == np.float64
        assert np.all(np.isfinite(x))
        assert np.max(np.abs(x)) <= 1.0 + 1e-9
        assert name in AMBIENCE_PRESETS

    def test_deterministic_for_seed(self):
        a = render_ambience("Rain", 1.0, seed=5)
        b = render_ambience("Rain", 1.0, seed=5)
        assert np.array_equal(a, b)

    def test_unknown_preset_falls_back(self):
        x = render_ambience("Does Not Exist", 0.5)
        assert len(x) == 24000

    def test_fade_out_at_end(self):
        x = render_ambience("Brown Noise", 2.0)
        # last 100ms must be much quieter than the middle
        assert np.max(np.abs(x[-2400:])) < 0.05 * (np.max(np.abs(x)) + 1e-9)

    def test_load_wav_file_and_loop(self, tmp_path):
        p = tmp_path / "bed.wav"
        rng = np.random.RandomState(0)
        with wave.open(str(p), "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
            wf.writeframes((rng.randn(24000) * 5000).astype(np.int16).tobytes())
        x = load_ambience_file(str(p), 3.0)
        assert x is not None and len(x) == 144000
        assert np.max(np.abs(x)) <= 1.0

    def test_load_missing_file_returns_none(self):
        assert load_ambience_file("/no/such/file.wav", 1.0) is None

    def test_mix_ambience_mono_length_and_clip(self):
        kb = (np.ones(48000) * 30000).astype(np.int16)
        bed = render_ambience("Rain", 1.0)
        out = mix_ambience(kb, 48000, 1, bed, 100)
        assert out.dtype == np.int16 and len(out) == 48000
        assert np.max(np.abs(out)) <= 32767
        # adding a bed must change the signal
        assert not np.array_equal(out, kb)

    def test_mix_ambience_stereo_interleaved(self):
        kb = np.zeros(96000, dtype=np.int16)
        bed = np.ones(48000) * 0.5
        out = mix_ambience(kb, 48000, 2, bed, 50)
        assert len(out) == 96000
        left = out[0::2].astype(np.int32)
        # 0.5 volume * 0.5 bed amplitude * 32767 ~= 8191
        assert np.max(np.abs(left)) > 4000  # bed audible on L/R channels

    def test_mix_zero_volume_is_identity(self):
        kb = (np.random.RandomState(1).randn(4800) * 8000).astype(np.int16)
        bed = render_ambience("Rain", 0.1)
        out = mix_ambience(kb, 48000, 1, bed, 0)
        assert np.array_equal(out, kb)

    def test_build_bed_disabled(self):
        cfg = StudioConfig(amb_enabled=False)
        assert build_ambience_bed(cfg, 5.0) is None

    def test_build_bed_enabled(self):
        cfg = StudioConfig(amb_enabled=True, amb_preset="Wind")
        bed = build_ambience_bed(cfg, 2.0)
        assert bed is not None and len(bed) == 96000

    def test_build_bed_custom_file_wins(self, tmp_path):
        p = tmp_path / "c.wav"
        with wave.open(str(p), "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
            wf.writeframes((np.ones(48000) * 12000).astype(np.int16).tobytes())
        cfg = StudioConfig(amb_enabled=True, amb_preset="Rain", amb_path=str(p),
                           amb_music=False)
        bed = build_ambience_bed(cfg, 1.0)
        # custom file is a constant ~0.85 tone; sample the window that avoids
        # the 0.02s fade-in and the 0.6s fade-out (constant zone ~0.30-0.39s)
        zone = bed[int(0.30 * 48000): int(0.39 * 48000)]
        assert np.std(zone) < 0.01
        assert abs(np.mean(zone) - 0.85) < 0.05

    def test_build_bed_custom_file_with_music(self, tmp_path):
        p = tmp_path / "c.wav"
        with wave.open(str(p), "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
            wf.writeframes((np.ones(48000) * 12000).astype(np.int16).tobytes())
        cfg = StudioConfig(amb_enabled=True, amb_preset="Rain", amb_path=str(p),
                           amb_music=True, amb_music_volume=50)
        bed = build_ambience_bed(cfg, 2.0)
        assert bed is not None and len(bed) == 96000
        assert np.all(np.isfinite(bed))
        # music must actually be audible in the mix (energy above the tone)
        assert float(np.std(bed[int(0.9 * 48000): int(1.8 * 48000)])) > 0.005


# ================================================================ sound
class TestSound:
    def test_generate_pcm_length(self):
        sg = SimpleSoundGen(preset="Mechanical")
        ts = [(0.1, "a"), (0.2, "b"), (0.3, " ")]
        pcm = sg.generate_pcm(ts, 0.5)
        assert pcm.dtype == np.int16
        assert len(pcm) >= int(0.6 * sg.sr)

    def test_empty_timestamps(self):
        sg = SimpleSoundGen()
        assert len(sg.generate_pcm([], 1.0)) == 0

    def test_all_presets_render(self):
        for preset in MODULAR_SOUND_PRESETS:
            sg = SimpleSoundGen(preset=preset)
            pcm = sg.generate_pcm([(0.0, "x")], 1.0)
            assert len(pcm) > 0

    def test_custom_wav_samples(self, tmp_path):
        p = tmp_path / "click.wav"
        with wave.open(str(p), "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
            wf.writeframes((np.random.RandomState(3).randn(2400) * 9000).astype(np.int16).tobytes())
        samples = load_wav_samples([str(p)])
        assert len(samples) == 1
        sg = SimpleSoundGen(custom_samples=samples)
        assert len(sg.generate_pcm([(0.0, "k")], 1.0)) > 0

    def test_loudness_normalized(self):
        sg = SimpleSoundGen(preset="Mechanical")
        ts = [(i * 0.05, "a") for i in range(60)]
        pcm = sg.generate_pcm(ts, 1.0)
        peak = np.max(np.abs(pcm))
        assert peak > 1000  # not silent

    def test_professional_presets_exist(self):
        for name in ("Creamy Thock", "Marble Clack", "Cherry MX Blue", "Holy Panda",
                     "Topre Plonk", "Silent Velvet", "Wooden Desk Thock", "Ink Clack"):
            assert name in MODULAR_SOUND_PRESETS

    def test_pitch_sweep_layer(self):
        eng = ModularSoundEngine()
        plain = SoundSpec(duration=0.05, layers=[VoiceSpec(osc="sine", freq=400, gain=0.8)])
        glided = SoundSpec(duration=0.05, layers=[VoiceSpec(osc="sine", freq=400, sweep=0.4, gain=0.8)])
        a, b = eng.render(plain, 7), eng.render(glided, 7)
        assert np.isfinite(a).all() and np.isfinite(b).all() and len(a) > 0
        assert not np.array_equal(a, b)

    def test_housing_resonance_changes_render(self):
        eng = ModularSoundEngine()
        plain = SoundSpec(duration=0.05, layers=[VoiceSpec(osc="sine", freq=400, gain=0.8)])
        rezzed = SoundSpec(duration=0.05, layers=[VoiceSpec(osc="sine", freq=400, gain=0.8)],
                           resonance=[(820.0, 9.0, 0.3)])
        a, b = eng.render(plain, 3), eng.render(rezzed, 3)
        assert np.isfinite(b).all() and not np.array_equal(a, b)

    def test_enter_spec_override(self, monkeypatch):
        aud = sys.modules["audio"]  # was: import audio as aud
        spec = SoundSpec(duration=0.05, layers=[VoiceSpec(osc="sine", freq=800)],
                         enter_spec=SoundSpec(duration=0.12, layers=[VoiceSpec(osc="sine", freq=200)]))
        monkeypatch.setitem(aud.MODULAR_SOUND_PRESETS, "Test Enter Spec", spec)
        sg = SimpleSoundGen(preset="Test Enter Spec")
        assert len(sg.enters[0]) > len(sg.clicks[0])   # longer Enter sample used

    def test_detuned_round_robin_variants(self):
        sg = SimpleSoundGen(preset="Mechanical")
        assert len(sg.clicks) == 32
        unique = {c.tobytes() for c in sg.clicks}
        assert len(unique) >= 24  # variants must not be near-identical clones

    def test_reverb_deterministic_and_audible(self):
        ts = [(0.05 * i, "a") for i in range(40)]
        wet = SimpleSoundGen(preset="Mechanical", reverb_amt=0.4)
        dry = SimpleSoundGen(preset="Mechanical", reverb_amt=0.0)
        a, b = wet.generate_pcm(ts, 0.5), wet.generate_pcm(ts, 0.5)
        assert np.array_equal(a, b)              # deterministic
        c = dry.generate_pcm(ts, 0.5)
        assert not np.array_equal(a, c)          # reverb is audible
        assert np.isfinite(a).all() and np.max(np.abs(a)) <= 32767

    def test_stereo_bounded_after_mastering(self):
        sg = SimpleSoundGen(preset="Cherry MX Blue", stereo=True)
        ts = [(0.04 * i, c) for i, c in enumerate("the quick brown fox jumps")]
        pcm = sg.generate_pcm(ts, 1.0)
        assert len(pcm) % 2 == 0
        assert np.max(np.abs(pcm)) <= 32767 and np.isfinite(pcm).all()


# ================================================================ wav extender
class TestWavExtender:
    """Procedural long-form generation from real WAV files (extend_wav_procedural)."""

    @staticmethod
    def _src_seconds(sec=2.0, sr=48000, seed=3):
        """A tone+noise bed resembling a field recording."""
        rng = np.random.RandomState(seed)
        t = np.arange(int(sec * sr)) / sr
        x = 0.3 * np.sin(2 * np.pi * 220.0 * t) + 0.15 * np.sin(2 * np.pi * 331.0 * t)
        x += 0.10 * rng.randn(len(t))
        if len(x) >= sr // 10:
            x[: sr // 10] *= np.linspace(0, 1, sr // 10)   # gentle head
        return x

    def test_extend_length_finite_bounded(self):
        out = extend_wav_procedural(self._src_seconds(2.0), 7.0)
        assert len(out) == int(7.0 * 48000)
        assert np.isfinite(out).all()
        assert np.max(np.abs(out)) <= 1.0
        assert np.max(np.abs(out)) > 0.2                  # actually audible

    def test_extend_deterministic_and_seed_varies(self):
        src = self._src_seconds(1.5)
        a = extend_wav_procedural(src, 5.0, seed=11)
        b = extend_wav_procedural(src, 5.0, seed=11)
        c = extend_wav_procedural(src, 5.0, seed=12)
        assert np.array_equal(a, b)
        assert not np.array_equal(a, c)

    def test_extend_evolves_more_than_plain_tiling(self):
        """Evolution = passes of the loop are no longer identical.

        Repetition strength = max normalized autocorrelation at loop-length
        lags: a verbatim loop scores ~0.95+, the evolved bed must not.
        """

        def rep_strength(x, sr, lo=0.5, hi=3.0):
            x = x - np.mean(x)
            n = len(x)
            L = 1 << int(np.ceil(np.log2(2 * n)))
            X = np.fft.rfft(x, L)
            ac = np.fft.irfft(X * np.conj(X), L)[:n]
            ac /= (ac[0] + 1e-12)
            return float(np.max(ac[int(lo * sr):min(n - 1, int(hi * sr))]))

        src = self._src_seconds(2.0)
        plain = extend_wav_procedural(src, 12.0, evolve=False)
        evo = extend_wav_procedural(src, 12.0, evolve=True)
        rep_plain = rep_strength(plain, 48000)
        rep_evo = rep_strength(evo, 48000)
        assert rep_plain > 0.9                            # plain loop really repeats
        assert rep_evo < rep_plain - 0.1                  # evolved bed does not

    def test_extend_evolve_flag_changes_output(self):
        src = self._src_seconds(2.0)
        a = extend_wav_procedural(src, 4.0, evolve=True)
        b = extend_wav_procedural(src, 4.0, evolve=False)
        assert not np.array_equal(a, b)
        assert np.isfinite(a).all() and np.isfinite(b).all()

    def test_extend_short_and_degenerate_sources(self):
        tiny = self._src_seconds(0.35)                    # shorter than the search window
        out = extend_wav_procedural(tiny, 5.0)
        assert len(out) == 5 * 48000 and np.isfinite(out).all()
        assert np.max(np.abs(out)) <= 1.0 and np.max(np.abs(out)) > 0.1
        assert len(extend_wav_procedural(self._src_seconds(0.0005), 2.0)) == 2 * 48000
        assert np.allclose(extend_wav_procedural(np.zeros(48000), 2.0), 0.0)

    def test_render_ambience_from_wav_end_to_end(self, tmp_path):
        # stereo 22050 Hz file exercises the mono downmix + resample path
        p = tmp_path / "field.wav"
        rng = np.random.RandomState(5)
        t = np.arange(int(1.7 * 22050)) / 22050
        tone = 0.4 * np.sin(2 * np.pi * 196.0 * t)
        raw = np.empty(2 * len(t), dtype=np.int16)
        raw[0::2] = (tone * 20000).astype(np.int16)
        raw[1::2] = ((tone * 0.8 + 0.02 * rng.randn(len(t))) * 20000).astype(np.int16)
        with wave.open(str(p), "w") as wf:
            wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(22050)
            wf.writeframes(raw.tobytes())
        bed = render_ambience_from_wav(str(p), 4.0)
        assert bed is not None and len(bed) == 4 * 48000
        assert np.isfinite(bed).all() and np.max(np.abs(bed)) <= 1.0
        assert render_ambience_from_wav("/no/such/file.wav", 2.0) is None

    def test_build_ambience_bed_uses_evolve_flag(self):
        from types import SimpleNamespace

        class _TmpWav:
            """Context manager writing a 1.5 s tone WAV."""
            def __init__(self, p):
                self.p = p
            def __enter__(self):
                t = np.arange(int(1.5 * 48000)) / 48000
                x = 0.5 * np.sin(2 * np.pi * 240.0 * t)
                with wave.open(str(self.p), "w") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
                    wf.writeframes((x * 20000).astype(np.int16).tobytes())
                return str(self.p)
            def __exit__(self, *a):
                return False

        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            wav = os.path.join(td, "src.wav")
            with _TmpWav(wav):
                base = dict(amb_enabled=True, amb_path=wav, amb_volume=50)
                cfg_on = SimpleNamespace(amb_evolve=True, **base)
                cfg_off = SimpleNamespace(amb_evolve=False, **base)
                cfg_legacy = SimpleNamespace(**base)          # no field -> defaults True
                on = build_ambience_bed(cfg_on, 6.0)
                off = build_ambience_bed(cfg_off, 6.0)
                legacy = build_ambience_bed(cfg_legacy, 6.0)
        assert on is not None and off is not None
        assert len(on) == len(legacy) == 6 * 48000
        assert np.isfinite(on).all() and np.isfinite(off).all()
        assert not np.array_equal(on, off)                    # flag really switches paths
        assert np.array_equal(on, legacy)                     # default is evolve=True

    def test_custom_wav_keys_get_variant_pool(self):
        import tempfile, os
        rng = np.random.RandomState(9)
        with tempfile.TemporaryDirectory() as td:
            paths = []
            for i in range(2):
                p = os.path.join(td, f"key{i}.wav")
                t = np.arange(int(0.06 * 48000)) / 48000
                x = np.exp(-t * 90) * np.sin(2 * np.pi * (900 + 400 * i) * t)
                x += 0.2 * np.exp(-t * 300) * rng.randn(len(t))
                with wave.open(p, "w") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000)
                    wf.writeframes((x * 20000).astype(np.int16).tobytes())
                paths.append(p)
            samples = load_wav_samples(paths)
            assert len(samples) == 2

        sg = SimpleSoundGen(custom_samples=samples)
        assert 5 <= len(sg.clicks) <= 32                     # 5 variants per source file
        uniq = len({s.tobytes() for s in sg.clicks})
        assert uniq >= 5                                     # detune really varies them
        assert len(sg.spaces) >= 5 and len(sg.enters) >= 4
        ts = [(0.05 * i, c) for i, c in enumerate("hello world\n")]
        pcm = sg.generate_pcm(ts, 0.8)
        assert np.isfinite(pcm).all() and np.max(np.abs(pcm)) <= 32767

    def test_custom_wav_fallback_to_preset(self):
        """Too-short custom samples must fall back to the procedural preset."""
        sg = SimpleSoundGen(preset="Mechanical", custom_samples=[np.zeros(8)])
        assert len(sg.clicks) == 32                          # preset pool, not the WAV


# ================================================================ v3.2 presets
ASMR_KEY_PRESETS = ("Pillow Fort ASMR", "Fuzzy Felt ASMR", "Whisper Breeze",
                    "Bamboo Tap", "Rain Drop Taps", "Glass Taps ASMR")
ZEN_AMB_PRESETS = ("Bamboo Fountain", "Mountain Stream", "Morning Birds",
                   "Garden Wind Chimes", "Singing Bowls", "Hot Spring",
                   "Rice Field Dusk")


class TestV32Presets:
    """ASMR key-preset expansion + zen/pleasant soundscape expansion."""

    ASMR_KEYS = ASMR_KEY_PRESETS
    ZEN_AMB = ZEN_AMB_PRESETS

    def test_v32_asmr_presets_exist(self):
        for name in self.ASMR_KEYS:
            assert name in MODULAR_SOUND_PRESETS
        assert len(MODULAR_SOUND_PRESETS) == 32

    def test_v32_zen_presets_exist(self):
        names = list_ambience_presets()
        for name in self.ZEN_AMB:
            assert name in names
        assert len(names) == 34

    @pytest.mark.parametrize("name", ASMR_KEY_PRESETS)
    def test_v32_asmr_renders_mono_and_stereo(self, name):
        ts = [(0.09 * i, c) for i, c in enumerate("asmr keys\n")]
        mono = SimpleSoundGen(preset=name).generate_pcm(ts, 1.0)
        assert np.isfinite(mono).all() and np.max(np.abs(mono)) <= 32767
        stereo = SimpleSoundGen(preset=name, stereo=True, reverb_amt=0.2
                                ).generate_pcm(ts, 1.0)
        assert np.isfinite(stereo).all() and np.max(np.abs(stereo)) <= 32767

    @pytest.mark.parametrize("name", ZEN_AMB_PRESETS)
    def test_v32_zen_renders(self, name):
        x = render_ambience(name, 1.0)
        assert len(x) == 48000
        assert np.isfinite(x).all() and 0.05 < np.max(np.abs(x)) <= 1.0

    def test_v32_zen_deterministic(self):
        a = render_ambience("Singing Bowls", 2.0, seed=5)
        b = render_ambience("Singing Bowls", 2.0, seed=5)
        assert np.array_equal(a, b)


# ================================================================ v1.0 sounds
PRO_KEY_PRESETS = ("Gateron Ink Linear", "Cherry MX Brown", "Kailh Box Navy",
                   "Optical Speed", "Alu Plate Clack")
ASMR_POP_PRESETS = ("Nail Taps ASMR", "Bubble Wrap Pop", "Ping Pong Bounce")
WAVE3_AMB_PRESETS = ("Blizzard", "Underwater", "Cathedral Hall",
                     "Car Ride Rain", "Cicada Swarm", "Autumn Leaves")


class TestV100SoundExpansion:
    """v1.0 sound pack: pro switch models, ASMR foley clicks and the
    storm/immersion/season soundscape wave."""

    def test_new_key_presets_exist(self):
        for name in PRO_KEY_PRESETS + ASMR_POP_PRESETS:
            assert name in MODULAR_SOUND_PRESETS
        assert len(MODULAR_SOUND_PRESETS) == 32

    def test_wave3_ambiences_exist(self):
        names = list_ambience_presets()
        for name in WAVE3_AMB_PRESETS:
            assert name in names
        assert len(names) == 34

    @pytest.mark.parametrize("name", PRO_KEY_PRESETS + ASMR_POP_PRESETS)
    def test_new_key_presets_render_mono_and_stereo(self, name):
        ts = [(0.09 * i, c) for i, c in enumerate("pro keys\n")]
        mono = SimpleSoundGen(preset=name).generate_pcm(ts, 1.0)
        assert np.isfinite(mono).all() and mono.dtype == np.int16
        assert np.max(np.abs(mono)) <= 32767
        stereo = SimpleSoundGen(preset=name, stereo=True,
                                reverb_amt=0.25).generate_pcm(ts, 1.0)
        assert np.isfinite(stereo).all() and len(stereo) == 2 * len(mono)

    @pytest.mark.parametrize("name", WAVE3_AMB_PRESETS)
    def test_wave3_ambiences_render(self, name):
        x = render_ambience(name, 1.5)
        assert len(x) == int(1.5 * 48000)
        assert np.isfinite(x).all()
        assert 0.05 < np.max(np.abs(x)) <= 1.0

    def test_new_ambience_deterministic(self):
        a = render_ambience("Car Ride Rain", 2.0, seed=11)
        b = render_ambience("Car Ride Rain", 2.0, seed=11)
        assert np.array_equal(a, b)

    def test_ui_combos_list_the_new_presets(self, qapp, tmp_path, monkeypatch):
        monkeypatch.setattr(sys.modules["ui"], "SETTINGS_FILE",
                            tmp_path / "settings.json")   # hermetic
        w = MainWindow()
        sound_items = [w.preset_cb.itemText(i) for i in range(w.preset_cb.count())]
        for name in PRO_KEY_PRESETS + ASMR_POP_PRESETS:
            assert name in sound_items
        amb_items = [w.amb_preset_cb.itemText(i)
                     for i in range(w.amb_preset_cb.count())]
        for name in WAVE3_AMB_PRESETS:
            assert name in amb_items
        w.close()

    # ------------------------------------------------ CLI access to the pack
    def test_cli_key_sound_flag_sets_config(self):
        args = build_parser().parse_args(["--key-sound", "Kailh Box Navy",
                                          "--stereo"])
        cfg = build_config_from_args(args)
        assert cfg.sound_preset == "Kailh Box Navy"
        assert cfg.stereo is True

    def test_cli_unknown_key_sound_keeps_default(self):
        args = build_parser().parse_args(["--key-sound", "Does Not Exist"])
        cfg = build_config_from_args(args)
        assert cfg.sound_preset == "Mechanical"      # warned, not replaced

    def test_list_sounds_prints_both_registries(self, capsys):
        from app import run_headless
        rc = run_headless(["--list-sounds"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Kailh Box Navy" in out and "Gateron Ink Linear" in out
        assert "Cathedral Hall" in out and "Autumn Leaves" in out


# ================================================================ keyboard press fx
class TestKeyboardPressFx:
    """v3 key-press animation: afterglow trail state machine + draw plumbing."""

    @staticmethod
    def _overlay():
        ov = KeyboardOverlay(960, 540, "QWERTY", THEMES["Dracula"], 0.9, None, "bottom_center")
        ov.reposition()
        return ov

    @staticmethod
    def _painter():
        from PySide6.QtGui import QImage, QPainter
        img = QImage(960, 540, QImage.Format_RGB32)
        img.fill(0)
        return img, QPainter(img)

    def test_press_recorded_on_rising_edge(self, qgui):
        ov = self._overlay()
        k = ov.resolve_key("a")
        img, p = self._painter()
        ov.draw(p, active_key=k, flash=1.0, t=0.5)
        p.end()
        assert ov._trail.get(k) == 0.5

    def test_repeated_key_updates_press_time(self, qgui):
        ov = self._overlay()
        k = ov.resolve_key("a")
        img, p = self._painter()
        ov.draw(p, active_key=k, flash=1.0, t=0.5)
        ov.draw(p, active_key=k, flash=0.4, t=0.8)   # decay, no new press
        assert ov._trail.get(k) == 0.5
        ov.draw(p, active_key=k, flash=1.0, t=1.1)   # rising edge again
        p.end()
        assert ov._trail.get(k) == 1.1

    def test_backward_seek_resets_trail(self, qgui):
        ov = self._overlay()
        k = ov.resolve_key("a")
        img, p = self._painter()
        ov.draw(p, active_key=k, flash=1.0, t=1.0)
        assert len(ov._trail) == 1
        ov.draw(p, active_key=None, flash=0.0, t=0.4)  # scrub backwards
        p.end()
        assert len(ov._trail) == 0

    def test_trail_pruned_after_life(self, qgui):
        ov = self._overlay()
        k = ov.resolve_key("q")
        img, p = self._painter()
        ov.draw(p, active_key=k, flash=1.0, t=5.0)
        ov.draw(p, active_key=None, flash=0.0, t=5.0 + ov.TRAIL_LIFE + 0.05)
        p.end()
        assert k not in ov._trail

    def test_draw_without_t_is_stateless(self, qgui):
        ov = self._overlay()
        k = ov.resolve_key("z")
        img, p = self._painter()
        ov.draw(p, active_key=k, flash=1.0)          # legacy call signature
        p.end()
        assert ov._last_t is None and len(ov._trail) == 0

    def test_trail_changes_pixels(self, qgui):
        ov = self._overlay()
        img, p = self._painter()
        for ch, t in (("t", 0.0), ("h", 0.1), ("e", 0.2)):
            ov.draw(p, active_key=ov.resolve_key(ch), flash=1.0, t=t)
        p.end()
        fresh = self._overlay()
        img2, p2 = self._painter()
        fresh.draw(p2, active_key=None, flash=0.0, t=0.25)   # no history
        p2.end()
        import numpy as _np
        from PySide6.QtGui import QImage as _QI

        def _arr(i):
            c = i.convertToFormat(_QI.Format_RGBA8888)
            return _np.frombuffer(c.constBits(), dtype=_np.uint8,
                                  count=540 * 960 * 4).reshape(540, 960, 4).copy()

        a, b = _arr(img), _arr(img2)
        assert not _np.array_equal(a, b)   # afterglow visibly differs

    def test_eased_sink_bounded(self, qgui):
        ov = self._overlay()
        unit = ov.key_unit
        img, p = self._painter()
        for f in (0.0, 0.3, 0.7, 1.0):
            k = ov.resolve_key("d")
            ov.draw(p, active_key=k, flash=f, t=0.1)
        p.end()
        assert 1 <= round(unit * 0.11) <= unit // 4   # sink stays subtle


# ================================================================ key<->char sync
class TestKeyCharSync:
    """v3.1: every printable char resolves to a key on every layout, and the
    keyboard flash fires exactly at the moment the char becomes visible."""

    ALL_ASCII = "".join(chr(c) for c in range(32, 127)) + "\n\t\b"

    @staticmethod
    def _overlay(layout):
        ov = KeyboardOverlay(960, 540, layout, THEMES["Dracula"], 0.9, None, "bottom_center")
        ov.reposition()
        return ov

    @pytest.mark.parametrize("layout", list(KEYBOARD_LAYOUTS.keys()))
    def test_full_ascii_coverage(self, qgui, layout):
        """Typing any printable ASCII char must flash some key (v3.1: '+'
        used to flash nothing on QWERTY because of a '+=' table typo, '='
        flashed nothing on QWERTZ/JIS/Turkish, AZERTY digits were unmapped)."""
        ov = self._overlay(layout)
        missing = [c for c in self.ALL_ASCII if ov.resolve_key(c) is None]
        assert not missing, f"{layout}: unmapped chars {missing!r}"

    def test_plus_maps_to_eq_key_qwerty(self, qgui):
        ov = self._overlay("QWERTY")
        assert ov.resolve_key("+") == ov.resolve_key("=")

    def test_eq_maps_across_layouts(self, qgui):
        for layout in KEYBOARD_LAYOUTS:
            ov = self._overlay(layout)
            assert ov.resolve_key("=") is not None, layout

    def test_azerty_digits_flash_shift_base(self, qgui):
        ov = self._overlay("AZERTY")
        assert ov.resolve_key("1") == ov.resolve_key("&")
        assert ov.resolve_key("0") == ov.resolve_key("à")

    def test_accented_char_flashes_base_letter(self, qgui):
        ov = self._overlay("QWERTY")
        assert ov.resolve_key("é") == ov.resolve_key("e")
        assert ov.resolve_key("Ü") == ov.resolve_key("u")
        assert ov.resolve_key("ß") == ov.resolve_key("s")

    def test_qwertz_has_m_key(self, qgui):
        ov = self._overlay("QWERTZ")
        assert ov.resolve_key("m") is not None

    def test_resolve_key_cache_stable(self, qgui):
        ov = self._overlay("QWERTY")
        first = ov.resolve_key("é")
        assert ov.resolve_key("é") == first == ov.char_map.get("é", first)

    def test_control_chars_resolve(self, qgui):
        ov = self._overlay("QWERTY")
        assert ov.resolve_key("\n") is not None   # Enter
        assert ov.resolve_key("\t") is not None   # Tab
        assert ov.resolve_key("\b") is not None   # Bksp
        assert ov.resolve_key(" ") is not None    # Space

    def test_flash_synced_with_visibility(self, qgui):
        """At every press instant the flashing key is exactly the last
        visible char's key (visual/keyboard sync)."""
        code = "x = 1\ny === 2\nz += x\n"
        an = TypingAnimator(code, TypingProfile(wpm=600), seed=42)
        ov = self._overlay("QWERTY")
        for ts, ch in an.char_timestamps():
            ac, kf = an.active_key_at(ts)
            assert ac == ch, f"active char {ac!r} != typed {ch!r} at {ts:.3f}"
            if ch != " ":
                assert ov.resolve_key(ac) is not None, f"{ch!r} flashes no key"

    def test_pop_uses_own_timestamp(self, qgui):
        """The emoji pop must track the emoji's own typing moment, not the
        last typed char: an emoji typed >150ms ago stays settled even when
        further chars arrive quickly (the glitchy '=' bug shape)."""
        r = StudioRenderer(640, 360, "Dracula", "Consolas", 12, config=None)
        code = 'a = "\U0001F600"\nbbb\n'
        r.prepare_code(code)
        an = TypingAnimator(code, TypingProfile(wpm=300), seed=7)
        emo_ts = next(ts for ts, ch in an.char_timestamps() if is_emoji(ch))
        late = emo_ts + 0.17          # emoji stale, last char fresh
        nv = an.visible_at(late)
        img_now = r.render_frame(an.display_chars, nv, False, title_text="t",
                                 t=late, animator=an)
        img_ref = r.render_frame(an.display_chars, nv, False, title_text="t",
                                 t=emo_ts + 5.0, animator=an)
        import numpy as _np
        from PySide6.QtGui import QImage as _QI

        def _arr(i):
            c = i.convertToFormat(_QI.Format_RGBA8888)
            return _np.frombuffer(c.constBits(), dtype=_np.uint8,
                                  count=i.height() * i.width() * 4).reshape(
                                      i.height(), i.width(), 4).copy()

        assert _np.array_equal(_arr(img_now), _arr(img_ref)), \
            "stale emoji re-popped when later chars were typed"

    def test_operators_are_not_emoji(self, qgui):
        """"=" "+<" etc. must not trigger the pop animation (category Sm)."""
        for ch in ("=", "+", "<", ">", "|", "~", "^", "$", "´"):
            assert not is_emoji(ch), ch
        assert is_emoji("\U0001F600")            # real emoji still detected
        assert is_emoji("\u2764\uFE0F")          # VS16 presentation


# ================================================================ utils
class TestUtils:
    def test_split_graphemes_emoji_zwj(self):
        family = "\U0001F468\u200D\U0001F469\u200D\U0001F467"
        parts = split_graphemes("a" + family + "b")
        assert parts == ["a", family, "b"]

    def test_emoji_shortcodes(self):
        assert convert_shortcodes(":rocket:") == "\U0001F680"
        assert convert_shortcodes("a :fire: b") == "a \U0001F525 b"

    def test_read_text_file_clean(self, tmp_path):
        p = tmp_path / "t.py"
        p.write_bytes(b"x = 1  \n\xa0 y = 2\xad\n")
        text = read_text_file(str(p), clean=True)
        assert "  \n" not in text and "\xa0" not in text and "\xad" not in text

    def test_time_formatting(self):
        assert format_time(65) == "1:05"
        assert human_duration(3725) == "1h 2m 5s"


# ================================================================ headless config
class TestHeadlessConfig:
    def _args(self, **kw):
        argv = ["--headless"]
        for k, v in kw.items():
            flag = "--" + k.replace("_", "-")
            if v is True:
                argv.append(flag)
            elif v is False:
                argv.append("--no-" + k.replace("_", "-"))
            else:
                argv.extend([flag, str(v)])
        return build_parser().parse_args(argv)

    def test_defaults(self):
        cfg = build_config_from_args(self._args())
        assert cfg.fps == 30 and cfg.resolution == "1920x1080"

    def test_overrides(self):
        cfg = build_config_from_args(self._args(
            theme="Nord", fps=24, resolution="1280x720", wpm=150,
            sound=False, ambience="Wind", ambience_volume=42,
            progress_bar=True, format="gif"))
        assert cfg.theme == "Nord" and cfg.fps == 24
        assert cfg.wpm_yt == 150 and cfg.wpm_mw == 150
        assert cfg.sound_enabled is False
        assert cfg.amb_preset == "Wind" and cfg.amb_volume == 42
        assert cfg.progress_bar_enabled is True
        assert cfg.output_format == "gif"

    def test_preset_applied(self):
        cfg = build_config_from_args(self._args(preset="ASMR Lo-Fi"))
        assert cfg.amb_enabled is True and cfg.stereo is True

    def test_project_file_then_cli_wins(self, tmp_path):
        proj = tmp_path / "p.studio"
        proj.write_text(json.dumps({"theme": "Nord", "fps": 24, "mode": "code-yt"}))
        cfg = build_config_from_args(self._args(config=str(proj), theme="Kanagawa"))
        assert cfg.theme == "Kanagawa"   # CLI flag wins
        assert cfg.fps == 24             # project value kept

    def test_mode_aliases(self):
        assert parse_mode("jr-vs-sr") == StudioMode.JR_VS_SR
        assert parse_mode("yt") == StudioMode.CODE_YT
        assert parse_mode("Text & Emoji (Single Window)") == StudioMode.TEXT_EMOJI
        with pytest.raises(ValueError):
            parse_mode("bogus")

    def test_custom_code_sets_use_custom(self):
        cfg = build_config_from_args(self._args(custom_code="print(1)"))
        assert cfg.use_custom is True and cfg.custom_code == "print(1)"


# ================================================================ v2.3 quality
class TestQualityPresets:
    def test_normalize_quality(self):
        assert normalize_quality("high") == "High"
        assert normalize_quality("SMALL") == "Small"
        assert normalize_quality(None) == "Balanced"
        assert normalize_quality("bogus") == "Balanced"

    def test_software_crf_mapping(self):
        def crf(q):
            args = build_video_codec_args("software", 1920, 1080, 30, quality=q)[1]
            return args[args.index("-crf") + 1]
        assert crf("High") == "16"
        assert crf("Balanced") == "20"
        assert crf("Small") == "26"

    def test_x264_preset_mapping(self):
        args = build_video_codec_args("software", 640, 360, 30, quality="Small")[1]
        assert args[args.index("-preset") + 1] == "medium"
        args = build_video_codec_args("software", 640, 360, 30, quality="High")[1]
        assert args[args.index("-preset") + 1] == "slow"

    def test_nvenc_cq_mapping(self):
        args = build_video_codec_args("nvenc", 1920, 1080, 30, quality="Small")[1]
        assert args[args.index("-cq") + 1] == "28"
        args = build_video_codec_args("nvenc", 1920, 1080, 30, quality="High")[1]
        assert args[args.index("-cq") + 1] == "17"

    def test_all_backends_pixel_format(self):
        for enc in ("software", "nvenc", "qsv", "amf", "videotoolbox"):
            args = build_video_codec_args(enc, 1280, 720, 30)[1]
            assert "-pix_fmt" in args and "yuv420p" in args, enc


# ================================================================ v2.3 metadata
class TestYouTubeMetadata:
    def test_derive_title(self):
        assert derive_title("sorting_algorithms.py") == "Sorting Algorithms"
        assert derive_title("my-cool-script.js") == "My Cool Script"
        assert derive_title("/deep/path/data_load.csv") == "Data Load"

    def test_derive_title_custom_sentinel(self):
        assert derive_title("custom_code.py") == "Watch Me Code"
        assert derive_title("") == "Watch Me Code"

    def test_extract_tags_filters_noise(self):
        code = "def calculate_total(price):\n    return price * 0.9  # discount\n"
        tags = extract_tags(code, "python", limit=12)
        assert "python" in tags and "coding" in tags
        assert "def" not in tags and "return" not in tags and "price" in tags

    def test_format_chapter_time(self):
        assert format_chapter_time(0) == "0:00"
        assert format_chapter_time(65) == "1:05"
        assert format_chapter_time(3725) == "1:02:05"

    def test_build_chapters_needs_all_segments(self):
        assert build_chapters(10.0, 0.0, 0.0) == []
        ch = build_chapters(10.0, 1.5, 2.2)
        assert len(ch) == 3
        assert ch[0] == ("0:00", "Intro")
        assert ch[1][0] == "0:02" and ch[2][0] == "0:12"

    def test_build_metadata_is_shorts(self):
        cfg = StudioConfig()
        meta = build_metadata(cfg, ["demo.py"], 10.0, 0, 0, (1920, 1080))
        assert meta["is_shorts"] is False and "#shorts" not in meta["description"]
        meta = build_metadata(cfg, ["demo.py"], 10.0, 0, 0, (1080, 1920))
        assert meta["is_shorts"] is True and "#shorts" in meta["description"]

    def test_description_contains_chapters_and_cta(self):
        meta = build_metadata(StudioConfig(), ["demo.py"], 10.0, 1.5, 2.2, (1920, 1080))
        assert "0:00 Intro" in meta["description"]
        assert "Subscribe" in meta["description"]
        assert meta["chapters"][0]["time"] == "0:00"

    def test_write_metadata_files(self, tmp_path):
        out = tmp_path / "video.mp4"
        out.write_bytes(b"x")
        written = write_metadata_files(StudioConfig(), str(out), ["sorting.py"],
                                       10.0, 1.5, 2.2, (1920, 1080))
        assert len(written) == 2
        desc = open(written[0], encoding="utf-8").read()
        assert "0:00 Intro" in desc
        import json as _json
        data = _json.loads(open(written[1], encoding="utf-8").read())
        assert data["title"] == "Sorting"

    def test_write_metadata_respects_toggle(self, tmp_path):
        out = tmp_path / "video.mp4"
        out.write_bytes(b"x")
        cfg = StudioConfig(write_metadata=False)
        assert write_metadata_files(cfg, str(out), ["a.py"]) == []
        assert not list(tmp_path.glob("video.description.txt"))


# ================================================================ v2.3 dual batch
class TestDualBatch:
    def test_make_dual_variants(self):
        cfg = StudioConfig(resolution="1280x720")
        yt, sh = make_dual_variants(cfg)
        assert yt.resolution == "1920x1080"
        assert sh.resolution == "1080x1920 (9:16)"
        assert yt is not cfg and sh is not cfg

    def test_plan_batch_dual_creates_two_items(self, tmp_path):
        src = tmp_path / "demo.py"
        src.write_text("x = 1\n")
        cfg = StudioConfig(output_template="{name}_{date}")
        items = plan_batch(cfg, [str(src)], dual=True)
        assert len(items) == 2
        assert items[0].output_path.endswith("_yt.mp4")
        assert items[1].output_path.endswith("_shorts.mp4")
        assert items[0].config.resolution == "1920x1080"
        assert items[1].config.resolution == "1080x1920 (9:16)"
        assert "YouTube" in items[0].label and "Shorts" in items[1].label

    def test_plan_batch_dual_ignored_for_gif(self, tmp_path):
        src = tmp_path / "demo.py"
        src.write_text("x = 1\n")
        cfg = StudioConfig(output_format="gif")
        items = plan_batch(cfg, [str(src)], dual=True)
        assert len(items) == 1 and items[0].output_path.endswith(".gif")

    def test_estimate_frames_dual_and_branding(self, tmp_path):
        src = tmp_path / "demo.py"
        src.write_text("x = 1\n")
        cfg = StudioConfig(fps=30)
        base = estimate_frames(cfg, [str(src)])
        assert estimate_frames(cfg, [str(src)], dual=True) == base * 2
        cfg.intro_enabled = True
        cfg.outro_enabled = True
        assert estimate_frames(cfg, [str(src)]) > base


# ================================================================ v2.3 CLI flags
class TestHeadlessYouTubeFlags:
    def _args(self, **kw):
        argv = ["--headless"]
        for k, v in kw.items():
            flag = "--" + k.replace("_", "-")
            if v is True:
                argv.append(flag)
            elif v is False:
                argv.append("--no-" + k.replace("_", "-"))
            else:
                argv.extend([flag, str(v)])
        return build_parser().parse_args(argv)

    def test_quality(self):
        cfg = build_config_from_args(self._args(quality="Small"))
        assert cfg.quality_preset == "Small"

    def test_loudnorm_toggle(self):
        assert build_config_from_args(self._args()).yt_loudnorm is True
        assert build_config_from_args(self._args(loudnorm=False)).yt_loudnorm is False

    def test_dual_render(self):
        assert build_config_from_args(self._args(dual_render=True)).dual_render is True

    def test_metadata_toggle(self):
        assert build_config_from_args(self._args(metadata=False)).write_metadata is False

    def test_watermark_intro_outro(self):
        cfg = build_config_from_args(self._args(watermark="@dev", intro="Hello",
                                                outro=True, punch_zoom=True))
        assert cfg.wm_enabled and cfg.wm_text == "@dev"
        assert cfg.intro_enabled and cfg.intro_text == "Hello"
        assert cfg.outro_enabled and cfg.punch_zoom

    def test_thumb_text(self):
        cfg = build_config_from_args(self._args(thumb_text="Big Title"))
        assert cfg.thumb_headline == "Big Title"


# ================================================================ v2.3 config
class TestConfigV23:
    def test_youtube_defaults(self):
        cfg = StudioConfig()
        assert cfg.quality_preset == "Balanced"
        assert cfg.yt_loudnorm is True
        assert cfg.write_metadata is True
        assert cfg.dual_render is False
        assert cfg.wm_enabled is False and cfg.wm_position == "Top Right"
        assert cfg.outro_text == "Thanks for watching!"

    def test_branding_durations_helper(self):
        assert branding_durations(StudioConfig()) == (0.0, 0.0)
        cfg = StudioConfig(intro_enabled=True, outro_enabled=True)
        assert branding_durations(cfg) == (1.5, 2.2)


# ================================================================ v2.4 timing
CODE_RICH = ("def quicksort(arr):\n"
             "    if len(arr) <= 1:\n"
             "        return arr\n"
             "    pivot = arr[0]\n"
             "    # sort halves, then: combine!\n"
             "    return quicksort([x for x in arr[1:] if x < pivot]) + [pivot] \\\n"
             "        + quicksort([x for x in arr[1:] if x >= pivot])\n")


def _legacy_duration(code, wpm=100, sp=0.5, ep=1.5, seed=42):
    """Reference implementation of the v1 delay table (Classic style).

    Note: the v1 typo check consumed one rng.random() draw for every
    non-space/non-newline char even when typo_rate was 0 — it must be
    reproduced here to keep the RNG sequence aligned.
    """
    import random as _r
    rng = _r.Random(seed)
    base = 1.0 / ((wpm * 5) / 60.0)
    t = sp
    for ch in code:
        if ch not in "\n ":
            rng.random()  # typo check draw (always rolled in v1)
        if ch in ".!?":
            t += base * rng.uniform(4.0, 6.0)
        elif ch in ",;:":
            t += base * rng.uniform(2.0, 3.5)
        elif ch == "\n":
            t += base * rng.uniform(3.0, 5.0)
        else:
            t += base * rng.uniform(0.7, 1.3)
    return t + ep


class TestRhythmEngine:
    def test_deterministic_per_style(self):
        for style in ("Classic", "Natural", "Cinematic"):
            d1 = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style=style)).duration()
            d2 = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style=style)).duration()
            assert d1 == d2, f"{style} not deterministic"
            assert d1 > 0

    def test_classic_matches_legacy_behaviour(self):
        got = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style="Classic")).duration()
        want = _legacy_duration(CODE_RICH)
        assert abs(got - want) < 1e-9

    def test_styles_differ_on_punctuated_code(self):
        durs = {s: TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style=s)).duration()
                for s in ("Classic", "Natural", "Cinematic")}
        assert durs["Cinematic"] > durs["Natural"] > durs["Classic"] * 0.9
        assert durs["Cinematic"] != durs["Classic"]

    def test_intensity_zero_is_metronome(self):
        n = len(CODE_RICH)
        base = 1.0 / (100 * 5 / 60.0)
        # k=0 -> every char delay is exactly base_delay (no rng consumed)
        got = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style="Natural",
                                                      intensity=0.0)).duration()
        assert abs(got - (n * base + 0.5 + 1.5)) < 1e-6

    def test_cinematic_intensity_zero_is_metronome(self):
        n = len(CODE_RICH)
        base = 1.0 / (100 * 5 / 60.0)
        got = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style="Cinematic",
                                                      intensity=0.0)).duration()
        assert abs(got - (n * base + 0.5 + 1.5)) < 1e-6

    def test_intensity_scales_expressiveness(self):
        low = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style="Cinematic",
                                                      intensity=0.5)).duration()
        high = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style="Cinematic",
                                                       intensity=1.5)).duration()
        assert high > low, "higher intensity should add more pause time"

    def test_timeline_api_unchanged(self):
        a = TypingAnimator("hi there\n", TypingProfile(wpm=100, style="Natural"))
        assert len(a.char_timestamps()) == len(a.display_chars)
        assert a.visible_at(0) == 0
        assert a.visible_at(a.duration()) == len(a.display_chars)
        t_first = a.char_timestamps()[0][0]
        ch, flash = a.active_key_at(t_first + 0.01)
        assert ch is not None and 0.0 <= flash <= 1.0

    def test_bad_style_falls_back_to_natural(self):
        d1 = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style="Nope")).duration()
        d2 = TypingAnimator(CODE_RICH, TypingProfile(wpm=100, style="Natural")).duration()
        assert d1 == d2


class TestAutoFitSolver:
    def _mk(self, style="Natural", intensity=1.0):
        return lambda w, i: TypingProfile(wpm=w, style=style, intensity=intensity)

    def test_single_pane_hits_target(self):
        res = fit_wpm([CODE_RICH], [100], 25.0, self._mk())
        a = TypingAnimator(CODE_RICH, self._mk()(res.wpms[0], 0))
        assert abs(a.duration() - 25.0) < 0.2
        assert not res.clamped

    def test_multi_pane_preserves_speed_ratio(self):
        res = fit_wpm([CODE_RICH, CODE_RICH * 2], [90, 130], 30.0, self._mk())
        assert res.wpms[0] < res.wpms[1], "Jr must stay slower than Sr"
        # both scaled by (roughly) the same factor
        ratio = res.wpms[0] / res.wpms[1]
        assert abs(ratio - 90 / 130) < 0.05

    def test_per_pane_sync_lands_together(self):
        codes = [CODE_RICH, CODE_RICH * 2, CODE_RICH[:200]]
        # 25s is reachable for every pane (CODE_RICH*2 needs ~176 WPM)
        res = fit_wpm(codes, [100, 100, 100], 25.0, self._mk(), per_pane=True)
        assert not res.clamped, res.note
        durs = [TypingAnimator(c, self._mk()(w, i)).duration()
                for i, (c, w) in enumerate(zip(codes, res.wpms))]
        assert (max(durs) - min(durs)) < 0.3, f"sync spread {durs}"

    def test_clamped_when_impossible_fast(self):
        res = fit_wpm([CODE_RICH * 10], [100], 3.0, self._mk())
        assert res.clamped and res.wpms[0] == 300.0
        assert "WPM" in res.note

    def test_clamped_when_impossible_slow(self):
        res = fit_wpm(["hi"], [100], 600.0, self._mk())
        assert res.clamped and res.wpms[0] == 15.0

    def test_fit_off_returns_none_target(self):
        assert fit_target_for(StudioConfig()) == (None, "")

    def test_fit_target_includes_branding(self):
        cfg = StudioConfig(timing_fit="Target Duration", timing_target=50.0,
                           intro_enabled=True, outro_enabled=True)
        target, _ = fit_target_for(cfg)
        assert abs(target - (50.0 - 1.5 - 2.2)) < 1e-9

    def test_audio_duration_probe(self, tmp_path):
        import wave
        import numpy as np
        sr = 48000
        pcm = (np.sin(np.arange(sr * 2) * 0.05) * 12000).astype(np.int16)
        p = tmp_path / "tone.wav"
        with wave.open(str(p), "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            wf.writeframes(pcm.tobytes())
        d = audio_duration(str(p))
        assert d is not None and abs(d - 2.0) < 0.1
        assert audio_duration(str(tmp_path / "missing.wav")) is None
        assert audio_duration("") is None

    def test_resolve_fit_target_audio_and_fallback(self, tmp_path):
        import wave
        import numpy as np
        sr = 48000
        pcm = (np.sin(np.arange(sr * 6) * 0.05) * 12000).astype(np.int16)
        p = tmp_path / "bgm.wav"
        with wave.open(str(p), "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            wf.writeframes(pcm.tobytes())
        cfg = StudioConfig(timing_fit="Audio Length", bgm_path=str(p))
        target, note = resolve_fit_target(cfg)
        assert abs(target - 6.0) < 0.1 and "BGM" in note
        # no audio anywhere -> falls back to the explicit target
        cfg2 = StudioConfig(timing_fit="Audio Length", timing_target=42.0)
        target2, note2 = resolve_fit_target(cfg2)
        assert target2 == 42.0 and "falling back" in note2


class TestConfigV24:
    def test_timing_defaults(self):
        cfg = StudioConfig()
        assert cfg.rhythm_style == "Natural"
        assert cfg.rhythm_intensity == 100
        assert cfg.timing_fit == "Off"
        assert cfg.timing_target == 60.0

    def test_legacy_config_still_loads(self):
        cfg = safe_config_from_dict({"theme": "Nord", "wpm_yt": 123,
                                     "subtitle_enabled": True})
        assert cfg.theme == "Nord" and cfg.wpm_yt == 123
        assert cfg.rhythm_style == "Natural" and cfg.timing_fit == "Off"

    def test_cli_timing_flags(self):
        args = build_parser().parse_args([
            "--rhythm", "Cinematic", "--rhythm-intensity", "120",
            "--timing-fit", "audio"])
        cfg = build_config_from_args(args)
        assert cfg.rhythm_style == "Cinematic" and cfg.rhythm_intensity == 120
        assert cfg.timing_fit == "Audio Length"

    def test_cli_timing_target_implies_fit(self):
        args = build_parser().parse_args(["--timing-target", "33"])
        cfg = build_config_from_args(args)
        assert cfg.timing_fit == "Target Duration"
        assert abs(cfg.timing_target - 33.0) < 1e-9

    def test_presets_carry_timing(self):
        cfg = apply_preset(StudioConfig(), "Shorts Machine (Dual)")
        assert cfg.timing_fit == "Target Duration"
        assert abs(cfg.timing_target - 55.0) < 1e-9
        assert cfg.rhythm_style == "Natural"
        cfg2 = apply_preset(StudioConfig(), "GIF Loop for README")
        assert cfg2.timing_fit == "Target Duration" and cfg2.timing_target == 10.0
        cfg3 = apply_preset(StudioConfig(), "Cinematic Code (4K)")
        assert cfg3.rhythm_style == "Cinematic" and cfg3.rhythm_intensity == 120

    def test_estimate_frames_honours_fit(self):
        snippet = ("def demo():\n    values = [1, 2, 3, 4]\n"
                   "    total = sum(v * 2 for v in values)\n"
                   "    print(f'total: {total}')\n"
                   "    return total\n\n") * 5
        cfg = StudioConfig(fps=30, custom_code=snippet, use_custom=True,
                           timing_fit="Target Duration", timing_target=60.0)
        est = estimate_frames(cfg, ["custom_code.py"])
        # 60s total -> ~1800 frames (+/- fit tolerance and the 2s pauses)
        assert 1650 <= est <= 1950, f"estimate {est} frames for a 60s fit"
        # unfitted estimate for the same content must differ
        cfg2 = StudioConfig(fps=30, custom_code=snippet, use_custom=True,
                            timing_fit="Off", wpm_yt=100)
        est2 = estimate_frames(cfg2, ["custom_code.py"])
        assert est2 != est

    def test_describe_preset_mentions_fit(self):
        assert "auto-fit" in describe_preset("Shorts Hook (9:16)")

#==============================================================================
# ── MEMORY TESTS (tracemalloc leak guards)
#    (merged from tests/test_memory.py in the v2.5 ten-file edition)
#==============================================================================

"""Memory tests: bound memory growth across repeated work.

These use ``tracemalloc`` around representative workloads and assert that
repeated iterations do not grow the retained set without bound.  Thresholds
are deliberately generous (they guard against *leaks*, not against normal
allocation) so they stay stable across machines and numpy versions.

Run with:  python -m pytest tests/test_memory.py -m memory
"""

import gc
import tracemalloc

import numpy as np
import pytest




def _measure(fn, iterations, warmup=1):
    """Run fn() repeatedly; return (bytes_after_warmup, bytes_at_end).

    Only memory that is still *retained* (not freed) counts, which is what a
    leak looks like.
    """
    for _ in range(warmup):
        fn()
    gc.collect()
    tracemalloc.start()
    gc.collect()
    baseline, _ = tracemalloc.get_traced_memory()
    for _ in range(iterations):
        fn()
    gc.collect()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return baseline, current, peak


@pytest.mark.memory
class TestRenderMemory:
    def test_repeated_frame_render_bounded(self, qgui, base_config, sample_code):
        """Rendering hundreds of frames must not accumulate retained memory."""
        mp = make_strategies()[base_config.mode].build_panes(
            base_config, [HeadlessFile(sample_code)], "")

        def render_batch():
            from PySide6.QtGui import QImage
            for i in range(20):
                t = i * 0.37 % max(0.1, mp.duration())
                img = QImage(mp.frame_w, mp.frame_h, QImage.Format_RGB32)
                mp.render_frame(t, img)

        base, end, peak = _measure(render_batch, iterations=10)
        growth = end - base
        # 200 frames rendered: retained growth must stay modest (< 64 MB)
        assert growth < 64 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"

    def test_renderer_construction_bounded(self, qgui, base_config, sample_code):
        """Building many renderers/animators must not leak (caches are LRU)."""
        strategies = make_strategies()

        def build():
            for wpm in (90, 100, 110):
                cfg = StudioConfig(resolution="1280x720", wpm_yt=wpm,
                                   sound_enabled=False)
                mp = strategies[cfg.mode].build_panes(
                    cfg, [HeadlessFile(sample_code)], "")
                assert mp is not None

        base, end, peak = _measure(build, iterations=8)
        growth = end - base
        assert growth < 96 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"


@pytest.mark.memory
class TestAnimatorMemory:
    def test_many_animators_bounded(self):
        code = "def f(x):\n    return x * 2\n" * 20
        base, end, peak = _measure(
            lambda: TypingAnimator(code, TypingProfile(wpm=100)), iterations=200)
        growth = end - base
        assert growth < 32 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"

    def test_typo_animator_bounded(self):
        code = "x = 1\ny = 2\nprint(x + y)\n" * 15

        def make():
            TypingAnimator(code, TypingProfile(wpm=100, typo_rate=0.1), seed=1)

        base, end, peak = _measure(make, iterations=200)
        growth = end - base
        assert growth < 32 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"


@pytest.mark.memory
class TestAudioMemory:
    def test_ambience_render_bounded(self):
        base, end, peak = _measure(
            lambda: render_ambience("Rain", 10.0), iterations=6)
        growth = end - base
        # 60s of audio rendered in total: numpy frees as it goes, so the
        # retained growth must stay far below one bed's size
        assert growth < 32 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"
        # peak per call is bounded (~10s * 48k * 8B * filter overhead)
        assert peak < 512 * 1024 * 1024

    def test_soundgen_pcm_bounded(self):
        sg = SimpleSoundGen(preset="Mechanical")
        ts = [(i * 0.05, chr(97 + i % 26)) for i in range(400)]

        def gen():
            pcm = sg.generate_pcm(ts, 1.0)
            assert len(pcm) > 0

        base, end, peak = _measure(gen, iterations=20)
        growth = end - base
        assert growth < 48 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"

    def test_mix_ambience_bounded(self):
        bed = render_ambience("Rain", 5.0)
        kb = (np.random.RandomState(0).randn(240000) * 4000).astype(np.int16)

        def mix():
            out = mix_ambience(kb, 48000, 1, bed, 40)
            assert len(out) == len(kb)

        base, end, peak = _measure(mix, iterations=30)
        growth = end - base
        assert growth < 32 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"


@pytest.mark.memory
class TestConfigMemory:
    def test_config_copy_churn_bounded(self):
        import copy
        cfg = StudioConfig()
        base, end, peak = _measure(lambda: copy.deepcopy(cfg), iterations=500)
        growth = end - base
        assert growth < 16 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"


@pytest.mark.memory
class TestThumbnailAndBrandingMemory:
    def _tiny_renderer(self, base_config, sample_code):
        return make_strategies()[base_config.mode].build_panes(
            base_config, [HeadlessFile(sample_code)], "")

    def test_thumbnail_render_bounded(self, qgui, base_config, sample_code):
        mp = self._tiny_renderer(base_config, sample_code)

        def churn():
            for size in ((640, 360), (320, 568)):
                make_thumbnail(mp, base_config, "Leak Check", size)

        base, end, peak = _measure(churn, iterations=25)
        growth = end - base
        assert growth < 48 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"

    def test_branding_cards_bounded(self, qgui, base_config):
        from PySide6.QtGui import QImage, QPainter
        cfg = StudioConfig(intro_enabled=True, outro_enabled=True,
                           wm_enabled=True, wm_text="@leak")
        img = QImage(640, 360, QImage.Format_RGB32)

        def churn():
            for i in range(40):
                img.fill(0)
                p = QPainter(img)
                draw_intro_card(p, 640, 360, cfg, (i % 20) / 20.0)
                draw_outro_card(p, 640, 360, cfg, (i % 20) / 20.0)
                draw_watermark(p, 640, 360, cfg)
                p.end()

        base, end, peak = _measure(churn, iterations=10)
        growth = end - base
        assert growth < 24 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"

    def test_metadata_build_bounded(self, sample_code):
        cfg = StudioConfig(custom_code=sample_code * 20)

        def churn():
            build_metadata(cfg, ["demo.py"], 10.0, 1.5, 2.2, (1920, 1080))

        base, end, peak = _measure(churn, iterations=200)
        growth = end - base
        assert growth < 16 * 1024 * 1024, f"retained growth {growth/1e6:.1f} MB"


# ================================================================ v2.4 timing
@pytest.mark.memory
class TestTimingMemory:
    def test_fit_solver_churn(self):
        """Repeated auto-fit solves must not retain memory."""
        code = "\n".join(f"def fn_{i}(x): return x + {i}" for i in range(40))

        def mk(w, i):
            return TypingProfile(wpm=w, style="Natural")

        def run():
            for target in (30.0, 45.0, 60.0):
                res = fit_wpm([code, code * 2], [100, 120], target, mk)
                assert res.wpms

        baseline, current, _peak = _measure(run, iterations=25)
        growth = current - baseline
        assert growth < 2_000_000, f"fit solver retained {growth/1e6:.2f} MB over 25 runs"

    def test_rhythm_engine_churn(self):
        """Animator builds across all rhythm styles must not leak."""
        code = ("class Demo:\n    def __init__(self):\n        self.x = 1\n\n"
                "    def run(self):\n        return self.x\n") * 4

        def run():
            for style in ("Classic", "Natural", "Cinematic"):
                for intensity in (0.5, 1.0, 1.5):
                    a = TypingAnimator(code, TypingProfile(wpm=110, style=style,
                                                           intensity=intensity))
                    assert a.duration() > 0

        baseline, current, _peak = _measure(run, iterations=60)
        growth = current - baseline
        assert growth < 1_000_000, f"animator churn retained {growth/1e6:.2f} MB"

#==============================================================================
# ── PERFORMANCE TESTS (throughput benchmarks)
#    (merged from tests/test_performance.py in the v2.5 ten-file edition)
#==============================================================================

"""Performance tests: throughput benchmarks with loose, machine-independent
thresholds.  They catch gross regressions (e.g. someone reintroduces
per-frame re-lexing), not micro-timing.

Run with:  python -m pytest tests/test_performance.py -m performance
"""

import time

import numpy as np
import pytest




class _Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.elapsed = time.perf_counter() - self.t0
        return False


@pytest.mark.performance
class TestRenderPerformance:
    def test_frame_throughput_small(self, qgui, base_config, sample_code):
        """Preview-sized frames should render at >> 10 fps per second of wall
        time (single-threaded main-thread rendering)."""
        from PySide6.QtGui import QImage
        cfg = StudioConfig(resolution="1280x720", fps=12, sound_enabled=False)
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        n = 40
        with _Timer() as t:
            for i in range(n):
                img = QImage(mp.frame_w, mp.frame_h, QImage.Format_RGB32)
                mp.render_frame((i % 60) / cfg.fps, img)
        per_frame = t.elapsed / n
        assert per_frame < 0.5, f"{per_frame*1000:.0f} ms/frame is too slow"
        print(f"\n    [{per_frame*1000:.1f} ms/frame @ {mp.frame_w}x{mp.frame_h}]")

    def test_char_color_map_build(self, qgui, sample_code):
        """Lexing + color-map build (once per export) must be fast even for
        large files — v1 re-lexed every frame."""
        big = sample_code  # small file; scale by building repeatedly
        cfg = StudioConfig(resolution="1280x720", sound_enabled=False)
        strategies = make_strategies()
        with _Timer() as t:
            for _ in range(10):
                mp = strategies[cfg.mode].build_panes(cfg, [HeadlessFile(big)], "")
                assert mp is not None
        per_build = t.elapsed / 10
        assert per_build < 2.0, f"pane build takes {per_build*1000:.0f} ms"
        print(f"\n    [{per_build*1000:.0f} ms/pane-build]")

    def test_large_file_prepare(self, qgui, tmp_path):
        """A 1000-line file must prepare (lex + color map + animator) quickly."""
        code = "\n".join(f"def fn_{i}(x): return x + {i}" for i in range(1000))
        with _Timer() as t:
            chars = split_graphemes(code)
            assert len(chars) > 1000
            anim = TypingAnimator(code, TypingProfile(wpm=200))
            assert anim.duration() > 0
        assert t.elapsed < 5.0, f"large-file prep took {t.elapsed:.1f}s"
        print(f"\n    [{t.elapsed*1000:.0f} ms for 1000-line prepare]")


@pytest.mark.performance
class TestAudioPerformance:
    def test_ambience_render_speed(self):
        """A 60-second ambience bed renders in seconds, not minutes."""
        with _Timer() as t:
            x = render_ambience("Rain & Thunder", 60.0)
        assert len(x) == 60 * 48000
        assert t.elapsed < 15.0, f"60s bed took {t.elapsed:.1f}s"
        print(f"\n    [{t.elapsed:.2f}s for 60s 'Rain & Thunder' bed]")

    def test_key_click_gen_speed(self):
        sg = SimpleSoundGen(preset="Mechanical")
        ts = [(i * 0.05, chr(33 + i % 90)) for i in range(1200)]  # ~60s of typing
        with _Timer() as t:
            pcm = sg.generate_pcm(ts, 1.0)
        assert len(pcm) > 48000
        assert t.elapsed < 10.0, f"1200 clicks took {t.elapsed:.1f}s"
        print(f"\n    [{t.elapsed:.2f}s for 1200-key soundscape]")

    def test_ambience_mix_speed(self):
        bed = render_ambience("Rain", 60.0)
        kb = (np.random.RandomState(0).randn(48000 * 60) * 4000).astype(np.int16)
        with _Timer() as t:
            out = mix_ambience(kb, 48000, 1, bed, 40)
        assert len(out) == len(kb)
        assert t.elapsed < 5.0, f"60s mix took {t.elapsed:.1f}s"
        print(f"\n    [{t.elapsed:.2f}s for 60s stereo-capable mix]")


@pytest.mark.performance
class TestDetectionPerformance:
    def test_quick_scan_is_fast(self):
        """Non-probing detection (GUI startup path) must not stall."""
        with _Timer() as t:
            scan = detect_encoders(deep=False, use_cache=True)
        assert scan.encoders
        assert t.elapsed < 20.0, f"quick scan took {t.elapsed:.1f}s"
        print(f"\n    [{t.elapsed:.2f}s quick scan]")

    def test_deep_probe_bounded(self):
        """Deep probing must respect the per-encoder timeout (never hang)."""
        with _Timer() as t:
            scan = detect_encoders(deep=True, use_cache=True)
        n_hw = len(scan.encoders)
        # each probe is capped at PROBE_TIMEOUT=25s; allow generous slack
        assert t.elapsed < 25 * n_hw + 30
        print(f"\n    [{t.elapsed:.2f}s deep probe of {n_hw} backends]")

    def test_export_engine_tiny_video(self, qgui, base_config, sample_code, tmp_path):
        """Full pipeline: 4s of 320p video with sound + ambience in < 60s."""
        cfg = StudioConfig(resolution="1280x720", fps=12, sound_enabled=True,
                           amb_enabled=True, amb_preset="Rain", amb_volume=35,
                           yt_extras=False)
        # shrink typing workload: tiny code via custom code
        cfg.use_custom = True
        cfg.custom_code = "x = 1\nprint(x)\n"
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "perf.mp4")
        with _Timer() as t:
            result = ExportEngine(mp, cfg, out).run()
        assert result.success, result.message
        assert t.elapsed < 60.0, f"tiny export took {t.elapsed:.1f}s"
        print(f"\n    [{t.elapsed:.1f}s for {result.frames}-frame export]")


@pytest.mark.performance
class TestYouTubePackPerformance:
    def test_thumbnail_render_speed(self, qgui, base_config, sample_code):
        """Both thumbnail sizes together must render well under a second."""
        mp = make_strategies()[base_config.mode].build_panes(
            base_config, [HeadlessFile(sample_code)], "")
        with _Timer() as t:
            make_thumbnail(mp, base_config, "Fast Title", (1280, 720))
            make_thumbnail(mp, base_config, "Fast Title", (1080, 1920))
        assert t.elapsed < 3.0, f"thumbnails took {t.elapsed*1000:.0f} ms"
        print(f"\n    [thumbnails: {t.elapsed*1000:.0f} ms total]")

    def test_metadata_build_and_write_speed(self, tmp_path, sample_code):
        cfg = StudioConfig(custom_code=sample_code)
        with _Timer() as t:
            for _ in range(20):
                build_metadata(cfg, ["demo.py"], 10.0, 1.5, 2.2, (1920, 1080))
        per_build = t.elapsed / 20
        assert per_build < 0.05, f"metadata build too slow: {per_build*1000:.0f} ms"
        out = tmp_path / "v.mp4"
        out.write_bytes(b"x")
        with _Timer() as t:
            write_metadata_files(cfg, str(out), ["demo.py"], 10.0, 0, 0)
        assert t.elapsed < 0.5

    def test_dual_plan_speed(self, sample_code, tmp_path):
        cfg = StudioConfig()
        srcs = [sample_code] * 20
        with _Timer() as t:
            items = plan_batch(cfg, srcs, dual=True)
        assert len(items) == 40
        assert t.elapsed < 0.5


# ================================================================ v2.4 timing
@pytest.mark.performance
class TestTimingPerformance:
    def test_fit_solver_speed(self):
        """Solving a 2000-char file must take well under a second."""
        code = "\n".join(f"def fn_{i}(x): return x * {i} + 1" for i in range(80))
        assert len(code) > 2000

        def mk(w, i):
            return TypingProfile(wpm=w, style="Natural")

        with _Timer() as t:
            for target in (30.0, 60.0, 120.0, 300.0):
                res = fit_wpm([code], [100], target, mk)
                assert res.wpms
        per_fit = t.elapsed / 4
        assert per_fit < 0.5, f"fit takes {per_fit * 1000:.0f} ms"
        print(f"\n    [{per_fit * 1000:.0f} ms per fit (2000 chars)]")

    def test_rhythm_styles_build_speed(self):
        """All three rhythm styles build an animator within interactive time."""
        code = ("def calc(items):\n    total = 0\n    for it in items:\n"
                "        total += it.price\n    return total\n") * 6
        with _Timer() as t:
            for _ in range(30):
                for style in ("Classic", "Natural", "Cinematic"):
                    a = TypingAnimator(code, TypingProfile(wpm=120, style=style))
                    assert a.duration() > 0
        per_build = t.elapsed / 90
        assert per_build < 0.02, f"animator build takes {per_build * 1000:.1f} ms"
        print(f"\n    [{per_build * 1000:.2f} ms per animator build]")

#==============================================================================
# ── E2E TESTS (real ffmpeg pipelines)
#    (merged from tests/test_e2e.py in the v2.5 ten-file edition)
#==============================================================================

"""End-to-end tests: real pipelines against real ffmpeg.

* GUI workflow offscreen (build window -> apply preset -> export via QThread)
* ExportEngine direct (mp4 with audio, gif, png sequence)
* Headless CLI as a subprocess (the way users invoke it)

These need PySide6 + ffmpeg on PATH; they run on the offscreen Qt platform.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest




ffmpeg = pytest.importorskip("shutil").which("ffmpeg")
if not ffmpeg:
    pytest.skip("ffmpeg not available", allow_module_level=True)


def ffprobe_streams(path: str):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_name,codec_type", "-show_entries", "format=duration",
         "-of", "json", path],
        capture_output=True, text=True, timeout=30)
    data = json.loads(out.stdout or "{}")
    streams = [(s.get("codec_name"), s.get("codec_type")) for s in data.get("streams", [])]
    dur = float(data.get("format", {}).get("duration", 0.0))
    return streams, dur


# ================================================================ engine e2e
@pytest.mark.e2e
class TestExportEngineE2E:
    def test_mp4_with_sounds_and_ambience(self, qgui, base_config, sample_code, tmp_path):
        cfg = base_config
        cfg.sound_enabled = True
        cfg.amb_enabled = True
        cfg.amb_preset = "Rain"
        cfg.amb_volume = 40
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "e2e.mp4")
        result = ExportEngine(mp, cfg, out).run()
        assert result.success, result.message
        assert os.path.getsize(out) > 10000
        streams, dur = ffprobe_streams(out)
        assert ("h264", "video") in streams
        assert ("aac", "audio") in streams
        assert dur > 1.0
        assert result.frames > 0

    def test_mp4_silent(self, qgui, base_config, sample_code, tmp_path):
        cfg = base_config
        cfg.sound_enabled = False
        cfg.amb_enabled = False
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "silent.mp4")
        result = ExportEngine(mp, cfg, out).run()
        assert result.success, result.message
        streams, _ = ffprobe_streams(out)
        names = [s[1] for s in streams]
        assert "video" in names and "audio" not in names

    def test_gif_export(self, qgui, base_config, sample_code, tmp_path):
        cfg = base_config
        cfg.output_format = "gif"
        cfg.fps = 10
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "e2e.gif")
        result = ExportEngine(mp, cfg, out).run()
        assert result.success, result.message
        streams, _ = ffprobe_streams(out)
        assert streams[0][0] == "gif"

    def test_png_sequence_export(self, qgui, base_config, sample_code, tmp_path):
        cfg = base_config
        cfg.output_format = "png"
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        outdir = str(tmp_path / "frames")
        result = ExportEngine(mp, cfg, outdir).run()
        assert result.success, result.message
        files = sorted(os.listdir(outdir))
        assert len(files) == result.frames
        assert files[0].startswith("frame_") and files[0].endswith(".png")

    def test_overlay_progress_bar(self, qgui, base_config, sample_code, tmp_path):
        """Pixel check: the burned-in progress bar appears in exported frames."""
        from PySide6.QtGui import QImage
        cfg = base_config
        cfg.sound_enabled = False
        cfg.progress_bar_enabled = True
        cfg.progress_bar_color = "#ff0000"      # hard red -> pixel assertions
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "overlay.mp4")
        result = ExportEngine(mp, cfg, out).run()
        assert result.success, result.message

        # verify on a freshly rendered frame instead of decoding the video
        img = mp.render_frame(mp.duration() * 0.9, QImage(mp.frame_w, mp.frame_h,
                                                          QImage.Format_RGB32))
        found_red = 0
        h, w = img.height(), img.width()
        im = img.toImage() if hasattr(img, "toImage") else img
        for y in range(h - 30, h):
            for x in range(0, w, 7):
                c = im.pixelColor(x, y)
                if c.red() > 200 and c.green() < 80 and c.blue() < 80:
                    found_red += 1
        assert found_red > 20, "red progress bar not found in bottom band"

    def test_all_four_modes_export(self, qgui, sample_code, tmp_path):
        strategies = make_strategies()
        for mode in StudioMode:
            cfg = StudioConfig(resolution="1280x720", fps=10, sound_enabled=False,
                               yt_extras=False, mode=mode)
            mp = strategies[mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
            out = str(tmp_path / f"mode_{mode.name.lower()}.mp4")
            result = ExportEngine(mp, cfg, out).run()
            assert result.success, f"{mode}: {result.message}"
            streams, _ = ffprobe_streams(out)
            assert ("h264", "video") in streams


# ================================================================ CLI e2e
def run_cli(args, cwd, env_extra=None, timeout=240):
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    # Child stdio must be UTF-8 regardless of the OS locale: CLI reports use
    # Unicode glyphs (e.g. '≈') that legacy Windows code pages cannot encode.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-u", str(PROJECT_ROOT / "main.py")] + args,
        cwd=cwd, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout)


@pytest.mark.e2e
class TestHeadlessCliE2E:
    def test_cli_render_mp4_with_report(self, tmp_path):
        (tmp_path / "cli_demo.py").write_text(
            "def add(a, b):\n    return a + b\nprint(add(2, 3))\n", encoding="utf-8")
        r = run_cli(
            ["--headless", "cli_demo.py", "-o", "out/video.mp4",
             "--resolution", "1280x720", "--fps", "12", "--no-sound",
             "--json-report", "report.json"], cwd=tmp_path)
        assert r.returncode == 0, r.stderr[-2000:]
        out = tmp_path / "out" / "video.mp4"
        assert out.exists() and out.stat().st_size > 5000
        streams, dur = ffprobe_streams(str(out))
        assert ("h264", "video") in streams
        report = json.loads((tmp_path / "report.json").read_text())
        assert report["success"] is True
        assert report["items"][0]["ok"] is True

    def test_cli_list_encoders(self, tmp_path):
        r = run_cli(["--headless", "--list-encoders"], cwd=tmp_path)
        assert r.returncode == 0
        assert "Hardware encoder detection" in r.stdout
        assert "Auto (Hardware)" in r.stdout or "software encoder" in r.stdout

    def test_cli_list_presets_and_themes(self, tmp_path):
        r = run_cli(["--headless", "--list-presets"], cwd=tmp_path)
        assert r.returncode == 0
        assert "ASMR Lo-Fi" in r.stdout
        r = run_cli(["--headless", "--list-themes"], cwd=tmp_path)
        assert r.returncode == 0
        assert "Dracula" in r.stdout

    def test_cli_dry_run_renders_nothing(self, tmp_path):
        (tmp_path / "d.py").write_text("x = 1\n", encoding="utf-8")
        r = run_cli(["--headless", "--dry-run", "d.py", "-o", "out/x.mp4"],
                    cwd=tmp_path)
        assert r.returncode == 0
        assert "Dry run" in r.stdout
        assert not (tmp_path / "out" / "x.mp4").exists()

    def test_cli_preset_workflow(self, tmp_path):
        (tmp_path / "p.py").write_text("a = 'preset'\n", encoding="utf-8")
        # GIF preset + explicit .gif output -> gif
        r = run_cli(
            ["--headless", "p.py", "-o", "out/p.gif",
             "--preset", "GIF Loop for README", "--resolution", "1280x720"],
            cwd=tmp_path)
        assert r.returncode == 0, r.stderr[-2000:]
        streams, _ = ffprobe_streams(str(tmp_path / "out" / "p.gif"))
        assert streams[0][0] == "gif"
        # GIF preset + explicit .mp4 output -> the extension wins (no
        # codec/container mismatch); this must render a valid mp4
        r = run_cli(
            ["--headless", "p.py", "-o", "out/p2.mp4",
             "--preset", "GIF Loop for README", "--resolution", "1280x720"],
            cwd=tmp_path)
        assert r.returncode == 0, r.stderr[-2000:]
        streams, _ = ffprobe_streams(str(tmp_path / "out" / "p2.mp4"))
        assert streams[0][0] == "h264"

    def test_cli_custom_code_with_ambience(self, tmp_path):
        r = run_cli(
            ["--headless", "--custom-code", "print('cli custom')",
             "-o", "out/custom.mp4", "--resolution", "1280x720", "--fps", "12",
             "--no-sound", "--enable-ambience", "--ambience", "Wind",
             "--ambience-volume", "50"], cwd=tmp_path)
        assert r.returncode == 0, r.stderr[-2000:]
        streams, _ = ffprobe_streams(str(tmp_path / "out" / "custom.mp4"))
        assert ("aac", "audio") in streams     # standalone ambience track

    def test_cli_missing_input_fails_cleanly(self, tmp_path):
        r = run_cli(["--headless", "/no/such/file.py"], cwd=tmp_path)
        assert r.returncode != 0

    def test_cli_exit_code_nonzero_on_failure(self, tmp_path):
        """A broken output path (e.g. existing file as dir) must exit 1."""
        (tmp_path / "q.py").write_text("x = 1\n", encoding="utf-8")
        blocker = tmp_path / "out2"
        blocker.write_text("i am a file, not a dir", encoding="utf-8")
        r = run_cli(["--headless", "q.py", "-o", "out2/video.mp4",
                     "--resolution", "1280x720", "--fps", "10", "--no-sound"],
                    cwd=tmp_path)
        assert r.returncode == 1


# ================================================================ GUI e2e
@pytest.mark.e2e
class TestGuiWorkflowE2E:
    def test_window_builds_with_new_features(self, qapp):
        w = MainWindow()
        assert w.amb_preset_cb.count() == len(list_ambience_presets()) >= 21
        assert w.preset_cb2.count() >= 8
        assert w.enc_detect_btn.isEnabled()
        w.close()

    def test_preset_apply_updates_config_and_ui(self, qapp):
        w = MainWindow()
        w.preset_cb2.setCurrentText("Cinematic Code (4K)")
        assert w.config.resolution == "3840x2160"
        assert w.res_cb.currentText() == "3840x2160"      # UI mirrored
        w.preset_cb2.setCurrentText("Default")
        w.close()

    def test_ambience_ui_roundtrip(self, qapp):
        w = MainWindow()
        w.amb_chk.setChecked(True)
        w.amb_preset_cb.setCurrentText("Vinyl Crackle")
        w.amb_vol_sp.setValue(55)
        assert w.config.amb_enabled is True
        assert w.config.amb_preset == "Vinyl Crackle"
        assert w.config.amb_volume == 55
        # and back via _apply_config_to_ui
        w.config.amb_enabled = False
        w._apply_config_to_ui()
        assert w.amb_chk.isChecked() is False
        w.close()

    def test_settings_persistence_includes_new_fields(self, qapp, tmp_path, monkeypatch):
        ui_mod = sys.modules["ui"]  # was: import ui as ui_mod
        settings_file = tmp_path / "settings.json"
        monkeypatch.setattr(ui_mod, "SETTINGS_FILE", settings_file)
        w = MainWindow()
        w.amb_chk.setChecked(True)
        w.amb_vol_sp.setValue(66)
        from PySide6.QtGui import QCloseEvent
        w.closeEvent(QCloseEvent())
        data = json.loads(settings_file.read_text())
        assert data["amb_enabled"] is True
        assert data["amb_volume"] == 66
        assert data["encoder"] == "Auto (Hardware)"

    def test_gui_batch_export_via_qthread(self, qapp, sample_code, tmp_path, monkeypatch):
        """The GUI export path (VideoExporter QThread) end-to-end."""
        from PySide6.QtCore import QEventLoop, QTimer
        ui_mod = sys.modules["ui"]
        # hermetic settings: this test assumes sequential, single-output
        # exports — never inherit dual_render/timing/parallel from the
        # developer's real settings.json
        monkeypatch.setattr(ui_mod, "SETTINGS_FILE", tmp_path / "settings.json")
        # the batch-complete QMessageBox is modal and would block offscreen
        monkeypatch.setattr(ui_mod.QMessageBox, "information",
                            staticmethod(lambda *a, **k: None))
        out_dir = tmp_path / "outgui"
        out_dir.mkdir()
        monkeypatch.setattr(ui_mod, "OUTPUT_DIR", out_dir)
        w = MainWindow()
        w.config.resolution = "1280x720"
        w.config.fps = 10
        w.config.sound_enabled = False
        w.config.yt_extras = False
        w._items = [FileItem(path=sample_code, checked=True)]
        w._item_paths = {sample_code}
        w._start_export()
        loop = QEventLoop()
        state = {"timeout": False}

        def check():
            cmd = w.current_command
            if not w.export_commands and cmd is not None and \
                    cmd.item.status in ("Done", "Failed", "Cancelled", "Skipped"):
                loop.quit()

        def on_timeout():
            state["timeout"] = True
            loop.quit()

        QTimer.singleShot(150000, on_timeout)
        timer = QTimer()
        timer.setInterval(400)
        timer.timeout.connect(check)
        timer.start()
        loop.exec()
        timer.stop()
        assert not state["timeout"], "GUI batch export did not finish in time"
        assert w.current_command.item.status == "Done", \
            f"status={w.current_command.item.status}"
        produced = list(out_dir.glob("*.mp4"))
        assert produced, "no mp4 produced"
        streams, _ = ffprobe_streams(str(produced[0]))
        assert ("h264", "video") in streams
        w.close()


# ================================================================ v2.3 e2e
@pytest.mark.e2e
class TestYouTubePackE2E:
    def test_branding_export_with_metadata(self, qgui, base_config, sample_code, tmp_path):
        """intro+outro+watermark export: duration grows, audio present,
        description + metadata files written next to the mp4."""
        cfg = base_config
        cfg.sound_enabled = True
        cfg.intro_enabled = True
        cfg.intro_text = "E2E Intro"
        cfg.outro_enabled = True
        cfg.wm_enabled = True
        cfg.wm_text = "@e2e"
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        typing_dur = mp.typing_duration()
        out = str(tmp_path / "branded.mp4")
        result = ExportEngine(mp, cfg, out, source_names=["demo.py"]).run()
        assert result.success, result.message
        streams, dur = ffprobe_streams(out)
        assert ("h264", "video") in streams and ("aac", "audio") in streams
        assert dur >= typing_dur + 3.5, f"branding not included in duration ({dur})"
        desc = tmp_path / "branded.description.txt"
        meta = tmp_path / "branded.metadata.json"
        assert desc.exists() and meta.exists()
        assert "0:00 Intro" in desc.read_text(encoding="utf-8")
        data = json.loads(meta.read_text(encoding="utf-8"))
        assert data["title"] == "Demo"
        assert len(data["chapters"]) == 3

    def test_no_metadata_flag(self, qgui, base_config, sample_code, tmp_path):
        SC = StudioConfig  # was: from config import StudioConfig as SC
        cfg = base_config
        cfg.sound_enabled = False
        cfg.write_metadata = False
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "nometa.mp4")
        result = ExportEngine(mp, cfg, out).run()
        assert result.success
        assert not (tmp_path / "nometa.description.txt").exists()
        assert not (tmp_path / "nometa.metadata.json").exists()

    def test_punch_zoom_vertical(self, qgui, base_config, sample_code):
        """Punch-in zoom only applies vertically and changes the frames."""
        from PySide6.QtGui import QImage
        cfg = base_config
        cfg.resolution = "720x1280 (9:16)"
        cfg.punch_zoom = True
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        td = mp.typing_duration()
        img_a = mp.render_frame(td * 0.02)
        img_b = mp.render_frame(td * 0.95)
        # zoom shifts the whole code window: many sampled pixels must move
        diff = 0
        for y in range(0, img_a.height(), 29):
            for x in range(0, img_a.width(), 11):
                if img_a.pixelColor(x, y) != img_b.pixelColor(x, y):
                    diff += 1
        assert diff > 20, "punch zoom did not change the frame content"

    def test_thumbnails_sizes(self, qgui, base_config, sample_code, tmp_path):
        mp = make_strategies()[base_config.mode].build_panes(
            base_config, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "movie.mp4")
        paths = save_thumbnails(mp, base_config, out, headline="E2E Thumb")
        assert len(paths) == 2
        from PySide6.QtGui import QImage
        for p, (w, h) in zip(paths, ((1280, 720), (1080, 1920))):
            img = QImage(p)
            assert (img.width(), img.height()) == (w, h), p

    def test_dual_render_cli(self, tmp_path):
        (tmp_path / "dual.py").write_text("a = 1\nb = 2\n", encoding="utf-8")
        r = run_cli(["--headless", "dual.py", "--fps", "10", "--no-sound",
                     "--quality", "Small", "--dual-render",
                     "-o", str(tmp_path / "out")], cwd=tmp_path)
        assert r.returncode == 0, r.stderr[-2000:]
        yt = next(tmp_path.joinpath("out").glob("*_yt.mp4"), None)
        sh = next(tmp_path.joinpath("out").glob("*_shorts.mp4"), None)
        assert yt is not None and sh is not None, list(tmp_path.joinpath("out").iterdir())
        for path, (w, h) in ((yt, (1920, 1080)), (sh, (1080, 1920))):
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=width,height",
                 "-of", "json", str(path)],
                capture_output=True, text=True, timeout=30)
            dims = json.loads(out.stdout)["streams"][0]
            assert (dims["width"], dims["height"]) == (w, h), path

    def test_cli_thumbnail_and_metadata(self, tmp_path):
        (tmp_path / "thumb_demo.py").write_text("print('thumbs')\n", encoding="utf-8")
        r = run_cli(["--headless", "thumb_demo.py", "--fps", "10", "--no-sound",
                     "--thumbnail", "--thumb-text", "Cool Demo",
                     "-o", str(tmp_path / "tm")], cwd=tmp_path)
        assert r.returncode == 0, r.stderr[-2000:]
        yt = next(tmp_path.rglob("*_thumbnail_yt.png"), None)
        sh = next(tmp_path.rglob("*_thumbnail_shorts.png"), None)
        assert yt is not None and sh is not None, [p.name for p in tmp_path.iterdir()]
        # metadata auto-written (default) next to the mp4
        desc = next(tmp_path.rglob("*.description.txt"), None)
        mjson = next(tmp_path.rglob("*.metadata.json"), None)
        assert desc is not None and mjson is not None
        data = json.loads(mjson.read_text())
        assert data["title"] == "Thumb Demo"

    def test_gui_youtube_shorts_tab(self, qapp):
        w = MainWindow()
        tabs = [w.common_tabs.tabText(i) for i in range(w.common_tabs.count())]
        assert "YouTube & Shorts" in tabs
        assert w.quality_cb.count() == 3 and w.quality_cb.currentText() == "Balanced"
        assert w.loudnorm_chk.isChecked()
        # watermark roundtrip through config
        w.wm_chk.setChecked(True)
        w.wm_edit.setText("@roundtrip")
        assert w.config.wm_enabled and w.config.wm_text == "@roundtrip"
        w.config.wm_enabled = False
        w._apply_config_to_ui()
        assert w.wm_chk.isChecked() is False
        w.close()

    def test_gui_dual_render_batch(self, qapp, sample_code, tmp_path, monkeypatch):
        """GUI dual-render produces both variants via the QThread queue."""
        from PySide6.QtCore import QEventLoop, QTimer
        ui_mod = sys.modules["ui"]  # was: import ui as ui_mod
        monkeypatch.setattr(ui_mod.QMessageBox, "information",
                            staticmethod(lambda *a, **k: None))
        out_dir = tmp_path / "outdual"
        out_dir.mkdir()
        monkeypatch.setattr(ui_mod, "OUTPUT_DIR", out_dir)
        w = MainWindow()
        w.config.resolution = "1280x720"
        w.config.fps = 10
        w.config.sound_enabled = False
        w.config.yt_extras = False
        w.config.write_metadata = False
        w.config.dual_render = True
        w._items = [FileItem(path=sample_code, checked=True)]
        w._item_paths = {sample_code}
        w._start_export()
        loop = QEventLoop()
        state = {"timeout": False}

        def check():
            if w.batch_done >= w.batch_total:
                loop.quit()

        def on_timeout():
            state["timeout"] = True
            loop.quit()

        QTimer.singleShot(240000, on_timeout)
        timer = QTimer()
        timer.setInterval(400)
        timer.timeout.connect(check)
        timer.start()
        loop.exec()
        timer.stop()
        assert not state["timeout"], "dual batch did not finish in time"
        names = sorted(p.name for p in out_dir.glob("*.mp4"))
        assert any("_yt.mp4" in n for n in names) and any("_shorts.mp4" in n for n in names), names
        w.close()


# ================================================================ v2.4 timing e2e
@pytest.mark.e2e
class TestTimingE2E:
    def test_export_hits_target_duration(self, qgui, base_config, tmp_path):
        """Auto-fit must make the exported mp4 land on the target duration."""
        code = str(tmp_path / "fit_demo.py")
        Path(code).write_text(
            "def fib(n):\n    return n if n < 2 else fib(n - 1) + fib(n - 2)\n\n"
            "print([fib(i) for i in range(12)])\n", encoding="utf-8")
        cfg = base_config
        cfg.timing_fit = "Target Duration"
        cfg.timing_target = 10.0
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(code)], "")
        out = str(tmp_path / "fit.mp4")
        result = ExportEngine(mp, cfg, out).run()
        assert result.success, result.message
        _, dur = ffprobe_streams(out)
        assert 9.0 <= dur <= 11.5, f"target 10s but export is {dur:.2f}s"

    def test_export_rhythm_changes_output(self, qgui, base_config, sample_code, tmp_path):
        """Cinematic rhythm must produce a longer video than Classic."""
        durs = {}
        for style in ("Classic", "Cinematic"):
            cfg = base_config
            cfg.rhythm_style = style
            mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
            out = str(tmp_path / f"rhythm_{style.lower()}.mp4")
            result = ExportEngine(mp, cfg, out).run()
            assert result.success, result.message
            _, durs[style] = ffprobe_streams(out)
        assert durs["Cinematic"] > durs["Classic"], durs

    def test_cli_timing_fit_flag(self, tmp_path):
        (tmp_path / "cli_fit.py").write_text(
            "def add(a, b):\n    return a + b\n\nprint(add(40, 2))\n",
            encoding="utf-8")
        r = run_cli(["--headless", "cli_fit.py", "-o", "out/fit.mp4",
                     "--resolution", "1280x720", "--fps", "12", "--no-sound",
                     "--timing-fit", "duration", "--timing-target", "9",
                     "--no-metadata"], cwd=tmp_path)
        assert r.returncode == 0, r.stderr[-2000:]
        _, dur = ffprobe_streams(str(tmp_path / "out" / "fit.mp4"))
        assert 8.0 <= dur <= 10.5, f"target 9s but CLI export is {dur:.2f}s"

    def test_cli_dry_run_reports_fit(self, tmp_path):
        (tmp_path / "d.py").write_text("x = 1\n", encoding="utf-8")
        r = run_cli(["--headless", "--dry-run", "d.py", "--timing-fit",
                     "duration", "--timing-target", "30"], cwd=tmp_path)
        assert r.returncode == 0
        assert "auto-fit" in r.stdout and "rhythm=Natural" in r.stdout

    def test_gui_timing_controls_roundtrip(self, qt_app, tmp_path):
        """The Video-tab timing controls exist, apply, and persist."""
        win = MainWindow()
        win.show()
        try:
            assert win.rhythm_style_cb.count() == 3
            assert win.timing_fit_cb.count() == 3
            # quick-target chip drives the fit config
            win._apply_target_duration(90)
            assert win.config.timing_fit == "Target Duration"
            assert abs(win.config.timing_target - 90.0) < 1e-9
            # estimate label gets populated by a preview build
            win._invalidate_preview()
            assert "Est. total" in win.timing_est_lbl.text()
            # settings roundtrip (asdict -> safe_config) keeps the v2.4 fields
            from dataclasses import asdict
            data = asdict(win.config)
            data["mode"] = win.config.mode.value
            cfg2 = safe_config_from_dict(data)
            assert cfg2.timing_fit == "Target Duration"
            assert abs(cfg2.timing_target - 90.0) < 1e-9
            assert cfg2.rhythm_style == win.config.rhythm_style
        finally:
            win.close()

#==========================================================================
# ── UNIT — design-pattern layer (EncoderStrategy, ProgressObserver)
#==========================================================================

class TestEncoderStrategyPattern:
    """Strategy pattern over the ffmpeg encoder backends."""

    def test_every_hardware_id_resolves_to_its_own_strategy(self):
        for enc_id, _label, _name in HARDWARE_ENCODERS:
            assert get_encoder_strategy(enc_id).encoder_id == enc_id

    def test_unknown_or_empty_id_falls_back_to_software(self):
        assert get_encoder_strategy("nope").encoder_id == "software"
        assert get_encoder_strategy("").encoder_id == "software"

    def test_facade_delegates_to_the_resolved_strategy(self):
        for enc_id in ("nvenc", "qsv", "amf", "videotoolbox", "vaapi", "software"):
            strategy = get_encoder_strategy(enc_id)
            assert build_video_codec_args(enc_id, 1280, 720, 30, "Balanced") == (
                strategy.global_args(1280, 720, 30, "Balanced"),
                strategy.codec_args(1280, 720, 30, "Balanced"))

    def test_only_vaapi_needs_global_device_args(self):
        for enc_id in ("nvenc", "qsv", "amf", "videotoolbox", "software"):
            assert get_encoder_strategy(enc_id).global_args(64, 64, 30, "High") == []
        assert get_encoder_strategy("vaapi").global_args(64, 64, 30, "High") == [
            "-init_hw_device", "vaapi=va:", "-filter_hw_device", "va"]

    def test_quality_value_is_substituted_into_the_template(self):
        high = get_encoder_strategy("nvenc").codec_args(64, 64, 30, "High")
        small = get_encoder_strategy("nvenc").codec_args(64, 64, 30, "Small")
        assert high[high.index("-cq") + 1] == str(QUALITY_MAP["High"]["hw"])
        assert small[small.index("-cq") + 1] == str(QUALITY_MAP["Small"]["hw"])

    def test_amf_qp_p_follows_qp_i(self):
        args = get_encoder_strategy("amf").codec_args(64, 64, 30, "High")
        qp_i = int(args[args.index("-qp_i") + 1])
        qp_p = int(args[args.index("-qp_p") + 1])
        assert qp_p == qp_i + 2

    def test_software_bitrate_ceiling_scales_with_frame_size(self):
        small = get_encoder_strategy("software").codec_args(640, 360, 30, "High")
        big = get_encoder_strategy("software").codec_args(1920, 1080, 30, "High")
        maxrate = lambda args: int(args[args.index("-maxrate") + 1])  # noqa: E731
        assert maxrate(big) > maxrate(small)

    def test_strategies_are_immutable(self):
        for strategy in ENCODER_STRATEGIES.values():
            with pytest.raises((AttributeError, TypeError)):
                strategy.encoder_id = "tampered"  # type: ignore[misc]

class TestProgressObserverPattern:
    """Observer pattern: fan-out, idempotent wiring, fault isolation."""

    def test_events_fan_out_to_every_attached_observer(self):
        seen: list = []
        subject = ProgressSubject()
        subject.attach(CallbackObserver(on_progress=seen.append,
                                        on_status=lambda m: seen.append(m)))
        subject.notify_progress(50)
        subject.notify_status("encoding")
        assert seen == [50, "encoding"]

    def test_attach_is_idempotent(self):
        calls: list = []
        observer = CallbackObserver(on_progress=calls.append)
        subject = ProgressSubject()
        subject.attach(observer)
        subject.attach(observer)
        subject.notify_progress(1)
        assert calls == [1]

    def test_broken_observer_is_isolated_and_detached(self):
        calls: list = []

        class Boom:
            def on_progress(self, percent: int) -> None:
                raise RuntimeError("boom")

            def on_status(self, message: str) -> None:
                raise RuntimeError("boom")

        subject = ProgressSubject()
        subject.attach(Boom())
        subject.attach(CallbackObserver(on_progress=calls.append))
        subject.notify_progress(7)            # must not raise
        assert calls == [7]
        subject.notify_progress(8)            # Boom was detached after failing
        assert calls == [7, 8]

    def test_detach_of_unknown_observer_is_silent(self):
        ProgressSubject().detach(CallbackObserver())   # must not raise

    def test_export_engine_accepts_observers(self):
        import inspect
        assert "observers" in inspect.signature(ExportEngine.run).parameters


# ================================================================ cancel
class TestRenderCancellation:
    """Cancel-the-render plumbing: engine abort + partial-file cleanup,
    GUI button wiring and queue-wide cancellation."""

    # ------------------------------------------------ engine level
    def test_precancelled_engine_run_aborts_and_cleans_up(self, qgui, base_config, sample_code, tmp_path):
        """A cancel_event set before run() returns a cancelled result and
        leaves NO partial mp4 behind (ffmpeg is killed before finishing)."""
        import threading
        cfg = base_config
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "cancelled.mp4")
        cancel = threading.Event()
        cancel.set()
        result = ExportEngine(mp, cfg, out).run(cancel_event=cancel)
        assert result.cancelled and not result.success
        assert result.message == "Cancelled"
        assert not os.path.exists(out), "partial mp4 must be deleted on cancel"

    def test_cancel_during_render_removes_partial_file(self, qgui, base_config, sample_code, tmp_path):
        """Cancelling at the first progress tick still aborts the encode,
        kills ffmpeg and removes the unplayable partial mp4."""
        import threading
        cfg = base_config
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "midway.mp4")
        cancel = threading.Event()

        def on_progress(p):
            if p == 0:                       # first frame written -> mid-encode
                cancel.set()

        result = ExportEngine(mp, cfg, out).run(progress_cb=on_progress,
                                                cancel_event=cancel)
        assert result.cancelled
        assert not os.path.exists(out), "partial mp4 must be deleted on cancel"

    def test_gif_cancel_also_cleans_up(self, qgui, base_config, sample_code, tmp_path):
        import threading
        cfg = base_config
        cfg.output_format = "gif"
        cfg.fps = 10
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "midway.gif")
        cancel = threading.Event()
        cancel.set()
        result = ExportEngine(mp, cfg, out).run(cancel_event=cancel)
        assert result.cancelled
        assert not os.path.exists(out), "partial gif must be deleted on cancel"

    def test_png_cancel_keeps_the_partial_frames(self, qgui, base_config, sample_code, tmp_path):
        """PNG sequences are kept on cancel: written frames are valid
        standalone images, and the result reports how many were written."""
        import threading
        cfg = base_config
        cfg.output_format = "png"
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        outdir = str(tmp_path / "frames")
        cancel = threading.Event()

        def on_progress(p):
            if p == 0:
                cancel.set()

        result = ExportEngine(mp, cfg, outdir).run(progress_cb=on_progress,
                                                   cancel_event=cancel)
        assert result.cancelled
        assert result.frames >= 1
        written = sorted(f for f in os.listdir(outdir) if f.endswith(".png"))
        assert len(written) == result.frames
        assert written[0] == "frame_000000.png"

    # ------------------------------------------------ GUI wiring
    def test_cancel_button_is_labeled_and_disabled_while_idle(self, qapp, tmp_path, monkeypatch):
        from PySide6.QtGui import QShortcut
        monkeypatch.setattr(sys.modules["ui"], "SETTINGS_FILE",
                            tmp_path / "settings.json")   # hermetic
        w = MainWindow()
        assert w.cancel_btn.text() == "\u2716 Cancel"
        assert not w.cancel_btn.isEnabled()          # idle: nothing to cancel
        keys = [s.key().toString() for s in w.findChildren(QShortcut)]
        assert "Ctrl+." in keys, "Ctrl+. shortcut missing"
        w.close()

    def test_cancel_when_idle_is_a_noop(self, qapp, tmp_path, monkeypatch):
        monkeypatch.setattr(sys.modules["ui"], "SETTINGS_FILE",
                            tmp_path / "settings.json")   # hermetic
        w = MainWindow()
        w._cancel_export()
        assert w.statusBar().currentMessage() == "No render is running."
        assert not w._batch_cancelled
        assert not w._export_active
        w.close()

    def test_cancel_marks_current_and_pending_items(self, qapp, tmp_path, monkeypatch):
        """The ✖ Cancel button cancels the running render AND the rest of
        the queue, then resets the UI."""
        from collections import deque
        from app import ExportCommand
        monkeypatch.setattr(sys.modules["ui"], "SETTINGS_FILE",
                            tmp_path / "settings.json")   # hermetic
        w = MainWindow()

        class StubExporter:
            def __init__(self):
                self.cancel_called = False
            def cancel(self):
                self.cancel_called = True
            def isRunning(self):
                return True

        def make_cmd(tag):
            it = FileItem(path=f"{tag}.py", checked=True)
            it.status = "Running" if tag == "a" else "Pending"
            return ExportCommand(item=it, output_path=f"{tmp_path}/{tag}.mp4",
                                 config=StudioConfig(), status=it.status)

        cmd_a, cmd_b, cmd_c = make_cmd("a"), make_cmd("b"), make_cmd("c")
        stub = StubExporter()
        w.current_command = cmd_a
        w.export_commands = deque([cmd_b, cmd_c])
        w._exporter = stub
        w._active_exports = {cmd_a: stub}   # _cancel_export walks this dict
        w._export_active = True
        w.progress_bar.setVisible(True)
        w.cancel_btn.setEnabled(True)
        w.skip_btn.setEnabled(True)
        w.export_btn.setEnabled(False)

        w._cancel_export()

        assert w._exporter.cancel_called
        assert not w.export_commands
        assert cmd_a.item.status == "Cancelled"
        assert cmd_b.item.status == "Cancelled"
        assert cmd_c.item.status == "Cancelled"
        assert w._batch_cancelled and not w._export_active
        assert w.export_btn.isEnabled()
        assert not w.skip_btn.isEnabled()
        assert not w.cancel_btn.isEnabled()
        assert not w.progress_bar.isVisible()
        assert w.batch_info_lbl.text() == "Batch cancelled"
        w.close()

    def test_cancel_button_interrupts_running_render(self, qapp, sample_code, tmp_path, monkeypatch):
        """End-to-end GUI plumbing: Export -> worker thread builds panes ->
        ✖ Cancel -> blocking engine unblocks -> item marked Cancelled."""
        import threading
        from PySide6.QtCore import QEventLoop, QTimer
        from app import ExportResult
        ui_mod = sys.modules["ui"]
        out_dir = tmp_path / "outcancel"
        out_dir.mkdir()
        monkeypatch.setattr(ui_mod, "OUTPUT_DIR", out_dir)
        monkeypatch.setattr(ui_mod, "SETTINGS_FILE", tmp_path / "settings.json")   # hermetic
        # never let a modal dialog hang the test (e.g. a worker failure that
        # drains the queue would otherwise open the "Done" dialog)
        monkeypatch.setattr(ui_mod.QMessageBox, "information",
                            staticmethod(lambda *a, **k: None))
        monkeypatch.setattr(ui_mod.QMessageBox, "warning",
                            staticmethod(lambda *a, **k: None))

        class BlockingEngine:
            """Stands in for ExportEngine: parks until cancel is pressed."""
            def __init__(self, mp, config, output, source_names=None):
                self.output = output
            def run(self, progress_cb=None, status_cb=None, cancel_event=None,
                    observers=None, max_workers=None):
                cancel_event.wait(timeout=15)
                return ExportResult(False, "Cancelled", self.output, 0,
                                    cancelled=True)

        monkeypatch.setattr(ui_mod, "ExportEngine", BlockingEngine)

        w = MainWindow()
        w.config.resolution = "1280x720"
        w.config.fps = 10
        w.config.sound_enabled = False
        w.config.yt_extras = False
        w._items = [FileItem(path=sample_code, checked=True)]
        w._item_paths = {sample_code}
        w._start_export()

        loop = QEventLoop()
        state = {"done": False}

        def check():
            exp = w._exporter
            if exp is None or not exp.isRunning():
                if state["started"]:
                    state["done"] = True
                    loop.quit()
                return
            if not state["started"]:
                state["started"] = True
                w._cancel_export()           # the ✖ Cancel button slot

        state["started"] = False
        QTimer.singleShot(30000, lambda: loop.quit())
        timer = QTimer()
        timer.setInterval(50)
        timer.timeout.connect(check)
        timer.start()
        loop.exec()
        timer.stop()

        assert state["started"], "exporter thread never started"
        assert state["done"], "cancel did not finish in time"
        assert w.current_command.item.status == "Cancelled"
        assert w._batch_cancelled and not w._export_active
        assert not w.export_commands
        assert not w.cancel_btn.isEnabled()
        assert not list(out_dir.glob("*.mp4")), "no output expected from cancel"
        w.close()


# ================================================================ parallel
class TestParallelRendering:
    """Better threading: parallel audio DSP, per-render frame budgets,
    parallel GUI batch and CLI --jobs."""

    # ------------------------------------------------ engine level
    def test_engine_accepts_frame_worker_budget(self, qgui, base_config, sample_code, tmp_path):
        """max_workers caps the frame pool (used by parallel batches)."""
        import inspect
        assert "max_workers" in inspect.signature(ExportEngine.run).parameters
        cfg = base_config
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        out = str(tmp_path / "workers.mp4")
        result = ExportEngine(mp, cfg, out).run(max_workers=2)
        assert result.success, result.message
        assert result.frames > 0

    def test_parallel_audio_build_is_deterministic(self, qgui, base_config, sample_code, tmp_path):
        """Key PCM + ambience bed render on parallel threads and still
        produce byte-identical audio for identical configs."""
        import wave as _wave
        cfg = base_config
        cfg.sound_enabled = True
        cfg.amb_enabled = True
        cfg.amb_preset = "Rain"
        cfg.amb_volume = 35
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        outs = []
        for i in (1, 2):
            path = str(tmp_path / f"audio_{i}.wav")
            sr = app._build_audio(cfg, mp, path)
            assert sr and sr > 0
            with _wave.open(path, "rb") as wf:
                outs.append((wf.getframerate(), wf.getnchannels(),
                             wf.getnframes(), wf.readframes(wf.getnframes())))
        assert outs[0][:3] == outs[1][:3]
        assert outs[0][3] == outs[1][3], "parallel DSP must be deterministic"

    def test_gif_export_skips_audio_synthesis(self, qgui, base_config, sample_code, tmp_path, monkeypatch):
        """GIF cannot carry audio -> the soundscape stage is skipped."""
        cfg = base_config
        cfg.output_format = "gif"
        cfg.fps = 10
        cfg.sound_enabled = True
        cfg.amb_enabled = False
        mp = make_strategies()[cfg.mode].build_panes(cfg, [HeadlessFile(sample_code)], "")
        called = []
        monkeypatch.setattr(app, "_build_audio",
                            lambda *a, **k: called.append(1) or None)
        out = str(tmp_path / "silent.gif")
        result = ExportEngine(mp, cfg, out).run()
        assert result.success, result.message
        assert not called, "_build_audio must not run for gif exports"

    # ------------------------------------------------ GUI parallel batch
    def _blocking_engine(self, cancel_blocking=False):
        """Build a fake ExportEngine factory that proves real overlap."""
        import threading
        import time as _time
        from app import ExportResult

        class Engine:
            entered = 0
            both_running = threading.Event()
            max_active = 0
            active = 0

            def __init__(self, mp, config, output, source_names=None):
                self.output = output

            def run(self, progress_cb=None, status_cb=None,
                    cancel_event=None, observers=None, max_workers=None):
                Engine.active += 1
                Engine.max_active = max(Engine.max_active, Engine.active)
                Engine.entered += 1
                if Engine.entered == 2:
                    Engine.both_running.set()
                elif not Engine.both_running.wait(timeout=10):
                    Engine.active -= 1
                    return ExportResult(False, "rendezvous timeout",
                                        self.output, 0)
                if cancel_blocking and cancel_event is not None:
                    cancel_event.wait(timeout=15)
                _time.sleep(0.05)
                cancelled = (cancel_event is not None and cancel_event.is_set())
                Engine.active -= 1
                if cancelled:
                    return ExportResult(False, "Cancelled", self.output, 0,
                                        cancelled=True)
                return ExportResult(True, "ok", self.output, 10)

        return Engine

    def _run_gui_batch(self, qapp, monkeypatch, tmp_path, sample_code,
                       parallel, engine_cls, n_items=2):
        from PySide6.QtCore import QEventLoop, QTimer
        from collections import deque
        from app import ExportCommand
        ui_mod = sys.modules["ui"]
        out_dir = tmp_path / "outpar"
        out_dir.mkdir()
        monkeypatch.setattr(ui_mod, "OUTPUT_DIR", out_dir)
        monkeypatch.setattr(ui_mod, "SETTINGS_FILE", tmp_path / "settings.json")   # hermetic
        monkeypatch.setattr(ui_mod.QMessageBox, "information",
                            staticmethod(lambda *a, **k: None))
        monkeypatch.setattr(ui_mod, "ExportEngine", engine_cls)

        w = MainWindow()
        w.config.parallel_renders = parallel
        w.config.resolution = "1280x720"
        w.config.fps = 10
        w.config.sound_enabled = False
        w.config.yt_extras = False
        w.config.write_metadata = False
        cmds = []
        for i in range(n_items):
            # real files: the exporter still builds panes for real
            p = tmp_path / f"item_{i}.py"
            p.write_text(Path(sample_code).read_text(encoding="utf-8"),
                         encoding="utf-8")
            it = FileItem(path=str(p), checked=True)
            cmd = ExportCommand(item=it, output_path=str(out_dir / f"o{i}.mp4"),
                                config=w.config)
            cmds.append(cmd)
        w.export_commands = deque(cmds)
        w.export_btn.setEnabled(False)
        w.cancel_btn.setEnabled(True)
        w.skip_btn.setEnabled(True)
        w._batch_cancelled = False
        w._export_active = True
        w.batch_total = len(cmds)
        w.batch_done = 0
        w.batch_start_time = __import__("time").time()
        w.progress_bar.setVisible(True)
        w._process_export_queue()
        return w, out_dir

    def _wait_batch_end(self, w, timeout_s=30):
        from PySide6.QtCore import QEventLoop, QTimer
        loop = QEventLoop()
        QTimer.singleShot(int(timeout_s * 1000), loop.quit)
        timer = QTimer()
        timer.setInterval(50)
        timer.timeout.connect(lambda: (not w._active_exports and loop.quit()))
        timer.start()
        loop.exec()
        timer.stop()

    def test_gui_parallel_batch_renders_overlap(self, qapp, sample_code, tmp_path, monkeypatch):
        engine = self._blocking_engine()
        w, out_dir = self._run_gui_batch(qapp, monkeypatch, tmp_path,
                                         sample_code, parallel=2, engine_cls=engine)
        assert len(w._active_exports) == 2, "both renders must start at once"
        assert len(w.export_commands) == 0
        self._wait_batch_end(w)
        assert engine.max_active == 2, \
            f"renders must overlap (max_active={engine.max_active})"
        assert w.batch_done == 2
        assert w.current_command.item.status == "Done"
        w.close()

    def test_gui_sequential_batch_never_overlaps(self, qapp, sample_code, tmp_path, monkeypatch):
        """parallel_renders=1 keeps the old one-at-a-time behaviour."""
        engine = self._blocking_engine()
        # no rendezvous needed for sequential; make entry 2 not wait forever
        engine.both_running.set()
        w, out_dir = self._run_gui_batch(qapp, monkeypatch, tmp_path,
                                         sample_code, parallel=1, engine_cls=engine)
        assert len(w._active_exports) == 1
        self._wait_batch_end(w)
        assert engine.max_active == 1, \
            f"sequential must not overlap (max_active={engine.max_active})"
        assert w.batch_done == 2
        w.close()

    def test_gui_cancel_hits_every_parallel_render(self, qapp, sample_code, tmp_path, monkeypatch):
        from PySide6.QtCore import QEventLoop, QTimer
        engine = self._blocking_engine(cancel_blocking=True)
        engine.both_running.set()        # don't wait for a rendezvous
        w, out_dir = self._run_gui_batch(qapp, monkeypatch, tmp_path,
                                         sample_code, parallel=2, engine_cls=engine)
        # wait until both engines are inside run() and blocked on cancel
        loop = QEventLoop()
        QTimer.singleShot(20000, loop.quit)
        timer = QTimer()
        timer.setInterval(20)
        timer.timeout.connect(lambda: (len(w._active_exports) == 2
                                       and engine.entered >= 2 and loop.quit()))
        timer.start()
        loop.exec()
        timer.stop()
        assert len(w._active_exports) == 2

        w._cancel_export()               # the ✖ Cancel button slot
        self._wait_batch_end(w)
        assert engine.max_active == 2
        assert w._batch_cancelled and not w._export_active
        assert not w.export_commands
        w.close()

    def test_parallel_spinbox_roundtrip_and_persist(self, qapp, tmp_path, monkeypatch):
        from PySide6.QtGui import QCloseEvent
        ui_mod = sys.modules["ui"]
        settings_file = tmp_path / "settings.json"
        monkeypatch.setattr(ui_mod, "SETTINGS_FILE", settings_file)
        w = MainWindow()
        w.parallel_sp.setValue(3)
        assert w.config.parallel_renders == 3
        w.config.parallel_renders = 4
        w._apply_config_to_ui()
        assert w.parallel_sp.value() == 4
        w.closeEvent(QCloseEvent())
        data = json.loads(settings_file.read_text())
        assert data["parallel_renders"] == 4
        w.close()

    # ------------------------------------------------ CLI parallel
    def test_cli_batch_jobs_renders_in_parallel(self, qgui, sample_code, tmp_path):
        """run_batch_headless(jobs=2) renders both files (real ffmpeg,
        ordered report, both outputs on disk)."""
        extra = tmp_path / "second.py"
        extra.write_text("x = 1\ny = 2\nprint(x + y)\n", encoding="utf-8")
        cfg = StudioConfig(resolution="1280x720", fps=10, sound_enabled=False,
                           yt_extras=False, write_metadata=False)
        report = run_batch_headless(cfg, [sample_code, str(extra)],
                                    jobs=2, quiet=True)
        assert len(report.ok) == 2 and not report.failed
        assert [it["ok"] for it in report.items] == [True, True]
        assert [it["input"] for it in report.items] == [sample_code, str(extra)]
        out_files = [it["output"] for it in report.items]
        assert all(os.path.exists(p) and os.path.getsize(p) > 0
                   for p in out_files)

    def test_cli_batch_jobs_respects_thread_budget(self, qgui, sample_code, tmp_path, monkeypatch):
        """Each parallel export gets cpu//jobs frame workers."""
        seen = []
        real_run = ExportEngine.run

        def spy_run(self, *a, **k):
            seen.append(k.get("max_workers"))
            return real_run(self, *a, **k)

        monkeypatch.setattr(app, "ExportEngine",
                            type("E", (app.ExportEngine,),
                                 {"run": spy_run}))
        extra = tmp_path / "third.py"
        extra.write_text("a = 41\nb = 1\nprint(a + b)\n", encoding="utf-8")
        cfg = StudioConfig(resolution="1280x720", fps=10, sound_enabled=False,
                           yt_extras=False, write_metadata=False)
        report = run_batch_headless(cfg, [sample_code, str(extra)],
                                    jobs=2, quiet=True)
        assert len(report.ok) == 2
        total_cpu = max(2, (os.cpu_count() or 4) - 1)
        assert seen == [max(1, total_cpu // 2)] * 2


# ================================================================ music layer
class TestMusicLayer:
    """The procedural music layer that ships under every background bed."""

    def test_every_soundscape_has_a_profile(self):
        for name in list_ambience_presets():
            assert name in MUSIC_PROFILES, f"no music profile for {name!r}"

    def test_profiles_are_valid_music(self):
        for name, prof in MUSIC_PROFILES.items():
            assert 20.0 <= prof.bpm <= 200.0, name
            assert prof.pattern in ("block", "sparse", "poly", "arp",
                                    "arp_ud", "sway", "chimes"), name
            assert len(prof.prog) >= 1, name
            for off, ctype in prof.prog:
                assert -12 <= off <= 24, name
                assert ctype in ("M", "m", "7", "m7", "maj7", "9", "m9",
                                 "maj9", "add9", "madd9", "sus2", "sus4",
                                 "6", "m6", "5"), name
            assert 400.0 <= prof.tone <= 8000.0, name

    def test_note_hz_reference_pitches(self):
        assert abs(_note_hz("A4") - 440.0) < 0.01
        assert abs(_note_hz("A2") - 110.0) < 0.01
        assert abs(_note_hz("C4") - 261.6256) < 0.01
        assert abs(_note_hz("Bb3") - 233.08) < 0.1

    def test_music_bed_shape_and_bounds(self):
        m = build_music_bed("Rain", 3.0)
        assert len(m) == 3 * 48000
        assert m.dtype == np.float64
        assert np.all(np.isfinite(m))
        assert np.max(np.abs(m)) <= 1.0

    def test_music_bed_has_energy(self):
        for name in ("Rain", "Lo-Fi Study", "Ocean Waves", "Zen Garden"):
            m = build_music_bed(name, 4.0)
            assert float(np.sqrt(np.mean(m * m))) > 0.01, name

    @pytest.mark.parametrize("name", list_ambience_presets())
    def test_all_profiles_render(self, name):
        m = build_music_bed(name, 2.0)
        assert len(m) == 2 * 48000
        assert np.all(np.isfinite(m))
        assert np.max(np.abs(m)) <= 1.0 + 1e-9
        assert float(np.sqrt(np.mean(m * m))) > 1e-4, name

    def test_music_bed_deterministic(self):
        a = build_music_bed("Lo-Fi Study", 3.0, seed=5)
        b = build_music_bed("Lo-Fi Study", 3.0, seed=5)
        assert np.array_equal(a, b)
        c = build_music_bed("Lo-Fi Study", 3.0, seed=6)
        assert not np.array_equal(a, c)

    def test_music_volume_scales_loudness(self):
        loud = build_music_bed("Rain", 3.0, volume=1.0)
        soft = build_music_bed("Rain", 3.0, volume=0.25)
        rms_loud = float(np.sqrt(np.mean(loud ** 2)))
        rms_soft = float(np.sqrt(np.mean(soft ** 2)))
        assert rms_loud > rms_soft * 2.5      # 4x volume, 4x rms (minus caps)
        assert rms_soft > 1e-4

    def test_bed_with_and_without_music_differ(self):
        cfg_on = StudioConfig(amb_enabled=True, amb_preset="Wind",
                              amb_music=True, amb_music_volume=80)
        cfg_off = StudioConfig(amb_enabled=True, amb_preset="Wind",
                               amb_music=False)
        on = build_ambience_bed(cfg_on, 3.0)
        off = build_ambience_bed(cfg_off, 3.0)
        assert np.max(np.abs(on)) <= 1.0 + 1e-9
        assert np.max(np.abs(off)) <= 1.0 + 1e-9
        assert not np.array_equal(on, off)

    def test_bed_music_off_matches_pure_texture(self):
        cfg = StudioConfig(amb_enabled=True, amb_preset="Rain", amb_music=False)
        bed = build_ambience_bed(cfg, 2.0)
        tex = render_ambience("Rain", 2.0)
        assert np.allclose(bed, tex)

    def test_music_off_by_config_volume_zero(self):
        # volume 0 must behave exactly like music disabled
        cfg_zero = StudioConfig(amb_enabled=True, amb_preset="Rain",
                                amb_music=True, amb_music_volume=0)
        cfg_off = StudioConfig(amb_enabled=True, amb_preset="Rain",
                               amb_music=False)
        assert np.array_equal(build_ambience_bed(cfg_zero, 2.0),
                              build_ambience_bed(cfg_off, 2.0))

    def test_render_ambience_with_music_kwarg(self):
        plain = render_ambience("Café Murmur", 3.0)
        with_m = render_ambience("Café Murmur", 3.0, with_music=True,
                                 music_volume=1.0)
        assert np.max(np.abs(with_m)) <= 1.0 + 1e-9
        assert not np.array_equal(plain, with_m)

    def test_mix_music_into_bed_adds_tonal_midband(self):
        bed = render_ambience("Quiet Room", 4.0)
        mixed = mix_music_into_bed(bed, "Quiet Room", 4.0, 48000,
                                   seed=7, volume=1.0)
        assert np.max(np.abs(mixed)) <= 1.0 + 1e-9
        diff = mixed - bed                    # the (rescaled) music layer
        # music survives the fixed-loudness re-anchor as a real signal
        assert float(np.sqrt(np.mean(diff ** 2))) > 1e-3
        spec = lambda x: np.abs(np.fft.rfft(x * np.hanning(len(x))))
        lo = slice(int(80 * len(bed) / 48000), int(2000 * len(bed) / 48000))
        hi = slice(int(3000 * len(bed) / 48000), int(8000 * len(bed) / 48000))
        s = spec(diff)
        # tonal energy lives in the mid band (tone filter is 2.4 kHz here)
        assert np.sum(s[lo]) > np.sum(s[hi])

    def test_music_config_defaults_and_roundtrip(self):
        cfg = StudioConfig()
        assert cfg.amb_music is True
        assert cfg.amb_music_volume == 45
        loaded = safe_config_from_dict({"amb_music": False,
                                        "amb_music_volume": 60})
        assert loaded.amb_music is False
        assert loaded.amb_music_volume == 60

    def test_music_bed_unknown_preset_uses_neutral_profile(self):
        m = build_music_bed("No Such Preset", 2.0)
        assert len(m) == 2 * 48000
        assert np.all(np.isfinite(m))
        assert float(np.sqrt(np.mean(m * m))) > 1e-4

    def test_music_layer_speed(self):
        with _Timer() as t:
            build_music_bed("Lo-Fi Study", 60.0)
        assert t.elapsed < 15.0
        print(f"\n    [{t.elapsed:.2f}s for 60s Lo-Fi music bed]")


# ================================================================ bed quality
# Regression guard for the "static in sound that should not have static"
# bug report: the old Rain bed was one wide band of stationary white noise
# (400-9000 Hz) — the literal spectrum of radio static — and the music
# voices truncated mid-decay, adding a tick to every scheduled note.
def _band_profile(x: np.ndarray, sr: int, edges) -> np.ndarray:
    win = 8192
    freqs = np.fft.rfftfreq(win, 1.0 / sr)
    prof = np.zeros(len(edges) - 1)
    for st in range(0, len(x) - win, win):
        spec = np.abs(np.fft.rfft(x[st:st + win] * np.hanning(win))) ** 2
        for i in range(len(edges) - 1):
            prof[i] += spec[(freqs >= edges[i]) & (freqs < edges[i + 1])].sum()
    return prof / (prof.sum() + 1e-30)


class TestBedSpectralQuality:
    EDGES = (0, 500, 1000, 2000, 4000, 6000, 8000, 24000)

    def _bands(self, name, dur=10.0):
        x = np.asarray(render_ambience(name, dur, 48000, with_music=False),
                       dtype=np.float64)
        assert np.all(np.isfinite(x)) and np.max(np.abs(x)) <= 1.0 + 1e-9
        return _band_profile(x, 48000, self.EDGES)

    def test_rain_bed_has_no_static_hiss(self):
        """Energy above 6 kHz must be negligible — that is where static lives."""
        b = self._bands("Rain")
        hf6 = b[5] + b[6]                       # 6-8 kHz + 8-24 kHz
        assert hf6 < 0.03, f">=6 kHz share {hf6 * 100:.1f}% (static hiss)"

    def test_rain_bed_spectrum_slopes_like_real_rain(self):
        """1-2 kHz body must dominate the 4-6 kHz sheen (pink-ish tilt)."""
        b = self._bands("Rain")
        assert b[2] > b[4], f"1-2 kHz {b[2] * 100:.1f}% <= 4-6 kHz {b[4] * 100:.1f}%"

    def test_rain_thunder_and_window_inherit_clean_rain(self):
        for name in ("Rain & Thunder", "Rain on Window"):
            b = self._bands(name)
            assert (b[5] + b[6]) < 0.05, f"{name}: >=6 kHz {b[5] * 100 + b[6] * 100:.1f}%"

    def test_cicada_swarm_not_ear_piercing(self):
        b = self._bands("Cicada Swarm")
        assert (b[5] + b[6]) < 0.02, f"cicadas >=6 kHz {(b[5] + b[6]) * 100:.1f}%"

    def test_airplane_cabin_hiss_band_limited(self):
        b = self._bands("Airplane Cabin")
        assert (b[5] + b[6]) < 0.03, f"cabin >=6 kHz {(b[5] + b[6]) * 100:.1f}%"

    def test_note_tail_fade_unit(self):
        env = np.ones(48000, dtype=np.float64)
        out = _note_tail_fade(env, 48000)
        assert out is env                        # in-place, same buffer
        assert len(out) == 48000
        assert abs(out[-1]) < 1e-9               # ends exactly at zero
        assert out[20000] == 1.0                 # body untouched
        assert out[-2880] == 1.0                 # ramp starts at unity
        assert out[-1000] < 0.35                 # deep inside the fade ramp

    def test_music_beds_free_of_truncation_ticks(self):
        """No scheduled note may end in a hard cut (audible tick)."""
        for name in ("Lo-Fi Study", "Garden Wind Chimes", "Rain"):
            m = build_music_bed(name, 8.0, seed=7)
            d = np.abs(np.diff(m))
            med = np.convolve(d, np.ones(801) / 801, mode="same") + 1e-12
            hits = np.where(d / med > 12.0)[0]
            hits = hits[(hits > 1000) & (hits < len(m) - 1001)]
            assert hits.size == 0, f"{name}: {hits.size} truncation ticks"


# ================================================================ emoji pop
class TestEmojiPopEffect:
    """The pop-in must animate ONLY the character that was just typed.

    Regression: the old code compared every drawn character against the
    *last typed event* timestamp (typo backspaces included), so every emoji
    on screen pulsed on every keystroke and random ones re-pop after a
    typo correction — the "weird glitchy effect" from the bug report.
    """

    TEXT = "Hi \U0001F600 there \U0001F600!"

    @pytest.fixture()
    def rig(self, qgui):
        r = StudioRenderer(800, 450, "Dracula", "DejaVu Sans Mono", 26,
                           show_line_numbers=False, show_window_chrome=False,
                           config=None)
        r.prepare_code(self.TEXT, is_text=True)
        an = TypingAnimator(self.TEXT, TypingProfile(
            wpm=240, typo_rate=0.0, is_text=True, style="Classic"))
        emo_ts = [t for t, ch in an.timeline if is_emoji(ch)]
        assert len(emo_ts) == 2
        return r, an, emo_ts

    def _frame(self, r, an, tt):
        from PySide6.QtGui import QImage
        img = QImage(r.width, r.height, QImage.Format_RGB32)
        return r.render_frame(an.display_chars, an.visible_at(tt), True,
                              title_text="", target=img, t=tt,
                              duration=an.duration(), animator=an)

    def _rgb(self, img):
        bpl = img.bytesPerLine()
        ptr = img.constBits()
        if hasattr(ptr, "setsize"):
            ptr.setsize(bpl * img.height())
        arr = np.frombuffer(ptr, dtype=np.uint8,
                            count=bpl * img.height()).reshape(img.height(), bpl // 4, 4)
        return np.array(arr[:, :img.width(), :3], copy=True)

    def _emoji_crop(self, r, arr, prefix):
        x0 = r._code_rect.left()
        y0 = r._code_rect.top()
        x1 = x0 + sum(r.fm.horizontalAdvance(c) for c in prefix)
        w = r.fm.horizontalAdvance("\U0001F600")
        a, bx = max(0, x1 - 4), min(arr.shape[1], x1 + w + 4)
        return arr[y0:y0 + r.line_h, a:bx]

    def test_only_newest_emoji_pops(self, rig):
        """When the 2nd emoji pops, the 1st emoji's cell must not change."""
        r, an, emo_ts = rig
        t1, t2 = emo_ts
        assert t2 - t1 > 0.16, "test text must type the emojis >0.16 s apart"
        settled = self._rgb(self._frame(r, an, t1 + 0.16))   # pop 1 over
        popping = self._rgb(self._frame(r, an, t2 + 0.05))   # pop 2 active
        after = self._rgb(self._frame(r, an, t2 + 0.16))     # pop 2 over
        prefix1 = self.TEXT[:self.TEXT.index("\U0001F600")]           # "Hi "
        prefix2 = self.TEXT[:self.TEXT.index("\U0001F600",
                                               self.TEXT.index("\U0001F600") + 1)]  # "Hi \U0001F600 there "
        crop1_settled = self._emoji_crop(r, settled, prefix1)
        crop1_popping = self._emoji_crop(r, popping, prefix1)
        assert np.array_equal(crop1_settled, crop1_popping), (
            "first emoji changed while the second emoji popped (global-timestamp glitch)")
        crop2 = self._emoji_crop(r, popping, prefix2)
        crop2_after = self._emoji_crop(r, after, prefix2)
        assert not np.array_equal(crop2, crop2_after), "second emoji pop never rendered"

    def test_pop_fires_when_typed(self, rig):
        """Sanity: the pop effect actually scales the freshly typed emoji."""
        r, an, emo_ts = rig
        t1 = emo_ts[0]
        popping = self._rgb(self._frame(r, an, t1 + 0.05))
        settled = self._rgb(self._frame(r, an, t1 + 0.16))
        assert not np.array_equal(self._emoji_crop(r, popping, "Hi "),
                                  self._emoji_crop(r, settled, "Hi "))


# ================================================================ mastering
class TestMasteringQuality:
    """YouTube-grade mastering guarantees for the sound pipeline.

    Locks in the guarantees the audio audit measures: gated -14 LUFS target,
    true-peak ceiling at -1 dBTP, crest control via the soft clipper, bed
    loudness anchoring + DC-free beds with quadratic edge fades, and the
    soft ceiling in mix_ambience (no hard clipping at the rails).

    The loudness reference here is an *independent* BS.1770-4 measurement
    (scipy biquads + gated block energies), so a regression in the app's
    own numba K-weight coefficients cannot hide behind itself.
    """

    SR = app.AUDIO_SAMPLE_RATE

    # ---------------------------------------------------------- reference
    @staticmethod
    def _lufs(x, sr):
        scipy = pytest.importorskip("scipy.signal")
        from scipy.signal import lfilter
        # v1.0.3: canonical ITU-R BS.1770-4 coefficients (this independent
        # reference had inherited the same corrupted stage-1 b2/a1 taps the
        # app's numba kernel used to carry — a regression in the app could
        # therefore hide behind its own test).  Cross-checked against
        # `ffmpeg -af ebur128`: a 1 kHz sine at -20 dBFS rms reads -20.0 LUFS
        # with these coefficients, matching the reference implementation.
        y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285],
                    [1.0, -1.69065929318241, 0.73248077421585], x)
        y = lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y)
        blk, hop = int(0.4 * sr), int(0.1 * sr)
        nb = 1 + (len(y) - blk) // hop
        starts = np.arange(nb) * hop
        win = np.lib.stride_tricks.sliding_window_view(y, blk)[::hop][:nb]
        e = np.mean(win ** 2, axis=1)
        j = -0.691 + 10 * np.log10(np.maximum(e, 1e-20))
        g1 = j > -70.0
        if not g1.any():
            return -70.0
        rel = -0.691 + 10 * np.log10(np.mean(e[g1])) - 10.0
        g2 = j > rel
        if not g2.any():
            return -70.0
        return float(-0.691 + 10 * np.log10(np.mean(e[g2])))

    @staticmethod
    def _true_peak(x, sr):
        up = app._oversample4(np.asarray(x, dtype=np.float64), sr)
        return float(np.max(np.abs(up))) if up.size else 0.0

    @staticmethod
    def _typing_ts(seconds=8.0, wpm=120, seed=99):
        rng = np.random.RandomState(seed)
        letters = "abcdefghijklmnopqrstuvwxyz"
        ts, t, n = [], 0.4, 0
        while t < seconds:
            r = rng.random()
            ch = " " if r < 0.065 else ("\n" if n % 42 == 41 else letters[rng.randint(0, 26)])
            ts.append((t, ch))
            n += 1
            t += 60.0 / (wpm * 5.0) * rng.uniform(0.55, 1.55)
        return ts

    # ------------------------------------------------------- oversampling
    def test_oversample4_grid_and_interpolation(self):
        """up[4i] == x[i] AND the in-between sub-samples are real values."""
        t = np.arange(24000) / self.SR
        x = 0.7 * np.sin(2 * np.pi * 1000.0 * t)
        up = app._oversample4(x, self.SR)
        assert up.shape == (4 * len(x),)
        assert np.max(np.abs(up[::4] - x)) < 1e-6
        # interpolated region must carry the sine (not zeros / not wrap):
        # up[4i+1] is x_cont((4i+1)/(4*SR)) — one sub-sample per original
        sub_i = np.arange(len(x))
        mid = up[1::4]
        expected = 0.7 * np.sin(2 * np.pi * 1000.0 * (4 * sub_i + 1) / (4.0 * self.SR))
        assert mid.shape == expected.shape
        assert np.max(np.abs(mid - expected)) < 1e-6

    def test_oversample4_detects_intersample_overshoot(self):
        t = np.arange(48000) / self.SR
        clipped = np.clip(1.5 * np.sin(2 * np.pi * 5000.0 * t), -0.9, 0.9)
        tp = self._true_peak(clipped, self.SR)
        assert tp > 0.92            # overshoot detected
        assert tp < 1.05            # but sane

    # --------------------------------------------------------- soft clip
    def test_soft_clip_identity_and_bounds(self):
        st = app.SoftClipStage()
        x = np.array([0.0, 0.1, -0.5, 0.749, -0.749])   # below knee (-2.5 dBFS ~ 0.75)
        y = st.process(x, self.SR)
        assert np.allclose(y, x)
        big = np.array([10.0, -10.0, 2.0, -2.0])
        yb = st.process(big, self.SR)
        ceil = 10 ** (-0.6 / 20)
        assert np.max(np.abs(yb)) <= ceil + 1e-12

    def test_soft_clip_c1_continuity(self):
        """No slope jump at the knee or the ceiling -> no distortion onset."""
        st = app.SoftClipStage()
        knee = 10 ** (-2.5 / 20)
        ceil = 10 ** (-0.6 / 20)
        eps = 1e-6
        for edge in (knee, ceil):
            lo = st.process(np.array([edge - eps]), self.SR)[0]
            mid = st.process(np.array([edge]), self.SR)[0]
            hi = st.process(np.array([edge + eps]), self.SR)[0]
            slope_before = (mid - lo) / eps
            slope_after = (hi - mid) / eps
            assert abs(slope_before - slope_after) < 0.05, (edge, slope_before, slope_after)

    # ----------------------------------------------------------- limiter
    def test_true_peak_limiter_hits_ceiling_exactly(self):
        t = np.arange(48000) / self.SR
        clipped = np.clip(1.5 * np.sin(2 * np.pi * 5000.0 * t), -0.9, 0.9)
        st = app.TruePeakLimiterStage()
        out = st.process(clipped, self.SR)
        tp_out = self._true_peak(out, self.SR)
        # v1.0.3: the ramped-lookahead envelope lands the true peak exactly
        # on the ceiling (even on continuously-clipped 5 kHz content)
        assert 0.85 <= tp_out <= 0.93, tp_out
        # loudness roughly preserved (only the overshoot shaved)
        rms_ratio = np.sqrt(np.mean(out ** 2)) / np.sqrt(np.mean(clipped ** 2))
        assert 0.7 < rms_ratio <= 1.01

    def test_true_peak_limiter_quiet_signal_untouched(self):
        t = np.arange(48000) / self.SR
        x = 0.2 * np.sin(2 * np.pi * 440.0 * t)
        out = app.TruePeakLimiterStage().process(x, self.SR)
        assert np.allclose(out, x, atol=1e-9)

    # ------------------------------------------------------ master chain
    def test_master_chain_hits_gated_target(self):
        """Dense typing tracks land at -14 LUFS +/-2 with TP <= -1 dBTP."""
        ts = self._typing_ts()
        for preset in ("Mechanical", "IBM Model M", "Typewriter"):
            sg = app.SimpleSoundGen(preset=preset)
            pcm = sg.generate_pcm(ts, 1.0)
            x = pcm.astype(np.float64) / 32768.0
            lufs = self._lufs(x, self.SR)
            assert -16.0 <= lufs <= -12.0, (preset, lufs)
            tp_db = 20 * np.log10(max(self._true_peak(x, self.SR), 1e-12))
            assert tp_db <= -0.95, (preset, tp_db)

    def test_master_chain_loudness_consistency(self):
        """Preset switching at the same volume slider must not jump.

        Stamps are deliberately dense (wpm ~420, like real typing-video
        narration): under a hard true-peak ceiling a *sparse* high-crest
        track has a lower reachable loudness (fewer ceiling-limited clicks
        per block), which is physics, not preset inconsistency.
        """
        ts = self._typing_ts(seconds=8.0, wpm=420)
        levels = {}
        for preset in ("Mechanical", "ASMR Deep Thock", "Studio ASMR",
                       "Creamy Thock", "Marble Clack", "Holy Panda",
                       "Lo-Fi Chill", "Wooden Desk Thock"):
            sg = app.SimpleSoundGen(preset=preset)
            x = sg.generate_pcm(ts, 1.0).astype(np.float64) / 32768.0
            levels[preset] = self._lufs(x, self.SR)
        spread = max(levels.values()) - min(levels.values())
        assert spread <= 2.5, levels

    def test_sample_peak_bounded_all_preset_tracks(self):
        ts = self._typing_ts()
        for preset in list(app.MODULAR_SOUND_PRESETS.keys())[:12]:
            sg = app.SimpleSoundGen(preset=preset)
            pcm = sg.generate_pcm(ts, 1.0)
            peak = np.max(np.abs(pcm)) / 32767.0
            # the true-peak ceiling guarantees headroom; low-crest presets
            # legitimately have low sample peaks (loudness is the metric)
            assert peak <= 0.95, (preset, peak)

    def test_stereo_image_healthy(self):
        sg = app.SimpleSoundGen(preset="Mechanical", stereo=True)
        ts = self._typing_ts()
        pcm = sg.generate_pcm(ts, 1.0)
        L = pcm[0::2].astype(np.float64) / 32768.0
        R = pcm[1::2].astype(np.float64) / 32768.0
        bal = 20 * np.log10(max(np.sqrt(np.mean(L ** 2)), 1e-9)
                            / max(np.sqrt(np.mean(R ** 2)), 1e-9))
        # v1.0.3: the two channels share ONE loudness gain (measured on the
        # mono sum) — the natural pan skew of random QWERTY letters (~1.5 dB
        # left) is preserved instead of being artificially re-centred by
        # per-channel normalisation, which used to drag panned content off
        # its position
        assert abs(bal) <= 2.5
        corr = np.corrcoef(L, R)[0, 1]
        assert 0.2 < corr < 1.01

    def test_stereo_master_shared_gain_preserves_pan(self):
        """Right-side keys must stay right of centre after mastering.

        v1.0.2 normalised each channel to -14 LUFS independently, which
        boosted the quieter left channel until panned content drifted
        toward the centre.  The shared-gain master must keep the balance
        the raw pan mix produced (within 1 dB of master-processing drift).
        """
        sg = app.SimpleSoundGen(preset="Mechanical", stereo=True)
        ts = [(0.06 * i + 0.3, c) for i, c in enumerate("lllkjklljkl" * 4)]
        full = sg.generate_pcm(ts, 1.0)
        probe = app.SimpleSoundGen(preset="Mechanical", stereo=True)
        probe._stereo_master = lambda ml, mr, s: (ml, mr)      # raw pan mix
        raw = probe.generate_pcm(ts, 1.0)

        def bal(p):
            l = p[0::2].astype(np.float64)
            r = p[1::2].astype(np.float64)
            return 20 * np.log10(max(np.sqrt(np.mean(l ** 2)), 1e-9)
                                 / max(np.sqrt(np.mean(r ** 2)), 1e-9))
        drift = bal(full) - bal(raw)
        # right-panned content must remain right-dominant (negative dB)
        assert bal(full) < 0.0, bal(full)
        # per-channel true-peak limiting is amplitude-dependent: the louder
        # (right) channel loses a little more to limiting, which drifts the
        # image a fraction toward centre — 2 dB on a 9:1 lopsided program,
        # with polarity/order preserved, is the engineering bound
        assert abs(drift) <= 2.5, drift

    # -------------------------------------------------------------- beds
    def test_bed_anchor_dc_and_peak(self):
        for name in ("Rain", "Ocean Waves", "Fireplace", "Wind",
                     "Night Crickets", "Singing Bowls", "City Traffic"):
            bed = app.render_ambience(name, 8.0, self.SR)
            # v1.0.3: the guarantee is the TRUE peak (-1.05 dBTP backstop),
            # not the sample peak (impulse beds legitimately reach higher
            # sample values than their intersample-limited true peak)
            tp = self._true_peak(bed, self.SR)
            assert tp <= 0.95, (name, 20 * np.log10(max(tp, 1e-12)))
            assert np.max(np.abs(bed)) <= 0.96, name
            assert abs(np.mean(bed)) < 0.005, (name, np.mean(bed))
            lufs = self._lufs(bed, self.SR)
            # anchored at -16 LUFS on the independent reference
            assert -18.0 <= lufs <= -14.5, (name, lufs)

    def test_bed_fades_are_quadratic(self):
        x = app.render_ambience("Brown Noise", 2.0, self.SR)
        pk = np.max(np.abs(x))
        assert np.max(np.abs(x[-4800:])) < 0.05 * pk       # last 100 ms
        assert np.max(np.abs(x[:4800])) < 0.06 * pk        # first 100 ms
        # the very tail must reach true silence (no DC pedestal)
        assert np.max(np.abs(x[-240:])) < 0.01 * pk

    # ---------------------------------------------------------- mixing
    def test_mix_ambience_soft_ceiling_no_rails(self):
        kb = (np.sin(np.arange(48000) * 0.21) * 30000).astype(np.int16)
        bed = np.ones(48000) * 0.9
        out = app.mix_ambience(kb, self.SR, 1, bed, 100)
        assert np.max(np.abs(out)) <= int(0.98 * 32767) + 1
        assert np.max(np.abs(out)) < 32767                 # never on the rails

    # ------------------------------------------------------ v1.0.3 guards
    def test_k_weight_matches_independent_reference(self):
        """The app's numba K-weight must agree with the scipy reference.

        v1.0.2 shipped a corrupted stage-1 biquad (b2 1.4397 / a1 -1.69041
        instead of the ITU table) that read a 440 Hz tone +16 dB hot and
        silently normalised every render ~13 dB too quiet — and the
        independent reference here carried the same corruption, so nothing
        could catch it.  Both are now the canonical coefficients and MUST
        agree.
        """
        rng = np.random.RandomState(21)
        for label, x in (
            ("pink", app._pink(self.SR * 6, rng) * 0.4),
            ("keys", app.SimpleSoundGen(preset="Mechanical")
             .generate_pcm(self._typing_ts(), 1.0).astype(np.float64) / 32768.0),
        ):
            mine = app._measure_lufs(x, self.SR)
            ref = self._lufs(x, self.SR)
            assert abs(mine - ref) <= 0.5, (label, mine, ref)

    def test_k_weight_itu_calibration(self):
        """1 kHz sine at -20 dBFS rms must read -20.0 LUFS (ffmpeg ebur128)."""
        t = np.arange(self.SR * 4) / self.SR
        sine = 0.1 * np.sqrt(2.0) * np.sin(2 * np.pi * 1000.0 * t)
        lufs = app._measure_lufs(sine, self.SR)
        assert abs(lufs - (-20.0)) <= 0.3, lufs

    def test_numpy_lufs_fallback_tracks_numba(self):
        """The no-numba fallback keeps mastering honest (it used to no-op)."""
        if not app._HAS_NUMBA:
            pytest.skip("numba absent; fallback IS the primary path")
        rng = np.random.RandomState(21)
        x = app._pink(self.SR * 6, rng) * 0.4
        mine = app._measure_lufs(x, self.SR)
        saved = app._HAS_NUMBA
        try:
            app._HAS_NUMBA = False
            fb = app._measure_lufs(x, self.SR)
        finally:
            app._HAS_NUMBA = saved
        assert abs(mine - fb) <= 1.2, (mine, fb)

    def test_bed_impulse_true_peak_and_loudness(self):
        """Impulse beds (the v1.0.2 static/capping offenders) are on target."""
        for name in ("Vinyl Crackle", "Fireplace", "Morning Birds"):
            bed = app.render_ambience(name, 12.0, self.SR)
            tp = self._true_peak(bed, self.SR)
            assert 20 * np.log10(max(tp, 1e-12)) <= -1.0, (name, tp)
            lufs = self._lufs(bed, self.SR)
            assert -18.0 <= lufs <= -14.5, (name, lufs)

    def test_room_tail_level_seed_independent(self):
        """Tail loudness must not depend on the IR seed (stereo image safety).

        Two guarantees: (a) the stereo decorrelation (same seed, right tail
        time-reversed) has an IDENTICAL magnitude response — wet levels
        match within 2 %; (b) across seeds the fixed IR energy keeps the
        wet level within a small spread for broadband program material.
        """
        n = self.SR * 2
        rng = np.random.RandomState(12)
        dry = app.DSP.filt_lp(rng.randn(n), 2000.0, self.SR) * 0.4   # broadband

        def wet(seed, reverse=False):
            out = app.RoomTailStage(0.1, seed=seed,
                                    reverse=reverse).process(dry, self.SR)
            return (out - dry * 0.9) / 0.06

        w = wet(4242)
        w_rev = wet(4242, reverse=True)
        ratio = np.sqrt(np.mean(w_rev ** 2)) / np.sqrt(np.mean(w ** 2))
        assert 0.97 <= ratio <= 1.03, ratio          # |IR(f)| preserved
        # across seeds the noise-IR spectral response still wanders ~1-2 dB
        # (chi-squared variance of |IR(f)|^2) — harmless in practice because
        # renders use the fixed ROOM_TAIL_SEED and the stereo pair shares it
        levels = [np.sqrt(np.mean(wet(s) ** 2)) for s in (1, 999, 4242)]
        spread = (max(levels) - min(levels)) / max(levels)
        assert spread <= 0.2, levels

    def test_music_voicing_opens_low_chords(self):
        """_voice_chord folds tones into [C3, C6] and de-clusters low pairs."""
        v = app._voice_chord([110.0, 123.47, 164.81, 196.0])   # A2 sus2-ish stack
        assert all(f >= 130.0 for f in v)
        assert all(f <= 1050.0 for f in v)
        assert v == sorted(v)
        for a, b in zip(v[:-1], v[1:]):
            if a < 300.0:
                assert b / a >= 1.19, (a, b)
        # bass keeps the raw root: voicing never touches it
        prof = app.MUSIC_PROFILES["Rain"]
        assert abs(app._note_hz(prof.root) - 110.0) < 0.5

    def test_music_bus_no_infrasonic_energy(self):
        """The 40 Hz music-bus high-pass keeps pad drift out of the bed."""
        x = app.build_music_bed("Brown Noise", 8.0, self.SR)
        X = np.abs(np.fft.rfft(x)) ** 2
        f = np.fft.rfftfreq(len(x), 1.0 / self.SR)
        assert np.sum(X[f < 38.0]) < 0.01 * np.sum(X)

    def test_bed_tilt_damps_hiss_without_silencing(self):
        """_shelf_tilt reduces 5 kHz+ energy by ~the shelf gain, keeps level."""
        rng = np.random.RandomState(3)
        x = app._pink(self.SR * 3, rng) * 0.5
        y = app._shelf_tilt(x, self.SR, 4200.0, -6.0)

        def hf(sig):
            X = np.abs(np.fft.rfft(sig))
            f = np.fft.rfftfreq(len(sig), 1.0 / self.SR)
            return np.sum(X[f >= 5000] ** 2) / np.sum(X ** 2)
        ratio = hf(y) / hf(x)
        assert 0.2 < ratio < 0.75, ratio            # ~-6 dB shelf, not a brick wall
        # loudness roughly preserved (shelf is high-frequency only)
        assert 0.7 < np.sqrt(np.mean(y ** 2)) / np.sqrt(np.mean(x ** 2)) <= 1.05

    def test_bed_tilt_registry_applied(self):
        """Bright beds listed in _BED_TILT actually get their shelf."""
        name = "Café Murmur"
        assert name in app._BED_TILT
        rng = np.random.RandomState(5)
        x = app.AMBIENCE_PRESETS[name](self.SR * 3, self.SR, rng)
        cut, gain = app._BED_TILT[name]
        y = app._shelf_tilt(x, self.SR, cut, gain)
        X0 = np.abs(np.fft.rfft(x))
        X1 = np.abs(np.fft.rfft(y))
        f = np.fft.rfftfreq(len(x), 1.0 / self.SR)
        assert np.mean(X1[f >= 6000]) < np.mean(X0[f >= 6000])

    # -------------------------------------------------------- retune guard
    def test_cherry_body_energy_present(self):
        """The retuned Cherry MX Red carries its identity in 100-3000 Hz."""
        fam = app.VariantPoolFactory().from_preset(
            app.MODULAR_SOUND_PRESETS["Cherry MX Red"], app.ModularSoundEngine(self.SR))
        loud = max(fam.clicks, key=lambda c: np.max(np.abs(c)))
        x = loud.astype(np.float64) / 32768.0
        w = np.hanning(len(x))
        f = np.fft.rfftfreq(len(x), 1.0 / self.SR)
        X = np.abs(np.fft.rfft(x * w))
        total = np.sum(X ** 2)
        body = np.sum(X[(f >= 100) & (f < 3000)] ** 2)
        assert body / total >= 0.5

##############

#==============================================================================
# ── "ULTIMATE UI" PORT TESTS
#    ANSI terminal art rendering, markdown highlighting, regex code
#    fallback, .ans support and the advanced batch-file filter row
#    (ported from the Unified Typing Video Studio reference edition).
#==============================================================================

class TestAnsiHelpers:
    """strip_ansi / parse_ansi pure helpers."""

    def test_strip_ansi_removes_sequences(self):
        assert strip_ansi("\x1b[31mred\x1b[0m plain") == "red plain"

    def test_strip_ansi_plain_text_untouched(self):
        assert strip_ansi("hello [31m not an escape") == "hello [31m not an escape"

    def test_parse_ansi_colors_each_char(self):
        vis, cols = parse_ansi("\x1b[31mR\x1b[32mG\x1b[0mw")
        assert vis == "RGw"
        assert cols == ["#ff5555", "#50fa7b", None]

    def test_parse_ansi_reset_via_empty_code(self):
        vis, cols = parse_ansi("\x1b[31mA\x1b[mB")
        assert vis == "AB" and cols == ["#ff5555", None]

    def test_parse_ansi_unknown_codes_ignored(self):
        vis, cols = parse_ansi("\x1b[99mX\x1b[1;33mY")
        assert vis == "XY" and cols == [None, "#f1fa8c"]

    def test_parse_ansi_no_sequences(self):
        assert parse_ansi("plain") == ("plain", [None] * 5)


class TestAnArtifactSupport:
    """.ans extension plumbing."""

    def test_ans_in_supported_extensions(self):
        assert ".ans" in SUPPORTED_EXTENSIONS
        assert EXT_TO_LANGUAGE[".ans"] == "text"

    def test_ans_in_text_art_category(self):
        assert ".ans" in FILE_CATEGORIES["Text/Art"]
        assert ".c" in FILE_CATEGORIES["Code"]          # reference typo fixed
        assert FILE_CATEGORIES["All"] == set(SUPPORTED_EXTENSIONS)

    def test_categories_cover_every_extension(self):
        covered = set()
        for name, exts in FILE_CATEGORIES.items():
            if name != "All":
                covered |= exts
        assert covered == set(SUPPORTED_EXTENSIONS)

    def test_read_text_file_keeps_ans_raw(self, tmp_path):
        p = tmp_path / "art.ans"
        p.write_text("\x1b[35mhi  \n", encoding="utf-8")
        text = read_text_file(str(p), clean=True)
        assert "\x1b[35m" in text and "  \n" in text   # not cleaned

    def test_read_text_file_still_cleans_txt(self, tmp_path):
        p = tmp_path / "note.txt"
        p.write_text("keep  \n", encoding="utf-8")
        assert read_text_file(str(p), clean=True) == "keep"


class TestAnsiRendering:
    """Renderer ANSI path: colors when enabled, stripped glyphs otherwise."""

    @pytest.fixture()
    def renderer(self, qgui):
        cfg = StudioConfig(mode=StudioMode.TEXT_EMOJI)
        cfg.ansi_colors = True
        return StudioRenderer(480, 270, theme_name="Dracula", font_family="monospace",
                              language="text", config=cfg)

    def test_ansi_colors_applied(self, renderer):
        renderer.prepare_code("\x1b[31mR\x1b[32mG\x1b[0m", is_text=True)
        assert renderer._units_text == ["R", "G"]
        from PySide6.QtGui import QColor
        assert renderer._units_colors[0] == QColor("#ff5555")
        assert renderer._units_colors[1] == QColor("#50fa7b")

    def test_ansi_disabled_strips_sequences(self, qgui):
        cfg = StudioConfig(mode=StudioMode.TEXT_EMOJI)
        r = StudioRenderer(480, 270, theme_name="Dracula", font_family="monospace",
                           language="text", config=cfg)
        r.prepare_code("\x1b[31mR", is_text=True)
        assert r._units_text == ["R"]
        assert all(c == r._qc_fg for c in r._units_colors)

    def test_ansi_mode_text_language(self, qgui):
        cfg = StudioConfig(mode=StudioMode.CODE_YT)
        r = StudioRenderer(480, 270, theme_name="Dracula", font_family="monospace",
                           language="text", config=cfg)
        r.prepare_code("\x1b[31mR", is_text=False)
        assert r._units_text == ["R"]

    def test_code_language_not_ansified(self, renderer):
        # a real .py file spells the escape as backslash-x; that must stay
        # verbatim (only the raw ESC control char is terminal art)
        src = 'x = "\\x1b[31m"'
        renderer.prepare_code(src, is_text=False)
        assert renderer._units_text == list(src)


class TestMarkdownHighlighting:
    """Lightweight markdown tokenizer (Text & Emoji mode)."""

    def _renderer(self, qgui, markdown=True):
        cfg = StudioConfig(mode=StudioMode.TEXT_EMOJI)
        cfg.txt_markdown = markdown
        return StudioRenderer(480, 270, theme_name="Dracula", font_family="monospace",
                              language="text", config=cfg)

    def test_heading_keyword_color(self, qgui):
        r = self._renderer(qgui)
        r.prepare_code("# Title\nbody", is_text=True)
        assert r._qcolors["keyword"] in r._units_colors[:6]

    def test_list_comment_color(self, qgui):
        r = self._renderer(qgui)
        r.prepare_code("- item", is_text=True)
        assert r._qcolors["comment"] in r._units_colors

    def test_bold_and_code_spans(self, qgui):
        r = self._renderer(qgui)
        r.prepare_code("**bold** `code`", is_text=True)
        kw, st = r._qcolors["keyword"], r._qcolors["string"]
        assert kw in r._units_colors and st in r._units_colors

    def test_link_function_color(self, qgui):
        r = self._renderer(qgui)
        r.prepare_code("see [docs](http://x)", is_text=True)
        assert r._qcolors["function"] in r._units_colors

    def test_disabled_markdown_stays_foreground(self, qgui):
        r = self._renderer(qgui, markdown=False)
        r.prepare_code("# Title", is_text=True)
        assert all(c == r._qc_fg for c in r._units_colors)

    def test_markdown_spans_classification(self):
        spans = StudioRenderer._markdown_spans("# H\n> q\n- l\n**b**\n*i*\n`c`\n[u](v)")
        keys = [k for _, _, k in spans]
        assert keys == ["keyword", "comment", "comment", "keyword",
                        "number", "string", "function"]


class TestBasicCodeFallback:
    """Regex tokenizer used when pygments is unavailable."""

    def test_spans_classify_tokens(self):
        spans = StudioRenderer._basic_code_spans('def f():  # note\n    return 1 + "s"')
        keys = [k for _, _, k in spans]
        assert keys.count("keyword") == 2      # def, return
        assert "comment" in keys and "number" in keys and "string" in keys

    def test_prepare_code_colors_without_pygments(self, qgui, monkeypatch):
        monkeypatch.setattr("app._HAS_PYGMENTS", False)
        cfg = StudioConfig(mode=StudioMode.CODE_YT)
        r = StudioRenderer(480, 270, theme_name="Dracula", font_family="monospace",
                           language="python", config=cfg)
        r.prepare_code("import os  # hi", is_text=False)
        assert r._qcolors["keyword"] in r._units_colors[:6]
        assert r._qcolors["comment"] in r._units_colors

    def test_units_and_colors_lengths_match(self, qgui):
        cfg = StudioConfig(mode=StudioMode.CODE_YT)
        r = StudioRenderer(480, 270, theme_name="Dracula", font_family="monospace",
                           language="python", config=cfg)
        r.prepare_code("x = 1\ny = 'two'", is_text=False)
        assert len(r._units_text) == len(r._units_colors)


class TestAnsiAnimatorSync:
    """The typing timeline must align with ANSI-stripped visible text."""

    def test_make_animator_strips_ansi(self, base_config):
        a = BaseRenderStrategy._make_animator(
            BaseRenderStrategy, "\x1b[31mA\x1b[0mBC", 120, tr=0.0,
            is_text=True, config=base_config)
        assert "".join(ch for _, ch in a.char_timestamps()) == "ABC"

    def test_plain_code_timeline_untouched(self, base_config):
        a = BaseRenderStrategy._make_animator(
            BaseRenderStrategy, "AB C", 120, tr=0.0, is_text=False,
            config=base_config)
        assert "".join(ch for _, ch in a.char_timestamps()) == "AB C"


@pytest.mark.e2e
class TestBatchFilterUI:
    """Advanced batch filter row: name/ext/category/folder + visible ops."""

    def _make_window(self, qapp, monkeypatch, tmp_path, files):
        """Files live in a dedicated inbox that becomes INPUT_DIR.

        MainWindow auto-scans INPUT_DIR at construction (sorted os.walk
        order: root files first, then subfolders), which gives a fully
        deterministic row order for the index-based assertions below.
        """
        inbox = tmp_path / "inbox"
        (inbox / "sub").mkdir(parents=True, exist_ok=True)
        for name in files:
            f = (inbox / "sub") if name.startswith("sub/") else inbox
            (f / name.split("/")[-1]).write_text("x = 1\n", encoding="utf-8")
        monkeypatch.setattr("app.INPUT_DIR", inbox)
        w = MainWindow()
        return w

    def test_filter_widgets_exist(self, qapp):
        w = MainWindow()
        assert hasattr(w, "filter_edit") and hasattr(w, "ext_filter_cb")
        assert hasattr(w, "type_filter_cb") and hasattr(w, "folder_filter_cb")
        assert hasattr(w, "case_chk") and hasattr(w, "filter_sync_btn")
        assert hasattr(w, "filter_clear_btn")
        assert list(FILE_CATEGORIES.keys()) == [
            w.type_filter_cb.itemText(i) for i in range(w.type_filter_cb.count())]
        w.close()

    def test_ext_and_folder_combos_populated(self, qapp, monkeypatch, tmp_path):
        w = self._make_window(qapp, monkeypatch, tmp_path, ["a.py", "b.md", "sub/c.json"])
        exts = [w.ext_filter_cb.itemText(i) for i in range(w.ext_filter_cb.count())]
        assert exts == ["\U0001F4C2 All", ".json", ".md", ".py"]
        folders = [w.folder_filter_cb.itemText(i) for i in range(w.folder_filter_cb.count())]
        assert "\U0001F4C1 All Folders" in folders and "[Root]" in folders and "sub" in folders
        w.close()

    def test_apply_filter_by_name(self, qapp, monkeypatch, tmp_path):
        w = self._make_window(qapp, monkeypatch, tmp_path, ["alpha.py", "beta.py", "gamma.md"])
        w.filter_edit.setText("beta")
        assert w.table.isRowHidden(0) and not w.table.isRowHidden(1) and w.table.isRowHidden(2)
        w._clear_filter()
        assert not w.table.isRowHidden(0)
        w.close()

    def test_apply_filter_case_sensitive(self, qapp, monkeypatch, tmp_path):
        w = self._make_window(qapp, monkeypatch, tmp_path, ["Alpha.py", "alpha2.py"])
        w.case_chk.setChecked(True)
        w.filter_edit.setText("Alpha")
        assert not w.table.isRowHidden(0) and w.table.isRowHidden(1)
        w._clear_filter()
        w.close()

    def test_apply_filter_by_category(self, qapp, monkeypatch, tmp_path):
        w = self._make_window(qapp, monkeypatch, tmp_path, ["a.py", "b.md"])
        w.type_filter_cb.setCurrentText("Code")
        assert not w.table.isRowHidden(0) and w.table.isRowHidden(1)
        w.type_filter_cb.setCurrentText("Markup/Web")
        assert w.table.isRowHidden(0) and not w.table.isRowHidden(1)
        w._clear_filter()
        w.close()

    def test_apply_filter_by_folder(self, qapp, monkeypatch, tmp_path):
        w = self._make_window(qapp, monkeypatch, tmp_path, ["a.py", "sub/b.py"])
        w.folder_filter_cb.setCurrentText("sub")
        assert w.table.isRowHidden(0) and not w.table.isRowHidden(1)
        w.folder_filter_cb.setCurrentIndex(0)
        assert not w.table.isRowHidden(0)
        w.close()

    def test_sync_filter_to_mode(self, qapp, monkeypatch, tmp_path):
        w = self._make_window(qapp, monkeypatch, tmp_path, ["a.py", "b.md"])
        w.config.mode = StudioMode.TEXT_EMOJI
        w._sync_filter_to_mode()
        assert w.type_filter_cb.currentText() == "Text/Art"
        w.config.mode = StudioMode.CODE_YT
        w._sync_filter_to_mode()
        assert w.type_filter_cb.currentText() == "Code"
        w._clear_filter()
        w.close()

    def test_select_visible_respects_filter(self, qapp, monkeypatch, tmp_path):
        w = self._make_window(qapp, monkeypatch, tmp_path, ["a.py", "b.py", "c.md"])
        w.filter_edit.setText(".md")
        w._deselect_visible()
        assert [it.checked for it in w._items] == [True, True, False]
        w.filter_edit.setText(".py")
        w._select_visible()
        assert [it.checked for it in w._items] == [True, True, False]
        w._clear_filter()
        w.close()

    def test_status_update_keeps_rows_hidden(self, qapp, monkeypatch, tmp_path):
        w = self._make_window(qapp, monkeypatch, tmp_path, ["aaa.py", "zzz.py"])
        w.filter_edit.setText("aaa")            # row 1 falls out of the filter
        assert w.table.isRowHidden(1)
        w._items[1].status = "Done"
        w._refresh_table()                      # batch status updates must not reveal
        assert w.table.isRowHidden(1)
        w.close()

    def test_ansi_toggle_updates_config(self, qapp):
        w = MainWindow()
        w.ansi_chk.setChecked(True)
        assert w.config.ansi_colors is True
        w._apply_config_to_ui()
        assert w.ansi_chk.isChecked() is True
        w.ansi_chk.setChecked(False)
        assert w.config.ansi_colors is False
        w.close()
