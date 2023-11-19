import midi

from programs import PROGRAMS, PERCUSSION

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

    ALLOWED_EVENT_TYPES = (midi.NoteOnEvent, midi.NoteOffEvent, midi.ControlChangeEvent, midi.Event)
    def __init__(self, event: midi.Event, program_number: Optional[int]):
        if program_number is not None and not(0 <= program_number <= 127):
            raise ValueError("Invalid program number")
        if not isinstance(event, midi.Event):
            raise TypeError("event must be an instance of midi.Event or a subclass thereof")
        self.event: midi.Event = event
        self.program_number: int = program_number
        if program_number is None or type(event) == midi.EndOfTrackEvent or type(event) == midi.TimeSignatureEvent or type(event) == midi.SetTempoEvent:
            self.program_name = "None"
        elif event.channel == 9:
            self.program_name = "0 - Drum Kit 0 "
        else:
            self.program_name = PROGRAMS[self.program_number]

    def __str__(self):
        return f"\n\n\n\n***MIDI_EVENT***\nProgram number: {self.program_number}\nProgram name: {self.program_name}\nEvent: {self.event}\n****************"

    def __repr__(self):
        return f"\n\n\n\n***MIDI_EVENT***\nProgram number: {self.program_number}\nProgram name: {self.program_name}\nEvent: {self.event}\n****************"
