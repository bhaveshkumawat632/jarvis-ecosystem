import os
import glob
import logging
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from youtube_uploader import YouTubeUploader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [LONGFORM DISPATCHER] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LongformDispatcher:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ready_dir = os.path.join(self.base_dir, "longform_factory", "ready_to_upload")
        os.makedirs(self.ready_dir, exist_ok=True)

    def dispatch(self):
        videos = glob.glob(os.path.join(self.ready_dir, "*.mp4"))
        if not videos:
            logger.warning("No polished 16:9 movies found in the queue. Longform Factory needs to make more!")
            return False

        videos.sort(key=os.path.getmtime)
        video_to_upload = videos[0]

        logger.info(f"[*] Dispatching Pre-Polished 16:9 Short Movie: {video_to_upload}")
        
        uploader = YouTubeUploader()
        # Uploading as a standard video, not a Short
        success = uploader.upload_video(video_to_upload)
        
        if success:
            logger.info("[*] Successfully uploaded longform video from the stockpile.")
            os.remove(video_to_upload)
            return True
            
        logger.error("[!] Failed to upload the longform video.")
        return False

if __name__ == "__main__":
    dispatcher = LongformDispatcher()
    dispatcher.dispatch()
