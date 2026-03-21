"""
Tests for the wet/dry reverb stem feature.

Covers:
  - Encapsulated_Midi_Track._has_reverb()
  - Encapsulated_Midi_Track._make_dry_pattern()
  - Encapsulated_Midi_Track.write() reverb branching
"""
import os
import pytest
import midi
from copy import deepcopy

from encapsulated_midi_track import Encapsulated_Midi_Track, REVERB_CONTROLLER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pattern_with_cc(cc_number: int, cc_value: int, resolution: int = 480) -> midi.Pattern:
    """Single-track pattern containing one ControlChangeEvent."""
    pattern = midi.Pattern(resolution=resolution)
    track = midi.Track()
    pc = midi.ProgramChangeEvent(tick=0, channel=0)
    pc.data = [0]
    track.append(pc)
    cc = midi.ControlChangeEvent(tick=0, channel=0)
    cc.data = [cc_number, cc_value]
    track.append(cc)
    on = midi.NoteOnEvent(tick=0, channel=0)
    on.data = [60, 80]
    track.append(on)
    track.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(track)
    return pattern


def _make_pattern_no_cc(resolution: int = 480) -> midi.Pattern:
    """Single-track pattern with no ControlChangeEvents at all."""
    pattern = midi.Pattern(resolution=resolution)
    track = midi.Track()
    pc = midi.ProgramChangeEvent(tick=0, channel=0)
    pc.data = [0]
    track.append(pc)
    on = midi.NoteOnEvent(tick=0, channel=0)
    on.data = [60, 80]
    track.append(on)
    track.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(track)
    return pattern


# ---------------------------------------------------------------------------
# _has_reverb
# ---------------------------------------------------------------------------

class TestHasReverb:
    def test_returns_true_when_cc91_nonzero(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 64)
        assert Encapsulated_Midi_Track._has_reverb(pattern) is True

    def test_returns_true_for_value_1(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 1)
        assert Encapsulated_Midi_Track._has_reverb(pattern) is True

    def test_returns_true_for_max_value_127(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 127)
        assert Encapsulated_Midi_Track._has_reverb(pattern) is True

    def test_returns_false_when_cc91_is_zero(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 0)
        assert Encapsulated_Midi_Track._has_reverb(pattern) is False

    def test_returns_false_when_no_cc_events(self):
        pattern = _make_pattern_no_cc()
        assert Encapsulated_Midi_Track._has_reverb(pattern) is False

    def test_returns_false_for_empty_pattern(self):
        assert Encapsulated_Midi_Track._has_reverb(midi.Pattern()) is False

    def test_returns_false_for_different_cc_number(self):
        # CC 7 is volume — not reverb
        pattern = _make_pattern_with_cc(7, 100)
        assert Encapsulated_Midi_Track._has_reverb(pattern) is False

    def test_returns_true_when_cc91_on_second_track(self):
        pattern = midi.Pattern(resolution=480)
        # transport track — no CC events
        transport = midi.Track()
        transport.append(midi.SetTempoEvent(tick=0))
        transport.append(midi.EndOfTrackEvent(tick=1))
        pattern.append(transport)
        # instrument track with reverb
        pattern.append(_make_pattern_with_cc(REVERB_CONTROLLER, 40)[0])
        assert Encapsulated_Midi_Track._has_reverb(pattern) is True

    def test_returns_false_when_only_transport_track(self):
        pattern = midi.Pattern(resolution=480)
        transport = midi.Track()
        transport.append(midi.SetTempoEvent(tick=0))
        transport.append(midi.EndOfTrackEvent(tick=1))
        pattern.append(transport)
        assert Encapsulated_Midi_Track._has_reverb(pattern) is False


# ---------------------------------------------------------------------------
# _make_dry_pattern
# ---------------------------------------------------------------------------

