
from src.services.group_order_utils import (
    generate_share_code,
    generate_member_credential,
    hash_credential
)


def test_share_code_length():
    # The default share code should contain 8 characters
    code = generate_share_code()

    assert len(code) == 8


def test_share_code_characters():
    # Share codes should only use allowed characters
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    for _ in range(100):
        code = generate_share_code()

        assert all(char in alphabet for char in code)


def test_share_codes_are_random():
    # Multiple generations should produce different codes
    codes = [generate_share_code() for _ in range(100)]

    assert len(set(codes)) == 100


def test_member_credential():
    # A private credential should be a nonempty string
    credential = generate_member_credential()

    assert isinstance(credential, str)
    assert len(credential) > 0


def test_credential_hashing():
    # The same credential should always produce the same hash
    credential = "test_private_credential"

    hash1 = hash_credential(credential)
    hash2 = hash_credential(credential)

    assert hash1 == hash2

    # A hash should not reveal the original credential
    assert hash1 != credential


def test_different_credentials_have_different_hashes():
    # Different inputs should produce different hash values
    hash1 = hash_credential("credential_one")
    hash2 = hash_credential("credential_two")

    assert hash1 != hash2
