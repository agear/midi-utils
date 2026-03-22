"""
Tests for main.py entry-point function.
"""
import os
import pytest
import midi

from main import main


class TestMainFileValidation:
    def test_raises_if_midi_file_not_found(self, tmp_path, soundfont_path):
        with pytest.raises(FileNotFoundError, match="MIDI file not found"):
            main(
                midi_file_path=str(tmp_path / "nonexistent.mid"),
                soundfont_path=soundfont_path,
                convert_to_wav=False,
                output_path=str(tmp_path / "placeholder"),
            )

    def test_raises_if_soundfont_not_found(self, simple_midi_file, tmp_path):
        with pytest.raises(FileNotFoundError, match="Soundfont file not found"):
            main(
                midi_file_path=simple_midi_file,
                soundfont_path=str(tmp_path / "missing.sf2"),
                convert_to_wav=False,
                output_path=str(tmp_path / "placeholder"),
            )


class TestMainExtraction:
    def test_creates_stem_files(self, simple_midi_file, tmp_path, soundfont_path):
        main(
            midi_file_path=simple_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            output_path=str(tmp_path / "placeholder"),
        )
        # Find any .mid files written under tmp_path
        mid_files = []
        for root, _, files in os.walk(str(tmp_path)):
            mid_files.extend(f for f in files if f.endswith(".mid"))
        assert len(mid_files) > 0

    def test_stem_files_are_valid_midi(self, simple_midi_file, tmp_path, soundfont_path):
        main(
            midi_file_path=simple_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            output_path=str(tmp_path / "placeholder"),
        )
        for root, _, files in os.walk(str(tmp_path)):
            for f in files:
                if f.endswith(".mid"):
                    reloaded = midi.read_midifile(os.path.join(root, f))
                    assert isinstance(reloaded, midi.Pattern)

    def test_returns_none(self, simple_midi_file, tmp_path, soundfont_path):
        result = main(
            midi_file_path=simple_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            output_path=str(tmp_path / "placeholder"),
        )
        assert result is None
