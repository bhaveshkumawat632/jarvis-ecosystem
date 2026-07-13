import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'character_memory.db')

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create Director_Styles Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Director_Styles (
        style_id TEXT PRIMARY KEY,
        name TEXT,
        preferred_lenses TEXT,
        color_grading_rules TEXT,
        pacing_baseline REAL
    )
    ''')

    # 2. Update Scenes Table with Directorial Metadata
    try:
        cursor.execute("ALTER TABLE Scenes ADD COLUMN director_style_id TEXT")
        cursor.execute("ALTER TABLE Scenes ADD COLUMN emotion_state TEXT")
        cursor.execute("ALTER TABLE Scenes ADD COLUMN narrative_tension INTEGER")
        cursor.execute("ALTER TABLE Scenes ADD COLUMN shot_type TEXT")
        cursor.execute("ALTER TABLE Scenes ADD COLUMN camera_motion TEXT")
        cursor.execute("ALTER TABLE Scenes ADD COLUMN duration_seconds REAL")
    except sqlite3.OperationalError as e:
        print(f"[*] Schema update note for Scenes: {e}")

    # 3. Create Audio_Timelines Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Audio_Timelines (
        audio_event_id TEXT PRIMARY KEY,
        scene_id TEXT,
        event_type TEXT,
        description TEXT,
        timestamp_start REAL,
        audio_url TEXT,
        FOREIGN KEY(scene_id) REFERENCES Scenes(scene_id)
    )
    ''')

    conn.commit()
    conn.close()
    print("[*] Director & Narrative Pacing Database Migration Complete.")

if __name__ == '__main__':
    migrate_database()
