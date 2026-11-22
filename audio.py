"""Audio layer: professional keypress-SFX engine (layered physical key model)
with custom WAV loading, plus 21 procedural ambience soundscapes, custom-file
looping and mixing."""

#==============================================================================
# ── SOUND — keypress SFX engine, presets, custom WAV loader
#    (merged from studio/sound.py in the v2.5 ten-file edition;
#     v2.6 re-sound-design: layered physical key model, housing resonance,
#     pitch-glide thumps, per-variant detune, room tail, 18 presets)
#==============================================================================

from __future__ import annotations

#==============================================================================
# ── SOUND — key-click DSP engine, presets, custom WAV loader
#    (merged from studio/sound.py in the v2.5 ten-file edition)
#==============================================================================

"""Modular sound design engine: DSP primitives, key-click presets and a
custom-WAV preset loader (Qt-free; only needs numpy + stdlib wave)."""

import random
import wave
from dataclasses import dataclass, field, replace
from typing import List, Optional, Tuple

import numpy as np

from config import AUDIO_SAMPLE_RATE
from config import logger

try:
    import numba
    from numba import njit, prange
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False


# ------------------------------------------------------------------ loudness
if _HAS_NUMBA:
    @njit(cache=True)
    def _nb_k_weight(x, sr):
        n = len(x); y = np.empty(n, dtype=np.float64)
        if sr == 48000:
            s1_b0 = 1.53512485958624; s1_b1 = -2.61187896900947; s1_b2 = 1.23925952524423
            s1_a1 = -1.69019851598276; s1_a2 = 0.732626261909496
            s2_b0 = 1.0; s2_b1 = -2.0; s2_b2 = 1.0
            s2_a1 = -1.99004745481143; s2_a2 = 0.990072500365666
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
    def _nb_compute_loudness(x_k):
        n = len(x_k)
        if n == 0:
            return -70.0
        s = 0.0
        for i in range(n):
            v = x_k[i]; s += v * v
        ms = s / n
        if ms < 1e-20:
            return -70.0
        return -0.691 + 10.0 * np.log10(ms)

    @njit(cache=True)
    def _nb_apply_gain(x, gain):
        n = len(x); out = np.empty(n, dtype=np.float64)
        for i in range(n):
            out[i] = x[i] * gain
        return out


def _normalize_to_lufs(x, sr, target_lufs=-14.0):
    if len(x) < sr // 2:
        return x
    if _HAS_NUMBA:
        xk = _nb_k_weight(x.astype(np.float64), sr)
        cl = _nb_compute_loudness(xk)
        if not np.isfinite(cl) or cl <= -70.0:
            return x
        gdb = target_lufs - cl
        gl = 10.0 ** (gdb / 20.0)
        return _nb_apply_gain(x.astype(np.float64), gl).astype(np.float32)
    return x


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


# ------------------------------------------------------------------ DSP kit
class DSP:
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
    def fir_lowpass(cutoff, sr=AUDIO_SAMPLE_RATE, n_taps=127):
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
    def to_int16(x, target_db=-1.0):
        pk = np.max(np.abs(x)) if len(x) > 0 else 0.0
        if pk < 1e-10:
            return np.zeros_like(x, dtype=np.int16)
        return np.clip(x * (10 ** (target_db / 20) / pk) * 32767, -32768, 32767).astype(np.int16)


# ------------------------------------------------------------------ presets
@dataclass
class VoiceSpec:
    osc: str = "sine"; freq: float = 440.0; fm_ratio: float = 1.0; fm_index: float = 0.0
    attack: float = 0.001; decay_rate: float = 30.0; attack_curve: float = 2.0
    filt: str = "none"; f_cutoff: float = 8000.0; f_high: float = 12000.0; f_q: float = 1.0
    drive: float = 0.0; gain: float = 0.5; delay: float = 0.0
    modes: Optional[List[Tuple[float, float, float]]] = None; inharmonicity: float = 0.0
    sweep: float = 0.0    # exponential pitch glide: end freq = freq * sweep (sine only; 0/1 = off)


@dataclass
class SoundSpec:
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


