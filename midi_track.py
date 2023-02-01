from programs import PROGRAMS, PERCUSSION
from copy import deepcopy
import midi

class Midi_Track:
    def __init__(self, events, track_number, controller):
        self.events = events
        self.programs = self._get_programs()
        self.transport = controller.transport
        self.resolution = controller.resolution
        self.midi_stem_path = controller.midi_stem_path
        self.songname = controller.songname
        self.track_number = self._get_formatted_track_number(i=track_number)
        self.patterns = []

    def _get_programs(self):
        programs = set()
        for event in self.events:
            programs.add(event.program_name)

        return list(programs)

    def _get_formatted_track_number(self, i):
        if len(str(i+1)) == 2:
            return str(i+1)
        track_number = "0"
        track_number += str(i+1)
        return track_number

    def get_extracted_programs(self):
        patterns = []
        for program in self.programs:
            if program == 'None':
                continue
            pattern = midi.Pattern(resolution=self.resolution)
            self.pattern.append(self.transport)
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
            self.patterns.append((program, pattern))

        return self.patterns

    def write(self):
        for pattern in self.patterns:
            midi.write_midifile(f"{self.midi_stem_path}/{self.songname} - {self.track_number} - {pattern[0]}.mid", pattern[1])
