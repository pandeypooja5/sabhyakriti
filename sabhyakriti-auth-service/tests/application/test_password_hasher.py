from hypothesis import given, settings, strategies as st

from application.services.password_hasher import hash_password, verify_password


@given(st.text(min_size=8, max_size=128))
@settings(max_examples=20)
def test_hash_verify_roundtrip(password: str) -> None:
    hashed = hash_password(password)
    assert verify_password(password, hashed)


@given(st.text(min_size=8, max_size=64))
@settings(max_examples=10)
def test_wrong_password_fails(password: str) -> None:
    hashed = hash_password(password)
    assert not verify_password(password + "x", hashed)


def test_hash_is_not_plaintext() -> None:
    h = hash_password("mysecret")
    assert "mysecret" not in h


def test_hashes_are_unique() -> None:
    h1 = hash_password("samepassword")
    h2 = hash_password("samepassword")
    assert h1 != h2  # salt ensures uniqueness
