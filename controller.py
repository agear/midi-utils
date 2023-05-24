import os
from copy import deepcopy
from typing import List, Dict, Set, Optional

import midi
import sf2_loader

import midi_event
from programs import PROGRAMS
from programs import PERCUSSION
import sf2_loader as sf
from midi_event import Midi_Event
from midi_track_ag import Midi_Track_AG
from percussion_instrument import Percussion_Instrument
from program import Program
import shutil


class Controller:
    def __init__(self, midi_file_path: str, base_path: Optional[str]="."):
        self.midi_file_path: str = midi_file_path
        self.songname, self.file_extension = os.path.splitext(os.path.basename(midi_file_path))
        self.soundfont: str = "/Users/agear/Documents/Projects/AGM/soundfont/gm.sf2"
        self.loader: sf.sf2_loader = sf.sf2_loader(self.soundfont)
        self.midi_multitrack: midi.Pattern = midi.read_midifile(self.midi_file_path)
        self.resolution: int = self.midi_multitrack.resolution
        self.stems_path: str = base_path + f"/{self.songname}"
        self.transport_track: midi.Track = midi.Track()
        self._make_directories()
        self.encapsulated_midi: List[Midi_Track_AG] = []

    def _make_directories(self) -> None:
        try:
            shutil.rmtree(self.stems_path)
            print(f"Deleted {self.stems_path}")
        except OSError as e:
            print("Error: %s : %s" % (self.stems_path, e.strerror))

        try:
            os.mkdir(self.stems_path)
        except:
            print("cant make stem path!!!!")
            quit()
        self.midi_stem_path = f"{self.stems_path}/midi_stems"
        try:
            os.mkdir(self.midi_stem_path)
        except:
            pass
        self.audio_stem_path = f"{self.stems_path}/audio_stems"
        try:
            os.mkdir(self.audio_stem_path)
        except:
            pass

    # MIDI STUFF

    def _get_transport_track(self) -> None:
        for track in enumerate(self.midi_multitrack):
            track_names = self.get_track_name(track)
            if len(track_names) == 0:
                self.transport_track = track
                return

    def extract_midi_stems(self) -> None:
        self._get_transport_track()

        for track_number, track in enumerate(self.midi_multitrack):
            self.encapsulated_midi.append(self.encapsulate_midi(track=track, track_number=track_number))

        for track in self.encapsulated_midi:
            track.write()

    def extract_midi_stems2(self) -> None:
        print("Extracting midi stems")
        for i, track in enumerate(self.midi_multitrack):
            track_names = self.get_track_name(track)
            if len(track_names) == 0:
                # print("TEMPO CHANGES????")
                # print(track)
                self.transport_track = track
                continue
            if track_names[0] == "0 - Drum Kit 0":
                self.extract_midi_drum_stems(i, track)
            pattern = midi.Pattern(resolution=self.resolution)
            if self.transport_track:
                pattern.append(self.transport_track)
            pattern.append(track)
            # print(pattern)
            if len(set(track_names)) == 1:
                track_name = track_names[0].program_name
                print(f"Extracting{self.midi_stem_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - {track_name}.mid")
                midi.write_midifile(f"{self.midi_stem_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - {track_name}.mid", pattern)
            else:
                encapsulated_midi = self.encapsulate_midi(track=track, track_number=i)
                # self.extract_program_changes(track=track, i=i, track_names=track_names)
                patterns = encapsulated_midi.extract_programs()
                for pattern in patterns:
                    midi.write_midifile(f"{self.midi_stem_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - {pattern[0]}.mid", pattern[1])

    def encapsulate_midi(self, track: midi.Track, track_number: int) -> Midi_Track_AG:
        print(f"Encapsulating track number {track_number}")
        current_program: int = None
        encapsulated_track: List[midi_event.Midi_Event] = []
        for event in track:
            event_copy: midi.Event = deepcopy(event)
            if type(event_copy) == midi.ProgramChangeEvent:
                current_program = event_copy.data[0]
            encapsulated_event: Midi_Event = Midi_Event(event=event_copy, program_number=current_program)

            encapsulated_track.append(encapsulated_event)


        encapsulated_track: Midi_Track_AG = Midi_Track_AG(events=encapsulated_track, track_number=track_number, controller=self)

        print(encapsulated_track.programs)

        return encapsulated_track

    # def extract_program_changes(self, track, i, track_names):
    #     # TODO figure out this algorithm!!!
    #     print(f"TRACK NAMES: {track_names}")
    #
    #     patterns = []
    #
    #     set_track_names = set()
    #
    #     reduced_track_names = []
    #
    #     for t in track_names:
    #         if t not in set_track_names:
    #             reduced_track_names.append(t)
    #             set_track_names.add(t)
    #
    #     print(f"REDUCED TRACK NAMES: {reduced_track_names}")
    #
    #
    #
    #     for instrument in reduced_track_names:
    #         print(instrument)
    #         pattern = midi.Pattern(resolution=self.resoultion)
    #         if self.transport_track:
    #             pattern.append(self.transport_track)
    #         current_program = instrument
    #         # TODO use a pointer???
    #         for event in track:
    #             event_copy = deepcopy(event)
    #             if type(event_copy) == midi.ProgramChangeEvent:
    #                 current_program = event_copy.data[0]
    #                 # print(current_program)

    def get_formatted_track_number(self, i: int) -> str:
        if len(str(i+1)) == 2:
            return str(i+1)
        track_number: str = "0"
        track_number += str(i+1)
        return track_number

    def extract_midi_drum_stems(self, i: int, track: midi.Track) -> None:
        percussion_instruments: List[Percussion_Instrument] = self.get_percussion_instruments(track)

        percussion_path: str = f"{self.midi_stem_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - 0 - Drum Kit 0"
        print(percussion_path)

        try:
            os.mkdir(percussion_path)
        except:
            print("Can't make percussion path")
            quit()

        for instrument in percussion_instruments:
            # TODO go through track and mute all other instruments...
            # TODO figure out of track is empty and delete it
            pattern: midi.Pattern = midi.Pattern(resolution=self.resolution)
            if self.transport_track:
                pattern.append(self.transport_track)
            percussion_track: midi.Track = midi.Track()
            for event in track:
                event_copy: midi.Event = deepcopy(event)
                if type(event_copy) == midi.NoteOnEvent:
                    # print(f"BEFORE:{event_copy}")
                    if event_copy.data[0] != instrument.number:
                        event_copy.data[1] = 0
                        # print(f"AFTER:{event_copy}")
                percussion_track.append(event_copy)
            pattern.append(percussion_track)
            # print(track)
            # print(instrument)
            # print(percussion_track)
            print(f"Extracting {percussion_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - 0 - Drum Kit 0 - {instrument.name}.mid")
            midi.write_midifile(f"{percussion_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - 0 - Drum Kit 0 - {instrument.name}.mid", pattern)

    def get_percussion_instruments(self, track) -> List[Percussion_Instrument]:
        percussion_instruments = set()
        for event in track:
            if type(event) == midi.NoteOnEvent:
                # print(f"Event data: {event}")
                # print(f"PERCUSSION: {PERCUSSION[event.data[0]]}")
                # percussion_instruments.add((event.data[0], PERCUSSION[event.data[0]]))
                percussion_instruments.add(Percussion_Instrument(event.data[0]))
        percussion_instruments = list(percussion_instruments)
        # percussion_instruments.sort()
        # print(percussion_instruments)
        return percussion_instruments

    def get_track_name(self, track: midi.Track):
        # print('checking track...')
        programs: List[Program] = []
        # pointers = []
        for i, event in enumerate(track):
            if type(event) == midi.ProgramChangeEvent:
                # print(f"EVENT: {event}")
                if event.channel == 9:
                    program = Program()
                    program.program_name = "0 - Drum Kit 0"
                    programs.append(program)
                    return programs
                else:
                    program = Program(event.data[0])
                    programs.append(program)
                    # pointers.append(i)

        # print(programs)
        # programs = list(programs)
        # print(f"Programs: {programs}")
        # print(f"Pointers: {pointers}")
        return programs

    # WAV STUFF

    def convert_to_wav(self, path):
        print("Starting conversion to .wav")

        # Bounce multitrack
        self.loader.export_midi_file(fr'{self.midi_file_path}', name=f'{self.audio_stem_path}/{self.songname} - All.wav', format='wav')

        for filename in os.listdir(path):
            f = os.path.join(path, filename)
            # checking if it is a file
            if os.path.isfile(f) and f[-4:] == self.file_extension:
                print(filename)
                filename = filename[:-4]

                self.loader.export_midi_file(fr'{f}', name=f'{self.audio_stem_path}/{filename}.wav', format='wav')
                print(f"Converting {filename} to {self.audio_stem_path}/{filename}.wav")
            else:
                print(f'dir: {filename}')
                self.convert_to_wav(path=f"{self.midi_stem_path}/{filename}")
