import os
import uuid
import logging
from .character_manager import get_db_connection
from .audio_gateway import AudioGateway

logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self, output_dir="rendered_output"):
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.gateway = AudioGateway()

    def generate_tts(self, dialogue_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT d.dialogue_text, c.voice_provider, c.voice_api_id
            FROM Dialogues d
            JOIN Characters c ON d.char_id = c.char_id
            WHERE d.dialogue_id = ?
        """, (dialogue_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
            
        text, provider, voice_id = row
        
        output_filename = os.path.join(self.output_dir, f"tts_{dialogue_id}.wav")
        
        # Route through the AudioGateway
        final_path = self.gateway.generate_with_retry(text, voice_id, output_filename)
        
        if final_path:
            cursor.execute("UPDATE Dialogues SET generated_audio_url = ?, sync_status = 'AUDIO_GENERATED' WHERE dialogue_id = ?", (final_path, dialogue_id))
            conn.commit()
            
        conn.close()
        return final_path

class LipSyncEngine:
    """
    Prepared architecture for future SyncLabs/Wav2Lip integration.
    Currently defines interfaces and asset schemas without invoking real APIs.
    """
    def __init__(self):
        pass

    def define_sync_job(self, video_path: str, audio_path: str) -> dict:
        """Schema definition for the future external API payload."""
        return {
            "video_url": video_path,
            "audio_url": audio_path,
            "sync_mode": "strict"
        }

    def process_scene_audio(self, scene_id, video_url):
        """
        Submits the generated video and audio to SyncLabs for lip-sync processing.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT dialogue_id, is_narration, generated_audio_url FROM Dialogues WHERE scene_id = ?", (scene_id,))
        dialogues = cursor.fetchall()
        
        synced_video = video_url
        
        import os, time, requests
        api_key = os.getenv("SYNCLABS_API_KEY")
        
        for d_id, is_narration, audio_url in dialogues:
            if not audio_url:
                continue
                
            if is_narration:
                logger.info(f"Dialogue {d_id} is narration. Standard muxing will apply in FFmpeg.")
            else:
                logger.info(f"Dialogue {d_id} requires lip-syncing. Sending to SyncLabs.")
                if not api_key:
                    raise ValueError("SYNCLABS_API_KEY is missing. Cannot perform Lip-Sync.")
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "video_url": synced_video,
                    "audio_url": audio_url,
                    "model": "sync-1.6.0"
                }
                
                res = requests.post("https://api.synclabs.so/video", headers=headers, json=payload, timeout=30)
                res.raise_for_status()
                job_id = res.json().get("id")
                
                # Poll for completion
                max_polls = 60
                for _ in range(max_polls):
                    status_res = requests.get(f"https://api.synclabs.so/video/{job_id}", headers=headers, timeout=30)
                    status_res.raise_for_status()
                    data = status_res.json()
                    if data.get("status") == "COMPLETED":
                        synced_video = data.get("video_url")
                        break
                    elif data.get("status") == "FAILED":
                        raise Exception(f"SyncLabs job {job_id} failed.")
                    time.sleep(10)
                
        # Update scenes with synced video URL
        cursor.execute("UPDATE Scenes SET generated_video_url = ? WHERE scene_id = ?", (synced_video, scene_id))
        conn.commit()
        conn.close()
        
        return synced_video
