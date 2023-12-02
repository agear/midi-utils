
# Generated by CodiumAI

import pytest
import midi
from encapsulated_midi_event import Encapsulated_Midi_Event
from programs import PROGRAMS

class TestMidiEvent:

    #  Midi_Event can be initialized with a midi event and program number
    def test_initialized_with_event_and_program_number(self):
        event = midi.Event()
        program_number = 1

        midi_event = Encapsulated_Midi_Event(event, program_number)

        assert midi_event.event == event
        assert midi_event.program_number == program_number

    #  Midi_Event can determine the program name based on the program number
    def test_determine_program_name_based_on_program_number(self):
        event = midi.Event()
        event.channel = 2
        program_number = 1

        midi_event = Encapsulated_Midi_Event(event, program_number)

        assert midi_event.program_name == PROGRAMS[program_number]

    #  Midi_Event can determine if the event channel is the drum channel
    def test_drum_channel(self):
        event = midi.Event()
        event.channel = 9
        program_number = 1

        midi_event = Encapsulated_Midi_Event(event, program_number)

        assert midi_event.program_name == "0 - Drum Kit 0"

    #  Midi_Event can determine the program name as "None" for certain event types
    def test_determine_program_name_as_none_for_certain_event_types(self):
        event = midi.EndOfTrackEvent()
        program_number = 1

        midi_event = Encapsulated_Midi_Event(event, program_number)

        assert midi_event.program_name == "None"

    #  Midi_Event can handle initialization with a None program number
    def test_handle_initialization_with_none_program_number(self):
        event = midi.Event()
        program_number = None

        midi_event = Encapsulated_Midi_Event(event, program_number)

        assert midi_event.program_name == "None"

    #  Midi_Event can handle initialization with an EndOfTrackEvent
    def test_handle_initialization_with_end_of_track_event(self):
        event = midi.EndOfTrackEvent()
        program_number = 1

        midi_event = Encapsulated_Midi_Event(event, program_number)

        assert midi_event.program_name == "None"

    #  Midi_Event can handle initialization with a TimeSignatureEvent
    def test_handle_initialization_with_time_signature_event(self):
        event = midi.TimeSignatureEvent()
        program_number = 1

        midi_event = Encapsulated_Midi_Event(event, program_number)

        assert midi_event.program_name == "None"

    #  Midi_Event Program Number and name default to None if Program number is not between 0 and 127
    def test_program_number_out_of_bounds(self):
        midi_event = Encapsulated_Midi_Event(midi.Event(), program_number=-5)

        assert midi_event.program_number == None
        assert midi_event.program_name == "None"

        midi_event = Encapsulated_Midi_Event(midi.Event(), program_number=-1)

        assert midi_event.program_number == None
        assert midi_event.program_name == "None"

        midi_event = Encapsulated_Midi_Event(midi.Event(), program_number=128)

        assert midi_event.program_number == None
        assert midi_event.program_name == "None"

    def test_raises_type_error(self):
        with pytest.raises(TypeError):
            Encapsulated_Midi_Event("midi_event", 35)


        with pytest.raises(TypeError):
            Encapsulated_Midi_Event({}, 35)

    #  Midi_Event produces str and repr
    def test_str_and_repr(self):
        event = midi.Event()
        program_number = 1

        midi_event = Encapsulated_Midi_Event(event, program_number)

        assert str(midi_event) == f"\n\n\n\n***MIDI_EVENT***\nProgram number: {program_number}\nProgram name: 1 - Bright Acoustic\nEvent: {event}\n****************"
        assert repr(midi_event) == f"\n\n\n\n***MIDI_EVENT***\nProgram number: {program_number}\nProgram name: 1 - Bright Acoustic\nEvent: {event}\n****************"
