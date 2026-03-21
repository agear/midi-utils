import os
from typing import List
from copy import deepcopy
import midi
from encapsulated_midi_event import Encapsulated_Midi_Event
from percussion_instrument import Percussion_Instrument
from typing import Optional

class Encapsulated_Midi_Track:
    """
        The Midi_Track_AG class represents a MIDI track and provides functionalities to extract and
        manipulate MIDI events within the track.

        Example Usage
        # Create a Midi_Track_AG object
        track = Midi_Track_AG(events, track_number, controller)

        # Extract programs from the track
        track.extract_programs()

        # Write the track to MIDI files
        track.write()

        # Extract MIDI drum stems from the track
        track.extract_midi_drum_stems(i, track)

        # Get the list of percussion instruments in the track
        percussion_instruments = Midi_Track_AG.get_percussion_instruments(track)
    """
    def __init__(self, events: midi.Track, track_number: int, controller):
        self.events: List[Encapsulated_Midi_Event] = self.encapsulate_midi_events(track=events, track_number=track_number)
        self.programs: List[str] = self._get_program_names()
        self.transport_track = controller.transport_track
        self.resolution: int = controller.resolution
        self.midi_stem_path: str = controller.midi_stem_path
        self.songname: str = controller.songname
        self.track_number: str = self._get_formatted_track_number(i=track_number)
        self.patterns: List[midi.Pattern] = []
        self.drums: str = self._is_drum_track()
        self.is_drums: bool = bool(self.drums)
        self.extract_programs()

    def encapsulate_midi_events(self, track: midi.Track, track_number: int):
        """
        Wrap each event in a track with its current program context.

        Args:
            track (midi.Track): MIDI track to encapsulate.
            track_number (int): Track number.

        Returns:
            List[Encapsulated_Midi_Event]: Encapsulated events.
        """
        current_program: Optional[int] = None
        encapsulated_track: List[Encapsulated_Midi_Event] = []
        for event in track:
            event_copy: midi.Event = deepcopy(event)
            if type(event_copy) == midi.ProgramChangeEvent:
                current_program = event_copy.data[0]
            encapsulated_event: Encapsulated_Midi_Event = Encapsulated_Midi_Event(event=event_copy, program_number=current_program)
            encapsulated_track.append(encapsulated_event)
        return encapsulated_track

    def _is_drum_track(self) -> str:
        """Checks if the track is a drum track by analyzing the MIDI events."""
        for event in self.events:
            if type(event.event) == midi.ProgramChangeEvent:
                if event.event.channel == 9:
                    self.extract_midi_drum_stems(i=self.track_number, track=self.events)
                    return "- 0 - Drum Kit 0 "
        return ""

    def _get_program_names(self):
        """Retrieves the unique program names from the MIDI events in the track."""
        program_names = set()
        for event in self.events:
            try:
                program_names.add(event.program_name)
            except AttributeError:
                pass


        print(f'Programs: {list(program_names)}')
        return list(program_names)

    def _get_formatted_track_number(self, i: int) -> str:
        """Formats the track number as a string with leading zeros if necessary."""
        if len(str(i+1)) == 2:
            return str(i+1)
        track_number = "0"
        track_number += str(i+1)
        return track_number

    def extract_programs(self):
        """Extracts programs from the track and creates MIDI patterns for each program."""
        for program_name in self.programs:
            if program_name == 'None':
                continue

            pattern = midi.Pattern(resolution=self.resolution)
            pattern.append(self.transport_track)
            track = midi.Track()
            for event in self.events:
                if event.program_name == 'None' or event.program_name == program_name:
                    track.append(deepcopy(event.event))
                elif type(event.event) == midi.NoteOnEvent and event.program_name != program_name:
                    event_copy = deepcopy(event.event)
                    event_copy.data[1] = 0  # mute NoteOns that belong to other programs
                    track.append(event_copy)
                else:
                    track.append(deepcopy(event.event))
            pattern.append(track)
            self.patterns.append((program_name, pattern))

        return self.patterns

    def write(self) -> None:
        """Writes the MIDI patterns to separate MIDI files."""
        for pattern in self.patterns:
            instrument_name = pattern[0]
            filename: str = f"{self.midi_stem_path}/{self.songname} - {self.track_number} {self.drums}- {instrument_name}.mid"
            midi.write_midifile(filename, pattern[1])

    def extract_midi_drum_stems(self, i: int, track: midi.Track) -> None:
        """
            Extracts MIDI drum stems from the track and saves them as separate MIDI files.

            Args:
                i (int): Track number.
                track (midi.Track): MIDI drum track.
        """
        percussion_instruments: List[Percussion_Instrument] = self.get_percussion_instruments(track)

        percussion_path: str = f"{self.midi_stem_path}/{self.songname} - {self.track_number} - 0 - Drum Kit 0"

        os.makedirs(name=percussion_path, exist_ok=True)

        for instrument in percussion_instruments:
            pattern: midi.Pattern = midi.Pattern(resolution=self.resolution)
            if self.transport_track:
                pattern.append(self.transport_track)
            percussion_track: midi.Track = midi.Track()
            for event in track:
                event_copy: midi.Event = deepcopy(event)
                if type(event_copy.event) == midi.NoteOnEvent and event_copy.event.data[0] != instrument.number:
                    event_copy.event.data[1] = 0  # mute other drum instruments
                percussion_track.append(event_copy.event)
            pattern.append(percussion_track)
            midi.write_midifile(f"{percussion_path}/{self.songname} - {self.track_number} - 0 - Drum Kit 0 - {instrument.name}.mid", pattern)

    @staticmethod
    def get_percussion_instruments(track: midi.Track) -> List[Percussion_Instrument]:
        """
        Retrieves the list of unique percussion instruments from the track.

        Args:
            track: List of Encapsulated_Midi_Event objects.

        Returns:
            List[Percussion_Instrument]: List of percussion instruments.
        """
        percussion_instruments = set()
        for event in track:
            if type(event.event) == midi.NoteOnEvent:
                percussion_instruments.add(Percussion_Instrument(event.event.data[0]))
        return list(percussion_instruments)
