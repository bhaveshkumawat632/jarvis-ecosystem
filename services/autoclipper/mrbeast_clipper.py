import os
import glob
import logging
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from youtube_uploader import YouTubeUploader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Dispatcher:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ready_dir = os.path.join(self.base_dir, "shorts_factory", "ready_to_upload")
        os.makedirs(self.ready_dir, exist_ok=True)

    def dispatch(self):
        # Find the oldest polished video in the queue
        videos = glob.glob(os.path.join(self.ready_dir, "*.mp4"))
        if not videos:
            logger.warning("No polished videos found in the queue. Factory needs to make more!")
            return False

        # Sort by creation time to upload the oldest first
        videos.sort(key=os.path.getmtime)
        video_to_upload = videos[0]

        logger.info(f"[*] Dispatching Pre-Polished Video: {video_to_upload}")
        
        uploader = YouTubeUploader()
        success = uploader.upload_video(video_to_upload)
        
        if success:
            logger.info("[*] Successfully uploaded from the stockpile.")
            # Remove the uploaded video from the queue so it doesn't upload again
            os.remove(video_to_upload)
            return True
            
        logger.error("[!] Failed to upload the video.")
        return False

if __name__ == "__main__":
    dispatcher = Dispatcher()
    dispatcher.dispatch()
