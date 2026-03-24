import logging
import os
import subprocess
import tempfile
from typing import List, Optional

import midi
import sf2_loader as sf
from encapsulated_midi_event import Encapsulated_Midi_Event
from encapsulated_midi_track import Encapsulated_Midi_Track
from percussion_instrument import Percussion_Instrument
from program import Program

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self, midi_file_path: str, soundfont_path: str, convert_to_wav: bool, output_path: Optional[str] = None):
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
            output_path (str, optional): Output path for storing stems, Defaults to current directory (".").
        """
        self.midi_file_path: str = midi_file_path
        self.songname, self.file_extension = os.path.splitext(os.path.basename(midi_file_path))
        logger.info("Loading %s", midi_file_path)
        self.convert_to_wav_flag: bool = convert_to_wav
        self.soundfont_path: str = soundfont_path
        self.loader: sf.sf2_loader = sf.sf2_loader(soundfont_path)
        self.midi_multitrack: midi.Pattern = self._load_midi(self.midi_file_path)
        self.resolution: int = self.midi_multitrack.resolution
        resolved_output = output_path if output_path is not None else os.path.dirname(os.path.abspath(midi_file_path))
        self.stems_path: str = os.path.join(resolved_output, f"{self.songname} Stems")
        logger.debug("Stems path: %s", self.stems_path)
        self.transport_track: midi.Track = midi.Track()
        self._make_directories()
        self.encapsulated_midi: List[Encapsulated_Midi_Track] = []


    @staticmethod
    def _load_midi(path: str) -> midi.Pattern:
        """
        Read a MIDI file, automatically correcting a zero track-count header.

        Some Guitar Pro exports write 0 in the MThd track-count field even
        though the file contains valid MTrk chunks.  The Python MIDI library
        honours that count literally and returns an empty Pattern, which causes
        all downstream processing to silently produce no output.

        When the header claims 0 tracks but the file contains at least one
        MTrk chunk, the header bytes are patched in a temporary copy and the
        corrected file is re-read.
        """
        pattern = midi.read_midifile(path)
        if len(pattern) > 0:
            return pattern

        with open(path, 'rb') as f:
            data = bytearray(f.read())

        actual = data.count(b'MTrk')
        if actual == 0:
            raise ValueError(f"MIDI file contains no track data: {path}")

        logger.warning(
            "Corrupt MIDI header in %s: track count is 0 but %d MTrk chunk(s) found — patching and reloading",
            path, actual,
        )
        # MThd layout: 4-byte tag | 4-byte length | 2-byte format | 2-byte ntracks | 2-byte division
        # ntracks is at bytes 10–11
        data[10] = (actual >> 8) & 0xFF
        data[11] = actual & 0xFF

        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            pattern = midi.read_midifile(tmp_path)
        finally:
            os.unlink(tmp_path)

        return pattern

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

    def _render_to_wav(self, midi_path: str, wav_path: str, *, reverb: bool) -> None:
        """
        Render a MIDI file to WAV using the FluidSynth CLI.

        Using the CLI (rather than sf2_loader's note-by-note renderer) means
        FluidSynth processes the full MIDI event stream natively — including
        CC 91 (Reverb Send Level) — producing output identical to VLC.

        Args:
            midi_path: Path to the source MIDI file.
            wav_path:  Destination WAV file path.
            reverb:    True to render with reverb active; False to suppress it
                       entirely (passes -R 0 -C 0 to FluidSynth).
        """
        cmd = ['fluidsynth', '-ni', '-a', 'file', '-T', 'wav', '-F', wav_path]
        if not reverb:
            cmd += ['-R', '0', '-C', '0']
        cmd += [self.soundfont_path, midi_path]
        logger.info("Rendering %s", wav_path)
        result = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL)
        if result.returncode != 0:
            raise RuntimeError(
                f"FluidSynth failed rendering {midi_path}: "
                f"{result.stderr.decode().strip()}"
            )

    def convert_to_wav(self, path: str) -> None:
        """
            Convert MIDI files to WAV format.

            Args:
                path (str): Path to the MIDI files.
        """
        logger.info("Starting WAV conversion for %s", path)
        # Write the in-memory pattern to a temp file so FluidSynth always
        # receives a valid MIDI header (the source file may be corrupt).
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            midi.write_midifile(tmp_path, self.midi_multitrack)
            # Bounce full multitrack — split into wet/dry if reverb is present
            if Encapsulated_Midi_Track._has_reverb(self.midi_multitrack):
                self._render_to_wav(tmp_path, f'{self.audio_stem_path}/{self.songname} - All - wet.wav', reverb=True)
                self._render_to_wav(tmp_path, f'{self.audio_stem_path}/{self.songname} - All - dry.wav', reverb=False)
            else:
                self._render_to_wav(tmp_path, f'{self.audio_stem_path}/{self.songname} - All.wav', reverb=False)
        finally:
            os.unlink(tmp_path)

        for filename in os.listdir(path):
            f = os.path.join(path, filename)
            stem_name, ext = os.path.splitext(filename)
            if os.path.isfile(f) and ext == self.file_extension:
                is_wet = stem_name.endswith(' - wet')
                self._render_to_wav(f, f'{self.audio_stem_path}/{stem_name}.wav', reverb=is_wet)
            else:
                self.convert_to_wav(path=f"{self.midi_stem_path}/{filename}")

