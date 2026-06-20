"""Local-only account storage for the Panda3D RPG prototype."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
import secrets
import sqlite3

from game import settings


DEFAULT_DB_PATH = settings.USERS_DB_PATH
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 32
MAX_USERNAME_LENGTH = 32


@dataclass(frozen=True)
class Account:
    username: str
    created_at: str
    last_login_at: str | None


class UsernameAlreadyExists(ValueError):
    """Raised when a local account username is already registered."""


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    connection = _connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                password_salt BLOB NOT NULL,
                password_hash BLOB NOT NULL,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def register_user(
    username: str,
    password: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> Account:
    username = _normalize_username(username)
    password_bytes = _password_to_bytes(password)
    init_db(db_path)

    connection = _connect(db_path)
    try:
        if _get_user_row(connection, username) is not None:
            raise UsernameAlreadyExists("Username already exists")

        salt = secrets.token_bytes(SALT_BYTES)
        password_hash = _hash_password(password_bytes, salt)
        created_at = _utc_now()
        connection.execute(
            """
            INSERT INTO users (
                username,
                password_salt,
                password_hash,
                created_at,
                last_login_at
            )
            VALUES (?, ?, ?, ?, NULL)
            """,
            (username, salt, password_hash, created_at),
        )
        connection.commit()
        return Account(username=username, created_at=created_at, last_login_at=None)
    finally:
        connection.close()


def verify_user(
    username: str,
    password: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> bool:
    username = _normalize_username(username)
    password_bytes = _password_to_bytes(password)
    init_db(db_path)

    connection = _connect(db_path)
    try:
        row = _get_user_row(connection, username)
        if row is None:
            return False
        return _password_matches(password_bytes, row["password_salt"], row["password_hash"])
    finally:
        connection.close()


def login_user(
    username: str,
    password: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> Account | None:
    username = _normalize_username(username)
    password_bytes = _password_to_bytes(password)
    init_db(db_path)

    connection = _connect(db_path)
    try:
        row = _get_user_row(connection, username)
        if row is None:
            return None
        if not _password_matches(password_bytes, row["password_salt"], row["password_hash"]):
            return None

        last_login_at = _utc_now()
        connection.execute(
            "UPDATE users SET last_login_at = ? WHERE username = ? COLLATE NOCASE",
            (last_login_at, username),
        )
        connection.commit()
        return Account(
            username=row["username"],
            created_at=row["created_at"],
            last_login_at=last_login_at,
        )
    finally:
        connection.close()


authenticate_user = login_user


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _get_user_row(connection: sqlite3.Connection, username: str) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT username, password_salt, password_hash, created_at, last_login_at
        FROM users
        WHERE username = ? COLLATE NOCASE
        """,
        (username,),
    ).fetchone()


def _normalize_username(username: str) -> str:
    normalized = username.strip()
    if not normalized:
        raise ValueError("Username is required")
    if len(normalized) > MAX_USERNAME_LENGTH:
        raise ValueError(f"Username must be {MAX_USERNAME_LENGTH} characters or fewer")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError("Username contains unsupported characters")
    return normalized


def _password_to_bytes(password: str) -> bytes:
    if not password:
        raise ValueError("Password is required")
    return password.encode("utf-8")


def _hash_password(password: bytes, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password,
        salt,
        PBKDF2_ITERATIONS,
    )


def _password_matches(password: bytes, salt: bytes, expected_hash: bytes) -> bool:
    candidate_hash = _hash_password(password, salt)
    return hmac.compare_digest(candidate_hash, expected_hash)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
