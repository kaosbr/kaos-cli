import sqlite3
import os
from pathlib import Path

class SessionManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_dir = Path.home() / ".local" / "share" / "kaos-cli"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / "sessions.db"
            
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Performance Tuning: WAL mode and normal synchronous for speed & stability
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA synchronous=NORMAL')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            # Silently fail or log to stderr if needed
            import sys
            print(f"[!] Error initializing DB: {e}", file=sys.stderr)

    def add_message(self, session_name: str, role: str, content: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages (session_name, role, content) VALUES (?, ?, ?)",
                    (session_name, role, content)
                )
                conn.commit()
        except Exception: pass

    def get_messages(self, session_name: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role, content FROM messages WHERE session_name = ? ORDER BY id ASC",
                    (session_name,)
                )
                return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
        except Exception: return []

    def clear_session(self, session_name: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE session_name = ?", (session_name,))
                conn.commit()
        except Exception: pass
