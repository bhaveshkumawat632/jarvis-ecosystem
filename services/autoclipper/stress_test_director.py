import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.director_engine import DirectorEngine
from memory.prompt_engine import PromptEngine

def run_director_stress_test():
    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    dir_engine = DirectorEngine()
    prompt_engine = PromptEngine()

    metrics = {
        "db_insert_times": [],
        "prompt_compile_times": [],
        "total_scenes": 0
    }

    print("Starting Director & Narrative Pacing Stress Test...")

    style_id = dir_engine.create_director_style("Action Blockbuster", "Wide angle", "High contrast", 4.0)
    char_id = char_mgr.create_character("Hero", "Tall", "Jeans")

    # 100 Scenes across 5 Projects
    projects = []
    for p_idx in range(5):
        pid = proj_mgr.create_project(title=f"Movie Part {p_idx+1}")
        projects.append(pid)

        # Simulate a tension curve (e.g., 3 Acts)
        for s_idx in range(20):
            if s_idx < 5:
                tension = 2 # Act 1 setup
            elif s_idx < 15:
                tension = 6 # Act 2 rising action
            else:
                tension = 9 # Act 3 climax

            is_dialogue = (s_idx % 3 == 0)

            # Insert Base Scene
            sid = proj_mgr.add_scene(pid, s_idx, [char_id], f"Scene {s_idx} action.")
            
            # Apply Directorial Metadata
            start_time = time.time()
            dir_engine.apply_direction_to_scene(sid, style_id, emotion="Determined", tension=tension, is_dialogue_heavy=is_dialogue)
            metrics['db_insert_times'].append(time.time() - start_time)

            # Compile Full Prompt with Director Metadata
            start_time = time.time()
            prompt = prompt_engine.compile_scene_prompt(sid)
            metrics['prompt_compile_times'].append(time.time() - start_time)
            
            metrics['total_scenes'] += 1

    print("Director Stress Test Completed.")
    print("Metrics:")
    print(f"Total Scenes Directed: {metrics['total_scenes']}")
    print(f"Average DB Update Latency (Director): {(sum(metrics['db_insert_times'])/len(metrics['db_insert_times']))*1000:.2f} ms")
    print(f"Average Final Prompt Compile Latency: {(sum(metrics['prompt_compile_times'])/len(metrics['prompt_compile_times']))*1000:.2f} ms")

if __name__ == "__main__":
    run_director_stress_test()
