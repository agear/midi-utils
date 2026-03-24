"""
Shared fixtures for the midi-utils test suite.

All MIDI data is created programmatically — no external test files required.
The bundled soundfont is used for tests that instantiate Controller.
"""
import os
import pytest
import midi

SOUNDFONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "soundfonts", "gm.sf2"
)


# ---------------------------------------------------------------------------
# MIDI pattern factories
# ---------------------------------------------------------------------------

def make_simple_pattern():
    """Transport track + one piano (program 0) track."""
    pattern = midi.Pattern(resolution=480)

    # Track 0 – transport (tempo only, no program change)
    transport = midi.Track()
    tempo = midi.SetTempoEvent(tick=0)
    tempo.set_bpm(120)
    transport.append(tempo)
    transport.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(transport)

    # Track 1 – Acoustic Grand Piano (program 0)
    piano = midi.Track()
    pc = midi.ProgramChangeEvent(tick=0, channel=0)
    pc.data = [0]
    piano.append(pc)
    on = midi.NoteOnEvent(tick=0, channel=0)
    on.data = [60, 80]
    piano.append(on)
    off = midi.NoteOffEvent(tick=480, channel=0)
    off.data = [60, 0]
    piano.append(off)
    piano.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(piano)

    return pattern


def make_multi_track_pattern():
    """
    Transport track + bass track + multi-program track + drum track.
    Used for richer integration tests.
    """
    pattern = midi.Pattern(resolution=480)

    # Track 0 – transport
    transport = midi.Track()
    tempo = midi.SetTempoEvent(tick=0)
    tempo.set_bpm(120)
    transport.append(tempo)
    transport.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(transport)

    # Track 1 – Acoustic Bass (program 32), channel 0
    bass = midi.Track()
    pc = midi.ProgramChangeEvent(tick=0, channel=0)
    pc.data = [32]
    bass.append(pc)
    on = midi.NoteOnEvent(tick=0, channel=0)
    on.data = [40, 70]
    bass.append(on)
    off = midi.NoteOffEvent(tick=480, channel=0)
    off.data = [40, 0]
    bass.append(off)
    bass.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(bass)

    # Track 2 – switches from Acoustic Grand (0) to Acoustic Guitar Steel (25)
    multi = midi.Track()
    pc1 = midi.ProgramChangeEvent(tick=0, channel=1)
    pc1.data = [0]
    multi.append(pc1)
    on1 = midi.NoteOnEvent(tick=0, channel=1)
    on1.data = [60, 80]
    multi.append(on1)
    pc2 = midi.ProgramChangeEvent(tick=240, channel=1)
    pc2.data = [25]
    multi.append(pc2)
    on2 = midi.NoteOnEvent(tick=0, channel=1)
    on2.data = [62, 80]
    multi.append(on2)
    multi.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(multi)

    # Track 3 – drums (channel 9): kick (36) and snare (38)
    drums = midi.Track()
    drum_pc = midi.ProgramChangeEvent(tick=0, channel=9)
    drum_pc.data = [0]
    drums.append(drum_pc)
    kick = midi.NoteOnEvent(tick=0, channel=9)
    kick.data = [36, 100]
    drums.append(kick)
    snare = midi.NoteOnEvent(tick=240, channel=9)
    snare.data = [38, 90]
    drums.append(snare)
    drums.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(drums)

    return pattern


def make_reverb_pattern(reverb_value: int = 64):
    """
    Simple pattern whose instrument track contains a CC 91 (reverb) event.
    reverb_value=0 produces a pattern that _has_reverb() should return False for.
    """
    pattern = midi.Pattern(resolution=480)

    # Track 0: transport
    transport = midi.Track()
    tempo = midi.SetTempoEvent(tick=0)
    tempo.set_bpm(120)
    transport.append(tempo)
    transport.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(transport)

    # Track 1: piano with CC 91 reverb
    piano = midi.Track()
    pc = midi.ProgramChangeEvent(tick=0, channel=0)
    pc.data = [0]
    piano.append(pc)
    cc_reverb = midi.ControlChangeEvent(tick=0, channel=0)
    cc_reverb.data = [91, reverb_value]
    piano.append(cc_reverb)
    on = midi.NoteOnEvent(tick=0, channel=0)
    on.data = [60, 80]
    piano.append(on)
    off = midi.NoteOffEvent(tick=480, channel=0)
    off.data = [60, 0]
    piano.append(off)
    piano.append(midi.EndOfTrackEvent(tick=1))
    pattern.append(piano)

    return pattern


def make_no_transport_pattern():
    """All tracks have program changes — no dedicated transport track."""
    pattern = midi.Pattern(resolution=480)
    for ch in range(2):
        track = midi.Track()
        pc = midi.ProgramChangeEvent(tick=0, channel=ch)
        pc.data = [ch]
        track.append(pc)
        on = midi.NoteOnEvent(tick=0, channel=ch)
        on.data = [60, 80]
        track.append(on)
        track.append(midi.EndOfTrackEvent(tick=1))
        pattern.append(track)
    return pattern


# ---------------------------------------------------------------------------
# File fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def soundfont_path():
    return SOUNDFONT_PATH


@pytest.fixture
def simple_midi_file(tmp_path):
    path = str(tmp_path / "simple.mid")
    midi.write_midifile(path, make_simple_pattern())
    return path


@pytest.fixture
def multi_track_midi_file(tmp_path):
    path = str(tmp_path / "multi.mid")
    midi.write_midifile(path, make_multi_track_pattern())
    return path


@pytest.fixture
def reverb_midi_file(tmp_path):
    path = str(tmp_path / "reverb.mid")
    midi.write_midifile(path, make_reverb_pattern(reverb_value=64))
    return path


@pytest.fixture
def no_reverb_midi_file(tmp_path):
    """Same structure as reverb_midi_file but CC 91 = 0 (no reverb)."""
    path = str(tmp_path / "no_reverb.mid")
    midi.write_midifile(path, make_reverb_pattern(reverb_value=0))
    return path


@pytest.fixture
def no_transport_midi_file(tmp_path):
    path = str(tmp_path / "notransport.mid")
    midi.write_midifile(path, make_no_transport_pattern())
    return path


# ---------------------------------------------------------------------------
# Controller fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_controller(simple_midi_file, tmp_path, soundfont_path):
    from controller import Controller
    return Controller(
        midi_file_path=simple_midi_file,
        soundfont_path=soundfont_path,
        convert_to_wav=False,
        output_path=str(tmp_path / "placeholder"),
    )


@pytest.fixture
def multi_controller(multi_track_midi_file, tmp_path, soundfont_path):
    from controller import Controller
    return Controller(
        midi_file_path=multi_track_midi_file,
        soundfont_path=soundfont_path,
        convert_to_wav=False,
        output_path=str(tmp_path / "placeholder"),
    )


# ---------------------------------------------------------------------------
# Minimal mock Controller for unit-testing Encapsulated_Midi_Track in isolation
# ---------------------------------------------------------------------------

class MockController:
    """Minimal stand-in for Controller used by Encapsulated_Midi_Track.__init__."""
    def __init__(self, midi_stem_path, songname, resolution=480, transport_track=None):
        self.midi_stem_path = midi_stem_path
        self.songname = songname
        self.resolution = resolution
        self.transport_track = transport_track if transport_track is not None else midi.Track()


@pytest.fixture
def mock_controller(tmp_path):
    stem_path = str(tmp_path / "midi_stems")
    os.makedirs(stem_path, exist_ok=True)
    return MockController(midi_stem_path=stem_path, songname="test_song")
