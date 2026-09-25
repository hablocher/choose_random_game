# -*- coding: utf-8 -*-
"""
Sound Effects (SFX) Engine for Choose Random Game.
Synthesizes crisp 16-bit PCM WAV sound effects natively (zero external dependencies)
and plays them via QSoundEffect (QtMultimedia) or winsound fallback.
"""
import os
import math
import wave
import struct
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
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(base_dir, "assets", "sounds")
    os.makedirs(target, exist_ok=True)
    _SOUND_DIR = target
    return _SOUND_DIR


def _write_wav(filepath: str, samples: list, sample_rate: int = 22050):
    """Writes normalized floating-point samples [-1.0, 1.0] to a 16-bit mono WAV file."""
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(1)        # mono
        wav.setsampwidth(2)        # 16-bit
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

    # 1. Tick (Roulette click): crisp 15ms click with sharp decay
    tick_path = os.path.join(s_dir, "tick.wav")
    if not os.path.exists(tick_path):
        duration = 0.018
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            env = math.exp(-t * 220.0)
            val = math.sin(2.0 * math.pi * 950.0 * t) * env
            samples.append(val)
        _write_wav(tick_path, samples, sample_rate)

    # 2. Click (UI button blip): pleasant 12ms interface feedback
    click_path = os.path.join(s_dir, "click.wav")
    if not os.path.exists(click_path):
        duration = 0.015
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            env = math.exp(-t * 180.0)
            val = math.sin(2.0 * math.pi * 1250.0 * t) * env
            samples.append(val)
        _write_wav(click_path, samples, sample_rate)

    # 3. Reveal (Hero mystery reveal / Reroll stop): ascending arpeggio
    reveal_path = os.path.join(s_dir, "reveal.wav")
    if not os.path.exists(reveal_path):
        notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
        note_dur = 0.07
        samples = []
        for freq in notes:
            n_samples = int(note_dur * sample_rate)
            for i in range(n_samples):
                t = i / sample_rate
                env = (1.0 - (i / n_samples)) ** 1.5
                val = (0.7 * math.sin(2.0 * math.pi * freq * t) + 
                       0.3 * math.sin(4.0 * math.pi * freq * t)) * env
                samples.append(val)
        _write_wav(reveal_path, samples, sample_rate)

    # 4. Victory (Mark as Finished / Jackpot): triumphant major chord fanfare
    victory_path = os.path.join(s_dir, "victory.wav")
    if not os.path.exists(victory_path):
        chords = [
            ([392.0, 493.88, 587.33], 0.12),
            ([523.25, 659.25, 783.99], 0.14),
            ([523.25, 659.25, 783.99, 1046.50], 0.40)
        ]
        samples = []
        for freqs, dur in chords:
            n_samples = int(dur * sample_rate)
            for i in range(n_samples):
                t = i / sample_rate
                env = math.exp(-t * (3.0 if dur > 0.2 else 8.0))
                val = sum(math.sin(2.0 * math.pi * f * t) for f in freqs) / len(freqs) * env
                samples.append(val)
        _write_wav(victory_path, samples, sample_rate)

    # 5. Achievement (Badge unlock jingle): rapid 8-bit sparkle chime
    achieve_path = os.path.join(s_dir, "achievement.wav")
    if not os.path.exists(achieve_path):
        notes = [659.25, 830.61, 987.77, 1318.51]  # E5, G#5, B5, E6
        note_dur = 0.08
        samples = []
        for freq in notes:
            n_samples = int(note_dur * sample_rate)
            for i in range(n_samples):
                t = i / sample_rate
                env = (1.0 - (i / n_samples)) ** 1.2
                val = (0.6 * math.sin(2.0 * math.pi * freq * t) +
                       0.3 * math.sin(6.0 * math.pi * freq * t)) * env
                samples.append(val)
        _write_wav(achieve_path, samples, sample_rate)


    # 6. Wolf Howl (Uivo de Caninos Brancos no Yukon): organic pitch-modulated howl
    howl_path = os.path.join(s_dir, "wolf_howl.wav")
    if not os.path.exists(howl_path):
        dur = 2.8
        n_samples = int(dur * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            if t < 0.6:
                p = t / 0.6
                f = 280.0 + 240.0 * (math.sin(p * math.pi / 2.0) ** 2)
            elif t < 2.0:
                vib = 6.0 * math.sin(2.0 * math.pi * 4.5 * t)
                f = 520.0 - 50.0 * ((t - 0.6) / 1.4) + vib
            else:
                p = (t - 2.0) / 0.8
                f = 470.0 - 150.0 * p
            if t < 0.4:
                env = t / 0.4
            elif t < 2.2:
                env = 1.0 - 0.2 * ((t - 0.4) / 1.8)
            else:
                env = 0.8 * max(0.0, 1.0 - (t - 2.2) / 0.6) ** 1.5
            phase = 2.0 * math.pi * f * t
            val = (0.65 * math.sin(phase) +
                   0.25 * math.sin(2.0 * phase) +
                   0.10 * math.sin(3.0 * phase)) * env
            samples.append(val * 0.85)
        _write_wav(howl_path, samples, sample_rate)

    # 7. Blizzard Wind (Vento Gelado da Nevasca do Yukon): atmospheric sub-zero gust
    wind_path = os.path.join(s_dir, "blizzard_wind.wav")
    if not os.path.exists(wind_path):
        import random
        dur = 1.8
        n_samples = int(dur * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            env = math.sin(math.pi * (t / dur)) ** 1.3
            whistle1 = math.sin(2.0 * math.pi * (320.0 + 120.0 * math.sin(2.5 * t)) * t)
            whistle2 = math.sin(2.0 * math.pi * (640.0 + 180.0 * math.sin(3.8 * t)) * t)
            noise = (random.random() * 2.0 - 1.0) * 0.4
            val = (0.4 * whistle1 + 0.25 * whistle2 + 0.35 * noise) * env
            samples.append(val * 0.75)
        _write_wav(wind_path, samples, sample_rate)

    # 8. Snow Crunch (Passos na Neve Fofa): crisp winter footstep
    crunch_path = os.path.join(s_dir, "snow_crunch.wav")
    if not os.path.exists(crunch_path):
        import random
        dur = 0.12
        n_samples = int(dur * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            env = max(0.0, 1.0 - (t / dur)) ** 2.2
            noise = random.random() * 2.0 - 1.0
            grain = math.sin(2.0 * math.pi * 1800.0 * t) * (1.0 if random.random() > 0.4 else -0.8)
            val = (0.6 * noise + 0.4 * grain) * env
            samples.append(val * 0.6)
        _write_wav(crunch_path, samples, sample_rate)

    # 9. Wolf Growl (Rosnado Selvagem de Alerta)
    growl_path = os.path.join(s_dir, "wolf_growl.wav")
    if not os.path.exists(growl_path):
        dur = 0.7
        n_samples = int(dur * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            env = math.sin(math.pi * (t / dur)) ** 0.8
            trem = (math.sin(2.0 * math.pi * 28.0 * t) + 1.0) * 0.5
            f = 95.0 + 20.0 * math.sin(2.0 * math.pi * 4.0 * t)
            val = math.sin(2.0 * math.pi * f * t) * trem * env
            samples.append(val * 0.85)
        _write_wav(growl_path, samples, sample_rate)

    # 10. Pack Victory (Uivo Triunfal / Conquista da Matilha)
    pack_vic_path = os.path.join(s_dir, "pack_victory.wav")
    if not os.path.exists(pack_vic_path):
        dur = 2.5
        n_samples = int(dur * sample_rate)
        samples = []
        chord = [329.63, 392.00, 493.88, 659.25]  # E minor Yukon triad
        for i in range(n_samples):
            t = i / sample_rate
            env = math.exp(-t * 1.5)
            vib = 4.0 * math.sin(2.0 * math.pi * 5.0 * t)
            val = sum(math.sin(2.0 * math.pi * (f + vib) * t) for f in chord) / len(chord) * env
            samples.append(val * 0.8)
        _write_wav(pack_vic_path, samples, sample_rate)


class SoundManager:
    """Manages sound effects playback, volume levels, and mute states."""

    def __init__(self, theme_mode: bool = True):
        self._muted = False
        self._volume = 0.75  # 0.0 to 1.0
        self._effects = {}
        self._has_qt_multimedia = False
        self._theme_mode = theme_mode
        self._sound_dir = _get_sound_dir()

        try:
            generate_synthesized_sounds()
        except Exception as e:
            logger.warning(f"Error generating synthesized sounds: {e}")

        # Try initializing PyQt6 QtMultimedia QSoundEffect
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl

            self._sound_effect_cls = QSoundEffect
            self._qurl_cls = QUrl
            self._has_qt_multimedia = True

            sound_keys = [
                "tick", "click", "reveal", "victory", "achievement",
                "wolf_howl", "blizzard_wind", "snow_crunch", "wolf_growl", "pack_victory"
            ]
            for key in sound_keys:
                wav_file = os.path.join(self._sound_dir, f"{key}.wav")
                if os.path.exists(wav_file):
                    effect = QSoundEffect()
                    effect.setSource(QUrl.fromLocalFile(wav_file))
                    effect.setVolume(self._volume)
                    self._effects[key] = effect
        except Exception as e:
            logger.debug(f"QtMultimedia not active, using native winsound fallback: {e}")
            self._has_qt_multimedia = False

    def set_theme_mode(self, enabled: bool):
        """Enable or disable Caninos Brancos thematic sounds."""
        self._theme_mode = bool(enabled)

    def is_theme_mode(self) -> bool:
        """Returns True if Caninos Brancos thematic sound mode is active."""
        return self._theme_mode

    def play(self, sound_name: str):
        """
        Plays the named sound effect.
        Thematic Caninos Brancos sounds: 'wolf_howl', 'blizzard_wind', 'snow_crunch', 'wolf_growl', 'pack_victory'.
        Also supports standard aliases ('reveal' -> 'wolf_howl', 'victory' -> 'pack_victory', etc.)
        """
        if self._muted:
            return

        thematic_aliases = {
            "reveal": "wolf_howl",
            "victory": "pack_victory",
            "howl": "wolf_howl",
            "wind": "blizzard_wind",
            "crunch": "snow_crunch",
            "growl": "wolf_growl"
        }
        if self._theme_mode:
            resolved = thematic_aliases.get(sound_name, sound_name)
        else:
            resolved = sound_name

        # 1. QtMultimedia playback
        target_key = resolved if resolved in self._effects else sound_name
        if self._has_qt_multimedia and target_key in self._effects:
            try:
                effect = self._effects[target_key]
                effect.setVolume(self._volume)

                effect.play()
                return
            except Exception as e:
                logger.debug(f"QtSoundEffect play failed: {e}")

        # 2. Windows native asynchronous fallback
        try:
            import winsound
            wav_file = os.path.join(self._sound_dir, f"{target_key}.wav")
            if not os.path.exists(wav_file):
                wav_file = os.path.join(self._sound_dir, f"{sound_name}.wav")
            if os.path.exists(wav_file):
                winsound.PlaySound(wav_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            logger.debug(f"winsound play failed: {e}")

    def toggle_mute(self) -> bool:
        """Toggles mute state. Returns new muted state."""
        self._muted = not self._muted
        return self._muted

    def is_muted(self) -> bool:
        return self._muted

    def set_muted(self, muted: bool):
        self._muted = bool(muted)

    def set_volume(self, volume: float):
        """Sets volume from 0.0 (silent) to 1.0 (full)."""
        self._volume = max(0.0, min(1.0, float(volume)))
        if self._has_qt_multimedia:
            for effect in self._effects.values():
                try:
                    effect.setVolume(self._volume)
                except Exception:
                    pass

    def get_volume(self) -> float:
        return self._volume


def get_sound_manager() -> SoundManager:
    """Singleton getter for global SoundManager."""
    global _SOUND_MANAGER
    if _SOUND_MANAGER is None:
        _SOUND_MANAGER = SoundManager()
    return _SOUND_MANAGER