MODULAR_SOUND_PRESETS = {
    # ── every click is built from the physical event chain of a real keypress:
    #    cap-contact snap → travel → delayed bottom-out → housing/plate modes
    #    → sub-bass weight (+ spring ping / return tick where the switch has one)
    "Mechanical": SoundSpec(duration=0.13, layers=[
        VoiceSpec(osc="noise_white", attack=0.0001, decay_rate=420.0, filt="bp", f_cutoff=2800, f_high=7000, drive=1.4, gain=0.42),
        VoiceSpec(osc="fm", freq=900, fm_ratio=2.4, fm_index=0.8, attack=0.0004, decay_rate=90.0, filt="lp", f_cutoff=3000, gain=0.28, delay=0.0025),
        VoiceSpec(osc="sine", freq=130, sweep=0.55, attack=0.0015, decay_rate=55.0, filt="lp", f_cutoff=500, gain=0.5, delay=0.002)
    ], resonance=[(820.0, 9.0, 0.30), (1350.0, 12.0, 0.18)], post_lp=8500.0),
    "Cherry MX Red": SoundSpec(duration=0.11, layers=[
        VoiceSpec(osc="noise_white", attack=0.0004, decay_rate=300.0, filt="bp", f_cutoff=1800, f_high=4500, gain=0.22),
        VoiceSpec(osc="sine", freq=115, sweep=0.6, attack=0.002, decay_rate=45.0, filt="lp", f_cutoff=450, gain=0.6),
        VoiceSpec(osc="sine", freq=68, attack=0.003, decay_rate=28.0, filt="lp", f_cutoff=220, gain=0.42, delay=0.0015)
    ], resonance=[(640.0, 8.0, 0.22)], post_lp=7000.0),
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
    # ── v2.6 professional presets
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
        VoiceSpec(osc="noise_white", attack=0.0001, decay_rate=900.0, filt="bp", f_cutoff=5000, f_high=9500, gain=0.4),
        VoiceSpec(osc="sine", freq=3350, attack=0.0004, decay_rate=30.0, filt="lp", f_cutoff=8000, gain=0.22, delay=0.001),
        VoiceSpec(osc="noise_white", attack=0.0003, decay_rate=320.0, filt="bp", f_cutoff=1500, f_high=4200, gain=0.3, delay=0.0022),
        VoiceSpec(osc="sine", freq=125, sweep=0.55, attack=0.002, decay_rate=48.0, filt="lp", f_cutoff=480, gain=0.5, delay=0.0025)
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
    # ── v3.2 ASMR expansion: soft-touch variants spread across the spectrum
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
}


