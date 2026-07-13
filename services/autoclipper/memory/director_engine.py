import uuid
import random
from .character_manager import get_db_connection

class DirectorEngine:
    def __init__(self):
        self.shot_types = ["Wide Shot", "Medium Shot", "Close-Up", "Over-the-Shoulder", "Extreme Close-Up"]
        self.camera_motions = ["Static", "Slow Pan Right", "Slow Dolly-In", "Handheld Tracking", "Orbit"]

    def create_director_style(self, name, preferred_lenses, color_grading, pacing_baseline):
        style_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Director_Styles (style_id, name, preferred_lenses, color_grading_rules, pacing_baseline) VALUES (?, ?, ?, ?, ?)",
            (style_id, name, preferred_lenses, color_grading, pacing_baseline)
        )
        conn.commit()
        conn.close()
        return style_id

    def calculate_scene_direction(self, action, tension, is_dialogue_heavy=False):
        # Prevent repetitive shots (simplified rule-based logic)
        shot = random.choice(self.shot_types)
        motion = random.choice(self.camera_motions)
        
        # Pacing logic based on tension
        if tension > 7:
            # High tension: fast cuts, dramatic shots
            duration = random.uniform(1.5, 3.5)
            if not is_dialogue_heavy:
                motion = "Handheld Tracking"
        elif tension < 4:
            # Low tension: slow burns
            duration = random.uniform(5.0, 10.0)
            motion = "Slow Pan Right"
        else:
            # Medium tension
            duration = random.uniform(3.5, 6.0)

        # Dialogue override
        if is_dialogue_heavy:
            shot = random.choice(["Medium Shot", "Close-Up", "Over-the-Shoulder"])

        return shot, motion, duration

    def apply_direction_to_scene(self, scene_id, style_id, emotion, tension, is_dialogue_heavy=False):
        shot, motion, duration = self.calculate_scene_direction("", tension, is_dialogue_heavy)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE Scenes 
               SET director_style_id = ?, emotion_state = ?, narrative_tension = ?, shot_type = ?, camera_motion = ?, duration_seconds = ?
               WHERE scene_id = ?""",
            (style_id, emotion, tension, shot, motion, duration, scene_id)
        )
        conn.commit()
        conn.close()

    def add_foley_cue(self, scene_id, description, timestamp):
        event_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Audio_Timelines (audio_event_id, scene_id, event_type, description, timestamp_start) VALUES (?, ?, ?, ?, ?)",
            (event_id, scene_id, "FOLEY", description, timestamp)
        )
        conn.commit()
        conn.close()
        return event_id
