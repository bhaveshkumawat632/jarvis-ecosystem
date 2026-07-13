import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.dialogue_manager import DialogueManager
from memory.lip_sync_engine import AudioGenerator, LipSyncEngine

def test_lipsync_pipeline():
    print("=======================================")
    print("[*] Testing Dialogue & Lip-Sync Pipeline")
    print("=======================================")

    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    dialogue_mgr = DialogueManager()
    audio_gen = AudioGenerator()
    sync_engine = LipSyncEngine()

    # 1. Define Character with a Voice Profile
    print("\n[+] Creating Character with Voice Profile...")
    char_id = char_mgr.create_character(
        name="Sarah",
        physical_traits="30yo female, black hair",
        clothing="lab coat",
        voice_provider="elevenlabs",
        voice_api_id="sarah_v2_professional"
    )

    # 2. Setup Scene
    project_id = proj_mgr.create_project(title="Sci-Fi Lab")
    scene_id = proj_mgr.add_scene(project_id, 1, [char_id], "Looking at a glowing vial.")

    # 3. Add Dialogue
    print("\n[+] Assigning Dialogue & Narration...")
    # On-screen speaking
    d1_id = dialogue_mgr.add_dialogue(scene_id, char_id, "This compound is highly unstable.", is_narration=False)
    # Voiceover (internal thought)
    d2_id = dialogue_mgr.add_dialogue(scene_id, char_id, "I hope I don't blow up the lab again.", is_narration=True)

    # 4. Generate TTS Audio
    print("\n[+] Generating TTS Audio Parallel to Video...")
    audio_url_1 = audio_gen.generate_tts(d1_id)
    audio_url_2 = audio_gen.generate_tts(d2_id)
    print(f"    -> Audio 1: {audio_url_1}")
    print(f"    -> Audio 2: {audio_url_2}")

    # 5. Run Lip Sync Orchestrator
    print("\n[+] Routing Video to Lip-Sync Gateway...")
    raw_video_url = "https://storage.googleapis.com/videos/raw_scene_1.mp4"
    final_video_url = sync_engine.sync_scene(scene_id, raw_video_url)

    print(f"\n[+] Final Rendered Video URL: {final_video_url}")

    print("\n=======================================")
    print("[*] Lip-Sync Pipeline Test Successful!")
    print("=======================================")

if __name__ == "__main__":
    test_lipsync_pipeline()
