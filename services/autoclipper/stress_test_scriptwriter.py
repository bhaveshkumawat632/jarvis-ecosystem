import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.scriptwriter_engine import ScriptwriterMatrix

def run_scriptwriter_stress_test():
    matrix = ScriptwriterMatrix()

    print("Starting Scriptwriter Matrix Stress Test (Long-Form 60-Min Feature)...")

    start_time = time.time()
    
    # 1. Ideation
    script_id, project_id = matrix.ideate_story("A 60-minute epic about AI.", 60)
    
    # 2. World Building
    char_id, env_id, style_id = matrix.build_world(script_id)
    
    # 3. Writing Scenes (Simulating a 120-scene feature film)
    # This will simulate sequential DB writing, CMS linking, Director applying, and Dialogue assigning.
    scene_start_time = time.time()
    matrix.write_scenes(project_id, char_id, env_id, style_id, num_scenes=120)
    scene_write_time = time.time() - scene_start_time
    
    # 4. QA
    matrix.run_qa(script_id)
    
    total_time = time.time() - start_time

    print("\nScriptwriter Matrix Stress Test Completed.")
    print("Metrics:")
    print(f"Total Scenes Written & Orchestrated: 120")
    print(f"Total Ecosystem Pipeline Population Time (Simulated LLM Latency + DB): {total_time:.2f} seconds")
    print(f"Average Scene Pipeline Latency (Write/Direct/Dialogue/Save): {(scene_write_time / 120)*1000:.2f} ms")

if __name__ == "__main__":
    run_scriptwriter_stress_test()