class ModularSoundEngine:
    def __init__(self, sr=AUDIO_SAMPLE_RATE):
        self.sr = sr

    def _render_voice(self, spec: VoiceSpec, n: int, rng: np.random.RandomState) -> np.ndarray:
        sig = np.zeros(n, dtype=np.float64)
        if spec.osc == "sine":
            if spec.sweep and 0.02 < spec.sweep < 0.999:
                # exponential pitch glide freq -> freq*sweep (phase-integrated,
                # no discontinuity): the physical "thump" of the slider bottoming out
                t = np.arange(n, dtype=np.float64) / self.sr
                dur = max(1e-6, n / self.sr)
                f_t = spec.freq * (spec.sweep ** (t / dur))
                sig = np.sin(2.0 * np.pi * np.cumsum(f_t) / self.sr)
            else:
                sig = DSP.osc_sine(spec.freq, n, self.sr)
        elif spec.osc == "fm":
            sig = DSP.osc_fm(spec.freq, spec.fm_ratio, spec.fm_index, n, self.sr)
        elif spec.osc == "saw":
            sig = DSP.osc_saw(spec.freq, n, self.sr)
        elif spec.osc == "noise_white":
            sig = DSP.noise_white(n, rng)
        elif spec.osc == "noise_pink":
            sig = DSP.noise_pink(n, rng)
        elif spec.osc == "noise_brown":
            sig = DSP.noise_brown(n, rng)
        elif spec.osc == "modal" and spec.modes:
            sig = DSP.modal(spec.modes, n, self.sr, spec.inharmonicity)

        sig *= DSP.env_exp(n, self.sr, attack=spec.attack, decay_rate=spec.decay_rate, attack_curve=spec.attack_curve)
        if spec.filt == "lp":
            sig = DSP.filt_lp(sig, spec.f_cutoff, self.sr)
        elif spec.filt == "hp":
            sig = DSP.filt_hp(sig, spec.f_cutoff, self.sr)
        elif spec.filt == "bp":
            sig = DSP.filt_bp(sig, spec.f_cutoff, spec.f_high, self.sr)
        elif spec.filt == "resonator":
            sig = DSP.filt_resonator(sig, spec.f_cutoff, spec.f_q, self.sr)
        if spec.drive > 0:
            sig = DSP.sat_tanh(sig, spec.drive)
        d = int(spec.delay * self.sr)
        if d > 0 and d < n:
            return np.concatenate([np.zeros(d, dtype=np.float64), sig[:n - d]]) * spec.gain
        return sig * spec.gain

    def render(self, spec: SoundSpec, seed: int) -> np.ndarray:
        rng = np.random.RandomState(seed)
        n = int(self.sr * spec.duration)
        mix = np.zeros(n, dtype=np.float64)
        # per-variant micro-detune (±0.35 st): the 32 round-robin variants no
        # longer share identical tonal layers, killing the machine-gun effect
        detune = 2.0 ** (rng.uniform(-0.35, 0.35) / 12.0)
        for v in spec.layers:
            if v.osc in ("sine", "fm", "modal"):
                v2 = replace(v, freq=v.freq * detune)
                if v2.osc == "modal" and v2.modes:
                    v2 = replace(v2, modes=[(f * detune, d, a) for (f, d, a) in v2.modes])
            else:
                v2 = v
            mix += self._render_voice(v2, n, rng)
        # housing / plate resonance: the case "answers" the impact — this is
        # the layer that separates a real board from a raw noise burst
        if spec.resonance:
            for rf, rq, rgn in spec.resonance:
                mix = mix + DSP.filt_resonator(mix, rf, rq, self.sr, gain=rgn)
        if spec.post_hp > 0:
            mix = DSP.filt_hp(mix, spec.post_hp, self.sr)
        if spec.post_lp > 0:
            mix = DSP.filt_lp(mix, spec.post_lp, self.sr)
        return DSP.to_int16(DSP.filt_hp(mix, 20.0, self.sr, n_taps=63))


# ------------------------------------------------------------------ WAV import
def load_wav_sample(path: str, target_sr: int = AUDIO_SAMPLE_RATE) -> np.ndarray:
    """Load a WAV file as mono float64 at target_sr, peak-normalised to 0.9.

    Supports 8/16/24/32-bit PCM; multi-channel audio is down-mixed and any
    sample rate is linearly resampled. Raises on unreadable files.
    """
    with wave.open(path, "rb") as w:
        nch, sampwidth, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)

    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sampwidth == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    elif sampwidth == 3:
        b = np.frombuffer(raw, dtype=np.uint8)
        usable = (len(b) // 3) * 3
        b = b[:usable].reshape(-1, 3)
        vals = (b[:, 0].astype(np.int32)
                | (b[:, 1].astype(np.int32) << 8)
                | (b[:, 2].astype(np.int32) << 16))
        vals = np.where(vals & 0x800000, vals - 0x1000000, vals)
        data = vals.astype(np.float64) / 8388608.0
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth * 8}-bit")

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

    max_len = int(target_sr * 0.35)  # key clicks should stay short
    if len(data) > max_len:
        data = data[:max_len]
    return np.ascontiguousarray(data, dtype=np.float64)


def load_wav_samples(paths: List[str]) -> List[np.ndarray]:
    out = []
    for p in paths:
        try:
            sample = load_wav_sample(p)
            if len(sample) > 16:
                out.append(sample)
        except Exception as e:
            logger.error(f"Failed to load custom WAV '{p}': {e}")
    return out


