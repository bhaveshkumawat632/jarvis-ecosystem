import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'character_memory.db')

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create Render_Jobs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Render_Jobs (
        job_id TEXT PRIMARY KEY,
        project_id TEXT,
        status TEXT,
        total_duration_rendered REAL,
        output_resolution TEXT,
        final_movie_url TEXT,
        FOREIGN KEY(project_id) REFERENCES Projects(project_id)
    )
    ''')

    conn.commit()
    conn.close()
    print("[*] Editor Matrix Database Migration Complete.")

if __name__ == '__main__':
    migrate_database()
