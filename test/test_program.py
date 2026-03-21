import pytest
from program import Program


class TestProgramInit:
    def test_default_is_zero(self):
        p = Program()
        assert p.program_number == 0
        assert p.get_program_name() == "0 - Acoustic Grand"

    def test_valid_min(self):
        p = Program(0)
        assert p.program_number == 0

    def test_valid_max(self):
        p = Program(127)
        assert p.program_number == 127
        assert p.get_program_name() == "127 - Gunshot"

    def test_valid_mid(self):
        p = Program(56)
        assert p.program_number == 56
        assert p.get_program_name() == "56 - Trumpet"

    def test_type_error_float(self):
        with pytest.raises(TypeError):
            Program(1.0)

    def test_type_error_string(self):
        with pytest.raises(TypeError):
            Program("0")

    def test_type_error_none(self):
        with pytest.raises(TypeError):
            Program(None)

    def test_type_error_list(self):
        with pytest.raises(TypeError):
            Program([0])

    def test_value_error_negative_one(self):
        with pytest.raises(ValueError):
            Program(-1)

    def test_value_error_large_negative(self):
        with pytest.raises(ValueError):
            Program(-100)

    def test_value_error_128(self):
        with pytest.raises(ValueError):
            Program(128)

    def test_value_error_large(self):
        with pytest.raises(ValueError):
            Program(500)


class TestProgramSetter:
    def test_setter_updates_number_and_name(self):
        p = Program(0)
        p.program_number = 56
        assert p.program_number == 56
        assert p.get_program_name() == "56 - Trumpet"

    def test_setter_valid_min(self):
        p = Program(50)
        p.program_number = 0
        assert p.program_number == 0
        assert p.get_program_name() == "0 - Acoustic Grand"

    def test_setter_valid_max(self):
        p = Program(0)
        p.program_number = 127
        assert p.program_number == 127

    def test_setter_type_error(self):
        p = Program(0)
        with pytest.raises(TypeError):
            p.program_number = "5"

    def test_setter_value_error_too_large(self):
        p = Program(0)
        with pytest.raises(ValueError):
            p.program_number = 128

    def test_setter_value_error_negative(self):
        p = Program(0)
        with pytest.raises(ValueError):
            p.program_number = -1

    def test_setter_name_stays_in_sync(self):
        p = Program(0)
        p.program_number = 1
        assert p._program_name == "1 - Bright Acoustic"


class TestProgramGetProgramName:
    def test_returns_correct_name_for_each_boundary(self):
        assert Program(0).get_program_name() == "0 - Acoustic Grand"
        assert Program(1).get_program_name() == "1 - Bright Acoustic"
        assert Program(126).get_program_name() == "126 - Applause"
        assert Program(127).get_program_name() == "127 - Gunshot"

    def test_all_128_programs_return_non_empty_string(self):
        for i in range(128):
            name = Program(i).get_program_name()
            assert isinstance(name, str)
            assert len(name) > 0

    def test_program_name_starts_with_number(self):
        for i in range(128):
            name = Program(i).get_program_name()
            assert name.startswith(str(i))
