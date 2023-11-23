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
        assert controller.convert_to_wav == TestController.convert_to_wav
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
        assert encapsulated_track.programs == ['None', '0 - Drum Kit 0']
        assert encapsulated_track.track_number == "02"

        # TODO: make more test midi tracks more instrument changes


    #  Controller can extract midi stems
    # def test_extract_midi_stems(self):
    #
    #     controller = Controller(midi_file_path=TestController.midi_file_path,
    #                             soundfont_path=TestController.soundfont_path,
    #                             convert_to_wav=TestController.convert_to_wav,
    #                             base_path=TestController.base_path)
    #
    #     controller.extract_midi_stems()
    #
    #     assert len(controller.encapsulated_midi) == len(controller.midi_multitrack) - 1
    #     assert isinstance(controller.transport_track, midi.Track)
    #     assert isinstance(controller.encapsulated_midi[0], Midi_Track_AG)
    #     assert isinstance(controller.encapsulated_midi[0].events[0], Midi_Event)
    #     assert isinstance(controller.encapsulated_midi[0].programs, list)
    #     assert isinstance(controller.encapsulated_midi[0].patterns, list)
    #
    # #  Controller can extract midi drum stems
    # def test_extract_midi_drum_stems(self):
    #
    #     controller = Controller(midi_file_path=TestController.midi_file_path,
    #                             soundfont_path=TestController.soundfont_path,
    #                             convert_to_wav=TestController.convert_to_wav,
    #                             base_path=TestController.base_path)
    #
    #     controller.extract_midi_drum_stems(0, controller.midi_multitrack[0])
    #
    #     assert len(os.listdir(controller.midi_stem_path)) == 1 or len(os.listdir(controller.midi_stem_path)) == 2
    #     assert len(os.listdir(f'{controller.midi_stem_path}/{controller.songname} - 01 - 0 - Drum Kit 0')) == len(controller.get_percussion_instruments(controller.midi_multitrack[0]))
    #
    # #  Controller can encapsulate midi tracks
    # def test_encapsulate_midi(self):
    #
    #
    #     controller = Controller(midi_file_path=TestController.midi_file_path,
    #                             soundfont_path=TestController.soundfont_path,
    #                             convert_to_wav=TestController.convert_to_wav,
    #                             base_path=TestController.base_path)
    #     encapsulated_track = controller.encapsulate_midi(controller.midi_multitrack[0], 0)
    #
    #     assert isinstance(encapsulated_track, Midi_Track_AG)
    #     assert isinstance(encapsulated_track.events[0], Midi_Event)
    #     assert isinstance(encapsulated_track.programs, list)
    #     assert isinstance(encapsulated_track.patterns, list)
    #
    # #  Controller can handle no transport track
    # def test_no_transport_track(self):
    #
    #     controller = Controller(midi_file_path=TestController.midi_file_path,
    #                             soundfont_path=TestController.soundfont_path,
    #                             convert_to_wav=TestController.convert_to_wav,
    #                             base_path=TestController.base_path)
    #     controller.transport_track = None
    #     controller.extract_midi_stems()
    #
    #     assert len(controller.encapsulated_midi) == len(controller.midi_multitrack)
    #
    # #  Controller can handle no program name
    # def test_no_program_name(self):
    #
    #
    #     controller = Controller(midi_file_path=TestController.midi_file_path,
    #                             soundfont_path=TestController.soundfont_path,
    #                             convert_to_wav=TestController.convert_to_wav,
    #                             base_path=TestController.base_path)
    #     controller.get_track_names(controller.midi_multitrack[0])
    #
    #     assert len(controller.get_track_names(controller.midi_multitrack[0])) == 0
    #
    # #  Controller can handle no audio stem path
    # # def test_no_audio_stem_path(self):
    # #
    # #     controller = Controller(midi_file_path=TestController.midi_file_path,
    # #                             soundfont_path=TestController.soundfont_path,
    # #                             convert_to_wav=TestController.convert_to_wav,
    # #                             base_path=TestController.base_path)
    # #
    # #     controller.audio_stem_path = None
    # #     controller.convert_to_wav(controller.audio_stem_path)
    # #
    # #     assert True
