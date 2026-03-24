"""
This script extracts MIDI stems from a MIDI file and converts them to WAV format.
"""
import os
import time
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from controller import Controller
from config import convert_to_wav, midi_file_paths, soundfont_path, output_path

logger = logging.getLogger(__name__)


def main(
    midi_file_path: str,
    soundfont_path: str,
    convert_to_wav: bool,
    output_path: Optional[str] = None,
    max_wav_workers: int = None,
) -> None:
    """
    Extract MIDI stems from a MIDI file and optionally render them to WAV.

    Args:
        midi_file_path (str): Path to the MIDI file.
        soundfont_path (str): Path to the Soundfont file.
        convert_to_wav (bool): Whether to render each stem to WAV.
        output_path (str, optional): Root output directory. Defaults to ".".
        max_wav_workers (int, optional): Max concurrent FluidSynth processes per
            file. Pass 1 when files are already being processed in parallel.
    """
    if not Path(midi_file_path).exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_file_path}")
    if not Path(soundfont_path).exists():
        raise FileNotFoundError(f"Soundfont file not found: {soundfont_path}")

    file_start = time.perf_counter()
    controller = Controller(
        midi_file_path=midi_file_path,
        soundfont_path=soundfont_path,
        convert_to_wav=convert_to_wav,
        output_path=output_path,
    )
    controller.extract_midi_stems()
    if convert_to_wav:
        controller.convert_to_wav(path=controller.midi_stem_path, max_workers=max_wav_workers)
    logger.info("Completed %s in %.2fs", Path(midi_file_path).name, time.perf_counter() - file_start)


if __name__ == "__main__":
    _log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "midi-utils.log")
    _fmt = "%(asctime)s [CLI] %(levelname)-8s %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=_fmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(_log_path, mode="a", encoding="utf-8"),
        ],
    )
    logging.info("=" * 72)
    logging.info("CLI run started — %d file(s) queued", len(midi_file_paths))

    start: float = time.perf_counter()

    cpu_count = os.cpu_count() or 4

    if len(midi_file_paths) == 1:
        # Single file: let convert_to_wav use all cores across stems.
        main(
            midi_file_path=midi_file_paths[0],
            soundfont_path=soundfont_path,
            convert_to_wav=convert_to_wav,
            output_path=output_path,
        )
    else:
        # Batch: parallelise across files. Each file gets max_wav_workers=1 so
        # the total concurrent FluidSynth processes stays at cpu_count, not
        # cpu_count² (which would thrash).
        errors = []
        with ProcessPoolExecutor(max_workers=cpu_count) as pool:
            futures = {
                pool.submit(
                    main,
                    midi_file_path=path,
                    soundfont_path=soundfont_path,
                    convert_to_wav=convert_to_wav,
                    output_path=output_path,
                    max_wav_workers=1,
                ): path
                for path in midi_file_paths
            }
            for fut in as_completed(futures):
                path = futures[fut]
                try:
                    fut.result()
                except Exception as exc:
                    logger.error("Failed %s: %s", path, exc)
                    errors.append(path)

        if errors:
            print(f"{len(errors)} file(s) failed — check logs above.")

    elapsed = round(time.perf_counter() - start, 2)
    logging.info("CLI run finished in %.2fs", elapsed)
    print(f"Finished in {elapsed} second(s)")
