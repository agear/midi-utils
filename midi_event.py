from programs import PROGRAMS, PERCUSSION

class Midi_Event:
    def __init__(self, event, program_number):
        self.event = event
        self.program_number = program_number
        if program_number == None:
            self.program_name = "None"
        else:
            self.program_name = PROGRAMS[self.program_number + 1]
