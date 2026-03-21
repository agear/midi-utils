"""
This script extracts MIDI stems from a MIDI file and converts them to WAV format.
"""
import time
import logging
from pathlib import Path
from typing import Optional

from controller import Controller
from config import convert_to_wav, midi_file_paths, soundfont_path, base_path

logger = logging.getLogger(__name__)


def main(midi_file_path: str, soundfont_path: str, convert_to_wav: bool, base_path: Optional[str] = ".") -> None:
    """
    Extract MIDI stems from a MIDI file and optionally render them to WAV.

    Args:
        midi_file_path (str): Path to the MIDI file.
        soundfont_path (str): Path to the Soundfont file.
        convert_to_wav (bool): Whether to render each stem to WAV.
        base_path (str, optional): Root output directory. Defaults to ".".
    """
    if not Path(midi_file_path).exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_file_path}")
    if not Path(soundfont_path).exists():
        raise FileNotFoundError(f"Soundfont file not found: {soundfont_path}")

    controller = Controller(
        midi_file_path=midi_file_path,
        soundfont_path=soundfont_path,
        convert_to_wav=convert_to_wav,
        base_path=base_path,
    )
    controller.extract_midi_stems()
    if convert_to_wav:
        controller.convert_to_wav(path=controller.midi_stem_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    start: float = time.perf_counter()

    for midi_file_path in midi_file_paths:
        main(
            midi_file_path=midi_file_path,
            soundfont_path=soundfont_path,
            convert_to_wav=convert_to_wav,
            base_path=base_path,
        )

    elapsed = round(time.perf_counter() - start, 2)
    print(f"Finished in {elapsed} second(s)")
