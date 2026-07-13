import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'character_memory.db')

def setup_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Characters (
        char_id TEXT PRIMARY KEY,
        name TEXT,
        base_physical_traits TEXT,
        base_clothing TEXT,
        master_prompt TEXT,
        reference_image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Projects (
        project_id TEXT PRIMARY KEY,
        title TEXT,
        aspect_ratio TEXT,
        global_style TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Scenes (
        scene_id TEXT PRIMARY KEY,
        project_id TEXT,
        sequence_order INTEGER,
        active_characters TEXT, 
        scene_action TEXT,
        continuity_modifiers TEXT,
        final_prompt TEXT,
        status TEXT,
        FOREIGN KEY(project_id) REFERENCES Projects(project_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Generations_Log (
        job_id TEXT PRIMARY KEY,
        scene_id TEXT,
        video_url TEXT,
        qa_score REAL,
        error_reason TEXT,
        attempt_number INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(scene_id) REFERENCES Scenes(scene_id)
    )
    ''')

    conn.commit()
    conn.close()
    print("[*] Character Memory Database Setup Complete.")

if __name__ == '__main__':
    setup_database()
