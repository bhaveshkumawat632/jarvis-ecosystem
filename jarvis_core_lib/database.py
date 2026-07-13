import os
import sqlite3

def get_db_connection(db_path=None):
    """Establishes an isolated database connection with dict row formatting."""
    if db_path is None:
        db_path = os.environ.get("SQLITE_DB_PATH", "production_show_bible.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enables column fetching by name string
        return conn
    except sqlite3.Error as e:
        raise Exception(f"Database Connection Failure: {str(e)}")
