from programs import PERCUSSION

class Percussion_Instrument:
    def __init__(self, number: int):
        if not (26 < number < 82):
            raise ValueError(f"Percussion Instrument number must be between 27 and 81. Received: {number}")

        self.number: int = number
        self.name: str = PERCUSSION[self.number]

    def __eq__(self, other):
        if isinstance(other, Percussion_Instrument):
            return self.number == other.number

        return False

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.number)
