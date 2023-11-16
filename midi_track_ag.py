from midi_event import Midi_Event
from typing import List
from copy import deepcopy
import midi

class Midi_Track_AG:
    def __init__(self, events: List[Midi_Event], track_number: int, controller):
        self.events: List[Midi_Event] = events
        self.programs: List[str] = self._get_programs()
        self.transport_track = controller.transport_track
        self.resolution: int = controller.resolution
        self.midi_stem_path: str = controller.midi_stem_path
        self.songname: str = controller.songname
        self.track_number: str = self._get_formatted_track_number(i=track_number)
        self.patterns: List[midi.Pattern] = []
        self.drums: str = self._is_drum_track()
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

        for program_name in self.programs:
            if program_name == 'None':
                print("Program is none")
                continue

            pattern = midi.Pattern(resolution=self.resolution)
            pattern.append(self.transport_track)
            track = midi.Track()
            for event in self.events:
                if event.program_name == 'None' or event.program_name == program_name:
                    # print(f"Appending {event.event}")
                    track.append(deepcopy(event.event))
                elif type(event.event) == midi.NoteOnEvent and event.program_name != program_name:
                    event_copy = deepcopy(event.event)
                    event_copy.data[1] = 0 # make any note ons that aren't in the current program name have 0 velocity
                    # print(f"Appending {event_copy}")
                    track.append(event_copy)
                else:
                    # print(f"Appending {event.event}")
                    track.append(deepcopy(event.event))
            pattern.append(track)
            self.patterns.append((program_name, pattern))

        # print(self.patterns)

        return self.patterns

    def write(self):
        for pattern in self.patterns:
            filename: str = f"{self.midi_stem_path}/{self.songname} - {self.track_number} {self.drums}- {pattern[0]}.mid"
            midi.write_midifile(filename, pattern[1])

