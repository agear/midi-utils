import os
from copy import deepcopy

import midi
from programs import PROGRAMS
from programs import PERCUSSION
import sf2_loader as sf


class Controller:
    def __init__(self, midi_file_path, base_path="."):
        self.midi_file_path = midi_file_path
        self.songname, self.file_extension = os.path.splitext(os.path.basename(midi_file_path))
        self.soundfont = "/Users/agear/Documents/Projects/AGM/soundfont/gm.sf2"
        self.loader = sf.sf2_loader(self.soundfont)
        self.midi_multitrack = midi.read_midifile(self.midi_file_path)
        self.resoultion = self.midi_multitrack.resolution
        self.stems_path = base_path + f"/{self.songname}"
        self.transport_track = None

        print(self.stems_path)

        self.make_directories()

    def make_directories(self):
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

    def extract_midi_stems(self):
        # TODO check for program changes and bounce separate stems
        # TODO check for fx/reverb and bounce both
        print("Extracting midi stems")
        for i, track in enumerate(self.midi_multitrack):
            track_names = self.get_track_name(track)
            if len(track_names) == 0:
                print("TEMPO CHANGES????")
                print(track)
                self.transport_track = track
                continue
            if track_names[0] == "0 - Drum Kit 0":
                self.extract_midi_drum_stems(i, track)
            pattern = midi.Pattern(resolution=self.resoultion)
            if self.transport_track:
                pattern.append(self.transport_track)
            pattern.append(track)
            # print(pattern)
            if len(set(track_names)) == 1:
                track_name = track_names[0][1]
                print(f"Extracting{self.midi_stem_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - {track_name}.mid")
                midi.write_midifile(f"{self.midi_stem_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - {track_name}.mid", pattern)
            else:
                self.extract_program_changes(track=track, i=i, track_names=track_names)

    def extract_program_changes(self, track, i, track_names):
        # TODO figure out this algorithm!!!
        print(f"TRACK NAMES: {track_names}")

        patterns = []

        for instrument in track_names:
            print(instrument)
            pattern = midi.Pattern(resolution=self.resoultion)
            if self.transport_track:
                pattern.append(self.transport_track)
            current_program = None
            # TODO use a pointer???
            for event in track:
                event_copy = deepcopy(event)
                if type(event_copy) == midi.ProgramChangeEvent:
                    current_program = event_copy.data[0]
                    print(current_program)






    def get_formatted_track_number(self, i):
        if len(str(i+1)) == 2:
            return str(i+1)
        track_number = "0"
        track_number += str(i+1)
        return track_number

    def extract_midi_drum_stems(self, i, track):
        percussion_instruments = self.get_percussion_instruments(track)

        percussion_path = f"{self.midi_stem_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - 0 - Drum Kit 0"
        print(percussion_path)

        try:
            os.mkdir(percussion_path)
        except:
            print("Can't make percussion path")
            quit()

        for instrument in percussion_instruments:
            # TODO go through track and mute all other instruments...
            # TODO figure out of track is empty and delete it
            pattern = midi.Pattern(resolution=self.resoultion)
            if self.transport_track:
                pattern.append(self.transport_track)
            percussion_track = midi.Track()
            for event in track:
                event_copy = deepcopy(event)
                if type(event_copy) == midi.NoteOnEvent:
                    # print(f"BEFORE:{event_copy}")
                    if event_copy.data[0] != instrument[0]:
                        event_copy.data[1] = 0
                        # print(f"AFTER:{event_copy}")
                percussion_track.append(event_copy)
            pattern.append(percussion_track)
            # print(track)
            # print(instrument)
            # print(percussion_track)
            print(f"Extracting {percussion_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - 0 - Drum Kit 0 - {instrument[1]}.mid")
            midi.write_midifile(f"{percussion_path}/{self.songname} - {self.get_formatted_track_number(i=i)} - 0 - Drum Kit 0 - {instrument[1]}.mid", pattern)

    def get_percussion_instruments(self, track):
        percussion_instruments = set()
        for event in track:
            if type(event) == midi.NoteOnEvent:
                # print(f"Event data: {event}")
                # print(f"PERCUSSION: {PERCUSSION[event.data[0]]}")
                percussion_instruments.add((event.data[0], PERCUSSION[event.data[0]]))
        percussion_instruments = list(percussion_instruments)
        percussion_instruments.sort()
        print(percussion_instruments)
        return percussion_instruments

    def get_track_name(self, track):
        # print('checking track...')
        programs = []
        for event in track:
            if type(event) == midi.ProgramChangeEvent:
                # print(f"EVENT: {event}")
                if event.channel == 9:
                    programs.append("0 - Drum Kit 0")
                    return programs
                else:
                    programs.append((event.data[0], PROGRAMS[event.data[0] + 1]))

        # print(programs)
        # programs = list(programs)
        return programs

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
