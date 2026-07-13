from celery import Celery
import os
import sys

# Ensure the root directory is in the path to access movie_generator
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("vidrush.tasks", broker=redis_url, backend=redis_url)

@celery_app.task(bind=True, max_retries=1)
def generate_video_task(self, project_id, idea, voice="en-US-GuyNeural", music_mood="cinematic"):
    print(f"[*] Celery Worker Initiating NVENC Pipeline for Project: {project_id}")
    
    try:
        # Update Celery state to processing
        self.update_state(state='PROCESSING', meta={'status': 'Generating story and assets...'})
        
        # Execute the hardened 5-layer pipeline
        celery_app.send_task("cinematic.generate_movie", args=[project_id, idea, voice, music_mood])
        
        return {'status': 'COMPLETED', 'project_id': project_id}
        
    except Exception as e:
        print(f"[-] Celery Task Crash: {str(e)}")
        # Do not automatically retry video renders to save API budget
        raise self.retry(exc=e, max_retries=0)
