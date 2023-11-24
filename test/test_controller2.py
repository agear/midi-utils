import pytest
from controller import Controller
from midi_track_ag import Midi_Track_AG
from midi_event import Midi_Event
import midi
import sf2_loader as sf
import os
from config import soundfont_path


class TestController:
    midi_file_path: str = "/Users/agear/Documents/Projects/AGM/percussion_test.mid"
    soundfont_path: str = soundfont_path
    convert_to_wav: bool = True
    base_path: str = "/Users/agear/Documents/Projects/Programming/Python/midi-utils/test/test_stems"


    def test_init(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        assert controller.midi_file_path == TestController.midi_file_path
        assert controller.songname == "percussion_test"
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
        assert controller.stems_path == f"{TestController.base_path}/percussion_test"
        assert controller.transport_track == midi.Track()
        assert controller.encapsulated_midi == []

    def test_get_transport_track(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)



        controller._get_transport_track()

        assert controller.transport_track[0].data[0] == 7
        assert controller.transport_track[0].data[1] == 161
        assert controller.transport_track[0].data[2] == 32

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
        assert '0 - Drum Kit 0' in encapsulated_track.programs
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

        percussion_instruments = controller.get_percussion_instruments(track=controller.midi_multitrack[1])

        assert len(percussion_instruments) == 3

        assert percussion_instruments[0].number == 51
        assert percussion_instruments[0].name == "51 - Ride Cymbal 1"
        assert percussion_instruments[1].number == 27
        assert percussion_instruments[1].name == "27 - High Q"
        assert percussion_instruments[2].number == 31
        assert percussion_instruments[2].name == "31 - Sticks"

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

        assert len(track_names) == 1

        assert track_names[0].program_number == 0
        assert track_names[0].program_name == "0 - Drum Kit 0"

        #TODO: get_track_names with single instruments and changing instruments
        #TODO: get_track_names with instrument a->instrument b->instrument


    def test_extract_midi_stems(self):
        # TODO: This needs to be much better/more robust.

        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        controller.extract_midi_stems()

        path = f"{TestController.base_path}/{controller.songname}/midi_stems/{controller.songname} - 01 - 0 - Drum Kit 0 - 0 - Drum Kit 0.mid"

        reimported = midi.read_midifile(path)

        assert reimported[0][0].data[0] == 7


    def test_convert_to_wav(self):
        controller = Controller(midi_file_path=TestController.midi_file_path,
                                soundfont_path=TestController.soundfont_path,
                                convert_to_wav=TestController.convert_to_wav,
                                base_path=TestController.base_path)

        controller.extract_midi_stems()
        controller.convert_to_wav(path=controller.midi_stem_path)

        assert False
