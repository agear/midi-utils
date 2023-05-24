from programs import PROGRAMS

class Program:
    def __init__(self, program_number: int=0):
        self.program_number: int = program_number
        self.program_name: str = PROGRAMS[self.program_number]
