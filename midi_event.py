import midi

from programs import PROGRAMS, PERCUSSION

class Midi_Event:
    def __init__(self, event, program_number):
        self.event: midi.Event = event
        self.program_number: int = program_number
        if program_number == None or type(event) == midi.EndOfTrackEvent:
            self.program_name = "None"
        elif event.channel == 9:
            self.program_name = "0 - Drum Kit 0 "
        else:
            self.program_name = PROGRAMS[self.program_number]

    def __str__(self):
        return f"\n\n\n\n***MIDI_EVENT***\nProgram number: {self.program_number}\nProgram name: {self.program_name}\nEvent: {self.event}\n****************"

    def __repr__(self):
        return f"\n\n\n\n***MIDI_EVENT***\nProgram number: {self.program_number}\nProgram name: {self.program_name}\nEvent: {self.event}\n****************"
