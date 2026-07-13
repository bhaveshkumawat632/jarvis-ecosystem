import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'character_memory.db')

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create Scripts Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Scripts (
        script_id TEXT PRIMARY KEY,
        project_id TEXT,
        user_prompt TEXT,
        genre TEXT,
        target_duration_minutes INTEGER,
        act_structure_json TEXT,
        generation_status TEXT,
        FOREIGN KEY(project_id) REFERENCES Projects(project_id)
    )
    ''')

    conn.commit()
    conn.close()
    print("[*] Scriptwriter Matrix Database Migration Complete.")

if __name__ == '__main__':
    migrate_database()
