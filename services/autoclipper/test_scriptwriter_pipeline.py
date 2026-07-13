import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.scriptwriter_engine import ScriptwriterMatrix
from memory.character_manager import get_db_connection

def test_scriptwriter_pipeline():
    print("=======================================")
    print("[*] Testing Autonomous LLM Scriptwriter Matrix")
    print("=======================================")

    matrix = ScriptwriterMatrix()
    
    # 1. Ideation
    print("\n[+] 1. Ideating Story from User Prompt...")
    user_prompt = "Make a 5-minute sci-fi movie about an astronaut finding a glowing artifact on Mars."
    script_id, project_id = matrix.ideate_story(user_prompt, duration_minutes=5)
    print(f"    -> Generated Script ID: {script_id}")

    # 2. World Building
    print("\n[+] 2. Building Worlds (CMS & ESM Population)...")
    char_id, env_id, style_id = matrix.build_world(script_id)
    print(f"    -> Generated Character ID: {char_id}")
    print(f"    -> Generated Environment ID: {env_id}")
    print(f"    -> Generated Director Style ID: {style_id}")

    # 3. Writing Scenes
    print("\n[+] 3. Writing Scenes (Rolling Context)...")
    matrix.write_scenes(project_id, char_id, env_id, style_id, num_scenes=5)
    print("    -> 5 Scenes written and directed successfully.")

    # 4. QA Check
    print("\n[+] 4. Running Narrative QA...")
    matrix.run_qa(script_id)
    print("    -> QA Passed. Status: READY_FOR_VIDEO")
    
    # Verify DB State
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM Scenes WHERE project_id = ?", (project_id,))
    scene_count = cursor.fetchone()[0]
    conn.close()

    print("\n=======================================")
    print(f"[*] Scriptwriter Pipeline Test Successful! Generated {scene_count} fully orchestrated scenes.")
    print("=======================================")

if __name__ == "__main__":
    test_scriptwriter_pipeline()
