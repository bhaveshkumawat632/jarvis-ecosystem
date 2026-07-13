import sqlite3
import uuid
import os
from .character_manager import get_db_connection

class DialogueManager:
    def __init__(self):
        pass

    def add_dialogue(self, scene_id, char_id, dialogue_text, is_narration=False):
        dialogue_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO Dialogues 
               (dialogue_id, scene_id, char_id, dialogue_text, is_narration, sync_status) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (dialogue_id, scene_id, char_id, dialogue_text, is_narration, 'PENDING')
        )
        conn.commit()
        conn.close()
        return dialogue_id

    def get_dialogues_for_scene(self, scene_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Dialogues WHERE scene_id = ?", (scene_id,))
        rows = cursor.fetchall()
        conn.close()
        
        dialogues = []
        for row in rows:
            dialogues.append({
                "dialogue_id": row[0],
                "scene_id": row[1],
                "char_id": row[2],
                "dialogue_text": row[3],
                "is_narration": bool(row[4]),
                "generated_audio_url": row[5],
                "sync_status": row[6]
            })
        return dialogues

    def update_audio_url(self, dialogue_id, audio_url):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Dialogues SET generated_audio_url = ?, sync_status = 'AUDIO_GENERATED' WHERE dialogue_id = ?", (audio_url, dialogue_id))
        conn.commit()
        conn.close()
        
    def update_sync_status(self, dialogue_id, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Dialogues SET sync_status = ? WHERE dialogue_id = ?", (status, dialogue_id))
        conn.commit()
        conn.close()
