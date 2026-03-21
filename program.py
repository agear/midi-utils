from programs import PROGRAMS

_NUM_PROGRAMS = 128  # General MIDI defines exactly 128 programs (0–127)


class Program:
    """
    Represents a General MIDI program (instrument) with validation.

    Example:
        program = Program(5)
        print(program.program_number)   # 5
        print(program.get_program_name())  # '5 - Electric Piano 2'
    """

    def __init__(self, program_number: int = 0):
        if not isinstance(program_number, int):
            raise TypeError(f"program_number must be an integer. Received: {program_number}")
        if not 0 <= program_number < _NUM_PROGRAMS:
            raise ValueError(f"Invalid program number. Received: {program_number}")
        self._program_number: int = program_number
        self._program_name: str = PROGRAMS[self._program_number]

    def get_program_name(self) -> str:
        return self._program_name

    @property
    def program_number(self):
        return self._program_number

    @program_number.setter
    def program_number(self, program_number):
        if not isinstance(program_number, int):
            raise TypeError(f"program_number must be an integer. Received: {program_number}")
        if not 0 <= program_number < _NUM_PROGRAMS:
            raise ValueError(f"Invalid program number. Received: {program_number}")
        self._program_number = program_number
        self._program_name = PROGRAMS[self._program_number]
