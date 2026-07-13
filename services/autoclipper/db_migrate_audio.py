import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'character_memory.db')

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update Characters Table with Voice Identity Metadata
    try:
        cursor.execute("ALTER TABLE Characters ADD COLUMN language TEXT DEFAULT 'en-US'")
        cursor.execute("ALTER TABLE Characters ADD COLUMN speaking_style TEXT")
        cursor.execute("ALTER TABLE Characters ADD COLUMN emotional_profile TEXT")
    except sqlite3.OperationalError as e:
        print(f"[*] Schema update note for Characters (Voice Identity): {e}")

    conn.commit()
    conn.close()
    print("[*] Audio Layer Database Migration Complete.")

if __name__ == '__main__':
    migrate_database()
