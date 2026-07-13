import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.environment_manager import EnvironmentManager
from memory.prompt_engine import PromptEngine

def test_esm_pipeline():
    print("=======================================")
    print("[*] Testing Environment & Spatial Memory Pipeline")
    print("=======================================")

    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    env_mgr = EnvironmentManager()
    prompt_engine = PromptEngine()

    # 1. Define Character
    print("\n[+] Fetching/Creating Character Profile...")
    char_id = char_mgr.create_character(
        name="Alex",
        physical_traits="25yo male, sharp jawline, messy brown hair",
        clothing="brown leather jacket"
    )

    # 2. Define Environment
    print("\n[+] Creating Environment Profile...")
    env_id = env_mgr.create_environment(
        name="The Neon Bar",
        architecture="a retro-futuristic dive bar with an oak counter, checkered floor, and rain-streaked windows",
        lighting="dim purple lighting with neon signs reflecting off wet surfaces"
    )

    # 3. Create Project
    project_id = proj_mgr.create_project(title="Cyber Heist", aspect_ratio="16:9", global_style="Cinematic, 35mm lens, 4k")

    # 4. Add Scenes (Testing location, object movement, weather changes)
    print("\n[+] Storyboarding Scenes...")
    
    # Scene 1: Introduction to the environment
    scene1_id = proj_mgr.add_scene(
        project_id=project_id,
        seq_order=1,
        active_chars=[char_id],
        action="Sitting at the bar, sipping a drink.",
        env_id=env_id,
        env_continuity="It is raining heavily outside.",
        camera_anchor="Camera facing the rain-streaked windows behind the bartender."
    )
    
    # Scene 2: Continuity state change in Environment and Character
    scene2_id = proj_mgr.add_scene(
        project_id=project_id,
        seq_order=2,
        active_chars=[char_id],
        action="Stands up quickly, dropping the glass.",
        continuity="Jacket is slightly wet.",
        env_id=env_id,
        env_continuity="The neon sign on the left is flickering wildly.",
        camera_anchor="Camera facing the oak counter from a low angle."
    )

    # 5. Compile Prompts
    print("\n[+] Compiling Prompts with CMS + ESM Integration...")
    prompt1 = prompt_engine.compile_scene_prompt(scene1_id)
    prompt2 = prompt_engine.compile_scene_prompt(scene2_id)
    
    print("\n--- SCENE 1 FINAL PROMPT ---")
    print(prompt1)
    
    print("\n--- SCENE 2 FINAL PROMPT ---")
    print(prompt2)

    print("\n=======================================")
    print("[*] ESM Pipeline Test Successful!")
    print("=======================================")

if __name__ == "__main__":
    test_esm_pipeline()
