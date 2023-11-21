"""
This script extracts MIDI stems from a MIDI file and converts them to WAV format.
"""

import time
from controller import Controller
from config import convert_to_wav, midi_file_paths, soundfont_path

def main(midi_file_path: str, soundfont_path: str, convert_to_wav: bool) -> None:
    """
    Main function to execute the MIDI stem extraction and conversion process.
    """

    # TODO: remove print statements
    # TODO: Encapsulate track???
    # TODO: Figure out reverb
    # TODO: Add multithreading (doesn't work with sf2_loader)
    # TODO: Don't bounce empty tracks (drums)
    # TODO: add test suite
    # TODO: add type hints




    controller = Controller(midi_file_path=midi_file_path, soundfont_path=soundfont_path, convert_to_wav=convert_to_wav)
    controller.extract_midi_stems()
    if convert_to_wav:
        controller.convert_to_wav(path=controller.midi_stem_path)


if __name__ == "__main__":

    # Grab current time before running the code
    start: float = time.perf_counter()

    for midi_file_path in midi_file_paths:
        main(midi_file_path=midi_file_path, soundfont_path=soundfont_path, convert_to_wav=convert_to_wav)

    # Grab current time after running the code
    end: float = time.perf_counter()

    # Calculate the execution time
    execution_time: float = round(end - start, 2)
    print(f"Finished in {execution_time} second(s)")
