import os
from midi_event import Midi_Event
from typing import List
from copy import deepcopy
import midi
from percussion_instrument import Percussion_Instrument

class Midi_Track_AG:
    def __init__(self, events: List[Midi_Event], track_number: int, controller):
        self.events: List[Midi_Event] = events
        self.programs: List[str] = self._get_program_names()
        self.transport_track = controller.transport_track
        self.resolution: int = controller.resolution
        self.midi_stem_path: str = controller.midi_stem_path
        self.songname: str = controller.songname
        self.track_number: str = self._get_formatted_track_number(i=track_number)
        self.patterns: List[midi.Pattern] = []
        self.drums: str = self._is_drum_track()
        self.is_drums: bool = False
        self.extract_programs()

    def _is_drum_track(self) -> str:
        print("Calling _is_drum_track()")
        for event in self.events:
            if type(event.event) == midi.ProgramChangeEvent:
                print(event.event)
                if event.event.channel == 9:
                    print("FOUND A DRUM TRACK!!!!")
                    self.extract_midi_drum_stems(i=self.track_number, track=self.events)
                    return "- 0 - Drum Kit 0 "
            # except:
            #     if event.event.channel == 9:
            #         return  "- 0 - Drum Kit 0"

        return ""

    def _get_program_names(self):
        program_names = set()
        for event in self.events:
            program_names.add(event.program_name)


        print(f'Programs: {list(program_names)}')
        return list(program_names)

    def _get_formatted_track_number(self, i):
        if len(str(i+1)) == 2:
            return str(i+1)
        track_number = "0"
        track_number += str(i+1)
        return track_number

    def extract_programs(self):
        print("Extracting programs...")
        if self.is_drums:
            self.controller.extract_midi_drum_stems(i=self.track_number, track=self.events)

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
                    event_copy.data[1] = 0 # make any NoteOns that aren't in the current program name have 0 velocity
                    # print(f"Appending {event_copy}")
                    track.append(event_copy)
                else:
                    # print(f"Appending {event.event}")
                    track.append(deepcopy(event.event))
            pattern.append(track)

            # if program_name == "0 - Drum Kit 0 ":
            #     # TODO: get specific percussion instrument name
            #     assert False
            self.patterns.append((program_name, pattern))

        # print(self.patterns)

        return self.patterns

    def write(self):
        for pattern in self.patterns:
            instrument_name = pattern[0]
            filename: str = f"{self.midi_stem_path}/{self.songname} - {self.track_number} {self.drums}- {instrument_name}.mid"
            midi.write_midifile(filename, pattern[1])

    def extract_midi_drum_stems(self, i: int, track: midi.Track) -> None:
        """
            Extract MIDI drum stems from the multitrack and save them as separate MIDI files.

            Args:
                i (int): Track number.
                track (midi.Track): MIDI drum track.
        """
        percussion_instruments: List[Percussion_Instrument] = self.get_percussion_instruments(track)

        percussion_path: str = f"{self.midi_stem_path}/{self.songname} - {self.track_number} - 0 - Drum Kit 0"
        print(percussion_path)

        try:
            os.mkdir(percussion_path)
        except:
            print("Can't make percussion path")
            quit()

        for instrument in percussion_instruments:
            # TODO go through track and mute all other instruments...
            # TODO figure out of track is empty and delete it
            print(f"Looking for {instrument}")
            pattern: midi.Pattern = midi.Pattern(resolution=self.resolution)
            if self.transport_track:
                pattern.append(self.transport_track)
            percussion_track: midi.Track = midi.Track()
            for event in track:
                event_copy: midi.Event = deepcopy(event)
                if type(event_copy.event) == midi.NoteOnEvent and event_copy.event.data[0] != instrument.number:
                        print("setting data = 0")
                        event_copy.event.data[1] = 0

                percussion_track.append(event_copy.event)
            pattern.append(percussion_track)
            print(f"Extracting {percussion_path}/{self.songname} - {self.track_number} - 0 - Drum Kit 0 - {instrument.name}.mid")
            midi.write_midifile(f"{percussion_path}/{self.songname} - {self.track_number} - 0 - Drum Kit 0 - {instrument.name}.mid", pattern)

    @staticmethod
    def get_percussion_instruments(track: midi.Track) -> List[Percussion_Instrument]:
        """
            Get the list of percussion instruments from the MIDI track.

            Args:
                track: MIDI track.

            Returns:
                List[Percussion_Instrument]: List of percussion instruments.
        """
        percussion_instruments = set()
        for event in track:
            print(type(event.event))
            if type(event.event) == midi.NoteOnEvent:
                print(event.event.data[0])
                percussion_instruments.add(Percussion_Instrument(event.event.data[0]))
        percussion_instruments = list(percussion_instruments)
        return percussion_instruments
