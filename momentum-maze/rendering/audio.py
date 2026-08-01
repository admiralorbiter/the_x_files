import math
from typing import Optional
import numpy as np
import pygame


class AudioSynthesizer:
    """
    Procedural real-time audio synthesizer for Momentum Maze events.
    Uses numpy array sound generation with pygame.mixer.Sound.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.enabled = True

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
        except Exception:
            self.enabled = False

        self._cache = {}

    def _make_sound(self, samples: np.ndarray) -> Optional[pygame.mixer.Sound]:
        if not self.enabled:
            return None
        # Convert float [-1.0, 1.0] to int16 [-32767, 32767]
        stereo = np.column_stack((samples, samples))
        audio_data = (stereo * 32767).astype(np.int16)
        return pygame.mixer.Sound(audio_data)

    def play_torque_pulse(self, torque: float):
        """Short mechanical pulse sound when committing a torque action."""
        if not self.enabled:
            return

        key = f"pulse_{torque:.2f}"
        if key not in self._cache:
            duration = 0.08
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            freq = 220.0 if torque > 0 else (160.0 if torque < 0 else 120.0)
            envelope = np.exp(-35.0 * t)
            wave = np.sin(2.0 * np.pi * freq * t) * envelope
            sound = self._make_sound(wave * 0.3)
            self._cache[key] = sound
        else:
            sound = self._cache[key]

        if sound:
            sound.play()

    def play_gate_passed(self):
        """Pleasant double chime when passing a state gate."""
        if not self.enabled:
            return

        key = "gate_passed"
        if key not in self._cache:
            duration = 0.25
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            envelope = np.exp(-12.0 * t)
            # Two harmonic tones (C5 + G5)
            wave = (np.sin(2.0 * np.pi * 523.25 * t) + 0.6 * np.sin(2.0 * np.pi * 783.99 * t)) * envelope
            sound = self._make_sound(wave * 0.35)
            self._cache[key] = sound
        else:
            sound = self._cache[key]

        if sound:
            sound.play()

    def play_separatrix_cross(self):
        """Resonant deep tone when crossing the E=2 separatrix."""
        if not self.enabled:
            return

        key = "separatrix_cross"
        if key not in self._cache:
            duration = 0.4
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            envelope = np.sin(np.pi * t / duration)  # Fade in/out swell
            wave = (np.sin(2.0 * np.pi * 146.83 * t) + 0.5 * np.sin(2.0 * np.pi * 220.0 * t)) * envelope
            sound = self._make_sound(wave * 0.4)
            self._cache[key] = sound
        else:
            sound = self._cache[key]

        if sound:
            sound.play()

    def play_hazard_failed(self):
        """Low buzzing alert when crashing or over-speeding."""
        if not self.enabled:
            return

        key = "hazard_failed"
        if key not in self._cache:
            duration = 0.35
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            envelope = np.exp(-6.0 * t)
            wave = (np.sin(2.0 * np.pi * 80.0 * t) + 0.8 * np.sin(2.0 * np.pi * 85.0 * t)) * envelope
            sound = self._make_sound(wave * 0.45)
            self._cache[key] = sound
        else:
            sound = self._cache[key]

        if sound:
            sound.play()

    def play_dock_success(self):
        """Triumphant major chord upon docking in target state."""
        if not self.enabled:
            return

        key = "dock_success"
        if key not in self._cache:
            duration = 0.6
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            envelope = np.exp(-4.0 * t)
            # C major triad (C5, E5, G5, C6)
            c5 = np.sin(2.0 * np.pi * 523.25 * t)
            e5 = np.sin(2.0 * np.pi * 659.25 * t)
            g5 = np.sin(2.0 * np.pi * 783.99 * t)
            c6 = np.sin(2.0 * np.pi * 1046.50 * t)
            wave = (c5 + e5 + g5 + 0.5 * c6) * 0.25 * envelope
            sound = self._make_sound(wave * 0.5)
            self._cache[key] = sound
        else:
            sound = self._cache[key]

        if sound:
            sound.play()
