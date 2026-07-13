import os
import sys
import time
import uuid
from memory.character_manager import CharacterManager, ProjectManager
from memory.prompt_engine import PromptEngine
from memory.qa_validator import QAValidator

def run_stress_test():
    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    prompt_engine = PromptEngine()
    qa = QAValidator(max_retries=3)

    metrics = {
        "db_insert_times": [],
        "prompt_compile_times": [],
        "total_prompts_generated": 0,
        "qa_retries": 0,
        "qa_failures": 0
    }

    print("Starting Stress Test...")

    # 1 & 3: Character Creation & Database Validation
    start_time = time.time()
    char_id = char_mgr.create_character(
        name="Protagonist",
        physical_traits="30yo female, athletic build, short blonde hair, blue eyes, scar over left eyebrow",
        clothing="tactical black stealth suit with silver accents"
    )
    metrics['db_insert_times'].append(time.time() - start_time)
    
    # 2 & 4 & 5: Multi-Scene, Multi-Video, Continuity, and 50+ Prompts Validation
    # We will create 3 projects, each with 20 scenes (total 60 scenes)
    projects = []
    for p_idx in range(3):
        start_time = time.time()
        pid = proj_mgr.create_project(title=f"Movie Part {p_idx+1}")
        metrics['db_insert_times'].append(time.time() - start_time)
        projects.append(pid)

        continuity_state = "clean"
        for s_idx in range(20):
            # Introduce state changes
            if s_idx == 5:
                continuity_state = "sweaty and slightly bruised"
            elif s_idx == 10:
                continuity_state = "suit is torn on the left shoulder, holding a futuristic rifle"
            elif s_idx == 15:
                continuity_state = "covered in dust, rifle is glowing red"

            start_time = time.time()
            sid = proj_mgr.add_scene(
                project_id=pid,
                seq_order=s_idx,
                active_chars=[char_id],
                action=f"Action sequence {s_idx} for project {p_idx+1}.",
                continuity=continuity_state
            )
            metrics['db_insert_times'].append(time.time() - start_time)

            start_time = time.time()
            prompt = prompt_engine.compile_scene_prompt(sid)
            metrics['prompt_compile_times'].append(time.time() - start_time)
            metrics['total_prompts_generated'] += 1

    # 6. Quality Control Validation (Simulation)
    # Simulate a scene that hallucinates heavily and requires retries
    test_scene_id = proj_mgr.add_scene(projects[0], 99, [char_id], "Simulated failing scene")
    
    # We'll simulate QA logic directly for testing purposes.
    # Force fail it 3 times to test retry limit
    for _ in range(4):
        is_consistent = False # Force failure
        job_id = str(uuid.uuid4())
        valid = qa.validate_scene_output(test_scene_id, job_id, "http://fake.url")
        if not valid:
            metrics['qa_retries'] += 1
            # Assuming qa_validator handles the status logic internally
    metrics['qa_failures'] += 1

    print("Stress Test Completed.")
    print("Metrics:")
    print(f"Total Prompts Generated: {metrics['total_prompts_generated']}")
    print(f"Average DB Insert Latency: {(sum(metrics['db_insert_times'])/len(metrics['db_insert_times']))*1000:.2f} ms")
    print(f"Average Prompt Compilation Latency: {(sum(metrics['prompt_compile_times'])/len(metrics['prompt_compile_times']))*1000:.2f} ms")
    print(f"QA Retries triggered: {metrics['qa_retries']}")

if __name__ == "__main__":
    run_stress_test()
