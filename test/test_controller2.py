import pytest
from controller import Controller
from encapsulated_midi_track import Encapsulated_Midi_Track
from encapsulated_midi_event import Encapsulated_Midi_Event
import midi
import sf2_loader as sf
import os
from config import soundfont_path


class TestController:
    midi_file_path: str = "/Users/agear/Documents/Projects/Programming/Python/midi-utils/test/test_files/test_file.mid"
    soundfont_path: str = soundfont_path
    convert_to_wav: bool = True
    base_path: str = "/Users/agear/Documents/Projects/Programming/Python/midi-utils/test/test_stems"


    def test_init(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        assert controller.midi_file_path == TestController.midi_file_path
        assert controller.songname == "test_file"
        assert controller.file_extension == ".mid"
        assert controller.convert_to_wav_flag == TestController.convert_to_wav
        assert isinstance(controller.loader, sf.sf2_loader)
        assert controller.loader.file == [TestController.soundfont_path]
        assert controller.loader.current_sfid == 1
        assert controller.loader.current_channel == 0
        assert controller.loader.current_bank == 0
        assert controller.loader
        midifile = midi.read_midifile(TestController.midi_file_path)
        for i in range(len(midifile)):
            for j in range(len(midifile[i])):
                assert type(controller.midi_multitrack[i][j]) == type(midifile[i][j])

        #TODO: Add assertions for _make_directories()

        assert controller.resolution == 480
        assert controller.stems_path == f"{TestController.base_path}/test_file"
        assert controller.transport_track == midi.Track()
        assert controller.encapsulated_midi == []

    def test_get_transport_track(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)



        controller._get_transport_track()

        assert controller.transport_track[0].data[0] == 11
        assert controller.transport_track[0].data[1] == 188
        assert controller.transport_track[0].data[2] == 206

        second_test = "/Users/agear/Documents/Projects/AGM/Guitar Pro PDFs/Finished/Aphids/Aphids2.mid"

        controller = Controller(midi_file_path=second_test,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        controller._get_transport_track()

        assert controller.transport_track == midi.Track()
        # TODO: Create test for track with no transport track



    def test_encapsulate_midi(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        encapsulated_track = controller.encapsulate_midi(track=midi.Track(), track_number=0)

        assert isinstance(encapsulated_track, Midi_Track_AG)

        assert encapsulated_track.programs == []
        assert encapsulated_track.track_number == "01"


        encapsulated_track = controller.encapsulate_midi(track=controller.midi_multitrack[1], track_number=1)

        # TODO: Does the program list need to contain 'None'?
        assert 'None' in encapsulated_track.programs
        assert '28 - Electric Guitar (muted)' in encapsulated_track.programs
        assert '4 - Electric Piano 1' in encapsulated_track.programs

        assert encapsulated_track.track_number == "02"

        # TODO: make more test midi tracks more instrument changes


    def test_get_percussion_instruments(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        percussion_instruments = controller.get_percussion_instruments(track=midi.Track())

        # Test that empty track has no percussion instruments
        assert percussion_instruments == []

        #TODO: What happens if non-percussion track is given to get_percussion_instruments()?

        percussion_instruments = controller.get_percussion_instruments(track=controller.midi_multitrack[0])

        # Test that transport track has now percussion instruments.
        assert percussion_instruments == []

        percussion_instruments = controller.get_percussion_instruments(track=controller.midi_multitrack[12])

        assert len(percussion_instruments) == 13

        test_numbers = [28, 31, 33, 34, 35, 36, 38, 39, 40, 41, 42, 43, 44]
        test_names = ["28 - Slap",
                      "31 - Sticks",
                      '33 - Metronome Click',
                      '34 - Metronome Bell',
                      '35 - Acoustic Bass Drum',
                      '36 - Bass Drum 1',
                      "38 - Acoustic Snare",
                      "39 - Hand Clap",
                      "40 - Electric Snare",
                      '41 - Low Floor Tom',
                      "42 - Closed Hi-Hat",
                      '43 - High Floor Tom',
                      "44 - Pedal Hi-Hat"]


        for percussion_instrument in percussion_instruments:
            assert percussion_instrument.number in test_numbers
            assert percussion_instrument.name in test_names



    def test_get_track_names(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        track_names = controller.get_track_names(track=midi.Track())

        assert track_names == []

        track_names = controller.get_track_names(track=controller.midi_multitrack[0])

        assert track_names == []

        track_names = controller.get_track_names(track=controller.midi_multitrack[1])

        assert len(track_names) == 3

        test_numbers = [4, 28]
        test_names = ['4 - Electric Piano 1', '28 - Electric Guitar (muted)']

        assert track_names[0].program_number in test_numbers
        assert track_names[0].get_program_name() in test_names
        assert track_names[1].program_number in test_numbers
        assert track_names[1].get_program_name() in test_names
        assert track_names[2].program_number in test_numbers
        assert track_names[2].get_program_name() in test_names

        #TODO: get_track_names with single instruments and changing instruments
        #TODO: get_track_names with instrument a->instrument b->instrument

        track_names = controller.get_track_names(track=controller.midi_multitrack[13])

        assert len(track_names) == 1

        assert track_names[0].program_number == 0
        assert track_names[0].program_name == "0 - Drum Kit 0"



    def test_extract_midi_stems(self):
        # TODO: This needs to be much better/more robust.

        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        controller.extract_midi_stems()

        path = f"{TestController.base_path}/{controller.songname}/midi_stems/{controller.songname} - 01 - 4 - Electric Piano 1.mid"

        reimported = midi.read_midifile(path)

        assert reimported[0][0].data[0] == 11


    def test_convert_to_wav(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        controller.extract_midi_stems()
        controller.convert_to_wav(path=controller.midi_stem_path)

        # TODO: Write some real assertions.
        assert False
