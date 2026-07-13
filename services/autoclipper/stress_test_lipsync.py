import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.dialogue_manager import DialogueManager
from memory.lip_sync_engine import AudioGenerator, LipSyncEngine

def run_lipsync_stress_test():
    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    dialogue_mgr = DialogueManager()
    audio_gen = AudioGenerator()
    sync_engine = LipSyncEngine()

    metrics = {
        "db_insert_times": [],
        "audio_gen_times": [],
        "total_dialogues": 0
    }

    print("Starting Lip-Sync Stress Test...")

    start_time = time.time()
    char_id = char_mgr.create_character("Hero", "Tall", "Jeans", voice_provider="elevenlabs", voice_api_id="joshua")
    metrics['db_insert_times'].append(time.time() - start_time)

    # 100 Dialogues across 5 Projects
    projects = []
    for p_idx in range(5):
        pid = proj_mgr.create_project(title=f"Movie Part {p_idx+1}")
        projects.append(pid)

        for s_idx in range(20): # 20 scenes per project
            sid = proj_mgr.add_scene(pid, s_idx, [char_id], "Speaking.")
            
            # Alternate between narration and standard dialogue
            is_narration = (s_idx % 2 == 0)

            start_time = time.time()
            did = dialogue_mgr.add_dialogue(sid, char_id, f"Line {s_idx}", is_narration=is_narration)
            metrics['db_insert_times'].append(time.time() - start_time)

            start_time = time.time()
            audio_gen.generate_tts(did)
            metrics['audio_gen_times'].append(time.time() - start_time)
            metrics['total_dialogues'] += 1
            
            # Note: We skip calling sync_engine here to save simulated time, 
            # we are mainly measuring DB and orchestration overhead.

    print("Lip-Sync Stress Test Completed.")
    print("Metrics:")
    print(f"Total Dialogues Generated: {metrics['total_dialogues']}")
    print(f"Average DB Insert Latency: {(sum(metrics['db_insert_times'])/len(metrics['db_insert_times']))*1000:.2f} ms")
    print(f"Average Audio Gen (Simulated) Latency: {(sum(metrics['audio_gen_times'])/len(metrics['audio_gen_times']))*1000:.2f} ms")

if __name__ == "__main__":
    run_lipsync_stress_test()
