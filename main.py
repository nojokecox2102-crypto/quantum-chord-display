#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quantum Chord Display - Realtime Guitar Chord Recognition
Microphone input -> Chord recognition -> LARGE display output
"""

import os
import sys
import time
import math
import threading
from dataclasses import dataclass

import numpy as np
from scipy import signal

# Audio input handling - try sounddevice first, fall back to ALSA
USE_SOUNDDEVICE = False
USE_ALSA = False

try:
    import sounddevice as sd
    USE_SOUNDDEVICE = True
except ImportError:
    pass

if not USE_SOUNDDEVICE:
    try:
        import alsaaudio
        USE_ALSA = True
    except ImportError:
        pass

# Audio configuration
SR = 22050              # Sample rate
N_FFT = 2048            # FFT size
HOP_LEN = 512           # Hop length
WIN_SEC = 0.75          # Window size in seconds
CHROM A_SMOOTH = 0.7    # Smoothing factor for chroma
CONF_MIN = 0.55         # Minimum confidence threshold

# Chord templates
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Major: 0,4,7; Minor: 0,3,7
CHORD_TEMPLATES = {}
for root in range(12):
    # Major
    maj = np.zeros(12)
    maj[root] = 1
    maj[(root + 4) % 12] = 1
    maj[(root + 7) % 12] = 1
    CHORD_TEMPLATES[NOTE_NAMES[root]] = maj
    
    # Minor
    minr = np.zeros(12)
    minr[root] = 1
    minr[(root + 3) % 12] = 1
    minr[(root + 7) % 12] = 1
    CHORD_TEMPLATES[NOTE_NAMES[root] + "m"] = minr


@dataclass
class ChordResult:
    """Chord recognition result"""
    label: str
    confidence: float


class AudioRingBuffer:
    """Thread-safe circular audio buffer"""
    def __init__(self, sr: int, seconds: float):
        self.sr = sr
        self.size = int(sr * seconds)
        self.buf = np.zeros(self.size, dtype=np.float32)
        self.write_idx = 0
        self.lock = threading.Lock()
        self.filled = False
    
    def push(self, x: np.ndarray) -> None:
        """Add audio data to buffer"""
        x = x.astype(np.float32, copy=False)
        n = len(x)
        if n == 0:
            return
        
        with self.lock:
            idx = self.write_idx
            end = idx + n
            
            if end <= self.size:
                self.buf[idx:end] = x
            else:
                first = self.size - idx
                self.buf[idx:] = x[:first]
                self.buf[:end % self.size] = x[first:]
            
            self.filled = True
            self.write_idx = end % self.size
    
    def read_last(self, n: int) -> np.ndarray:
        """Read last n samples"""
        n = min(n, self.size)
        with self.lock:
            if not self.filled and self.write_idx < n:
                return self.buf[:self.write_idx].copy()
            
            start = (self.write_idx - n) % self.size
            if start < self.write_idx:
                return self.buf[start:self.write_idx].copy()
            else:
                return np.concatenate((self.buf[start:], self.buf[:self.write_idx])).copy()


def chroma_from_audio(y: np.ndarray, sr: int, n_fft: int = 2048) -> np.ndarray:
    """Extract chromagram from audio"""
    if y.size < n_fft:
        return np.zeros(12, dtype=np.float32)
    
    y = y - float(np.mean(y))
    hop = n_fft // 4
    win = np.hanning(n_fft).astype(np.float32)
    
    chroma_acc = np.zeros(12, dtype=np.float32)
    frames = 0
    
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)
    
    for start in range(0, len(y) - n_fft, hop):
        frame = y[start:start + n_fft] * win
        fft_mag = np.abs(np.fft.rfft(frame))
        
        # Map frequency bins to chromatic scale
        for bin_idx, freq in enumerate(freqs):
            if freq < 20 or freq > sr / 2 or fft_mag[bin_idx] < 1e-10:
                continue
            
            midi_pitch = 69.0 + 12.0 * math.log2(freq / 440.0)
            chroma_bin = int(round(midi_pitch)) % 12
            chroma_acc[chroma_bin] += fft_mag[bin_idx]
        
        frames += 1
    
    if frames > 0:
        chroma_acc /= frames
    
    # Normalize
    total = np.sum(chroma_acc)
    if total > 0:
        chroma_acc /= total
    
    return chroma_acc


def best_chord(chroma: np.ndarray) -> tuple:
    """Find best matching chord"""
    chroma = np.maximum(chroma, 0)
    s = np.sum(chroma)
    if s > 0:
        chroma = chroma / s
    
    best_name, best_score = "—", 0.0
    
    for name, template in CHORD_TEMPLATES.items():
        tpl = np.maximum(template, 0)
        tpl_sum = np.sum(tpl)
        if tpl_sum > 0:
            tpl = tpl / tpl_sum
        
        score = np.dot(chroma, tpl)
        if score > best_score:
            best_score = score
            best_name = name
    
    return best_name, best_score


def record_sounddevice(ring_buf: AudioRingBuffer) -> None:
    """Record from sounddevice"""
    try:
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"Audio status: {status}")
            ring_buf.push(indata[:, 0])
        
        stream = sd.InputStream(
            callback=audio_callback,
            samplerate=SR,
            channels=1,
            blocksize=4096,
            latency='low'
        )
        stream.start()
        
        while True:
            time.sleep(0.1)
    except Exception as e:
        print(f"Sounddevice error: {e}")


def record_alsa(ring_buf: AudioRingBuffer, device: str = "default") -> None:
    """Record from ALSA"""
    try:
        inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device=device)
        inp.setchannels(1)
        inp.setrate(SR)
        inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        inp.setperiodsize(1024)
        
        while True:
            l, data = inp.read()
            if l > 0:
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                ring_buf.push(audio_data)
            time.sleep(0.01)
    except Exception as e:
        print(f"ALSA error: {e}")


def clear_screen() -> None:
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_large(text: str) -> None:
    """Print text in LARGE format"""
    clear_screen()
    print("\n" * 5)
    print(" " * 10 + "="*60)
    print(" " * 20)
    # MEGA LARGE ASCII (block letters)
    print(" " * 15 + text)
    print(" " * 20)
    print(" " * 10 + "="*60)
    print("\n" * 3)
    print(" " * 15 + "[Press 'q' to quit]")


def main():
    """Main program"""
    if not USE_SOUNDDEVICE and not USE_ALSA:
        print("ERROR: No audio backend available!")
        print("Install: pip install sounddevice OR pip install pyalsaaudio")
        sys.exit(1)
    
    print(f"Audio backend: {'sounddevice' if USE_SOUNDDEVICE else 'ALSA'}")
    print(f"Sample rate: {SR} Hz")
    print(f"Window: {WIN_SEC}s")
    print("Starting in 2 seconds...")
    time.sleep(2)
    
    # Create ring buffer
    ring_buf = AudioRingBuffer(SR, WIN_SEC)
    
    # Start recording in background thread
    if USE_SOUNDDEVICE:
        rec_thread = threading.Thread(target=record_sounddevice, args=(ring_buf,), daemon=True)
    else:
        rec_thread = threading.Thread(target=record_alsa, args=(ring_buf,), daemon=True)
    
    rec_thread.start()
    time.sleep(0.5)  # Let buffer fill
    
    # Main loop
    smoothed_chroma = None
    last_chord = "—"
    last_score = 0.0
    
    try:
        while True:
            # Get audio data
            n_samples = int(SR * WIN_SEC)
            audio_data = ring_buf.read_last(n_samples)
            
            if len(audio_data) == 0:
                time.sleep(0.01)
                continue
            
            # Extract chroma
            chroma = chroma_from_audio(audio_data, SR, N_FFT)
            
            # Smooth
            if smoothed_chroma is None:
                smoothed_chroma = chroma
            else:
                smoothed_chroma = CHROMA_SMOOTH * smoothed_chroma + (1 - CHROMA_SMOOTH) * chroma
            
            # Recognize chord
            chord_name, confidence = best_chord(smoothed_chroma)
            
            # Threshold
            if confidence < CONF_MIN:
                chord_name = "—"
            
            # Only print if changed
            if chord_name != last_chord or (chord_name != "—" and abs(confidence - last_score) > 0.05):
                print_large(f"{chord_name} ({confidence:.2f})")
                last_chord = chord_name
                last_score = confidence
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