class TestMakeDryPattern:
    def test_returns_midi_pattern(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 64)
        dry = Encapsulated_Midi_Track._make_dry_pattern(pattern)
        assert isinstance(dry, midi.Pattern)

    def test_original_pattern_not_mutated(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 64)
        Encapsulated_Midi_Track._make_dry_pattern(pattern)
        # Original CC 91 value must still be 64
        for track in pattern:
            for event in track:
                if type(event) == midi.ControlChangeEvent and event.data[0] == REVERB_CONTROLLER:
                    assert event.data[1] == 64

    def test_dry_pattern_cc91_zeroed(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 64)
        dry = Encapsulated_Midi_Track._make_dry_pattern(pattern)
        for track in dry:
            for event in track:
                if type(event) == midi.ControlChangeEvent and event.data[0] == REVERB_CONTROLLER:
                    assert event.data[1] == 0

    def test_dry_pattern_has_cc91_zero_prepended(self):
        """A CC 91 = 0 event must appear at the start of each instrument track."""
        pattern = _make_pattern_no_cc()
        dry = Encapsulated_Midi_Track._make_dry_pattern(pattern)
        for track in dry:
            # Skip meta-only tracks (no channel attribute)
            has_channel = any(hasattr(e, "channel") for e in track)
            if not has_channel:
                continue
            first_cc91 = next(
                (e for e in track
                 if type(e) == midi.ControlChangeEvent and e.data[0] == REVERB_CONTROLLER),
                None,
            )
            assert first_cc91 is not None
            assert first_cc91.data[1] == 0
            assert first_cc91.tick == 0

    def test_transport_track_not_modified(self):
        """The transport (no-channel) track must be left completely untouched."""
        pattern = midi.Pattern(resolution=480)
        transport = midi.Track()
        tempo = midi.SetTempoEvent(tick=0)
        tempo.set_bpm(120)
        transport.append(tempo)
        transport.append(midi.EndOfTrackEvent(tick=1))
        pattern.append(transport)
        instrument = _make_pattern_with_cc(REVERB_CONTROLLER, 64)[0]
        pattern.append(instrument)

        dry = Encapsulated_Midi_Track._make_dry_pattern(pattern)
        dry_transport = dry[0]
        # Transport events must be identical in count to the original
        assert len(dry_transport) == len(transport)

    def test_non_reverb_cc_events_preserved(self):
        """CC events for other controllers must be untouched in the dry copy."""
        pattern = midi.Pattern(resolution=480)
        track = midi.Track()
        pc = midi.ProgramChangeEvent(tick=0, channel=0)
        pc.data = [0]
        track.append(pc)
        cc_vol = midi.ControlChangeEvent(tick=0, channel=0)
        cc_vol.data = [7, 100]   # CC 7 = volume
        track.append(cc_vol)
        cc_rev = midi.ControlChangeEvent(tick=0, channel=0)
        cc_rev.data = [REVERB_CONTROLLER, 64]
        track.append(cc_rev)
        track.append(midi.EndOfTrackEvent(tick=1))
        pattern.append(track)

        dry = Encapsulated_Midi_Track._make_dry_pattern(pattern)
        vol_events = [
            e for t in dry for e in t
            if type(e) == midi.ControlChangeEvent and e.data[0] == 7
        ]
        assert len(vol_events) == 1
        assert vol_events[0].data[1] == 100

    def test_resolution_preserved(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 64, resolution=960)
        dry = Encapsulated_Midi_Track._make_dry_pattern(pattern)
        assert dry.resolution == 960

    def test_note_events_preserved(self):
        pattern = _make_pattern_with_cc(REVERB_CONTROLLER, 64)
        dry = Encapsulated_Midi_Track._make_dry_pattern(pattern)
        note_ons = [
            e for t in dry for e in t if type(e) == midi.NoteOnEvent
        ]
        assert len(note_ons) == 1
        assert note_ons[0].data == [60, 80]

    def test_multiple_cc91_events_all_zeroed(self):
        pattern = midi.Pattern(resolution=480)
        track = midi.Track()
        pc = midi.ProgramChangeEvent(tick=0, channel=0)
        pc.data = [0]
        track.append(pc)
        for val in [40, 80, 100]:
            cc = midi.ControlChangeEvent(tick=0, channel=0)
            cc.data = [REVERB_CONTROLLER, val]
            track.append(cc)
        track.append(midi.EndOfTrackEvent(tick=1))
        pattern.append(track)

        dry = Encapsulated_Midi_Track._make_dry_pattern(pattern)
        cc91_values = [
            e.data[1] for t in dry for e in t
            if type(e) == midi.ControlChangeEvent and e.data[0] == REVERB_CONTROLLER
        ]
        assert all(v == 0 for v in cc91_values)


# ---------------------------------------------------------------------------
# write() — reverb branching
# ---------------------------------------------------------------------------