# ------------------------------------------------------------------ generator
class SimpleSoundGen:
    _QWERTY_ROWS = ("`1234567890-=", "qwertyuiop[]\\", "asdfghjkl;'", "zxcvbnm,./")
    _ROW_PITCH_SHIFT = [1.5, 0.5, -0.5, -2.0]

    def __init__(self, sr=AUDIO_SAMPLE_RATE, preset="Mechanical", stereo=False,
                 reverb_amt=0.1, custom_samples: Optional[List[np.ndarray]] = None):
        self.sr = sr
        self.preset = preset
        self.stereo = stereo
        self.reverb_amt = reverb_amt
        self.engine = ModularSoundEngine(sr)

        if custom_samples:
            base = [np.asarray(s, dtype=np.float64) for s in custom_samples if len(np.asarray(s)) > 16]
            if base:
                # Build a detuned variant pool from each user sample so the
                # round-robin never plays the exact same waveform twice in a
                # row (same treatment the procedural presets get).
                pool: List[np.ndarray] = []
                for s in base[:4]:
                    s = _normalize(s.copy(), 0.9)
                    for st in (0.0, 0.4, -0.4, 0.9, -0.9):
                        pool.append(s if st == 0.0 else self._pitch_shift_f(s, st))
                self.clicks = pool[:32]
                self.spaces = [self._pitch_shift_f(s, -3.0) for s in pool[:8]] or pool
                self.enters = [self._pitch_shift_f(s, -5.0) for s in pool[:4]] or pool
                return

        spec = MODULAR_SOUND_PRESETS.get(preset, MODULAR_SOUND_PRESETS["Mechanical"])
        enter_spec = spec.enter_spec or spec
        space_spec = spec.space_spec or spec
        self.clicks = [self.engine.render(spec, i) for i in range(32)]
        self.spaces = [self.engine.render(space_spec, 100 + i) for i in range(16)]
        self.enters = [self.engine.render(enter_spec, 200 + i) for i in range(8)]

    @staticmethod
    def _pitch_shift(sound: np.ndarray, semitones: float) -> np.ndarray:
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

    @classmethod
    def _pitch_shift_f(cls, sound: np.ndarray, semitones: float) -> np.ndarray:
        """Pitch shift keeping the float domain (for custom WAV samples)."""
        shifted = cls._pitch_shift(
            np.clip(sound * 32767, -32768, 32767).astype(np.int16), semitones)
        return shifted.astype(np.float64) / 32767.0

    def _get_pitch_shift(self, char: str) -> float:
        if char in (" ", "\n", "\t"):
            return -3.0
        c = char.lower()
        for r, row in enumerate(self._QWERTY_ROWS):
            if c in row:
                return self._ROW_PITCH_SHIFT[r]
        return 0.0

    def generate_pcm(self, timestamps, volume=0.5):
        if not timestamps:
            return np.zeros(0, dtype=np.int16)
        sr = self.sr
        total = max(ts for ts, _ in timestamps) + 0.3
        n = int(sr * total)
        rng = random.Random(98765)
        raw, starts_i, pans = [], [], []
        for ts, ch in timestamps:
            if ch == "\n":
                snd, vm, pan = rng.choice(self.enters), rng.uniform(1.05, 1.20), 0.2
            elif ch == " ":
                snd, vm, pan = rng.choice(self.spaces), rng.uniform(1.00, 1.15), 0.0
            else:
                base_snd = rng.choice(self.clicks)
                shift = self._get_pitch_shift(ch)
                if shift != 0:
                    snd = self._shift_sample(base_snd, shift)
                else:
                    snd = base_snd
                vm, pan = rng.uniform(0.90, 1.12), rng.uniform(-0.3, 0.3)
            s = int(ts * sr); e = min(s + len(snd), n)
            if s < n:
                raw.append(snd[:e - s].astype(np.float32) * volume * vm)
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
            ml = _normalize_to_lufs(self._room_tail(ml), sr)
            mr = _normalize_to_lufs(self._room_tail(mr), sr)
            mx = max(float(np.max(np.abs(ml))) if len(ml) else 0.0,
                     float(np.max(np.abs(mr))) if len(mr) else 0.0)
            if mx > 1.0:  # peak-safe mastering: scale before the hard clip
                ml = ml * (0.98 / mx); mr = mr * (0.98 / mx)
            out = np.empty(n * 2, dtype=np.int16)
            out[0::2] = np.clip(ml * 32767, -32768, 32767).astype(np.int16)
            out[1::2] = np.clip(mr * 32767, -32768, 32767).astype(np.int16)
            return out

        starts = np.array(starts_i, dtype=np.int64)
        lengths = np.array([len(s) for s in raw], dtype=np.int64)
        flat = np.concatenate(raw)
        offsets = np.zeros(len(raw), dtype=np.int64)
        for i in range(1, len(raw)):
            offsets[i] = offsets[i - 1] + lengths[i - 1]
        mix = np.zeros(n, dtype=np.float32)
        for i in range(len(starts)):
            mix[int(starts[i]):int(starts[i] + lengths[i])] += flat[int(offsets[i]):int(offsets[i] + lengths[i])]
        mix = _normalize_to_lufs(self._room_tail(mix), sr)
        mx = float(np.max(np.abs(mix))) if len(mix) else 0.0
        if mx > 1.0:  # peak-safe mastering: scale before the hard clip
            mix = mix * (0.98 / mx)
        return np.clip(mix * 32767, -32768, 32767).astype(np.int16)

    def _room_tail(self, x: np.ndarray) -> np.ndarray:
        """Deterministic small-room tail: the subtle 'recorded in a real room'
        glue that separates raw synth clicks from produced keyboard SFX."""
        amt = float(self.reverb_amt)
        if amt <= 0.0 or len(x) < 256:
            return x
        sr = self.sr
        n_ir = max(64, int(sr * 0.11))
        rng = np.random.RandomState(4242)  # fixed seed -> deterministic
        ir = rng.randn(n_ir) * np.exp(-np.arange(n_ir, dtype=np.float64) / (sr * 0.020))
        ir = DSP.filt_lp(ir, 5200, sr)[:n_ir]
        ir = ir - np.mean(ir)
        pk = float(np.max(np.abs(ir)))
        if pk < 1e-9:
            return x
        ir = ir / pk
        wet = _fft_convolve_chunked(np.asarray(x, dtype=np.float64), ir)[:len(x)]
        k = min(0.45, amt)
        out = np.asarray(x, dtype=np.float64) * (1.0 - k) + wet * (k * 0.6)
        return out.astype(np.float32)

    def _shift_sample(self, snd, shift: float):
        """Pitch shift samples of either int16 (presets) or float (custom WAV)."""
        if snd.dtype == np.int16:
            return self._pitch_shift(snd, shift)
        shifted = self._pitch_shift(
            np.clip(snd * 32767, -32768, 32767).astype(np.int16), shift)
        return shifted.astype(np.float64) / 32767.0

