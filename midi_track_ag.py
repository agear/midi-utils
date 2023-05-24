from programs import PROGRAMS, PERCUSSION
# from controller import Controller
from midi_event import Midi_Event
from typing import List
from copy import deepcopy
import midi

class Midi_Track_AG:
    def __init__(self, events: List[Midi_Event], track_number: int, controller):
        self.events: List[Midi_Event] = events
        self.programs = self._get_programs()
        self.transport_track = controller.transport_track
        self.resolution: int = controller.resolution
        self.midi_stem_path = controller.midi_stem_path
        self.songname = controller.songname
        self.track_number = self._get_formatted_track_number(i=track_number)
        self.patterns = []
        self.drums = self._is_drum_track()
        self.extract_programs()

    def _is_drum_track(self) -> str:
        print("Calling _is_drum_track()")
        for event in self.events:
            if type(event.event) == midi.ProgramChangeEvent:
                print(event.event)
                if event.event.channel == 9:
                    print("FOUND A DRUM TRACK!!!!")
                    return "- 0 - Drum Kit 0 "
            # except:
            #     if event.event.channel == 9:
            #         return  "- 0 - Drum Kit 0"

        return ""

    def _get_programs(self):
        programs = set()
        for event in self.events:
            programs.add(event.program_name)


        print(f'Programs: {list(programs)}')
        return list(programs)

    def _get_formatted_track_number(self, i):
        if len(str(i+1)) == 2:
            return str(i+1)
        track_number = "0"
        track_number += str(i+1)
        return track_number

    def extract_programs(self):
        print("Extracting programs...")
        patterns = []
        for program in self.programs:
            if program == 'None':
                continue
                print("Program is none")
            pattern = midi.Pattern(resolution=self.resolution)
            pattern.append(self.transport_track)
            track = midi.Track()
            for event in self.events:
                if event.program_name == 'None' or event.program_name == program:
                    # print(f"Appending {event.event}")
                    track.append(deepcopy(event.event))
                elif type(event.event) == midi.NoteOnEvent:
                    event_copy = deepcopy(event.event)
                    event_copy.data[1] = 0
                    # print(f"Appending {event_copy}")
                    track.append(event_copy)
                else:
                    # print(f"Appending {event.event}")
                    track.append(deepcopy(event.event))
            pattern.append(track)
            self.patterns.append((program, pattern))

        # print(self.patterns)

        return self.patterns

    def write(self):
        for pattern in self.patterns:
            try:
                print(f"Writing {self.midi_stem_path}/{self.songname} - {self.track_number} {self.drums}- {pattern[0]}.mid")
                midi.write_midifile(f"{self.midi_stem_path}/{self.songname} - {self.track_number} {self.drums}- {pattern[0]}.mid", pattern[1])
            except:
                print(f"ERROR: Couldn't write {self.midi_stem_path}/{self.songname} - {self.track_number} - {pattern[0]}.mid")
