"""
Tests for Encapsulated_Midi_Track.

Uses a MockController (from conftest.py) and programmatically built midi.Track
objects so tests have no dependency on real MIDI files.
"""
import os
import pytest
import midi
from copy import deepcopy

from encapsulated_midi_track import Encapsulated_Midi_Track
from encapsulated_midi_event import Encapsulated_Midi_Event
from percussion_instrument import Percussion_Instrument


# ---------------------------------------------------------------------------
# Helpers: build raw midi.Track objects with specific event sequences
# ---------------------------------------------------------------------------

def piano_track():
    """One program change (piano, prog 0) followed by note on/off."""
    t = midi.Track()
    pc = midi.ProgramChangeEvent(tick=0, channel=0)
    pc.data = [0]
    t.append(pc)
    on = midi.NoteOnEvent(tick=0, channel=0)
    on.data = [60, 80]
    t.append(on)
    off = midi.NoteOffEvent(tick=480, channel=0)
    off.data = [60, 0]
    t.append(off)
    t.append(midi.EndOfTrackEvent(tick=1))
    return t


def two_program_track():
    """Switches from Acoustic Grand (0) to Acoustic Guitar Steel (25)."""
    t = midi.Track()
    pc1 = midi.ProgramChangeEvent(tick=0, channel=0)
    pc1.data = [0]
    t.append(pc1)
    on1 = midi.NoteOnEvent(tick=0, channel=0)
    on1.data = [60, 80]
    t.append(on1)
    pc2 = midi.ProgramChangeEvent(tick=240, channel=0)
    pc2.data = [25]
    t.append(pc2)
    on2 = midi.NoteOnEvent(tick=0, channel=0)
    on2.data = [64, 70]
    t.append(on2)
    t.append(midi.EndOfTrackEvent(tick=1))
    return t


def drum_track():
    """Drum track: channel 9 program change + kick (36) and snare (38)."""
    t = midi.Track()
    pc = midi.ProgramChangeEvent(tick=0, channel=9)
    pc.data = [0]
    t.append(pc)
    kick = midi.NoteOnEvent(tick=0, channel=9)
    kick.data = [36, 100]
    t.append(kick)
    snare = midi.NoteOnEvent(tick=240, channel=9)
    snare.data = [38, 90]
    t.append(snare)
    t.append(midi.EndOfTrackEvent(tick=1))
    return t


def empty_track():
    t = midi.Track()
    t.append(midi.EndOfTrackEvent(tick=1))
    return t