#==============================================================================
# ── AMBIENCE — 28 soundscapes + file looping + mixer
#    (merged from studio/ambience.py in the v2.5 ten-file edition)
#==============================================================================

"""Background ambience engine: procedurally generated soundscapes and
custom audio file loading, mixed under the keyboard sounds (Qt-free).

Every preset is deterministic for a given seed and rendered fully vectorised
with numpy (FFT filtering), so a 60-second bed renders in well under a second.

Custom files: WAV is read with the stdlib ``wave`` module; any other format
(mp3/m4a/ogg/flac...) is decoded through an ffmpeg pipe.  Files are looped
with a short equal-power crossfade so there is no audible seam, then faded
out at the very end of the bed.
"""

import math
import shutil
import subprocess
import wave
from typing import Dict, List, Optional

import numpy as np

from config import AUDIO_SAMPLE_RATE
from config import logger

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

# ------------------------------------------------------------------ helpers
def _xlp(x, cutoff, sr, n_taps=127):
    """FFT low-pass (matches sound.DSP.filt_lp but local to avoid heavy import)."""
    n = np.arange(n_taps, dtype=np.float64)
    fc = min(max(1.0, cutoff), sr / 2.0 - 1.0) / sr
    center = (n_taps - 1) / 2.0
    h = np.sinc(2 * fc * (n - center))
    w = 0.42 - 0.5 * np.cos(2 * np.pi * n / (n_taps - 1)) + 0.08 * np.cos(4 * np.pi * n / (n_taps - 1))
    h *= w
    s = h.sum()
    if s > 0:
        h /= s
    n_fft = 1 << ((len(x) + n_taps - 1).bit_length())
    X = np.fft.rfft(x, n_fft)
    H = np.fft.rfft(h, n_fft)
    return np.fft.irfft(X * H, n_fft)[: len(x)]


