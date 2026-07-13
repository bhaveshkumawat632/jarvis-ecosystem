import os
import random
import yt_dlp
import uuid
from celery.schedules import crontab
from tasks.autoclip_worker import celery_app, process_viral_clip

celery_app.conf.task_always_eager = True

TOPICS = [
    "Hindi podcast motivation",
    "Business case study Hindi",
    "Fascinating science facts Hindi",
    "History mysteries Hindi",
    "Tech podcast Hindi"
]

def find_copyright_free_video():
    """
    Searches YouTube for a random topic, strictly filtering for 
    Creative Commons (Copyright Free) licenses.
    """
    topic = random.choice(TOPICS)
    print(f"[*] AI Hunter Waking Up... Searching topic: '{topic}'")
    
    search_query = f"ytsearch5:{topic} creative commons"

    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(search_query, download=False)
            
            if 'entries' in search_results and search_results['entries']:
                video_info = random.choice(search_results['entries'])
                video_url = video_info.get('url')
                title = video_info.get('title')
                
                print(f"[+] Found Copyright-Free Match: {title}")
                print(f"[+] URL: {video_url}")
                return video_url
            else:
                print("[-] No valid videos found in this search.")
                return None
                
    except Exception as e:
        print(f"[-] Hunter Error: {str(e)}")
        return None

@celery_app.task
def dispatch_daily_batch():
    print("=======================================")
    print("[*] 2:00 AM IST: NIGHT SHIFT INITIATED")
    print("=======================================")
    for _ in range(2):
        target_url = find_copyright_free_video()
        if target_url:
            project_id = f"nightshift_{uuid.uuid4().hex[:8]}"
            print(f"[*] Dispatching {project_id} to Celery Queue...")
            process_viral_clip.delay(project_id, target_url)

# --- CELERY BEAT CLOCKWORK CONFIGURATION ---
celery_app.conf.timezone = 'Asia/Kolkata'

celery_app.conf.beat_schedule = {
    'run-night-shift-every-day-at-2am': {
        'task': 'tasks.youtube_hunter.dispatch_daily_batch',
        'schedule': crontab(hour=2, minute=0),
    },
}

if __name__ == "__main__":
    dispatch_daily_batch()
