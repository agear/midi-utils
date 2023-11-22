import midi

from programs import PROGRAMS, PERCUSSION
from typing import Optional


class Midi_Event:
    """
        The Midi_Event class represents a MIDI event and its associated program number and program name.

        Example Usage
        event = midi.Event()
        program_number = 1
        midi_event = Midi_Event(event, program_number)
        print(midi_event.program_number)  # Output: 1
        print(midi_event.program_name)  # Output: "1 - Bright Acoustic"
        print(midi_event.event)  # Output: <midi.Event object at 0x000001>

        Main functionalities
        The Midi_Event class initializes a MIDI event object and assigns it a program number and program name.
        The program number is used to determine the program name based on a predefined dictionary of program names.
        The program name is set to "None" if the program number is None or if the event is an end of track event,
        time signature event, or set tempo event.
        If the event's channel is 9, indicating a percussion instrument, the program name is set to "0 - Drum Kit 0".
    """
    ALLOWED_EVENT_TYPES = (midi.AbstractEvent,
                            midi.Event,
                            midi.MetaEvent,
                            midi.NoteEvent,
                            midi.NoteOnEvent,
                            midi.NoteOffEvent,
                            midi.AfterTouchEvent,
                            midi.ControlChangeEvent,
                            midi.ProgramChangeEvent,
                            midi.ChannelAfterTouchEvent,
                            midi.PitchWheelEvent,
                            midi.SysexEvent,
                            midi.SequenceNumberMetaEvent,
                            midi.MetaEventWithText,
                            midi.TextMetaEvent,
                            midi.CopyrightMetaEvent,
                            midi.TrackNameEvent,
                            midi.InstrumentNameEvent,
                            midi.LyricsEvent,
                            midi.MarkerEvent,
                            midi.CuePointEvent,
                            midi.ProgramNameEvent,
                            midi.ChannelPrefixEvent,
                            midi.PortEvent,
                            midi.TrackLoopEvent,
                            midi.EndOfTrackEvent,
                            midi.SetTempoEvent,
                            midi.SmpteOffsetEvent,
                            midi.TimeSignatureEvent,
                            midi.KeySignatureEvent,
                            midi.SequencerSpecificEvent,
                           )

    def __init__(self, event: midi.Event, program_number: Optional[int]):
        if program_number is not None:
            if not(0 <= program_number <= 127):
                program_number = None
        if not isinstance(event, Midi_Event.ALLOWED_EVENT_TYPES):
            raise TypeError("event must be an instance of midi.Event or a subclass thereof")
        self.event: midi.Event = event
        self.program_number: Optional[int] = program_number
        self.program_name: str = self._get_program_name()


    def _get_program_name(self):
        if self.program_number is None:
            return "None"

        try:
            if self.event.channel == 9:
                return "0 - Drum Kit 0"
            return PROGRAMS[self.program_number]
        except AttributeError:
            return "None"

    def _generate_string(self):
        return f"\n\n\n\n***MIDI_EVENT***\nProgram number: {self.program_number}\nProgram name: {self.program_name}\nEvent: {self.event}\n****************"

    def __str__(self):
        return self._generate_string()

    def __repr__(self):
        return self._generate_string()
