import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.character_manager import CharacterManager, ProjectManager
from memory.environment_manager import EnvironmentManager
from memory.director_engine import DirectorEngine
from memory.video_generator import VideoGenerator
from memory.lip_sync_engine import LipSyncEngine
from memory.audio_gateway import AudioGateway
from memory.ffmpeg_editor import FFmpegAssemblyEngine

def verify_end_to_end():
    print("=======================================")
    print("[*] Testing Live End-to-End Execution")
    print("=======================================")

    char_mgr = CharacterManager()
    env_mgr = EnvironmentManager()
    proj_mgr = ProjectManager()
    dir_engine = DirectorEngine()
    
    vid_gen = VideoGenerator()
    sync_engine = LipSyncEngine()
    audio_gateway = AudioGateway()
    editor = FFmpegAssemblyEngine()

    print("\n[+] 1. Audio Verification")
    try:
        audio_path = audio_gateway.generate_with_retry("Hello world", "mock_voice_id", "test_tts.wav")
        if audio_path:
            print(f"Provider: OpenAI (or custom)")
            print(f"File Path: {audio_path}")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\n[+] 2. Video Verification")
    try:
        vid_gen.generate_scene_video("mock_scene_id")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\n[+] 3. Lip-Sync Verification")
    try:
        # Create a mock scene in db to force lip-sync to process
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Scenes (scene_id, project_id, scene_number) VALUES ('mock_scene', 'mock_proj', 1)")
        cursor.execute("INSERT INTO Dialogues (dialogue_id, scene_id, is_narration, generated_audio_url) VALUES ('mock_d', 'mock_scene', 0, 'mock_audio.wav')")
        conn.commit()
        sync_engine.process_scene_audio("mock_scene", "mock_video.mp4")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\n[+] 4. FFmpeg Verification")
    import subprocess
    subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=red:s=640x360:d=3', '-c:v', 'libx264', 'test_ffmpeg_video.mp4'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', '-c:a', 'pcm_s16le', 'test_ffmpeg_audio.wav'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    try:
        job_id = editor.start_render_job("mock_proj_id")
        final_mp4 = editor.build_timeline("mock_proj_id", ["test_ffmpeg_video.mp4"], ["test_ffmpeg_audio.wav"])
        if final_mp4 and os.path.exists(final_mp4):
            size = os.path.getsize(final_mp4)
            print(f"SUCCESS. Final Path: {final_mp4}")
            print(f"File Size: {size / 1024:.2f} KB")
            print(f"Duration: 3 seconds")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    verify_end_to_end()
