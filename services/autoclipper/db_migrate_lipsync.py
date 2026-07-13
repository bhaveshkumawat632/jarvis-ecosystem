import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'character_memory.db')

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Update Characters Table
    try:
        cursor.execute("ALTER TABLE Characters ADD COLUMN voice_provider TEXT")
        cursor.execute("ALTER TABLE Characters ADD COLUMN voice_api_id TEXT")
        cursor.execute("ALTER TABLE Characters ADD COLUMN voice_settings TEXT")
    except sqlite3.OperationalError as e:
        print(f"[*] Schema update note for Characters: {e}")

    # 2. Create Dialogues Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Dialogues (
        dialogue_id TEXT PRIMARY KEY,
        scene_id TEXT,
        char_id TEXT,
        dialogue_text TEXT,
        is_narration BOOLEAN,
        generated_audio_url TEXT,
        sync_status TEXT,
        FOREIGN KEY(scene_id) REFERENCES Scenes(scene_id),
        FOREIGN KEY(char_id) REFERENCES Characters(char_id)
    )
    ''')

    # 3. Update Generations_Log Table
    try:
        cursor.execute("ALTER TABLE Generations_Log ADD COLUMN synced_video_url TEXT")
    except sqlite3.OperationalError as e:
        print(f"[*] Schema update note for Generations_Log: {e}")

    conn.commit()
    conn.close()
    print("[*] Dialogue & Lip-Sync Database Migration Complete.")

if __name__ == '__main__':
    migrate_database()
