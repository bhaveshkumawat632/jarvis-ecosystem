import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.prompt_engine import PromptEngine
from memory.qa_validator import QAValidator

def test_pipeline():
    print("=======================================")
    print("[*] Testing Character Memory Pipeline")
    print("=======================================")

    # 1. Initialize Modules
    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    prompt_engine = PromptEngine()
    qa = QAValidator()

    # 2. Define Character (Only done once, remembered forever)
    print("\n[+] Creating Character Profile...")
    char_id = char_mgr.create_character(
        name="Alex",
        physical_traits="25yo male, sharp jawline, messy brown hair, emerald green eyes",
        clothing="weathered brown leather jacket and dark jeans"
    )
    print(f"    -> Character DB ID: {char_id}")

    # 3. Create a Project
    print("\n[+] Initializing Project...")
    project_id = proj_mgr.create_project(title="Alex's Cyberpunk Adventure", aspect_ratio="16:9", global_style="Cinematic, Cyberpunk lighting, 8k resolution")
    print(f"    -> Project DB ID: {project_id}")

    # 4. Add Scenes with Continuity
    print("\n[+] Storyboarding Scenes...")
    scene1_id = proj_mgr.add_scene(
        project_id=project_id,
        seq_order=1,
        active_chars=[char_id],
        action="Walking down a neon-lit alleyway, looking around cautiously."
    )
    
    scene2_id = proj_mgr.add_scene(
        project_id=project_id,
        seq_order=2,
        active_chars=[char_id],
        action="Running away from a flying drone.",
        continuity="Jacket is slightly wet from rain, holding a glowing blue device in right hand."
    )

    # 5. Compile Prompts
    print("\n[+] Compiling Prompts with Memory Engine...")
    prompt1 = prompt_engine.compile_scene_prompt(scene1_id)
    prompt2 = prompt_engine.compile_scene_prompt(scene2_id)
    
    print("\n--- SCENE 1 PROMPT ---")
    print(prompt1)
    
    print("\n--- SCENE 2 PROMPT ---")
    print(prompt2)

    # 6. Simulate QA / Retry Validation
    print("\n[+] Simulating Video Generation & QA Check...")
    job_id_1 = str(uuid.uuid4())
    is_valid = qa.validate_scene_output(scene1_id, job_id_1, "https://storage.googleapis.com/veo/fake_video_1.mp4")
    if is_valid:
        print("    -> Scene 1 passed Vision QC and is marked COMPLETED.")

    print("\n=======================================")
    print("[*] Pipeline Test Successful!")
    print("=======================================")

if __name__ == "__main__":
    test_pipeline()
