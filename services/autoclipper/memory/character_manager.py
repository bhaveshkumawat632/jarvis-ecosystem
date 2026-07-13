import sqlite3
import os
import uuid
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db', 'character_memory.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

class CharacterManager:
    def __init__(self):
        pass

    def create_character(self, name, physical_traits, clothing, reference_url="", voice_provider="elevenlabs", voice_api_id="default_voice"):
        char_id = str(uuid.uuid4())
        master_prompt = f"Character '{name}': {physical_traits}. Usually wearing {clothing}. (Highly consistent face and body type)"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Characters (char_id, name, base_physical_traits, base_clothing, master_prompt, reference_image_url, voice_provider, voice_api_id, voice_settings) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (char_id, name, physical_traits, clothing, master_prompt, reference_url, voice_provider, voice_api_id, "{}")
        )
        conn.commit()
        conn.close()
        return char_id

    def get_character(self, char_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Characters WHERE char_id = ?", (char_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            # Note: row length will now be 9 due to added columns
            return {
                "char_id": row[0],
                "name": row[1],
                "physical_traits": row[2],
                "clothing": row[3],
                "master_prompt": row[4],
                "reference_url": row[5],
                "voice_provider": row[6] if len(row) > 6 else "elevenlabs",
                "voice_api_id": row[7] if len(row) > 7 else "default_voice",
                "voice_settings": row[8] if len(row) > 8 else "{}"
            }
        return None

class ProjectManager:
    def __init__(self):
        pass

    def create_project(self, title, aspect_ratio="16:9", global_style="Cinematic, 4k"):
        project_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Projects (project_id, title, aspect_ratio, global_style) VALUES (?, ?, ?, ?)",
            (project_id, title, aspect_ratio, global_style)
        )
        conn.commit()
        conn.close()
        return project_id

    def add_scene(self, project_id, seq_order, active_chars, action, continuity="", env_id=None, env_continuity="", camera_anchor=""):
        scene_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO Scenes 
               (scene_id, project_id, sequence_order, active_characters, scene_action, continuity_modifiers, status, active_environment_id, env_continuity_modifiers, camera_spatial_anchor) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (scene_id, project_id, seq_order, json.dumps(active_chars), action, continuity, "PENDING", env_id, env_continuity, camera_anchor)
        )
        conn.commit()
        conn.close()
        return scene_id
