import uuid
import os
import subprocess
import json
import logging
from .character_manager import get_db_connection

logger = logging.getLogger(__name__)

class FFmpegAssemblyEngine:
    def __init__(self, output_dir="rendered_output"):
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def start_render_job(self, project_id, resolution="1920x1080"):
        job_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO Render_Jobs 
               (job_id, project_id, status, total_duration_rendered, output_resolution) 
               VALUES (?, ?, ?, ?, ?)""",
            (job_id, project_id, "ASSEMBLING_TIMELINE", 0.0, resolution)
        )
        conn.commit()
        conn.close()
        return job_id

    def validate_assets(self, video_files, audio_files):
        """Check if all files exist on disk before rendering."""
        missing = []
        for f in video_files + audio_files:
            if not os.path.exists(f):
                missing.append(f)
        if missing:
            raise FileNotFoundError(f"Missing assets: {missing}")
        return True

    def build_timeline(self, project_id, video_files, dialogue_files, bgm_file=None):
        """Constructs render chunks given input lists. Real system would query DB for file paths."""
        self.validate_assets(video_files, dialogue_files)
        
        # We will split into chunks. For simplicity, just 1 chunk containing all passed files.
        chunk_data = {
            "chunk_0": {
                "videos": video_files,
                "dialogue": dialogue_files,
                "bgm": bgm_file
            }
        }
        return chunk_data

    def render_chunk(self, job_id, chunk_name, chunk_data):
        videos = chunk_data["videos"]
        dialogue = chunk_data["dialogue"]
        bgm = chunk_data.get("bgm")
        
        out_file = os.path.join(self.output_dir, f"{job_id}_{chunk_name}.mp4")
        
        # Build FFmpeg command
        # Complex filter to concatenate video and mix audio
        cmd = ["ffmpeg", "-y"]
        
        for v in videos:
            cmd.extend(["-i", v])
        
        for d in dialogue:
            cmd.extend(["-i", d])
            
        if bgm:
            cmd.extend(["-i", bgm])
            
        # Simplified filter graph for POC: concat videos, mix audio.
        # In full production, this includes `xfade` for transitions and `sidechaincompress` for ducking.
        filter_str = ""
        v_streams = ""
        a_streams = ""
        for i in range(len(videos)):
            v_streams += f"[{i}:v:0]"
            
        filter_str += f"{v_streams}concat=n={len(videos)}:v=1:a=0[v];"
        
        # Combine dialogue tracks (simplified: just taking the first one for the poc)
        # Adding BGM mix if present
        if bgm:
            bgm_idx = len(videos) + len(dialogue)
            # amix dialogue + bgm
            filter_str += f"[{len(videos)}:a:0][{bgm_idx}:a:0]amix=inputs=2:duration=first:dropout_transition=2[a]"
        else:
            filter_str += f"[{len(videos)}:a:0]anull[a]"
            
        cmd.extend(["-filter_complex", filter_str, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-c:a", "aac", out_file])
        
        logger.info(f"FFmpeg Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg Error: {result.stderr}")
                self._update_job_status(job_id, "FAILED")
                return False
                
            self._update_job_status(job_id, "RENDERING_CHUNK")
            return out_file
        except Exception as e:
            logger.error(f"Render exception: {e}")
            self._update_job_status(job_id, "FAILED")
            return False

    def concatenate_chunks(self, job_id, chunk_files):
        list_file_path = os.path.join(self.output_dir, f"{job_id}_list.txt")
        final_out = os.path.join(self.output_dir, f"final_{job_id}.mp4")
        
        with open(list_file_path, "w") as f:
            for c in chunk_files:
                f.write(f"file '{os.path.abspath(c)}'\n")
                
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path, "-c", "copy", final_out]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"Concat Error: {result.stderr}")
            self._update_job_status(job_id, "FAILED")
            return None
            
        self._update_job_status(job_id, "COMPLETED", final_out)
        return final_out
        
    def _update_job_status(self, job_id, status, url=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if url:
            cursor.execute("UPDATE Render_Jobs SET status = ?, final_movie_url = ? WHERE job_id = ?", (status, url, job_id))
        else:
            cursor.execute("UPDATE Render_Jobs SET status = ? WHERE job_id = ?", (status, job_id))
        conn.commit()
        conn.close()

    def recover_job(self, job_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Render_Jobs SET status = 'ASSEMBLING_TIMELINE' WHERE job_id = ?", (job_id,))
        conn.commit()
        conn.close()
        return True
