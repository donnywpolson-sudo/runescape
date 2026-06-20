from __future__ import annotations

import sqlite3

import pytest

from game.engine import auth


def test_registering_user_stores_password_material_without_plaintext(tmp_path):
    db_path = tmp_path / "users.db"

    account = auth.register_user("alice", "correct horse battery staple", db_path)

    assert account.username == "alice"
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT password_salt, password_hash FROM users WHERE username = ?",
            ("alice",),
        ).fetchone()

    assert row is not None
    salt, password_hash = row
    assert salt
    assert password_hash
    assert b"correct horse battery staple" not in salt
    assert b"correct horse battery staple" not in password_hash


def test_preventing_duplicate_usernames(tmp_path):
    db_path = tmp_path / "users.db"
    auth.register_user("alice", "first-password", db_path)

    with pytest.raises(auth.UsernameAlreadyExists):
        auth.register_user("alice", "second-password", db_path)


def test_verifying_correct_password(tmp_path):
    db_path = tmp_path / "users.db"
    auth.register_user("alice", "swordfish", db_path)

    assert auth.verify_user("alice", "swordfish", db_path)


def test_rejecting_wrong_password(tmp_path):
    db_path = tmp_path / "users.db"
    auth.register_user("alice", "swordfish", db_path)

    assert not auth.verify_user("alice", "wrong-password", db_path)


def test_login_updates_last_login_timestamp(tmp_path):
    db_path = tmp_path / "users.db"
    auth.register_user("alice", "swordfish", db_path)

    account = auth.login_user("alice", "swordfish", db_path)

    assert account is not None
    assert account.last_login_at is not None
