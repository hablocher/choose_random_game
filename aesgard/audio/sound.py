# -*- coding: utf-8 -*-
"""
Sound Effects (SFX) Engine for Canino Gaming.
Synthesizes crisp 16-bit PCM WAV sound effects natively (zero external dependencies)
and plays them via QSoundEffect (QtMultimedia) or winsound fallback.
Supports White Fang / Caninos Brancos wild arctic soundscapes (wolf howl, blizzard wind, snow crunch, growl).
"""
import os
import math
import wave
import struct
import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_SOUND_DIR: Optional[str] = None
_SOUND_MANAGER: Optional['SoundManager'] = None


def _get_sound_dir() -> str:
    """Returns directory where synthesized WAV assets are stored."""
    global _SOUND_DIR
    if _SOUND_DIR:
        return _SOUND_DIR
    # Find project root
    cur = os.path.abspath(__file__)
    for _ in range(4):
        cur = os.path.dirname(cur)
        if os.path.exists(os.path.join(cur, "assets")) or os.path.exists(os.path.join(cur, "choose_random_game.ini")):
            break
    target = os.path.join(cur, "assets", "sounds")
    os.makedirs(target, exist_ok=True)
    _SOUND_DIR = target
    return _SOUND_DIR


def _write_wav(filepath: str, samples: list, sample_rate: int = 22050):
    """Writes normalized floating-point samples [-1.0, 1.0] to a 16-bit mono WAV file."""
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(1)        # mono
        wav.setsampwidth(2)        # 16-bit
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        data = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            int_val = int(clamped * 32767.0)
            data.extend(struct.pack('<h', int_val))
        wav.writeframes(data)


def generate_synthesized_sounds():
    """Generates all standard retro arcade sound effect files if they do not exist."""
    s_dir = _get_sound_dir()
    sample_rate = 22050

    # 1. Click
    p_click = os.path.join(s_dir, "click.wav")
    if not os.path.exists(p_click):
        n = int(sample_rate * 0.04)
        samples = [math.sin(2 * math.pi * 800 * (i / sample_rate)) * (1.0 - i / n) for i in range(n)]
        _write_wav(p_click, samples, sample_rate)

    # 2. Roulette Tick
    p_tick = os.path.join(s_dir, "tick.wav")
    if not os.path.exists(p_tick):
        n = int(sample_rate * 0.025)
        samples = [math.sin(2 * math.pi * 1200 * (i / sample_rate)) * (1.0 - i / n) * 0.7 for i in range(n)]
        _write_wav(p_tick, samples, sample_rate)

    # 3. Reveal / Jackpot
    p_reveal = os.path.join(s_dir, "reveal.wav")
    if not os.path.exists(p_reveal):
        n = int(sample_rate * 0.35)
        samples = []
        for i in range(n):
            t = i / sample_rate
            f = 440 + 440 * (i / n)
            v = math.sin(2 * math.pi * f * t) * (1.0 - i / n)
            samples.append(v * 0.8)
        _write_wav(p_reveal, samples, sample_rate)

    # 4. Victory / Launch Fanfare
    p_vic = os.path.join(s_dir, "victory.wav")
    if not os.path.exists(p_vic):
        chord_freqs = [523.25, 659.25, 783.99, 1046.50]
        n = int(sample_rate * 0.6)
        samples = []
        for i in range(n):
            t = i / sample_rate
            env = 1.0 - (i / n)
            v = sum(math.sin(2 * math.pi * f * t) for f in chord_freqs) / len(chord_freqs)
            samples.append(v * env * 0.9)
        _write_wav(p_vic, samples, sample_rate)

    # 5. Achievement / Golden Chime
    p_ach = os.path.join(s_dir, "achievement.wav")
    if not os.path.exists(p_ach):
        n = int(sample_rate * 0.5)
        samples = []
        for i in range(n):
            t = i / sample_rate
            f = 880 + 200 * math.sin(2 * math.pi * 8 * t)
            env = math.exp(-3.0 * (i / n))
            v = math.sin(2 * math.pi * f * t) * env
            samples.append(v * 0.85)
        _write_wav(p_ach, samples, sample_rate)


