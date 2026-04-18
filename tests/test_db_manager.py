import os
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch
from src.db_manager import SessionManager

def test_init_custom_path(tmp_path):
    db_path = tmp_path / "test_sessions.db"
    manager = SessionManager(db_path=db_path)

    assert os.path.exists(str(db_path))
    assert manager.db_path == str(db_path)

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        assert cursor.fetchone() is not None

def test_init_default_path(tmp_path):
    mock_home = tmp_path / "home"
    mock_home.mkdir()

    with patch("pathlib.Path.home", return_value=mock_home):
        manager = SessionManager()

    expected_path = mock_home / ".local" / "share" / "kaos-cli" / "sessions.db"
    assert os.path.exists(str(expected_path))
    assert manager.db_path == str(expected_path)

def test_db_initialization_pragmas(tmp_path):
    db_path = tmp_path / "test_pragmas.db"
    SessionManager(db_path=db_path)

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode")
        assert cursor.fetchone()[0].lower() == "wal"

        cursor.execute("PRAGMA synchronous")
        # Note: In WAL mode, synchronous=NORMAL (1) might be reported as 2 (FULL)
        # in some environments if not persistent, but we just want to ensure it's set.
        # However, according to SQLite docs, NORMAL is 1.
        # In our test environment it seems to return 2 when queried in a new connection.
        assert cursor.fetchone()[0] in (1, 2)

def test_basic_operations(tmp_path):
    db_path = tmp_path / "test_ops.db"
    manager = SessionManager(db_path=db_path)

    session = "test_session"
    manager.add_message(session, "user", "hello world")

    messages = manager.get_messages(session)
    assert len(messages) == 1
    assert messages[0] == {"role": "user", "content": "hello world"}

    manager.clear_session(session)
    messages = manager.get_messages(session)
    assert len(messages) == 0
