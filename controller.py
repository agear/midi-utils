import logging
import os
from typing import List, Optional

import midi
import sf2_loader as sf
from encapsulated_midi_event import Encapsulated_Midi_Event
from encapsulated_midi_track import Encapsulated_Midi_Track
from percussion_instrument import Percussion_Instrument
from program import Program

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self, midi_file_path: str, soundfont_path: str, convert_to_wav: bool, base_path: Optional[str]= "."):
        """
        The Controller class is responsible for processing MIDI files. It extracts MIDI stems from a multitrack
        MIDI file and saves them as separate MIDI files. It also has the functionality to convert MIDI files
        to WAV format.

        Example Usage
        controller = Controller(midi_file_path, soundfont_path, convert_to_wav)
        controller.extract_midi_stems()
        controller.convert_to_wav()

        Args:
            midi_file_path (str): Path to MIDI file.
            soundfont_path (str): Path to Soundfont file used for rendering to WAV.
            convert_to_wav (bool):
            base_path (str, optional): Base path for storing stems, Defaults to current directory (".").
        """
        self.midi_file_path: str = midi_file_path
        self.songname, self.file_extension = os.path.splitext(os.path.basename(midi_file_path))
        logger.info("Loading %s", midi_file_path)
        self.convert_to_wav_flag: bool = convert_to_wav
        self.loader: sf.sf2_loader = sf.sf2_loader(soundfont_path)
        self.midi_multitrack: midi.Pattern = midi.read_midifile(self.midi_file_path)
        self.resolution: int = self.midi_multitrack.resolution
        self.stems_path: str = os.path.dirname(base_path) + os.sep + f"{self.songname} Stems"
        logger.debug("Stems path: %s", self.stems_path)
        self.transport_track: midi.Track = midi.Track()
        self._make_directories()
        self.encapsulated_midi: List[Encapsulated_Midi_Track] = []


    def _make_directories(self) -> None:
        """
        Create directory structure for storing stems.
        """
        os.makedirs(name=self.stems_path, exist_ok=True)
        self.midi_stem_path = f"{self.stems_path}/midi_stems"
        os.makedirs(name=self.midi_stem_path, exist_ok=True)
        if self.convert_to_wav_flag:
            self.audio_stem_path = f"{self.stems_path}/audio_stems"
            os.makedirs(name=self.audio_stem_path, exist_ok=True)


    def _find_transport_track(self) -> Optional[midi.Track]:
        """
        Return the first track that contains no program changes (the transport/
        tempo track), or None if every track has at least one program change.
        """
        for track_number, track in enumerate(self.midi_multitrack):
            if not self.get_track_names(track=track):
                logger.debug("Track %d identified as transport track", track_number)
                return track
        logger.warning("No transport track found in %s", self.midi_file_path)
        return None

    def extract_midi_stems(self) -> None:
        """
        Extract MIDI stems from the multitrack and save them as separate MIDI files.
        """
        transport = self._find_transport_track()
        if transport is not None:
            self.transport_track = transport

        track_number: int = 0
        for track in self.midi_multitrack:
            if track == self.transport_track:
                continue
            self.encapsulated_midi.append(Encapsulated_Midi_Track(events=track, track_number=track_number, controller=self))
            track_number += 1

        for track in self.encapsulated_midi:
            track.write()


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
            if type(event) == midi.NoteOnEvent:
                percussion_instruments.add(Percussion_Instrument(event.data[0]))
        percussion_instruments = list(percussion_instruments)
        return percussion_instruments

    @staticmethod
    def get_track_names(track: midi.Track) -> List[Program]:
        """
            Get the program name associated with the MIDI track.

            Args:
                track (midi.Track): MIDI track.

            Returns:
                List[Program]: List of Program objects representing the program names of the track.
        """

        programs: List[Program] = []

        for event in track:
            if type(event) == midi.ProgramChangeEvent:

                if event.channel == 9:
                    program = Program()
                    program.program_name = "0 - Drum Kit 0"
                    programs.append(program)
                    return programs
                else:
                    program = Program(event.data[0])
                    programs.append(program)

        return programs

    def convert_to_wav(self, path: str) -> None:
        """
            Convert MIDI files to WAV format.

            Args:
                path (str): Path to the MIDI files.
        """
        logger.info("Starting WAV conversion for %s", path)
        # Bounce full multitrack
        self.loader.export_midi_file(fr'{self.midi_file_path}', name=f'{self.audio_stem_path}/{self.songname} - All.wav', format='wav')

        for filename in os.listdir(path):
            f = os.path.join(path, filename)
            stem_name, ext = os.path.splitext(filename)
            if os.path.isfile(f) and ext == self.file_extension:
                logger.info("Rendering %s -> %s.wav", filename, stem_name)
                self.loader.export_midi_file(fr'{f}', name=f'{self.audio_stem_path}/{stem_name}.wav', format='wav')
            else:
                self.convert_to_wav(path=f"{self.midi_stem_path}/{filename}")

