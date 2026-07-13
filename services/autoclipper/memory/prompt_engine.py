import sqlite3
import os
import json
from .character_manager import get_db_connection, CharacterManager
from .environment_manager import EnvironmentManager

class PromptEngine:
    def __init__(self):
        self.char_mgr = CharacterManager()
        self.env_mgr = EnvironmentManager()

    def compile_scene_prompt(self, scene_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get Scene Details
        cursor.execute("""
            SELECT project_id, active_characters, scene_action, continuity_modifiers, 
                   active_environment_id, env_continuity_modifiers, camera_spatial_anchor,
                   shot_type, camera_motion, emotion_state, director_style_id
            FROM Scenes WHERE scene_id = ?
        """, (scene_id,))
        scene_row = cursor.fetchone()
        if not scene_row:
            return None
        
        project_id, active_chars_json, action, continuity, env_id, env_continuity, camera_anchor, shot_type, camera_motion, emotion, style_id = scene_row
        active_chars = json.loads(active_chars_json)
        
        # Get Director Style
        dir_style_str = ""
        if style_id:
            cursor.execute("SELECT preferred_lenses, color_grading_rules FROM Director_Styles WHERE style_id = ?", (style_id,))
            dir_row = cursor.fetchone()
            if dir_row:
                dir_style_str = f"Lenses: {dir_row[0]}. Grading: {dir_row[1]}. "

        
        # Get Project Details
        cursor.execute("SELECT global_style FROM Projects WHERE project_id = ?", (project_id,))
        proj_row = cursor.fetchone()
        global_style = proj_row[0] if proj_row else ""
        
        # Compile Master Prompts for Characters
        character_prompts = []
        for cid in active_chars:
            char = self.char_mgr.get_character(cid)
            if char:
                character_prompts.append(char['master_prompt'])
                
        merged_chars = " | ".join(character_prompts)

        # Compile Master Prompt for Environment
        env_prompt = ""
        if env_id:
            env = self.env_mgr.get_environment(env_id)
            if env:
                env_prompt = env['master_env_prompt']
        
        # Build Final Prompt
        final_prompt = f"Style: {global_style}. "
        
        if dir_style_str:
            final_prompt += f"Director Style: {dir_style_str}"
        if shot_type:
            final_prompt += f"Shot: {shot_type}. "
        if camera_motion:
            final_prompt += f"Camera Motion: {camera_motion}. "
        if emotion:
            final_prompt += f"Emotional Tone: {emotion}. "
            
        if env_prompt:
            final_prompt += f"Environment: {env_prompt}. "
            if env_continuity:
                final_prompt += f"Environment State: {env_continuity}. "
            if camera_anchor:
                final_prompt += f"Camera Anchor: {camera_anchor}. "

        if merged_chars:
            final_prompt += f"Subject(s): {merged_chars}. "
        if continuity:
            final_prompt += f"Character State: {continuity}. "
        
        final_prompt += f"Action: {action}"

        
        # Save to DB
        cursor.execute("UPDATE Scenes SET final_prompt = ? WHERE scene_id = ?", (final_prompt, scene_id))
        conn.commit()
        conn.close()
        
        return final_prompt

