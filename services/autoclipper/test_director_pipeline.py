import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.director_engine import DirectorEngine
from memory.prompt_engine import PromptEngine

def test_director_pipeline():
    print("=======================================")
    print("[*] Testing AI Director & Narrative Pacing Engine")
    print("=======================================")

    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    dir_engine = DirectorEngine()
    prompt_engine = PromptEngine()

    # 1. Define Director Style
    print("\n[+] Creating Director Style...")
    style_id = dir_engine.create_director_style(
        name="Cinematic Thriller",
        preferred_lenses="Anamorphic 35mm, Shallow Depth of Field",
        color_grading="Cool blue tones, high contrast, desaturated",
        pacing_baseline=5.0
    )

    # 2. Setup Project & Character
    project_id = proj_mgr.create_project(title="Heist Movie")
    char_id = char_mgr.create_character("Thief", "Athletic", "Black tactical gear")
    
    # 3. Add Scene (Dialogue Heavy, Low Tension)
    print("\n[+] Directing Scene 1 (Dialogue, Tension=3)...")
    scene1_id = proj_mgr.add_scene(project_id, 1, [char_id], "Checking the vault blueprints.")
    dir_engine.apply_direction_to_scene(scene1_id, style_id, emotion="Focused", tension=3, is_dialogue_heavy=True)

    # 4. Add Scene (Action Heavy, High Tension)
    print("\n[+] Directing Scene 2 (Action, Tension=9)...")
    scene2_id = proj_mgr.add_scene(project_id, 2, [char_id], "Running down the hallway from guards.")
    dir_engine.apply_direction_to_scene(scene2_id, style_id, emotion="Panic", tension=9, is_dialogue_heavy=False)

    # 5. Add Foley
    print("\n[+] Adding Foley Sound Timelines...")
    dir_engine.add_foley_cue(scene2_id, "Heavy combat boots sprinting on concrete", timestamp=0.5)
    dir_engine.add_foley_cue(scene2_id, "Alarm sirens blaring in background", timestamp=0.0)

    # 6. Output Prompts
    print("\n[+] Compiling Prompts with Director Integration...")
    prompt1 = prompt_engine.compile_scene_prompt(scene1_id)
    prompt2 = prompt_engine.compile_scene_prompt(scene2_id)
    
    print("\n--- SCENE 1 FINAL PROMPT ---")
    print(prompt1)
    
    print("\n--- SCENE 2 FINAL PROMPT ---")
    print(prompt2)

    print("\n=======================================")
    print("[*] Director Pipeline Test Successful!")
    print("=======================================")

if __name__ == "__main__":
    test_director_pipeline()
