"""
This script extracts MIDI stems from a MIDI file and converts them to WAV format.
"""

import time
from controller import Controller
from config import convert_to_wav, midi_file_paths

def main(midi_file_path: str, convert_to_wav: bool) -> None:
    """
    Main function to execute the MIDI stem extraction and conversion process.
    """

    # TODO: Figure out why drum tracks aren't named
    # TODO: remove print statements
    # TODO: Encapsulate track???
    # TODO: first track should be 01
    # TODO: Figure out reverb
    # TODO: Add multithreading
    # TODO: Don't bounce empty tracks (drums)
    # TODO: add test suite
    # TODO: add type hints

    # Grab current time before running the code
    start: float = time.perf_counter()


    controller = Controller(midi_file_path, convert_to_wav)
    controller.extract_midi_stems()
    if convert_to_wav:
        controller.convert_to_wav(path=controller.midi_stem_path)

    # Grab current time after running the code
    end: float = time.perf_counter()

    # Calculate the execution time
    execution_time: float = round(end - start, 2)
    print(f"Finished in {execution_time} second(s)")

if __name__ == "__main__":

    for midi_file_path in midi_file_paths:
        main(midi_file_path, convert_to_wav)
