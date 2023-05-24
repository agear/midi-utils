from programs import PERCUSSION

class Percussion_Instrument:
    def __init__(self, number: int):
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
