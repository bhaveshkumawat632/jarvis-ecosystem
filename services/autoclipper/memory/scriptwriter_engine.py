import uuid
import json
import time
from .character_manager import get_db_connection, CharacterManager, ProjectManager
from .environment_manager import EnvironmentManager
from .director_engine import DirectorEngine
from .dialogue_manager import DialogueManager
from .llm_gateway import LLMGateway

class ScriptwriterMatrix:
    def __init__(self):
        self.char_mgr = CharacterManager()
        self.env_mgr = EnvironmentManager()
        self.proj_mgr = ProjectManager()
        self.dir_engine = DirectorEngine()
        self.dialogue_mgr = DialogueManager()
        self.llm = LLMGateway()

    def ideate_story(self, user_prompt, duration_minutes=15):
        sys_prompt = "You are a professional screenwriter. Return JSON with 'genre' and 'act_structure_json' containing Act1, Act2, Act3 descriptions."
        user_msg = f"Prompt: {user_prompt}. Duration: {duration_minutes} min."
        
        response = self.llm.execute_with_retry(sys_prompt, user_msg, required_keys=["genre", "act_structure_json"])
        
        if not response:
            raise Exception("LLM Ideation Failed.")

        project_id = self.proj_mgr.create_project(title="Auto-Generated Movie")
        script_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO Scripts 
               (script_id, project_id, user_prompt, genre, target_duration_minutes, act_structure_json, generation_status) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (script_id, project_id, user_prompt, response["genre"], duration_minutes, json.dumps(response["act_structure_json"]), "PLANNING")
        )
        conn.commit()
        conn.close()
        
        return script_id, project_id

    def build_world(self, script_id):
        sys_prompt = "Extract the main protagonist and primary location. Return JSON with 'char_name', 'char_body', 'char_clothing', 'env_name', 'env_architecture', 'env_lighting', 'dir_name', 'dir_lenses', 'dir_grading'."
        user_msg = f"Create world for script ID: {script_id}"
        
        response = self.llm.execute_with_retry(sys_prompt, user_msg, required_keys=["char_name", "env_name", "dir_name"])
        
        if not response:
            raise Exception("LLM World Building Failed.")
        
        # Create a protagonist and an environment
        char_id = self.char_mgr.create_character(
            response.get("char_name", "Protagonist"), 
            response.get("char_body", "Average"), 
            response.get("char_clothing", "Casual")
        )
        env_id = self.env_mgr.create_environment(
            response.get("env_name", "Location 1"), 
            response.get("env_architecture", "Modern"), 
            response.get("env_lighting", "Daylight")
        )
        
        # Setup Director Style
        style_id = self.dir_engine.create_director_style(
            response.get("dir_name", "Standard Style"), 
            response.get("dir_lenses", "35mm"), 
            response.get("dir_grading", "Natural"), 
            5.0
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Scripts SET generation_status = 'WRITING_SCENES' WHERE script_id = ?", (script_id,))
        conn.commit()
        conn.close()
        
        return char_id, env_id, style_id

    def write_scenes(self, project_id, char_id, env_id, style_id, num_scenes=10):
        # Rolling context loop
        for s_idx in range(num_scenes):
            sys_prompt = "Write the next scene. Return JSON: 'action', 'tension' (1-10), 'is_dialogue' (bool), 'dialogue_text'."
            user_msg = f"Scene index {s_idx} of {num_scenes}."
            
            response = self.llm.execute_with_retry(sys_prompt, user_msg, required_keys=["action", "tension", "is_dialogue"])
            
            if not response:
                raise Exception(f"Scene {s_idx} generation failed.")

            tension = int(response.get("tension", 5))
            is_dialogue = bool(response.get("is_dialogue", False))
            action_text = response.get("action", f"Scene {s_idx}")
            
            # Create Scene via CMS
            scene_id = self.proj_mgr.add_scene(
                project_id=project_id,
                seq_order=s_idx,
                active_chars=[char_id],
                action=action_text,
                env_id=env_id
            )
            
            # Apply Director Metadata
            self.dir_engine.apply_direction_to_scene(scene_id, style_id, emotion="Determined", tension=tension, is_dialogue_heavy=is_dialogue)
            
            # Assign Dialogue if applicable
            if is_dialogue and "dialogue_text" in response:
                self.dialogue_mgr.add_dialogue(scene_id, char_id, response["dialogue_text"], is_narration=False)
                
    def run_qa(self, script_id):
        sys_prompt = "Perform Narrative QA. Return JSON with 'passed' (bool) and 'reason'."
        user_msg = f"Check script {script_id}"
        
        response = self.llm.execute_with_retry(sys_prompt, user_msg, required_keys=["passed"])
        
        if response and response.get("passed", True):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Scripts SET generation_status = 'READY_FOR_VIDEO' WHERE script_id = ?", (script_id,))
            conn.commit()
            conn.close()
            return True
        return False
