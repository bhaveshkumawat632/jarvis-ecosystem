import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('/home/junglee01/jarvis_ecosystem')
from tasks.autoclip_worker import process_viral_clip, celery_app

celery_app.conf.task_always_eager = True

def run_mrbeast():
    project_id = f"mrbeast_{uuid.uuid4().hex[:6]}"
    test_url = "https://www.youtube.com/watch?v=__fmDj0ZJ1Q"
    
    print(f"[*] Starting Auto Clipper for MrBeast video: {test_url}")
    process_viral_clip(project_id, test_url)
    print(f"[+] Successfully finished generating clips for {project_id}")

if __name__ == "__main__":
    run_mrbeast()