def no_program_track():
    """Events but no program change (e.g. a transport/tempo track)."""
    t = midi.Track()
    tempo = midi.SetTempoEvent(tick=0)
    tempo.set_bpm(120)
    t.append(tempo)
    t.append(midi.EndOfTrackEvent(tick=1))
    return t


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEncapsulatedMidiTrackInit:
    def test_attributes_set_from_controller(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert track.transport_track is mock_controller.transport_track
        assert track.resolution == mock_controller.resolution
        assert track.midi_stem_path == mock_controller.midi_stem_path
        assert track.songname == mock_controller.songname

    def test_track_number_formatted(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert track.track_number == "01"

    def test_events_encapsulated(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert isinstance(track.events, list)
        assert all(isinstance(e, Encapsulated_Midi_Event) for e in track.events)

    def test_programs_populated(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert isinstance(track.programs, list)

    def test_non_drum_track_drums_empty(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert track.drums == ""

    def test_drum_track_drums_label(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=drum_track(), track_number=0, controller=mock_controller
        )
        assert track.drums == "- 0 - Drum Kit 0 "

    def test_patterns_list_created(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert isinstance(track.patterns, list)


class TestEncapsulateMidiEvents:
    def test_all_events_wrapped(self, mock_controller):
        raw = piano_track()
        track = Encapsulated_Midi_Track(
            events=raw, track_number=0, controller=mock_controller
        )
        assert len(track.events) == len(raw)

    def test_events_before_program_change_have_none(self, mock_controller):
        """Events before the first ProgramChangeEvent get program_number=None."""
        raw = no_program_track()
        track = Encapsulated_Midi_Track(
            events=raw, track_number=0, controller=mock_controller
        )
        assert all(e.program_number is None for e in track.events)

    def test_program_number_set_after_program_change(self, mock_controller):
        raw = piano_track()  # first event is ProgramChangeEvent(data=[0])
        track = Encapsulated_Midi_Track(
            events=raw, track_number=0, controller=mock_controller
        )
        # The ProgramChangeEvent itself gets tagged with program 0
        pc_event = track.events[0]
        assert pc_event.program_number == 0
        # Subsequent events also carry program 0
        note_on_event = track.events[1]
        assert note_on_event.program_number == 0

    def test_program_number_updates_on_second_change(self, mock_controller):
        raw = two_program_track()
        track = Encapsulated_Midi_Track(
            events=raw, track_number=0, controller=mock_controller
        )
        # events[0] = ProgramChange(0), events[1] = NoteOn (prog 0)
        # events[2] = ProgramChange(25), events[3] = NoteOn (prog 25)
        assert track.events[0].program_number == 0
        assert track.events[1].program_number == 0
        assert track.events[2].program_number == 25
        assert track.events[3].program_number == 25

    def test_empty_track_returns_empty_list(self, mock_controller):
        raw = empty_track()
        track = Encapsulated_Midi_Track(
            events=raw, track_number=0, controller=mock_controller
        )
        assert len(track.events) == 1  # EndOfTrack


class TestIsDrumTrack:
    def test_non_drum_returns_empty_string(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert track._is_drum_track() == ""

    def test_drum_returns_label(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=drum_track(), track_number=0, controller=mock_controller
        )
        assert track._is_drum_track() == "- 0 - Drum Kit 0 "

    def test_no_program_track_returns_empty_string(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=no_program_track(), track_number=0, controller=mock_controller
        )
        assert track._is_drum_track() == ""


class TestGetProgramNames:
    def test_includes_program_name_for_piano(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        names = track._get_program_names()
        assert "0 - Acoustic Grand" in names

    def test_includes_none_for_events_before_program_change(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        # EndOfTrackEvent has no channel → program_name = "None"
        names = track._get_program_names()
        assert "None" in names

    def test_two_programs_both_present(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=two_program_track(), track_number=0, controller=mock_controller
        )
        names = track._get_program_names()
        assert "0 - Acoustic Grand" in names
        assert "25 - Acoustic Guitar (steel)" in names

    def test_returns_list(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert isinstance(track._get_program_names(), list)

    def test_no_duplicates(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        names = track._get_program_names()
        assert len(names) == len(set(names))


class TestGetFormattedTrackNumber:
    def test_zero_indexed_becomes_01(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert track._get_formatted_track_number(0) == "01"

    def test_single_digit_tracks_padded(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        for i in range(9):
            result = track._get_formatted_track_number(i)
            assert result == f"0{i + 1}"

    def test_double_digit_tracks_not_padded(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        for i in range(9, 99):
            result = track._get_formatted_track_number(i)
            assert result == str(i + 1)
            assert len(result) == 2

    def test_track_number_9_gives_10(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        assert track._get_formatted_track_number(9) == "10"


class TestExtractPrograms:
    def test_creates_pattern_for_each_non_none_program(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        # piano_track has program 0 ("0 - Acoustic Grand") plus "None" (EndOfTrack)
        non_none = [p for p in track.programs if p != "None"]
        assert len(track.patterns) == len(non_none)

    def test_pattern_names_match_programs(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        for program_name, pattern in track.patterns:
            assert isinstance(program_name, str)
            assert isinstance(pattern, midi.Pattern)

    def test_pattern_resolution_matches_controller(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        for _, pattern in track.patterns:
            assert pattern.resolution == mock_controller.resolution

    def test_two_programs_yield_two_patterns(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=two_program_track(), track_number=0, controller=mock_controller
        )
        program_names = {name for name, _ in track.patterns}
        assert "0 - Acoustic Grand" in program_names
        assert "25 - Acoustic Guitar (steel)" in program_names

    def test_note_on_for_other_program_muted(self, mock_controller):
        """NoteOnEvents not belonging to the current pattern's program have velocity 0."""
        track = Encapsulated_Midi_Track(
            events=two_program_track(), track_number=0, controller=mock_controller
        )
        for program_name, pattern in track.patterns:
            for midi_track in pattern:
                for event in midi_track:
                    if isinstance(event, midi.NoteOnEvent):
                        # Find what program this event belongs to in the original
                        for enc_event in track.events:
                            if (enc_event.event is event or
                                    (type(enc_event.event) == type(event) and
                                     enc_event.event.data == event.data and
                                     enc_event.program_name != program_name and
                                     enc_event.program_name != "None")):
                                assert event.data[1] == 0


class TestWrite:
    def test_creates_midi_files(self, mock_controller, tmp_path):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        track.write()
        files = list(os.listdir(mock_controller.midi_stem_path))
        assert len(files) == len(track.patterns)

    def test_filenames_contain_songname(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        track.write()
        files = os.listdir(mock_controller.midi_stem_path)
        for f in files:
            assert mock_controller.songname in f

    def test_filenames_contain_track_number(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=2, controller=mock_controller
        )
        track.write()
        files = os.listdir(mock_controller.midi_stem_path)
        for f in files:
            assert "03" in f

    def test_filenames_have_mid_extension(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        track.write()
        files = os.listdir(mock_controller.midi_stem_path)
        for f in files:
            assert f.endswith(".mid")

    def test_written_files_are_valid_midi(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=piano_track(), track_number=0, controller=mock_controller
        )
        track.write()
        for f in os.listdir(mock_controller.midi_stem_path):
            full = os.path.join(mock_controller.midi_stem_path, f)
            if os.path.isfile(full):
                reloaded = midi.read_midifile(full)
                assert isinstance(reloaded, midi.Pattern)


class TestGetPercussionInstruments:
    def test_empty_track_returns_empty(self):
        enc_events = []
        result = Encapsulated_Midi_Track.get_percussion_instruments(enc_events)
        assert result == []

    def test_no_note_on_events_returns_empty(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=no_program_track(), track_number=0, controller=mock_controller
        )
        result = Encapsulated_Midi_Track.get_percussion_instruments(track.events)
        assert result == []

    def test_drum_track_returns_instruments(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=drum_track(), track_number=0, controller=mock_controller
        )
        result = Encapsulated_Midi_Track.get_percussion_instruments(track.events)
        numbers = {pi.number for pi in result}
        assert 36 in numbers
        assert 38 in numbers

    def test_no_duplicates_in_result(self, mock_controller):
        """Same drum note appearing twice should only create one Percussion_Instrument."""
        t = midi.Track()
        pc = midi.ProgramChangeEvent(tick=0, channel=9)
        pc.data = [0]
        t.append(pc)
        for _ in range(3):
            kick = midi.NoteOnEvent(tick=0, channel=9)
            kick.data = [36, 100]
            t.append(kick)
        t.append(midi.EndOfTrackEvent(tick=1))

        track = Encapsulated_Midi_Track(
            events=t, track_number=0, controller=mock_controller
        )
        result = Encapsulated_Midi_Track.get_percussion_instruments(track.events)
        assert len(result) == 1

    def test_returns_percussion_instrument_objects(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=drum_track(), track_number=0, controller=mock_controller
        )
        result = Encapsulated_Midi_Track.get_percussion_instruments(track.events)
        for item in result:
            assert isinstance(item, Percussion_Instrument)


class TestExtractMidiDrumStems:
    def test_creates_subdirectory(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=drum_track(), track_number=0, controller=mock_controller
        )
        # extract_midi_drum_stems is called during __init__ via _is_drum_track
        drum_dir = os.path.join(
            mock_controller.midi_stem_path,
            f"{mock_controller.songname} - {track.track_number} - 0 - Drum Kit 0",
        )
        assert os.path.isdir(drum_dir)

    def test_creates_one_file_per_percussion_instrument(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=drum_track(), track_number=0, controller=mock_controller
        )
        drum_dir = os.path.join(
            mock_controller.midi_stem_path,
            f"{mock_controller.songname} - {track.track_number} - 0 - Drum Kit 0",
        )
        files = [f for f in os.listdir(drum_dir) if f.endswith(".mid")]
        assert len(files) == 2  # kick (36) and snare (38)

    def test_drum_stem_files_are_valid_midi(self, mock_controller):
        track = Encapsulated_Midi_Track(
            events=drum_track(), track_number=0, controller=mock_controller
        )
        drum_dir = os.path.join(
            mock_controller.midi_stem_path,
            f"{mock_controller.songname} - {track.track_number} - 0 - Drum Kit 0",
        )
        for f in os.listdir(drum_dir):
            full = os.path.join(drum_dir, f)
            reloaded = midi.read_midifile(full)
            assert isinstance(reloaded, midi.Pattern)
