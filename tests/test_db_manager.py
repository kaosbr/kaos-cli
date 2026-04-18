import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add the parent directory to sys.path to allow importing from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db_manager import SessionManager


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_session_manager_init(temp_db):
    manager = SessionManager(db_path=temp_db)
    assert os.path.exists(temp_db)

    # Check if table exists
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        assert cursor.fetchone() is not None


def test_add_and_get_messages(temp_db):
    manager = SessionManager(db_path=temp_db)

    session_name = "test_session"
    manager.add_message(session_name, "user", "Hello world")
    manager.add_message(session_name, "assistant", "Hi there")

    messages = manager.get_messages(session_name)
    assert len(messages) == 2
    assert messages[0] == {"role": "user", "content": "Hello world"}
    assert messages[1] == {"role": "assistant", "content": "Hi there"}


def test_clear_session(temp_db):
    manager = SessionManager(db_path=temp_db)

    session_name1 = "test_session1"
    session_name2 = "test_session2"

    manager.add_message(session_name1, "user", "Msg 1")
    manager.add_message(session_name2, "user", "Msg 2")

    manager.clear_session(session_name1)

    assert len(manager.get_messages(session_name1)) == 0
    assert len(manager.get_messages(session_name2)) == 1


def test_invalid_db_path():
    # Attempting to use a directory as a db_path or a path we can't write to
    manager = SessionManager(db_path="/dev/null/invalid.db")

    # These should silently fail and not raise exceptions
    manager.add_message("test", "user", "msg")
    messages = manager.get_messages("test")
    assert messages == []
    manager.clear_session("test")