def _hp(x, cutoff, sr, n_taps=63):
    hlp = _xlp(x, cutoff, sr, n_taps)
    h = -hlp
    h[len(h) // 2] += 1.0
    return h


def _bp(x, lo, hi, sr):
    return _xlp(x, hi, sr) - _xlp(x, lo, sr)


def _noise(n, rng):
    return rng.randn(n)


def _pink(n, rng):
    white = rng.randn(n)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, 1.0 / AUDIO_SAMPLE_RATE)
    freqs[0] = max(freqs[1] if len(freqs) > 1 else 1.0, 1.0)
    fft[1:] /= np.sqrt(np.abs(freqs[1:]))
    fft[0] = 0
    out = np.fft.irfft(fft, n=n)
    pk = np.max(np.abs(out)) or 1.0
    return out / pk


def _brown(n, rng):
    white = rng.randn(n)
    brown = np.cumsum(white)
    brown -= np.linspace(brown[0], brown[-1], n)  # remove drift
    pk = np.max(np.abs(brown)) or 1.0
    return brown / pk


def _lfo(n, sr, freq, phase=0.0, lo=0.0, hi=1.0):
    t = np.arange(n, dtype=np.float64) / sr
    return lo + (hi - lo) * (0.5 + 0.5 * np.sin(2 * np.pi * freq * t + phase))


def _fade_edges(x, sr, fade_in=0.05, fade_out=0.5):
    n_in = min(len(x), int(fade_in * sr))
    n_out = min(len(x), int(fade_out * sr))
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out)
    return x


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


def _normalize(x, peak=0.9):
    mx = np.max(np.abs(x))
    if mx > 1e-9:
        x = x / mx * peak
    return x


# ------------------------------------------------------------------ presets
def _p_rain(n, sr, rng):
    x = _hp(_bp(_noise(n, rng), 400, 9000, sr), 300, sr)
    x *= _lfo(n, sr, 0.07, phase=rng.random() * 6.28, lo=0.75, hi=1.0)
    # sparse droplet patters on a surface
    x += 0.25 * _impulses(n, sr, rng, density=14.0, amp=1.0)
    # occasional heavy drops: lower, fuller splats under the hiss
    x += 0.4 * _xlp(_impulses(n, sr, rng, density=1.3, amp=1.0), 1800, sr)
    return _normalize(x, 0.75)


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


def _p_brown(n, sr, rng):
    x = _xlp(_brown(n, rng), 500, sr)
    return _normalize(x, 0.8)


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


def _p_wind(n, sr, rng):
    base = _brown(n, rng)
    band1 = _bp(base, 180, 700, sr)
    band2 = _bp(base, 500, 1800, sr)
    gust = _lfo(n, sr, 0.05, phase=rng.random() * 6.28, lo=0.2, hi=1.0)
    gust = _xlp(gust, 3.0, sr, n_taps=255)
    x = band1 * gust + band2 * (gust ** 2) * 0.7
    # whistle
    x += 0.08 * np.sin(2 * np.pi * (700 + 300 * _lfo(n, sr, 0.03)) * np.arange(n) / sr) * (gust ** 3)
    return _normalize(x, 0.7)


def _p_space(n, sr, rng):
    t = np.arange(n) / sr
    drone = (np.sin(2 * np.pi * 55 * t) * 0.5
             + np.sin(2 * np.pi * (55 * 1.007) * t) * 0.5   # slow beat
             + np.sin(2 * np.pi * 110.3 * t) * 0.3
             + np.sin(2 * np.pi * 220.7 * t) * 0.12)
    drone *= _lfo(n, sr, 0.02, phase=1.0, lo=0.55, hi=1.0)
    air = _xlp(_pink(n, rng), 900, sr) * 0.18
    sparkle = _bp(_noise(n, rng), 3000, 8000, sr) * _lfo(n, sr, 0.11, lo=0.0, hi=0.05)
    return _normalize(drone + air + sparkle, 0.6)


def _p_vinyl(n, sr, rng):
    hiss = _xlp(_noise(n, rng), 6000, sr) * 0.05
    crackle = _impulses(n, sr, rng, density=9.0, amp=1.0) * 0.5
    pops = _impulses(n, sr, rng, density=0.35, amp=2.0)
    rumble = _xlp(_brown(n, rng), 90, sr) * 0.25
    return _normalize(hiss + crackle + pops + rumble, 0.55)


