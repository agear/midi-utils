import logging
from programs import PERCUSSION
from typing import Union

logger = logging.getLogger(__name__)

_warned_notes: set = set()

class Percussion_Instrument:
    """
    The Percussion_Instrument class represents a percussion instrument with a number and a name. It provides methods for comparing instruments, converting to a string, and generating a hash value.
    Example Usage
    # Create a percussion instrument with number 35
    instrument = Percussion_Instrument(35)

    # Print the name of the instrument
    print(instrument)  # Output: "35 - Acoustic Bass Drum"

    # Compare two instruments
    instrument1 = Percussion_Instrument(35)
    instrument2 = Percussion_Instrument(36)
    print(instrument1 == instrument2)  # Output: False
    """
    def __init__(self, number: int):
        if not isinstance(number, int):
            raise TypeError(f"Number should be an integer. Received: {type(number)}")
        self.number: int = number
        if number not in PERCUSSION and number not in _warned_notes:
            _warned_notes.add(number)
            logger.warning("Non-standard percussion note %d — not in PERCUSSION dictionary", number)
        self.name: str = PERCUSSION.get(number, f"{number} - Unknown Percussion")

    def __eq__(self, other) -> bool:
        if isinstance(other, Percussion_Instrument):
            return self.number == other.number

        return NotImplemented

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash((self.number, self.name))
