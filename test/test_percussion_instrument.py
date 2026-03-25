import pytest
from percussion_instrument import Percussion_Instrument
from programs import PERCUSSION


VALID_NUMBERS = sorted(PERCUSSION.keys())
MIN_KEY = min(VALID_NUMBERS)
MAX_KEY = max(VALID_NUMBERS)

# A number that is in the valid integer range but not in the PERCUSSION dict
INVALID_IN_RANGE = next(n for n in range(0, 200) if n not in PERCUSSION)


class TestPercussionInstrumentInit:
    def test_valid_kick(self):
        pi = Percussion_Instrument(36)
        assert pi.number == 36
        assert pi.name == PERCUSSION[36]

    def test_valid_min_key(self):
        pi = Percussion_Instrument(MIN_KEY)
        assert pi.number == MIN_KEY
        assert pi.name == PERCUSSION[MIN_KEY]

    def test_valid_max_key(self):
        pi = Percussion_Instrument(MAX_KEY)
        assert pi.number == MAX_KEY
        assert pi.name == PERCUSSION[MAX_KEY]

    def test_valid_all_percussion_keys(self):
        for key in VALID_NUMBERS:
            pi = Percussion_Instrument(key)
            assert pi.number == key
            assert pi.name == PERCUSSION[key]

    def test_type_error_float(self):
        with pytest.raises(TypeError):
            Percussion_Instrument(36.0)

    def test_type_error_string(self):
        with pytest.raises(TypeError):
            Percussion_Instrument("36")

    def test_type_error_none(self):
        with pytest.raises(TypeError):
            Percussion_Instrument(None)

    def test_type_error_list(self):
        with pytest.raises(TypeError):
            Percussion_Instrument([36])

    def test_unknown_note_gets_fallback_name(self):
        pi = Percussion_Instrument(INVALID_IN_RANGE)
        assert pi.name == f"{INVALID_IN_RANGE} - Unknown Percussion"

    def test_unknown_note_zero(self):
        pi = Percussion_Instrument(0)
        assert pi.name == "0 - Unknown Percussion"

    def test_unknown_note_negative(self):
        pi = Percussion_Instrument(-1)
        assert pi.name == "-1 - Unknown Percussion"

    def test_unknown_note_large(self):
        pi = Percussion_Instrument(200)
        assert pi.name == "200 - Unknown Percussion"

    def test_unknown_note_emits_warning(self, caplog):
        import logging
        import percussion_instrument
        percussion_instrument._warned_notes.discard(INVALID_IN_RANGE)
        with caplog.at_level(logging.WARNING, logger="percussion_instrument"):
            Percussion_Instrument(INVALID_IN_RANGE)
        assert any(str(INVALID_IN_RANGE) in m for m in caplog.messages)


class TestPercussionInstrumentEquality:
    def test_equal_same_number(self):
        a = Percussion_Instrument(36)
        b = Percussion_Instrument(36)
        assert a == b

    def test_not_equal_different_numbers(self):
        a = Percussion_Instrument(36)
        b = Percussion_Instrument(38)
        assert a != b

    def test_eq_with_string_returns_not_implemented(self):
        pi = Percussion_Instrument(36)
        assert pi.__eq__("36") is NotImplemented

    def test_eq_with_int_returns_not_implemented(self):
        pi = Percussion_Instrument(36)
        assert pi.__eq__(36) is NotImplemented

    def test_eq_with_none_returns_not_implemented(self):
        pi = Percussion_Instrument(36)
        assert pi.__eq__(None) is NotImplemented


class TestPercussionInstrumentStr:
    def test_str_returns_name(self):
        pi = Percussion_Instrument(36)
        assert str(pi) == PERCUSSION[36]

    def test_str_contains_number(self):
        pi = Percussion_Instrument(36)
        assert "36" in str(pi)


class TestPercussionInstrumentHash:
    def test_same_number_same_hash(self):
        a = Percussion_Instrument(36)
        b = Percussion_Instrument(36)
        assert hash(a) == hash(b)

    def test_different_number_different_hash(self):
        a = Percussion_Instrument(36)
        b = Percussion_Instrument(38)
        assert hash(a) != hash(b)

    def test_usable_in_set_deduplicates(self):
        instruments = {
            Percussion_Instrument(36),
            Percussion_Instrument(36),
            Percussion_Instrument(38),
        }
        assert len(instruments) == 2

    def test_usable_as_dict_key(self):
        pi = Percussion_Instrument(36)
        d = {pi: "kick"}
        assert d[pi] == "kick"
