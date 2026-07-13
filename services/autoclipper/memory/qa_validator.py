import sqlite3
import os
import time
from .character_manager import get_db_connection

class QAValidator:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def validate_scene_output(self, scene_id, job_id, video_url):
        """
        In a production environment, this would extract a keyframe
        and pass it to a Vision LLM (e.g. GPT-4o or Nim Vision) to 
        validate against the character's physical description.
        
        For now, this serves as the simulated QA layer.
        """
        print(f"[QA] Inspecting visual output for Scene {scene_id} (Job: {job_id})")
        
        # Simulate Vision Check (Assuming 95% pass rate for the logic)
        # We will assume it passes for integration purposes.
        is_consistent = True
        qa_score = 0.95
        error_reason = ""
        
        if not is_consistent:
            qa_score = 0.40
            error_reason = "Major hallucination: Character hair color mismatch."

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Log the attempt
        cursor.execute("SELECT attempt_number FROM Generations_Log WHERE scene_id = ? ORDER BY attempt_number DESC LIMIT 1", (scene_id,))
        last_attempt = cursor.fetchone()
        attempt_num = (last_attempt[0] + 1) if last_attempt else 1

        cursor.execute(
            "INSERT INTO Generations_Log (job_id, scene_id, video_url, qa_score, error_reason, attempt_number) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, scene_id, video_url, qa_score, error_reason, attempt_num)
        )
        
        if is_consistent:
            cursor.execute("UPDATE Scenes SET status = 'COMPLETED' WHERE scene_id = ?", (scene_id,))
            conn.commit()
            conn.close()
            return True
        else:
            if attempt_num >= self.max_retries:
                cursor.execute("UPDATE Scenes SET status = 'QC_FAILED' WHERE scene_id = ?", (scene_id,))
                conn.commit()
                conn.close()
                print(f"[-] QA Failed permanently after {self.max_retries} retries for Scene {scene_id}.")
                return False
            else:
                cursor.execute("UPDATE Scenes SET status = 'PENDING' WHERE scene_id = ?", (scene_id,))
                conn.commit()
                conn.close()
                print(f"[*] QA Failed. Retrying Scene {scene_id} (Attempt {attempt_num + 1})...")
                return False

