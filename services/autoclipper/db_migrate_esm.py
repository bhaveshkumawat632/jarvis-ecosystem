import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'character_memory.db')

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create Environments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Environments (
        env_id TEXT PRIMARY KEY,
        name TEXT,
        base_architecture TEXT,
        base_lighting_colors TEXT,
        master_env_prompt TEXT,
        reference_image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Add columns to Scenes table
    try:
        cursor.execute("ALTER TABLE Scenes ADD COLUMN active_environment_id TEXT")
        cursor.execute("ALTER TABLE Scenes ADD COLUMN env_continuity_modifiers TEXT")
        cursor.execute("ALTER TABLE Scenes ADD COLUMN camera_spatial_anchor TEXT")
    except sqlite3.OperationalError as e:
        print(f"[*] Schema update note: {e}")

    conn.commit()
    conn.close()
    print("[*] Environment Spatial Memory (ESM) Database Migration Complete.")

if __name__ == '__main__':
    migrate_database()
