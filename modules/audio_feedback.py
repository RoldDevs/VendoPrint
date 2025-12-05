"""
Audio Feedback Module
Handles audio cues and sound effects
"""

import logging
import os
import subprocess

class AudioFeedback:
    def __init__(self):
        self.sounds_dir = 'static/sounds'
        os.makedirs(self.sounds_dir, exist_ok=True)
        self.audio_enabled = True
    
    def play_coin_sound(self):
        """Play sound when coin is inserted"""
        try:
            if self.audio_enabled:
                # Use aplay for ALSA or paplay for PulseAudio
                sound_file = os.path.join(self.sounds_dir, 'coin.wav')
                if os.path.exists(sound_file):
                    subprocess.Popen(['aplay', sound_file], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                else:
                    # Generate beep sound using system beep
                    subprocess.Popen(['beep', '-f', '800', '-l', '100'],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        except Exception as e:
            # Silently fail if audio not available
            pass
    
    def play_printing_sound(self):
        """Play sound when printing starts"""
        try:
            if self.audio_enabled:
                sound_file = os.path.join(self.sounds_dir, 'printing.wav')
                if os.path.exists(sound_file):
                    subprocess.Popen(['aplay', sound_file],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                else:
                    # Generate progress sound
                    subprocess.Popen(['beep', '-f', '600', '-l', '200'],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        except Exception as e:
            pass
    
    def play_completion_sound(self):
        """Play sound when printing completes"""
        try:
            if self.audio_enabled:
                sound_file = os.path.join(self.sounds_dir, 'complete.wav')
                if os.path.exists(sound_file):
                    subprocess.Popen(['aplay', sound_file],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                else:
                    # Generate completion beep
                    subprocess.Popen(['beep', '-f', '1000', '-l', '300'],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        except Exception as e:
            pass
    
    def play_error_sound(self):
        """Play sound when error occurs"""
        try:
            if self.audio_enabled:
                sound_file = os.path.join(self.sounds_dir, 'error.wav')
                if os.path.exists(sound_file):
                    subprocess.Popen(['aplay', sound_file],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                else:
                    # Generate error beep (low frequency)
                    subprocess.Popen(['beep', '-f', '400', '-l', '500'],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        except Exception as e:
            pass
    
    def set_enabled(self, enabled):
        """Enable or disable audio feedback"""
        self.audio_enabled = enabled

