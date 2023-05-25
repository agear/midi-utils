"""
This script extracts MIDI stems from a MIDI file and converts them to WAV format.
"""

from controller import Controller
import time

def main() -> None:
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

    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/Aphids/Aphids2.mid"
    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/0.7/0.71.mid"
    midi_file_path: str ="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/Aleksei's Visions of Chess War/Aleksei's Visions of Chess War.mid"
    # midi_file_path="/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/The Human Body (Can Run On Sugar Alone Goddamnit!)/The human body can run on sugar alone, God damn it!8.mid"


    controller = Controller(midi_file_path)
    controller.extract_midi_stems()
    controller.convert_to_wav(path=controller.midi_stem_path)

    # Grab current time after running the code
    end: float = time.perf_counter()

    # Calculate the execution time
    execution_time: float = round(end - start, 2)
    print(f"Finished in {execution_time} second(s)")

if __name__ == "__main__":
    main()
