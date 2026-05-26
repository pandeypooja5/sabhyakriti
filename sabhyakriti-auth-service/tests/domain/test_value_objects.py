import pytest
from hypothesis import given, strategies as st

from domain.value_objects import IndianPhoneNumber, TokenPair, UserRole


class TestIndianPhoneNumber:
    @pytest.mark.parametrize("number", [
        "9876543210", "8012345678", "7000000001", "6111111111",
        "+919876543210", "919876543210", "09876543210",
    ])
    def test_valid_numbers(self, number: str) -> None:
        phone = IndianPhoneNumber(number)
        assert len(phone.number) == 10
        assert phone.number[0] in "6789"

    @pytest.mark.parametrize("number", [
        "5876543210",   # starts with 5 — invalid
        "123456789",    # 9 digits
        "12345678901",  # 11 digits
        "abcdefghij",   # non-numeric
        "",
    ])
    def test_invalid_numbers_raise(self, number: str) -> None:
        with pytest.raises(ValueError):
            IndianPhoneNumber(number)

    @given(st.text(alphabet=st.characters(blacklist_categories=("Nd",)), min_size=1, max_size=15))
    def test_non_digit_strings_raise(self, s: str) -> None:
        # Property: any string with no digits should raise
        if not any(c.isdigit() for c in s):
            with pytest.raises(ValueError):
                IndianPhoneNumber(s)

    def test_str_returns_normalised(self) -> None:
        assert str(IndianPhoneNumber("+919876543210")) == "9876543210"


class TestTokenPair:
    def test_defaults(self) -> None:
        tp = TokenPair(access_token="a", refresh_token="r")
        assert tp.token_type == "Bearer"
        assert tp.expires_in == 1800


class TestUserRole:
    def test_values(self) -> None:
        assert UserRole.CUSTOMER == "CUSTOMER"
        assert UserRole.ADMIN == "ADMIN"
