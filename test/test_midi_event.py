import pytest
import midi
from encapsulated_midi_event import Encapsulated_Midi_Event
from programs import PROGRAMS


class TestEncapsulatedMidiEventInit:
    def test_stores_event_and_program_number(self):
        event = midi.NoteOnEvent()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 1)
        assert me.event is event
        assert me.program_number == 1

    def test_program_number_none(self):
        me = Encapsulated_Midi_Event(midi.Event(), None)
        assert me.program_number is None
        assert me.program_name == "None"

    def test_program_number_zero(self):
        event = midi.Event()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 0)
        assert me.program_number == 0
        assert me.program_name == PROGRAMS[0]

    def test_program_number_127(self):
        event = midi.Event()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 127)
        assert me.program_number == 127
        assert me.program_name == PROGRAMS[127]

    def test_out_of_range_negative_becomes_none(self):
        me = Encapsulated_Midi_Event(midi.Event(), -1)
        assert me.program_number is None
        assert me.program_name == "None"

    def test_out_of_range_negative_large(self):
        me = Encapsulated_Midi_Event(midi.Event(), -5)
        assert me.program_number is None
        assert me.program_name == "None"

    def test_out_of_range_128_becomes_none(self):
        me = Encapsulated_Midi_Event(midi.Event(), 128)
        assert me.program_number is None
        assert me.program_name == "None"

    def test_out_of_range_large_becomes_none(self):
        me = Encapsulated_Midi_Event(midi.Event(), 999)
        assert me.program_number is None
        assert me.program_name == "None"

    def test_type_error_for_string_event(self):
        with pytest.raises(TypeError):
            Encapsulated_Midi_Event("not_an_event", 1)

    def test_type_error_for_dict_event(self):
        with pytest.raises(TypeError):
            Encapsulated_Midi_Event({}, 1)

    def test_type_error_for_int_event(self):
        with pytest.raises(TypeError):
            Encapsulated_Midi_Event(42, 1)

    def test_type_error_for_none_event(self):
        with pytest.raises(TypeError):
            Encapsulated_Midi_Event(None, 1)


class TestGetProgramName:
    def test_none_program_number_returns_none_string(self):
        me = Encapsulated_Midi_Event(midi.Event(), None)
        assert me.program_name == "None"

    def test_drum_channel_9_returns_drum_kit(self):
        event = midi.Event()
        event.channel = 9
        me = Encapsulated_Midi_Event(event, 1)
        assert me.program_name == "0 - Drum Kit 0"

    def test_non_drum_channel_returns_program_name(self):
        event = midi.Event()
        event.channel = 2
        me = Encapsulated_Midi_Event(event, 1)
        assert me.program_name == PROGRAMS[1]

    def test_channel_0_returns_correct_name(self):
        event = midi.NoteOnEvent()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 56)
        assert me.program_name == "56 - Trumpet"

    def test_end_of_track_event_has_no_channel_returns_none(self):
        me = Encapsulated_Midi_Event(midi.EndOfTrackEvent(), 1)
        assert me.program_name == "None"

    def test_set_tempo_event_returns_none(self):
        me = Encapsulated_Midi_Event(midi.SetTempoEvent(), 5)
        assert me.program_name == "None"

    def test_time_signature_event_returns_none(self):
        me = Encapsulated_Midi_Event(midi.TimeSignatureEvent(), 1)
        assert me.program_name == "None"

    def test_key_signature_event_returns_none(self):
        me = Encapsulated_Midi_Event(midi.KeySignatureEvent(), 1)
        assert me.program_name == "None"

    def test_track_name_event_returns_none(self):
        me = Encapsulated_Midi_Event(midi.TrackNameEvent(), 1)
        assert me.program_name == "None"

    def test_all_valid_programs_on_non_drum_channel(self):
        for prog in range(128):
            event = midi.Event()
            event.channel = 0
            me = Encapsulated_Midi_Event(event, prog)
            assert me.program_name == PROGRAMS[prog]

    def test_program_change_event_non_drum(self):
        event = midi.ProgramChangeEvent()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 32)
        assert me.program_name == PROGRAMS[32]

    def test_note_on_event_drum_channel(self):
        event = midi.NoteOnEvent()
        event.channel = 9
        me = Encapsulated_Midi_Event(event, 0)
        assert me.program_name == "0 - Drum Kit 0"


class TestEncapsulatedMidiEventAllowedTypes:
    """Verify every type in ALLOWED_EVENT_TYPES can be instantiated."""

    def test_abstract_event(self):
        me = Encapsulated_Midi_Event(midi.AbstractEvent(), None)
        assert me.program_name == "None"

    def test_base_event(self):
        me = Encapsulated_Midi_Event(midi.Event(), None)
        assert me.program_name == "None"

    def test_meta_event(self):
        me = Encapsulated_Midi_Event(midi.MetaEvent(), None)
        assert me.program_name == "None"

    def test_note_on_event(self):
        event = midi.NoteOnEvent()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 0)
        assert me.event is event

    def test_note_off_event(self):
        event = midi.NoteOffEvent()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 0)
        assert me.event is event

    def test_control_change_event(self):
        event = midi.ControlChangeEvent()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 0)
        assert me.event is event

    def test_pitch_wheel_event(self):
        event = midi.PitchWheelEvent()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 0)
        assert me.event is event

    def test_sysex_event(self):
        me = Encapsulated_Midi_Event(midi.SysexEvent(), None)
        assert me.program_name == "None"

    def test_end_of_track_event(self):
        me = Encapsulated_Midi_Event(midi.EndOfTrackEvent(), 1)
        assert me.program_name == "None"

    def test_sequence_number_meta_event(self):
        me = Encapsulated_Midi_Event(midi.SequenceNumberMetaEvent(), None)
        assert me.program_name == "None"

    def test_text_meta_event(self):
        me = Encapsulated_Midi_Event(midi.TextMetaEvent(), None)
        assert me.program_name == "None"


class TestEncapsulatedMidiEventStrRepr:
    def test_str_contains_program_number(self):
        event = midi.Event()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 1)
        assert "1" in str(me)

    def test_str_contains_program_name(self):
        event = midi.Event()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 1)
        assert "1 - Bright Acoustic" in str(me)

    def test_repr_equals_str(self):
        event = midi.Event()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 1)
        assert str(me) == repr(me)

    def test_str_exact_format(self):
        event = midi.Event()
        event.channel = 0
        me = Encapsulated_Midi_Event(event, 1)
        expected = (
            f"\n\n\n\n***MIDI_EVENT***\n"
            f"Program number: 1\n"
            f"Program name: 1 - Bright Acoustic\n"
            f"Event: {event}\n"
            f"****************"
        )
        assert str(me) == expected

    def test_str_with_none_program(self):
        me = Encapsulated_Midi_Event(midi.Event(), None)
        assert "None" in str(me)
