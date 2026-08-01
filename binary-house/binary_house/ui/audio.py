import math
import struct
import pygame

class AudioSynthesizer:
    """Minimal runtime audio synthesizer for 2-adic digit inheritance.
    
    Synthesizes additive audio motifs for digits b₀, b₁, b₂ using Pygame Sound objects.
    Rooms sharing near digits share sonic harmonic layers.
    """
    def __init__(self):
        self.sounds: dict[tuple[int, int, int], pygame.mixer.Sound] = {}
        self.enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.enabled = True
        except Exception:
            # Fallback if audio hardware unavailable in headless environment
            self.enabled = False

    def _generate_sound(self, b0: int, b1: int, b2: int) -> pygame.mixer.Sound | None:
        if not self.enabled:
            return None
        
        sample_rate = 22050
        duration = 0.3  # seconds
        num_samples = int(sample_rate * duration)
        
        # Base frequencies for digits 0, 1, 2
        f0 = 220.0 if b0 == 0 else 330.0    # A3 vs E4 (Root layer)
        f1 = 440.0 if b1 == 0 else 554.37  # A4 vs C#5 (Floor/Harmonic layer)
        f2 = 659.25 if b2 == 0 else 880.0  # E5 vs A5 (Texture/Overtone layer)

        raw_samples = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            # Fade envelope to avoid clicks
            env = math.sin(math.pi * i / num_samples)
            
            val = (0.5 * math.sin(2 * math.pi * f0 * t) +
                   0.3 * math.sin(2 * math.pi * f1 * t) +
                   0.2 * math.sin(2 * math.pi * f2 * t))
            
            sample_val = int(val * env * 16384)
            sample_val = max(-32768, min(32767, sample_val))
            raw_samples.extend(struct.pack('<h', sample_val))

        try:
            return pygame.mixer.Sound(buffer=bytes(raw_samples))
        except Exception:
            return None

    def play_room_motif(self, b0: int, b1: int, b2: int):
        """Play the sonic motif for a room's first 3 near-digits."""
        if not self.enabled:
            return
        key = (b0, b1, b2)
        if key not in self.sounds:
            snd = self._generate_sound(b0, b1, b2)
            if snd:
                self.sounds[key] = snd

        snd = self.sounds.get(key)
        if snd:
            snd.play()
