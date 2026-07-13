import sqlite3
import os
import uuid
from .character_manager import get_db_connection

class EnvironmentManager:
    def __init__(self):
        pass

    def create_environment(self, name, architecture, lighting, reference_url=""):
        env_id = str(uuid.uuid4())
        master_env_prompt = f"Location '{name}': {architecture}. Atmosphere: {lighting}. (Maintain structural integrity and layout)"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Environments (env_id, name, base_architecture, base_lighting_colors, master_env_prompt, reference_image_url) VALUES (?, ?, ?, ?, ?, ?)",
            (env_id, name, architecture, lighting, master_env_prompt, reference_url)
        )
        conn.commit()
        conn.close()
        return env_id

    def get_environment(self, env_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Environments WHERE env_id = ?", (env_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "env_id": row[0],
                "name": row[1],
                "architecture": row[2],
                "lighting": row[3],
                "master_env_prompt": row[4],
                "reference_url": row[5]
            }
        return None
