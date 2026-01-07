#!/usr/bin/env bash
set -e

echo "Installing Quantum Chord Display..."

# Update system
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip alsa-utils

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Test audio: arecord -l"
echo "2. Run: python3 quantum_chord_display.py"
echo ""
echo "For full code and instructions, see README.md"
