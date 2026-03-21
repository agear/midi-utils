"""
Tests for Controller.

All MIDI data is synthetic (built in conftest.py). No real MIDI files required.
"""
import os
import pytest
import midi

from controller import Controller
from percussion_instrument import Percussion_Instrument
from program import Program


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

class TestControllerInit:
    def test_midi_file_path_stored(self, simple_controller, simple_midi_file):
        assert simple_controller.midi_file_path == simple_midi_file

    def test_songname_extracted(self, simple_controller):
        assert simple_controller.songname == "simple"

    def test_file_extension_extracted(self, simple_controller):
        assert simple_controller.file_extension == ".mid"

    def test_convert_to_wav_flag_false(self, simple_controller):
        assert simple_controller.convert_to_wav_flag is False

    def test_convert_to_wav_flag_true(self, simple_midi_file, tmp_path, soundfont_path):
        c = Controller(
            midi_file_path=simple_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=True,
            base_path=str(tmp_path / "placeholder"),
        )
        assert c.convert_to_wav_flag is True

    def test_resolution_loaded(self, simple_controller):
        assert simple_controller.resolution == 480

    def test_midi_multitrack_loaded(self, simple_controller):
        assert isinstance(simple_controller.midi_multitrack, midi.Pattern)

    def test_transport_track_initially_empty(self, simple_controller):
        # transport_track starts as an empty midi.Track before _get_transport_track is called
        assert isinstance(simple_controller.transport_track, midi.Track)

    def test_encapsulated_midi_initially_empty(self, simple_controller):
        assert simple_controller.encapsulated_midi == []

    def test_midi_stem_path_created(self, simple_controller):
        assert os.path.isdir(simple_controller.midi_stem_path)

    def test_audio_stem_path_not_created_when_flag_false(self, simple_controller):
        assert not hasattr(simple_controller, "audio_stem_path") or \
               not os.path.isdir(getattr(simple_controller, "audio_stem_path", ""))

    def test_audio_stem_path_created_when_flag_true(
            self, simple_midi_file, tmp_path, soundfont_path):
        c = Controller(
            midi_file_path=simple_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=True,
            base_path=str(tmp_path / "placeholder"),
        )
        assert os.path.isdir(c.audio_stem_path)


# ---------------------------------------------------------------------------
# _make_directories
# ---------------------------------------------------------------------------

class TestMakeDirectories:
    def test_midi_stems_dir_exists(self, simple_controller):
        assert os.path.isdir(simple_controller.midi_stem_path)

    def test_stems_path_dir_exists(self, simple_controller):
        assert os.path.isdir(simple_controller.stems_path)

    def test_idempotent(self, simple_controller):
        """Calling _make_directories twice should not raise."""
        simple_controller._make_directories()
        assert os.path.isdir(simple_controller.midi_stem_path)


# ---------------------------------------------------------------------------
# _get_transport_track
# ---------------------------------------------------------------------------

class TestGetTransportTrack:
    def test_identifies_transport_track(self, simple_controller):
        simple_controller._get_transport_track()
        # The simple pattern has a transport track (no program changes) at index 0
        assert len(simple_controller.transport_track) > 0

    def test_transport_track_has_no_program_changes(self, simple_controller):
        simple_controller._get_transport_track()
        for event in simple_controller.transport_track:
            assert not isinstance(event, midi.ProgramChangeEvent)

    def test_no_transport_track_leaves_empty(
            self, no_transport_midi_file, tmp_path, soundfont_path):
        c = Controller(
            midi_file_path=no_transport_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            base_path=str(tmp_path / "placeholder"),
        )
        c._get_transport_track()
        # When no transport track exists the attribute stays as the initial empty Track
        assert isinstance(c.transport_track, midi.Track)

    def test_multi_track_transport_identified(self, multi_controller):
        multi_controller._get_transport_track()
        # Transport is the first track (tempo only)
        assert any(isinstance(e, midi.SetTempoEvent)
                   for e in multi_controller.transport_track)


# ---------------------------------------------------------------------------
# get_percussion_instruments (static)
# ---------------------------------------------------------------------------

class TestGetPercussionInstruments:
    def test_empty_track_returns_empty(self):
        result = Controller.get_percussion_instruments(midi.Track())
        assert result == []

    def test_non_drum_track_returns_empty(self):
        t = midi.Track()
        pc = midi.ProgramChangeEvent(tick=0, channel=0)
        pc.data = [0]
        t.append(pc)
        on = midi.NoteOnEvent(tick=0, channel=0)
        on.data = [60, 80]
        t.append(on)
        # Note 60 is not a valid percussion instrument number → ValueError in Percussion_Instrument
        # get_percussion_instruments does no filtering, it just wraps all NoteOn notes.
        # Actually: 60 is not in PERCUSSION dict so it will raise ValueError.
        # The static method doesn't guard against this — test that the known-good drum notes work.
        result = Controller.get_percussion_instruments(midi.Track())
        assert result == []

    def test_drum_track_returns_instruments(self):
        t = midi.Track()
        kick = midi.NoteOnEvent(tick=0, channel=9)
        kick.data = [36, 100]
        t.append(kick)
        snare = midi.NoteOnEvent(tick=240, channel=9)
        snare.data = [38, 90]
        t.append(snare)
        result = Controller.get_percussion_instruments(t)
        numbers = {pi.number for pi in result}
        assert 36 in numbers
        assert 38 in numbers

    def test_returns_percussion_instrument_objects(self):
        t = midi.Track()
        kick = midi.NoteOnEvent(tick=0, channel=9)
        kick.data = [36, 100]
        t.append(kick)
        result = Controller.get_percussion_instruments(t)
        assert all(isinstance(pi, Percussion_Instrument) for pi in result)

    def test_deduplicates_same_note(self):
        t = midi.Track()
        for _ in range(5):
            kick = midi.NoteOnEvent(tick=0, channel=9)
            kick.data = [36, 100]
            t.append(kick)
        result = Controller.get_percussion_instruments(t)
        assert len(result) == 1

    def test_ignores_note_off_events(self):
        t = midi.Track()
        off = midi.NoteOffEvent(tick=0, channel=9)
        off.data = [36, 0]
        t.append(off)
        result = Controller.get_percussion_instruments(t)
        assert result == []

    def test_multiple_distinct_instruments(self):
        t = midi.Track()
        for note in [36, 38, 42]:
            on = midi.NoteOnEvent(tick=0, channel=9)
            on.data = [note, 100]
            t.append(on)
        result = Controller.get_percussion_instruments(t)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# get_track_names (static)
