# Quantum Chord Display

Realtime Guitar Chord Recognition for Quantum Tiny Linux - Microphone input to display output.

Your father plays a guitar chord → The device recognizes it via the built-in microphone → Shows the chord name in HUGE letters on the display.

## Features

✅ Real-time chord recognition (0 lag streaming)  
✅ No Deep Learning - Fast & lightweight  
✅ Works on Tiny Linux (minimal CPU/RAM)  
✅ GIANT display text for easy viewing  
✅ Automatic audio backend selection (sounddevice or ALSA)  
✅ Smooth, flicker-free display

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/nojokecox2102-crypto/quantum-chord-display.git
cd quantum-chord-display
```

### 2. Setup Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -U pip
pip install -r requirements.txt
```

### 3. Test Your Microphone (IMPORTANT!)

```bash
arecord -l                                    # List recording devices
arecord -D default -f S16_LE -r 44100 -c 1 -d 3 test.wav  # Record 3 seconds
aplay test.wav                                # Play it back
```

If this works, the program will work!

### 4. Run the Program

```bash
python3 main.py
```

Play a chord on the guitar → See the chord name displayed HUGE on screen.

**Exit:** Press `q`

## What It Recognizes

Major chords: C, C#, D, D#, E, F, F#, G, G#, A, A#, B  
Minor chords: Cm, C#m, Dm, D#m, Em, Fm, F#m, Gm, G#m, Am, A#m, Bm

## How It Works

1. **Audio Capture**: Records audio from your microphone in real-time (no 1-second delay)
2. **Chroma Extraction**: Fast FFT-based pitch analysis (no TensorFlow)
3. **Template Matching**: Compares the detected pitches against known chord patterns
4. **Display Output**: Shows the best matching chord

## Performance Tips

If you're getting lag:

- **Reduce CPU load**: Edit `main.py`, change `N_FFT = 1024` (was 2048)
- **Lower sample rate**: Change `SR = 16000` (was 22050)
- **Faster response**: Change `WIN_SEC = 0.5` (was 0.75)

If recognition is "jumpy" (changing chords too fast):

- Increase `CHROMA_SMOOTH = 0.8` (was 0.7)
- Increase `CONF_MIN = 0.65` (was 0.55)

## File Structure

```
quantum-chord-display/
├── main.py              # Main program (all-in-one)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Requirements

- **Python**: 3.7+
- **OS**: Linux (Debian, Ubuntu, Tiny Linux, etc.)
- **Audio**: ALSA or PortAudio-compatible system
- **Microphone**: Any working input device

## Troubleshooting

### "No module named 'sounddevice'"

Try installing portaudio first:

```bash
sudo apt-get install portaudio19-dev
pip install sounddevice
```

If that doesn't work, the program will fall back to ALSA (pyalsaaudio).

### "Can't find audio device"

Check available devices:

```bash
cat /proc/asound/cards
arecord -l
```

### "Recording nothing / Silent output"

1. Check microphone is plugged in
2. Check volume: `alsamixer`
3. Test with `arecord -D default test.wav` then `aplay test.wav`

### "Chord recognition is wrong"

1. Get closer to the microphone
2. Play chords more clearly/firmly
3. Reduce background noise
4. Adjust `CONF_MIN` threshold in `main.py`

## License

MIT - Use freely

## Author

Built for Quantum Tiny Linux devices 🎸🎵