def _p_server(n, sr, rng):
    t = np.arange(n) / sr
    hum = (np.sin(2 * np.pi * 120 * t) * 0.4 + np.sin(2 * np.pi * 240 * t) * 0.15)
    fan = _xlp(_brown(n, rng), 350, sr) * 0.9
    hiss = _xlp(_noise(n, rng), 10000, sr) * 0.05
    return _normalize(hum + fan + hiss, 0.7)


def _p_fire(n, sr, rng):
    bed = _xlp(_brown(n, rng), 220, sr) * 0.9
    crackle = _impulses(n, sr, rng, density=6.0, amp=1.0)
    crackle = _xlp(crackle, 4500, sr)
    whoosh = _bp(_noise(n, rng), 80, 400, sr) * _lfo(n, sr, 0.23, lo=0.1, hi=0.6)
    return _normalize(bed + crackle + whoosh, 0.7)


def _p_keyboard_room(n, sr, rng):
    """Lightly reverberant 'empty office' bed: airy noise + distant hum."""
    air = _xlp(_pink(n, rng), 2500, sr) * 0.5
    hum = np.sin(2 * np.pi * 60 * np.arange(n) / sr) * 0.08
    hvac = _bp(_noise(n, rng), 100, 300, sr) * 0.25
    return _normalize(air + hum + hvac, 0.55)


# ------------------------------------------------- richer soundscapes (v2.6)
def _p_ocean(n, sr, rng):
    """Ocean waves: overlapping swells with foam hiss cresting at the peak."""
    bed = _xlp(_brown(n, rng), 240, sr) * 0.55
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


def _p_forest(n, sr, rng):
    """Forest dawn: soft breeze, leaf rustle and distant birdsong."""
    breeze = _bp(_noise(n, rng), 150, 900, sr)
    breeze *= _lfo(n, sr, 0.06, phase=rng.random() * 6.28, lo=0.2, hi=0.7)
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


def _p_city(n, sr, rng):
    """City street: distant traffic wash with passing-vehicle whooshes."""
    x = _xlp(_brown(n, rng), 200, sr) * 0.5
    x += _bp(_noise(n, rng), 90, 420, sr) * _lfo(n, sr, 0.043, phase=rng.random() * 6.28,
                                                 lo=0.3, hi=0.8) * 0.5
    nw = int(3.0 * sr)
    for _ in range(max(1, int(n / sr / 9.0))):   # one pass every ~9 s
        nw_eff = min(nw, max(2, n - 2))          # never longer than the bed
        tw = np.arange(nw_eff) / sr
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


def _p_night_city(n, sr, rng):
    """Midnight city: deep drone, airy wash and one far-off siren."""
    t = np.arange(n) / sr
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


def _p_train(n, sr, rng):
    """Night train: rail-joint rhythm, bogie rumble and cabin hiss."""
    t = np.arange(n) / sr
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


def _p_cabin(n, sr, rng):
    """Airplane cabin: layered jet thrust, engine beat and air hiss."""
    t = np.arange(n) / sr
    thrust = _xlp(_brown(n, rng), 130, sr) * 1.1
    thrust += _bp(_noise(n, rng), 70, 240, sr) * 0.5
    hiss = _bp(_noise(n, rng), 900, 6500, sr) * 0.16
    beat = 1.0 + 0.06 * np.sin(2 * np.pi * 11.5 * t) + 0.04 * np.sin(2 * np.pi * 3.7 * t + 1.3)
    return _normalize(thrust * beat + hiss, 0.7)


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


# ------------------------------------------------- zen & pleasant (v3.2)
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


def _p_stream(n, sr, rng):
    """Mountain stream: lively babbling brook — chattery bubbles over a
    constant water bed."""
    bed = _bp(_noise(n, rng), 300, 5200, sr)
    x = bed * 0.5 * _lfo(n, sr, 0.09, phase=rng.random() * 6.28, lo=0.6, hi=1.0)
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


