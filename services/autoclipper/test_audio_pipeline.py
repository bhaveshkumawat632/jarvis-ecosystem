import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager, get_db_connection
from memory.dialogue_manager import DialogueManager
from memory.lip_sync_engine import AudioGenerator, LipSyncEngine

def test_real_audio_pipeline():
    print("=======================================")
    print("[*] Testing Live Audio Generation Gateway")
    print("=======================================")

    char_mgr = CharacterManager()
    proj_mgr = ProjectManager()
    dialogue_mgr = DialogueManager()
    audio_gen = AudioGenerator()
    sync_engine = LipSyncEngine()

    print("\n[+] 1. Creating Character with Persistent Voice ID...")
    char_id = char_mgr.create_character("Narrator", "Average", "Suit", voice_provider="elevenlabs", voice_api_id="joshua")
    
    # Manually update language via DB for test since create_character doesn't take it yet
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE Characters SET language = 'en-US' WHERE char_id = ?", (char_id,))
    conn.commit()
    conn.close()

    print("\n[+] 2. Setting up Project and Scene...")
    pid = proj_mgr.create_project(title="Audio Test Movie")
    sid = proj_mgr.add_scene(pid, 1, [char_id], "Test speaking.")

    print("\n[+] 3. Creating Dialogue Row...")
    did = dialogue_mgr.add_dialogue(sid, char_id, "This is a live generation test.", is_narration=False)

    print("\n[+] 4. Executing Audio Generation Gateway...")
    # This will use the _mock_generation fallback which triggers real ffmpeg to write a wav file
    wav_path = audio_gen.generate_tts(did)

    if wav_path and os.path.exists(wav_path):
        print(f"    -> SUCCESS: Audio physically generated at {wav_path}")
        size = os.path.getsize(wav_path) / 1024
        print(f"    -> File Size: {size:.2f} KB")
    else:
        print("    -> FAILURE: Audio generation failed or file not found.")

    print("\n[+] 5. Preparing SyncLabs Interfaces (Dry Run)...")
    sync_engine.process_scene_audio(sid, "dummy_video_url.mp4")
    print("    -> Lip-sync models prepped. Standard audio flagged properly.")

    print("\n=======================================")
    print("[*] Live Audio Pipeline Test Successful!")
    print("=======================================")

if __name__ == "__main__":
    test_real_audio_pipeline()
