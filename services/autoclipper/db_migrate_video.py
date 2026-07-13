import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'character_memory.db')

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Video_Jobs Table to track async video generation requests
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Video_Jobs (
                job_id TEXT PRIMARY KEY,
                scene_id TEXT,
                provider TEXT,
                prompt TEXT,
                status TEXT,
                download_url TEXT,
                local_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add generated_video_url to Scenes if not exists
        cursor.execute("ALTER TABLE Scenes ADD COLUMN generated_video_url TEXT")
    except sqlite3.OperationalError as e:
        print(f"[*] Schema update note for Video Layer: {e}")

    conn.commit()
    conn.close()
    print("[*] Video Layer Database Migration Complete.")

if __name__ == '__main__':
    migrate_database()