AMBIENCE_PRESETS: Dict[str, callable] = {
    "Rain": _p_rain,
    "Rain & Thunder": _p_rain_thunder,
    "Rain on Window": _p_rain_window,
    "Ocean Waves": _p_ocean,
    "Forest Dawn": _p_forest,
    "Night Crickets": _p_crickets,
    "Wind": _p_wind,
    "Fireplace": _p_fire,
    "Café Murmur": _p_cafe,
    "Library": _p_library,
    "Zen Garden": _p_zen,
    "City Traffic": _p_city,
    "Midnight City": _p_night_city,
    "Night Train": _p_train,
    "Airplane Cabin": _p_cabin,
    "Lo-Fi Study": _p_lofi,
    "Space Drone": _p_space,
    "Vinyl Crackle": _p_vinyl,
    "Server Room": _p_server,
    "Brown Noise": _p_brown,
    "Quiet Room": _p_keyboard_room,
    # ── v3.2 zen & pleasant expansion
    "Bamboo Fountain": _p_bamboo_fountain,
    "Mountain Stream": _p_stream,
    "Morning Birds": _p_morning_birds,
    "Garden Wind Chimes": _p_wind_chimes,
    "Singing Bowls": _p_singing_bowls,
    "Hot Spring": _p_hot_spring,
    "Rice Field Dusk": _p_frog_pond,
}


def list_ambience_presets() -> List[str]:
    return list(AMBIENCE_PRESETS.keys())


def render_ambience(preset: str, duration: float, sr: int = AUDIO_SAMPLE_RATE,
                    seed: int = 7) -> np.ndarray:
    """Render an ambience bed: mono float64 in [-1, 1], length = duration*sr."""
    n = max(1, int(duration * sr))
    fn = AMBIENCE_PRESETS.get(preset)
    if fn is None:
        fn = AMBIENCE_PRESETS["Rain"]
    rng = np.random.RandomState(seed)
    x = fn(n, sr, rng)
    return _fade_edges(x, sr)


# ------------------------------------------------------------------ files
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
        else:
            # ffmpeg path already returns mono float64 at the target rate
            return _decode_with_ffmpeg(path, sr)
        if sw == 2:
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
        elif sw == 4:
            data = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
        elif sw == 1:
            data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
        elif sw == 3:
            b = np.frombuffer(raw, dtype=np.uint8)
            usable = (len(b) // 3) * 3
            b = b[:usable].reshape(-1, 3)
            vals = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
                    | (b[:, 2].astype(np.int32) << 16))
            vals = np.where(vals & 0x800000, vals - 0x1000000, vals)
            data = vals.astype(np.float64) / 8388608.0
        else:
            logger.error(f"Unsupported audio WAV width: {sw * 8}-bit")
            return None
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


# ------------------------------------------------------------------ mixing
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
        left = np.clip(left + bed * gain, -1.0, 1.0)
        right = np.clip(right + bed_r * gain, -1.0, 1.0)
        out = np.empty(len(kb_pcm), dtype=np.int16)
        out[0::2] = (left * 32767).astype(np.int16)
        out[1::2] = (right * 32767).astype(np.int16)
        return out

    if kb_pcm.dtype == np.int16:
        mono = kb_pcm.astype(np.float64) / 32768.0
    else:
        mono = kb_pcm.astype(np.float64)
    mono = np.clip(mono + bed * gain, -1.0, 1.0)
    return np.clip(mono * 32767, -32768, 32767).astype(np.int16)


def build_ambience_bed(config, duration: float, sr: int = AUDIO_SAMPLE_RATE) -> Optional[np.ndarray]:
    """Resolve the configured ambience (custom file first, then preset).

    A custom file is procedurally extended to ``duration`` (see
    :func:`extend_wav_procedural`); set ``config.amb_evolve = False`` for the
    plain verbatim loop of the old behaviour.
    """
    if not getattr(config, "amb_enabled", False):
        return None
    if duration <= 0:
        return None
    path = getattr(config, "amb_path", "") or ""
    if path:
        src = _load_wav_mono(path, sr)
        if src is not None:
            evolve = bool(getattr(config, "amb_evolve", True))
            return extend_wav_procedural(src, duration, sr, evolve=evolve)
        logger.warning(f"Ambience file '{path}' failed; using preset "
                       f"'{getattr(config, 'amb_preset', 'Rain')}' instead")
    return render_ambience(getattr(config, "amb_preset", "Rain"), duration, sr)
