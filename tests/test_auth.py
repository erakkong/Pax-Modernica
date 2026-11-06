"""
Unit tests for Pax Modernica Argon2id Security & Auth.
"""

import pytest
from server.auth.security import hash_password, verify_password, generate_session_token

def test_argon2id_hashing():
    pw = "Kaiserreich1700!"
    hashed = hash_password(pw)
    assert hashed.startswith("$argon2id$")
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_session_token_entropy():
    t1 = generate_session_token()
    t2 = generate_session_token()
    assert len(t1) == 64
    assert t1 != t2
