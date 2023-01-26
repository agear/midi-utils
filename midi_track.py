from programs import PROGRAMS, PERCUSSION
from copy import deepcopy
import midi

class Midi_Track:
    def __init__(self, events, transport, resolution):
        self.events = events
        self.programs = self._get_programs()
        self.transport = transport
        self.resolution = resolution

    def _get_programs(self):
        programs = set()
        for event in self.events:
            programs.add(event.program_name)

        return list(programs)

    def get_extracted_programs(self):
        patterns = []
        for program in self.programs:
            if program == 'None':
                continue
            pattern = midi.Pattern(resolution=self.resolution)
            pattern.append(self.transport)
            track = midi.Track()
            for event in self.events:
                if event.program_name == 'None' or event.program_name == program:
                    track.append(deepcopy(event.event))
                elif type(event.event) == midi.NoteOnEvent:
                    event_copy = deepcopy(event.event)
                    event_copy.data[1] = 0
                    track.append(event_copy)
                else:
                    track.append(deepcopy(event.event))
            pattern.append(track)
            patterns.append((program, pattern))

        return patterns




