import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.environment_manager import EnvironmentManager
from memory.director_engine import DirectorEngine
from memory.video_generator import VideoGenerator
from memory.lip_sync_engine import LipSyncEngine

def test_real_video_pipeline():
    print("=======================================")
    print("[*] Testing Live Video Generation Gateway")
    print("=======================================")

    char_mgr = CharacterManager()
    env_mgr = EnvironmentManager()
    proj_mgr = ProjectManager()
    dir_engine = DirectorEngine()
    vid_gen = VideoGenerator()
    sync_engine = LipSyncEngine()

    print("\n[+] 1. Initializing CMS, ESM, and Director Metadata...")
    char_id = char_mgr.create_character("Hero", "Tall", "Armor")
    env_id = env_mgr.create_environment("Castle", "Gothic", "Moody")
    style_id = dir_engine.create_director_style("Epic", "Wide", "Teal/Orange", 5.0)
    
    pid = proj_mgr.create_project(title="Video Test Movie")
    sid = proj_mgr.add_scene(pid, 1, [char_id], "Hero stands heroically.", env_id=env_id)
    dir_engine.apply_direction_to_scene(sid, style_id, "Determined", 8, False)

    print("\n[+] 2. Compiling Master Prompt and Submitting Video Job...")
    mp4_path = vid_gen.generate_scene_video(sid)

    if mp4_path and os.path.exists(mp4_path):
        print(f"    -> SUCCESS: Video physically generated at {mp4_path}")
        size = os.path.getsize(mp4_path) / 1024
        print(f"    -> File Size: {size:.2f} KB")
    else:
        print("    -> FAILURE: Video generation failed or file not found.")
        return

    print("\n[+] 3. Preparing SyncLabs Execution Layer (Dry Run)...")
    sync_engine.process_scene_audio(sid, mp4_path)
    print("    -> Lip-sync model processed video logic.")

    print("\n=======================================")
    print("[*] Live Video Pipeline Test Successful!")
    print("=======================================")

if __name__ == "__main__":
    test_real_video_pipeline()