class TestWriteReverbBranching:
    def test_wet_and_dry_files_created_when_reverb_present(
            self, reverb_midi_file, tmp_path, soundfont_path):
        from controller import Controller
        c = Controller(
            midi_file_path=reverb_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            base_path=str(tmp_path / "placeholder"),
        )
        c.extract_midi_stems()
        files = os.listdir(c.midi_stem_path)
        wet_files = [f for f in files if f.endswith("- wet.mid")]
        dry_files = [f for f in files if f.endswith("- dry.mid")]
        assert len(wet_files) >= 1
        assert len(dry_files) >= 1

    def test_wet_and_dry_count_match(
            self, reverb_midi_file, tmp_path, soundfont_path):
        from controller import Controller
        c = Controller(
            midi_file_path=reverb_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            base_path=str(tmp_path / "placeholder"),
        )
        c.extract_midi_stems()
        files = os.listdir(c.midi_stem_path)
        wet = [f for f in files if f.endswith("- wet.mid")]
        dry = [f for f in files if f.endswith("- dry.mid")]
        assert len(wet) == len(dry)

    def test_single_file_created_when_no_reverb(
            self, no_reverb_midi_file, tmp_path, soundfont_path):
        from controller import Controller
        c = Controller(
            midi_file_path=no_reverb_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            base_path=str(tmp_path / "placeholder"),
        )
        c.extract_midi_stems()
        files = os.listdir(c.midi_stem_path)
        mid_files = [f for f in files if f.endswith(".mid")]
        wet_files = [f for f in files if f.endswith("- wet.mid")]
        dry_files = [f for f in files if f.endswith("- dry.mid")]
        assert len(mid_files) >= 1
        assert len(wet_files) == 0
        assert len(dry_files) == 0

    def test_dry_file_has_cc91_zero(self, reverb_midi_file, tmp_path, soundfont_path):
        from controller import Controller
        c = Controller(
            midi_file_path=reverb_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            base_path=str(tmp_path / "placeholder"),
        )
        c.extract_midi_stems()
        dry_files = [
            f for f in os.listdir(c.midi_stem_path)
            if f.endswith("- dry.mid")
        ]
        assert dry_files, "No dry stem file found"
        for fname in dry_files:
            reloaded = midi.read_midifile(os.path.join(c.midi_stem_path, fname))
            for track in reloaded:
                for event in track:
                    if type(event) == midi.ControlChangeEvent and event.data[0] == REVERB_CONTROLLER:
                        assert event.data[1] == 0, f"CC 91 not zeroed in dry stem: {fname}"

    def test_wet_file_preserves_cc91(self, reverb_midi_file, tmp_path, soundfont_path):
        from controller import Controller
        c = Controller(
            midi_file_path=reverb_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            base_path=str(tmp_path / "placeholder"),
        )
        c.extract_midi_stems()
        wet_files = [
            f for f in os.listdir(c.midi_stem_path)
            if f.endswith("- wet.mid")
        ]
        assert wet_files, "No wet stem file found"
        for fname in wet_files:
            reloaded = midi.read_midifile(os.path.join(c.midi_stem_path, fname))
            cc91_values = [
                event.data[1] for track in reloaded for event in track
                if type(event) == midi.ControlChangeEvent and event.data[0] == REVERB_CONTROLLER
            ]
            assert any(v > 0 for v in cc91_values), \
                f"Expected non-zero CC 91 in wet stem: {fname}"

    def test_wet_and_dry_are_valid_midi(self, reverb_midi_file, tmp_path, soundfont_path):
        from controller import Controller
        c = Controller(
            midi_file_path=reverb_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            base_path=str(tmp_path / "placeholder"),
        )
        c.extract_midi_stems()
        for fname in os.listdir(c.midi_stem_path):
            full = os.path.join(c.midi_stem_path, fname)
            if os.path.isfile(full) and fname.endswith(".mid"):
                assert isinstance(midi.read_midifile(full), midi.Pattern)

    def test_simple_track_unchanged_filename_without_reverb(
            self, simple_midi_file, tmp_path, soundfont_path):
        """The existing simple fixture has no CC 91 — filenames must not have wet/dry."""
        from controller import Controller
        c = Controller(
            midi_file_path=simple_midi_file,
            soundfont_path=soundfont_path,
            convert_to_wav=False,
            base_path=str(tmp_path / "placeholder"),
        )
        c.extract_midi_stems()
        files = os.listdir(c.midi_stem_path)
        assert not any("wet" in f or "dry" in f for f in files)
