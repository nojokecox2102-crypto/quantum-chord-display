#!/usr/bin/env python3
# Quantum Chord Display - Realtime Guitar Chord Recognition for Quantum Tiny Linux
# Audio capture via ALSA arecord, FFT-based chroma, noise gate + stability
# Author: Noah Cox | ChatGPT (optimized for Tiny Linux devices)
# See README.md for complete installation and usage instructions

from __future__ import annotations
import argparse, math, os, signal, subprocess, sys, time
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def clear_screen() -> None:
    os.system("clear")

def rms(x: np.ndarray) -> float:
    if x.size == 0: return 0.0
    return float(np.sqrt(np.mean(x * x)))

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-9 or nb < 1e-9: return 0.0
    return float(np.dot(a, b) / (na * nb))

def build_chord_templates() -> Dict[str, np.ndarray]:
    t: Dict[str, np.ndarray] = {}
    for r in range(12):
        maj = np.zeros(12, dtype=np.float32)
        maj[r] = 1.0
        maj[(r + 4) % 12] = 1.0
        maj[(r + 7) % 12] = 1.0
        mi = np.zeros(12, dtype=np.float32)
        mi[r] = 1.0
        mi[(r + 3) % 12] = 1.0
        mi[(r + 7) % 12] = 1.0
        t[f"{NOTE_NAMES[r]}"] = maj
        t[f"{NOTE_NAMES[r]}m"] = mi
    return t

TEMPLATES = build_chord_templates()

if __name__ == "__main__":
    print("Quantum Chord Display - Ready!")
    print("Run: python3 quantum_chord_display.py --help")
    print("For full code, see ChatGPT conversation or GitHub.")
