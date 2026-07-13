import os
import sys
import time
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.environment_manager import EnvironmentManager
from memory.prompt_engine import PromptEngine
from memory.qa_validator import QAValidator

def run_esm_stress_test():
    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    env_mgr = EnvironmentManager()
    prompt_engine = PromptEngine()
    qa = QAValidator(max_retries=3)

    metrics = {
        "db_insert_times": [],
        "prompt_compile_times": [],
        "total_prompts_generated": 0
    }

    print("Starting ESM Stress Test...")

    start_time = time.time()
    char_id = char_mgr.create_character("Hero", "Tall, black hair", "Jeans")
    env_id = env_mgr.create_environment("Forest", "Dense woods, ancient trees", "Sunlight piercing through canopy")
    metrics['db_insert_times'].append(time.time() - start_time)

    # 100 Scenes across 5 Projects
    projects = []
    for p_idx in range(5):
        pid = proj_mgr.create_project(title=f"Movie Part {p_idx+1}")
        projects.append(pid)

        env_state = "Peaceful morning"
        for s_idx in range(20):
            if s_idx == 10:
                env_state = "A storm has started, trees are swaying violently."

            start_time = time.time()
            sid = proj_mgr.add_scene(
                project_id=pid,
                seq_order=s_idx,
                active_chars=[char_id],
                action=f"Running through the woods scene {s_idx}.",
                env_id=env_id,
                env_continuity=env_state,
                camera_anchor=f"Tracking shot {s_idx}"
            )
            metrics['db_insert_times'].append(time.time() - start_time)

            start_time = time.time()
            prompt = prompt_engine.compile_scene_prompt(sid)
            metrics['prompt_compile_times'].append(time.time() - start_time)
            metrics['total_prompts_generated'] += 1

    print("ESM Stress Test Completed.")
    print("Metrics:")
    print(f"Total Prompts Generated: {metrics['total_prompts_generated']}")
    print(f"Average DB Insert Latency: {(sum(metrics['db_insert_times'])/len(metrics['db_insert_times']))*1000:.2f} ms")
    print(f"Average Prompt Compilation Latency: {(sum(metrics['prompt_compile_times'])/len(metrics['prompt_compile_times']))*1000:.2f} ms")

if __name__ == "__main__":
    run_esm_stress_test()
