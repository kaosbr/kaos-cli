import unittest
import sqlite3
import tempfile
import os
import io
from unittest.mock import patch
from pathlib import Path

import sys
# Adiciona src ao path para importar db_manager
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db_manager import SessionManager


class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "sessions.db")
        self.manager = SessionManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_db_success(self):
        # Database should have been initialized in setUp
        self.assertTrue(os.path.exists(self.db_path))

        # Verify schema
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages';")
            table = cursor.fetchone()
            self.assertIsNotNone(table)

    @patch('sqlite3.connect')
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_init_db_failure(self, mock_stderr, mock_connect):
        mock_connect.side_effect = sqlite3.Error("Mocked DB error")

        # Should not raise exception
        manager = SessionManager(os.path.join(self.temp_dir.name, "fail.db"))
        self.assertIsNotNone(manager)

        # Verify stderr output
        self.assertIn("[!] Error initializing DB: Mocked DB error", mock_stderr.getvalue())

    def test_add_and_get_messages_success(self):
        session_name = "test_session"
        self.manager.add_message(session_name, "user", "Hello world")
        self.manager.add_message(session_name, "assistant", "Hi there!")

        messages = self.manager.get_messages(session_name)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello world")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "Hi there!")

    def test_get_messages_empty_session(self):
        messages = self.manager.get_messages("non_existent_session")
        self.assertEqual(len(messages), 0)

    def test_get_messages_with_known_records(self):
        session_name = "known_records_session"
        # Setup test db with known records directly via sqlite3 to test get_messages logic
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Insert out of order to ensure get_messages sorts by id ASC
            cursor.execute("INSERT INTO messages (id, session_name, role, content) VALUES (?, ?, ?, ?)", (2, session_name, "assistant", "Response"))
            cursor.execute("INSERT INTO messages (id, session_name, role, content) VALUES (?, ?, ?, ?)", (1, session_name, "user", "Hello"))
            # Insert record for another session to ensure filtering works
            cursor.execute("INSERT INTO messages (id, session_name, role, content) VALUES (?, ?, ?, ?)", (3, "other_session", "user", "Other"))
            conn.commit()

        messages = self.manager.get_messages(session_name)

        self.assertEqual(len(messages), 2)
        # Verify ordering by id ASC
        self.assertEqual(messages[0], {"role": "user", "content": "Hello"})
        self.assertEqual(messages[1], {"role": "assistant", "content": "Response"})

    @patch('sqlite3.connect')
    def test_add_message_failure(self, mock_connect):
        mock_connect.side_effect = sqlite3.Error("Mocked DB error")

        # Should not raise exception
        self.manager.add_message("session", "user", "test")

    @patch('sqlite3.connect')
    def test_get_messages_failure(self, mock_connect):
        mock_connect.side_effect = sqlite3.Error("Mocked DB error")

        # Should return empty list on failure
        messages = self.manager.get_messages("session")
        self.assertEqual(messages, [])

    def test_clear_session_success(self):
        session_name = "test_session"
        self.manager.add_message(session_name, "user", "Hello world")
        self.manager.add_message("other_session", "user", "Don't delete me")

        self.manager.clear_session(session_name)

        messages = self.manager.get_messages(session_name)
        self.assertEqual(len(messages), 0)

        other_messages = self.manager.get_messages("other_session")
        self.assertEqual(len(other_messages), 1)

    @patch('sqlite3.connect')
    def test_clear_session_failure(self, mock_connect):
        mock_connect.side_effect = sqlite3.Error("Mocked DB error")

        # Should not raise exception
        self.manager.clear_session("session")

if __name__ == '__main__':
    unittest.main()
