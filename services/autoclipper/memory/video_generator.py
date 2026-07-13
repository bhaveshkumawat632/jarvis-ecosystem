import os
import logging
from .prompt_engine import PromptEngine
from .video_gateway import VideoGateway
from .character_manager import get_db_connection

logger = logging.getLogger(__name__)

class VideoGenerator:
    def __init__(self, output_dir="rendered_output"):
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.gateway = VideoGateway()
        self.prompt_engine = PromptEngine()

    def generate_scene_video(self, scene_id: str):
        # 1. Compile prompt using CMS, ESM, and Director
        master_prompt = self.prompt_engine.compile_scene_prompt(scene_id)
        
        # 2. Submit to Gateway
        job_id = self.gateway.submit_with_retry(master_prompt)
        if not job_id:
            logger.error(f"Failed to submit video job for scene {scene_id}")
            return None
            
        provider = self.gateway.provider_type
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO Video_Jobs (job_id, scene_id, provider, prompt, status) 
               VALUES (?, ?, ?, ?, 'PENDING')""",
            (job_id, scene_id, provider, master_prompt)
        )
        conn.commit()

        # 3. Poll for completion
        download_url = self.gateway.poll_job(job_id)
        
        if not download_url:
            cursor.execute("UPDATE Video_Jobs SET status = 'FAILED' WHERE job_id = ?", (job_id,))
            conn.commit()
            conn.close()
            return None
            
        cursor.execute("UPDATE Video_Jobs SET status = 'COMPLETED', download_url = ? WHERE job_id = ?", (download_url, job_id))
        conn.commit()

        # 4. Download Asset
        output_filename = os.path.join(self.output_dir, f"video_{scene_id}.mp4")
        
        success = self.gateway.download_asset(download_url, output_filename)
            
        if success:
            cursor.execute("UPDATE Video_Jobs SET local_path = ? WHERE job_id = ?", (output_filename, job_id))
            cursor.execute("UPDATE Scenes SET generated_video_url = ? WHERE scene_id = ?", (output_filename, scene_id))
            conn.commit()
            
        conn.close()
        return output_filename