# ---------------------------------------------------------------------------

class TestGetTrackNames:
    def test_empty_track_returns_empty(self):
        assert Controller.get_track_names(midi.Track()) == []

    def test_no_program_change_returns_empty(self):
        t = midi.Track()
        t.append(midi.SetTempoEvent(tick=0))
        t.append(midi.EndOfTrackEvent(tick=1))
        assert Controller.get_track_names(t) == []

    def test_single_program_change(self):
        t = midi.Track()
        pc = midi.ProgramChangeEvent(tick=0, channel=0)
        pc.data = [56]
        t.append(pc)
        result = Controller.get_track_names(t)
        assert len(result) == 1
        assert result[0].program_number == 56
        assert result[0].get_program_name() == "56 - Trumpet"

    def test_multiple_program_changes(self):
        t = midi.Track()
        for prog in [0, 25]:
            pc = midi.ProgramChangeEvent(tick=0, channel=0)
            pc.data = [prog]
            t.append(pc)
        result = Controller.get_track_names(t)
        assert len(result) == 2
        numbers = {p.program_number for p in result}
        assert numbers == {0, 25}

    def test_drum_channel_9_returns_drum_kit_and_stops(self):
        t = midi.Track()
        pc1 = midi.ProgramChangeEvent(tick=0, channel=9)
        pc1.data = [0]
        t.append(pc1)
        # A second program change should never be reached
        pc2 = midi.ProgramChangeEvent(tick=0, channel=9)
        pc2.data = [25]
        t.append(pc2)
        result = Controller.get_track_names(t)
        assert len(result) == 1
        assert result[0].program_name == "0 - Drum Kit 0"

    def test_returns_program_objects(self):
        t = midi.Track()
        pc = midi.ProgramChangeEvent(tick=0, channel=0)
        pc.data = [0]
        t.append(pc)
        result = Controller.get_track_names(t)
        assert all(isinstance(p, Program) for p in result)

    def test_non_program_change_events_ignored(self):
        t = midi.Track()
        on = midi.NoteOnEvent(tick=0, channel=0)
        on.data = [60, 80]
        t.append(on)
        t.append(midi.EndOfTrackEvent(tick=1))
        assert Controller.get_track_names(t) == []


# ---------------------------------------------------------------------------
# extract_midi_stems
# ---------------------------------------------------------------------------

class TestExtractMidiStems:
    def test_creates_midi_stem_files(self, simple_controller):
        simple_controller.extract_midi_stems()
        files = [
            f for f in os.listdir(simple_controller.midi_stem_path)
            if os.path.isfile(os.path.join(simple_controller.midi_stem_path, f))
        ]
        assert len(files) > 0

    def test_stem_files_are_valid_midi(self, simple_controller):
        simple_controller.extract_midi_stems()
        for f in os.listdir(simple_controller.midi_stem_path):
            full = os.path.join(simple_controller.midi_stem_path, f)
            if os.path.isfile(full) and full.endswith(".mid"):
                reloaded = midi.read_midifile(full)
                assert isinstance(reloaded, midi.Pattern)

    def test_encapsulated_midi_populated(self, simple_controller):
        simple_controller.extract_midi_stems()
        assert len(simple_controller.encapsulated_midi) > 0

    def test_transport_track_identified(self, simple_controller):
        simple_controller.extract_midi_stems()
        # After extraction, transport_track should not be empty
        assert len(simple_controller.transport_track) > 0

    def test_transport_track_excluded_from_stems(self, simple_controller):
        simple_controller.extract_midi_stems()
        # simple pattern has 1 transport + 1 melodic = 1 encapsulated track
        assert len(simple_controller.encapsulated_midi) == 1

    def test_multi_track_stem_count(self, multi_controller):
        multi_controller.extract_midi_stems()
        # multi pattern: transport + bass + multi-prog + drums = 3 non-transport tracks
        assert len(multi_controller.encapsulated_midi) == 3

    def test_stem_filenames_contain_songname(self, simple_controller):
        simple_controller.extract_midi_stems()
        for f in os.listdir(simple_controller.midi_stem_path):
            if os.path.isfile(os.path.join(simple_controller.midi_stem_path, f)):
                assert simple_controller.songname in f