def generate_thematic_sounds():
    """
    Synthesizes custom acoustic sounds inspired by Jack London's Caninos Brancos (White Fang):
    - wolf_howl.wav: Haunting Yukon wolf howl with natural vibrato and resonant overtones.
    - blizzard_wind.wav: White-noise sweep simulating arctic wind gust across frozen pines.
    - snow_crunch.wav: Soft, rhythmic crunch of snow under paws in the subzero Yukon wild.
    - wolf_growl.wav: Low rumbling wild animal growl with frequency modulation.
    """
    s_dir = _get_sound_dir()
    sample_rate = 22050

    # 1. Wolf Howl (Uivo de Caninos Brancos)
    p_howl = os.path.join(s_dir, "wolf_howl.wav")
    if not os.path.exists(p_howl):
        duration = 1.8
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / sample_rate
            p = t / duration
            # Frequency pitch contour
            if p < 0.25:
                freq = 280 + (460 - 280) * (p / 0.25)
            elif p < 0.70:
                vib = 12.0 * math.sin(2 * math.pi * 5.5 * t)
                freq = 460 + vib
            else:
                drop_p = (p - 0.70) / 0.30
                freq = 460 - (460 - 220) * (drop_p ** 1.3)

            # Natural swell & fade envelope
            if p < 0.20:
                env = p / 0.20
            elif p < 0.65:
                env = 1.0
            else:
                env = max(0.0, 1.0 - (p - 0.65) / 0.35)

            # Fundamental + soft harmonics
            f1 = math.sin(2 * math.pi * freq * t)
            f2 = 0.35 * math.sin(2 * math.pi * freq * 2.0 * t)
            f3 = 0.15 * math.sin(2 * math.pi * freq * 3.0 * t)
            # Gentle breath turbulence
            noise = (random.random() * 2.0 - 1.0) * 0.04
            samples.append((f1 + f2 + f3 + noise) * env * 0.75)
        _write_wav(p_howl, samples, sample_rate)

    # 2. Blizzard Wind (Rajada de Vento da Nevasca do Yukon)
    p_wind = os.path.join(s_dir, "blizzard_wind.wav")
    if not os.path.exists(p_wind):
        duration = 1.4
        n = int(sample_rate * duration)
        samples = []
        last_val = 0.0
        for i in range(n):
            t = i / sample_rate
            p = t / duration
            # Bell envelope
            env = math.sin(math.pi * p) ** 1.8
            # Lowpass filtered noise
            white = random.random() * 2.0 - 1.0
            last_val = last_val * 0.88 + white * 0.12
            # Whistle resonance
            whistle = 0.25 * math.sin(2 * math.pi * (320 + 80 * math.sin(2 * math.pi * 1.5 * t)) * t)
            samples.append((last_val + whistle) * env * 0.8)
        _write_wav(p_wind, samples, sample_rate)

    # 3. Snow Crunch (Passos na Neve Ártica)
    p_snow = os.path.join(s_dir, "snow_crunch.wav")
    if not os.path.exists(p_snow):
        duration = 0.22
        n = int(sample_rate * duration)
        samples = []
        last_val = 0.0
        for i in range(n):
            t = i / sample_rate
            p = t / duration
            env = (1.0 - p) ** 2.2
            # Granular crunch
            white = random.random() * 2.0 - 1.0
            last_val = last_val * 0.65 + white * 0.35
            low_thump = 0.4 * math.sin(2 * math.pi * 95 * t)
            samples.append((last_val * 0.7 + low_thump) * env * 0.75)
        _write_wav(p_snow, samples, sample_rate)

    # 4. Wolf Growl (Rosnado Protetor da Selva)
    p_growl = os.path.join(s_dir, "wolf_growl.wav")
    if not os.path.exists(p_growl):
        duration = 0.65
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / sample_rate
            p = t / duration
            env = math.sin(math.pi * p)
            # Low AM rumble
            am = 0.5 + 0.5 * math.sin(2 * math.pi * 32 * t)
            freq = 110 + 20 * math.sin(2 * math.pi * 5 * t)
            base = math.sin(2 * math.pi * freq * t)
            grit = (random.random() * 2.0 - 1.0) * 0.25
            samples.append((base * am + grit) * env * 0.75)
        _write_wav(p_growl, samples, sample_rate)


class SoundManager:
    """
    Manages SFX playback with intelligent fallbacks:
    1. QtMultimedia.QSoundEffect (non-blocking, low-latency, cross-platform)
    2. winsound (Windows native fallback)
    3. Silently ignores errors if audio device is unavailable.
    """

    def __init__(self):
        self._muted = False
        self._effects = {}
        self._qsound_available = False
        self._theme_mode = True

        generate_synthesized_sounds()
        generate_thematic_sounds()
        self._init_qsound()

    def _init_qsound(self):
        try:
            from PyQt6.QtCore import QUrl
            from PyQt6.QtMultimedia import QSoundEffect
            self._QSoundEffect = QSoundEffect
            self._QUrl = QUrl
            self._qsound_available = True
        except ImportError:
            self._qsound_available = False
            logger.info("PyQt6.QtMultimedia not available; using native sound fallback.")

    def set_mute(self, muted: bool):
        self._muted = muted

    def is_muted(self) -> bool:
        return self._muted

    def set_theme_mode(self, enabled: bool):
        self._theme_mode = enabled

    def is_theme_mode(self) -> bool:
        return self._theme_mode

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, float(volume)))
        for eff in self._effects.values():
            try:
                eff.setVolume(self._volume)
            except Exception:
                pass

    def get_volume(self) -> float:
        return getattr(self, '_volume', 0.8)

    def play(self, sound_name: str):
        if self._muted:
            return

        # White Fang Theme Audio Remapping
        actual_name = sound_name
        if self._theme_mode:
            theme_map = {
                "victory": "wolf_howl",
                "reveal": "blizzard_wind",
                "click": "snow_crunch",
                "jackpot": "wolf_howl",
                "danger": "wolf_growl",
            }
            actual_name = theme_map.get(sound_name, sound_name)

        s_dir = _get_sound_dir()
        filepath = os.path.join(s_dir, f"{actual_name}.wav")
        if not os.path.exists(filepath):
            filepath = os.path.join(s_dir, f"{sound_name}.wav")
            if not os.path.exists(filepath):
                return

        if self._qsound_available:
            try:
                if actual_name not in self._effects:
                    eff = self._QSoundEffect()
                    eff.setSource(self._QUrl.fromLocalFile(filepath))
                    eff.setVolume(0.8)
                    self._effects[actual_name] = eff
                self._effects[actual_name].play()
                return
            except Exception as e:
                logger.debug(f"QSoundEffect error for {actual_name}: {e}")

        # Fallback to winsound on Windows
        try:
            import winsound
            winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass


def get_sound_manager() -> SoundManager:
    global _SOUND_MANAGER
    if _SOUND_MANAGER is None:
        _SOUND_MANAGER = SoundManager()
    return _SOUND_MANAGER
