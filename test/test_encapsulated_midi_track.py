import pytest
from encapsulated_midi_event import Encapsulated_Midi_Event
from controller import Controller
from encapsulated_midi_track import Encapsulated_Midi_Track
import midi
from config import soundfont_path


class TestEncapsulatedMidiTrack:
    midi_file_path: str = "/Users/agear/Documents/Projects/Programming/Python/midi-utils/test/test_files/test_file.mid"
    soundfont_path: str = soundfont_path
    convert_to_wav: bool = True
    base_path: str = "/Users/agear/Documents/Projects/Programming/Python/midi-utils/test/test_stems"

    controller = Controller(midi_file_path=midi_file_path,
                            soundfont_path=soundfont_path,
                            convert_to_wav=convert_to_wav,
                            base_path=base_path)

    midifile = midi.read_midifile(midi_file_path)
    events = midifile[2]

    def test_init(self):
        track = Encapsulated_Midi_Track(events=TestEncapsulatedMidiTrack.midifile[3], track_number=1,
                                        controller=TestEncapsulatedMidiTrack.controller)

        assert track.events
        assert track.programs
        assert track.transport_track == TestEncapsulatedMidiTrack.controller.transport_track
        assert track.resolution == TestEncapsulatedMidiTrack.controller.resolution
        assert track.midi_stem_path == TestEncapsulatedMidiTrack.controller.midi_stem_path
        assert track.songname == "test_file"
        assert track.track_number == "02"
        # assert track.patterns
        assert track.drums == ""
        assert not track.is_drums
        # assert track.events == TestMidiTrackAg.events
        # TODO: add mort asserts


    def test_is_drum_track(self):


        track_not_drums = Encapsulated_Midi_Track(events=TestEncapsulatedMidiTrack.midifile[3], track_number=3,
                                        controller=TestEncapsulatedMidiTrack.controller)

        assert track_not_drums._is_drum_track() == ""

        track_drums = Encapsulated_Midi_Track(events=TestEncapsulatedMidiTrack.midifile[13], track_number=13,
                                        controller=TestEncapsulatedMidiTrack.controller)

        assert track_drums._is_drum_track() == "- 0 - Drum Kit 0 "


    def test_get_program_names(self):
        track = Encapsulated_Midi_Track(events=TestEncapsulatedMidiTrack.midifile[3], track_number=3,
                                        controller=TestEncapsulatedMidiTrack.controller)

        assert 'None' in track._get_program_names()
        assert '39 - Synth Bass 2' in track._get_program_names()

        track = Encapsulated_Midi_Track(events=TestEncapsulatedMidiTrack.midifile[1], track_number=1,
                                        controller=TestEncapsulatedMidiTrack.controller)

        assert 'None' in track._get_program_names()
        assert '4 - Electric Piano 1' in track._get_program_names()
        assert '28 - Electric Guitar (muted)' in track._get_program_names()


    def test_get_formatted_track_number(self):
        track = Encapsulated_Midi_Track(events=TestEncapsulatedMidiTrack.midifile[3], track_number=3,
                                        controller=TestEncapsulatedMidiTrack.controller)

        assert track._get_formatted_track_number(i=3) == "04"

        # TODO: Add error handling -- track number can't be negative
        # assert track._get_formatted_track_number(i=-1) == "04"

        assert track._get_formatted_track_number(i=0) == "01"
        assert track._get_formatted_track_number(i=1) == "02"
        assert track._get_formatted_track_number(i=2) == "03"
        assert track._get_formatted_track_number(i=3) == "04"
        assert track._get_formatted_track_number(i=4) == "05"
        assert track._get_formatted_track_number(i=5) == "06"
        assert track._get_formatted_track_number(i=6) == "07"
        assert track._get_formatted_track_number(i=7) == "08"
        assert track._get_formatted_track_number(i=8) == "09"
        assert track._get_formatted_track_number(i=9) == "10"
        assert track._get_formatted_track_number(i=10) == "11"
        assert track._get_formatted_track_number(i=11) == "12"
        assert track._get_formatted_track_number(i=12) == "13"
        assert track._get_formatted_track_number(i=13) == "14"
        assert track._get_formatted_track_number(i=14) == "15"
        assert track._get_formatted_track_number(i=15) == "16"
        assert track._get_formatted_track_number(i=16) == "17"
        assert track._get_formatted_track_number(i=17) == "18"
        assert track._get_formatted_track_number(i=18) == "19"
        assert track._get_formatted_track_number(i=19) == "20"


    # #  Midi_Track_AG can be initialized with a list of Midi_Event objects, a track number, and a controller object.
    # def test_initialized_with_list_of_midi_events(self):
    #     events = [Midi_Event(event, program_number) for event, program_number in zip(midi_events, program_numbers)]
    #     track_number = 1
    #     controller = Controller()
    #     midi_track = Midi_Track_AG(events, track_number, controller)
    #
    #     assert isinstance(midi_track.events, list)
    #     assert isinstance(midi_track.programs, list)
    #     assert isinstance(midi_track.transport_track, midi.Track)
    #     assert isinstance(midi_track.resolution, int)
    #     assert isinstance(midi_track.midi_stem_path, str)
    #     assert isinstance(midi_track.songname, str)
    #     assert isinstance(midi_track.track_number, str)
    #     assert isinstance(midi_track.patterns, list)
    #     assert isinstance(midi_track.drums, str)
    #     assert isinstance(midi_track.is_drums, bool)
    #
    # #  Midi_Track_AG can extract the program names from its list of Midi_Event objects.
    # def test_extract_program_names(self):
    #     events = [Midi_Event(event, program_number) for event, program_number in zip(midi_events, program_numbers)]
    #     track_number = 1
    #     controller = Controller()
    #     midi_track = Midi_Track_AG(events, track_number, controller)
    #
    #     program_names = midi_track._get_program_names()
    #
    #     assert isinstance(program_names, list)
    #     assert all(isinstance(name, str) for name in program_names)
    #
    # #  Midi_Track_AG can generate a formatted track number based on its track number attribute.
    # def test_generate_formatted_track_number(self):
    #     events = [Midi_Event(event, program_number) for event, program_number in zip(midi_events, program_numbers)]
    #     track_number = 1
    #     controller = Controller()
    #     midi_track = Midi_Track_AG(events, track_number, controller)
    #
    #     formatted_track_number = midi_track._get_formatted_track_number(i=track_number)
    #
    #     assert isinstance(formatted_track_number, str)
    #     assert formatted_track_number == "01"
    #
    # #  Midi_Track_AG can encapsulate its list of Midi_Event objects into a list of midi.Pattern objects.
    # def test_encapsulate_midi_events(self):
    #     events = [Midi_Event(event, program_number) for event, program_number in zip(midi_events, program_numbers)]
    #     track_number = 1
    #     controller = Controller()
    #     midi_track = Midi_Track_AG(events, track_number, controller)
    #
    #     patterns = midi_track.extract_programs()
    #
    #     assert isinstance(patterns, list)
    #     assert all(isinstance(pattern, tuple) for pattern in patterns)
    #     assert all(
    #         isinstance(program_name, str) and isinstance(pattern, midi.Pattern) for program_name, pattern in patterns)
    #
    # #  Midi_Track_AG can write its list of midi.Pattern objects to disk.
    # def test_write_midi_patterns_to_disk(self):
    #     events = [Midi_Event(event, program_number) for event, program_number in zip(midi_events, program_numbers)]
    #     track_number = 1
    #     controller = Controller()
    #     midi_track = Midi_Track_AG(events, track_number, controller)
    #
    #     midi_track.write()
    #
    #     # Add assertions to check if the MIDI files were successfully written to disk
    #
    # #  Midi_Track_AG can extract MIDI drum stems from its list of Midi_Event objects and save them as separate MIDI files.
    # def test_extract_midi_drum_stems(self):
    #     events = [Midi_Event(event, program_number) for event, program_number in zip(midi_events, program_numbers)]
    #     track_number = 1
    #     controller = Controller()
    #     midi_track = Midi_Track_AG(events, track_number, controller)
    #
    #     midi_track.extract_midi_drum_stems(i=track_number, track=midi_track.events)
    #
    #     # Add assertions to check if the MIDI drum stems were successfully extracted and saved as separate MIDI files
