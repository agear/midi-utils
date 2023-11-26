from programs import PERCUSSION

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
        if not (26 < number < 82):
            raise ValueError(f"Percussion Instrument number must be between 27 and 81. Received: {number}")

        self.number: int = number
        self.name: str = PERCUSSION[self.number]

    def __eq__(self, other):
        if isinstance(other, Percussion_Instrument):
            return self.number == other.number

        return NotImplemented

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash((self.number, self.name))
