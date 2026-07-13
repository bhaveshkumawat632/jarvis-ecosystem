import uuid
import sys
import os

# Append the current directory to PYTHONPATH so tasks can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tasks.autoclip_worker import process_viral_clip, celery_app

# Run synchronously for this test environment to bypass Redis
celery_app.conf.task_always_eager = True

def run_quick_demo():
    print("==========================================================")
    print("      @Ahgori_ AI Factory - QUICK DEMO TEST RUN           ")
    print("==========================================================")
    
    # You can paste any YouTube link here when prompted.
    # By default, I've set a short podcast snippet for a fast test.
    test_url = input("Enter YouTube URL (Press Enter to use default test video): ")
    
    if not test_url.strip():
        # Default test video (Short, clear speech, easy to track)
        test_url = "https://www.youtube.com/watch?v=FLe43lF6cK0" 
        
    project_id = f"demo_run_{uuid.uuid4().hex[:6]}"
    
    print(f"\n[*] Project ID: {project_id}")
    print(f"[*] Target URL: {test_url}")
    print("[*] Sending task to your i3 Processor...")
    
    # This command dispatches the job to your Celery worker
    process_viral_clip.delay(project_id, test_url)
    
    print("\n[+] Task successfully dispatched!")
    print("[👉] Open your 'Celery Worker' terminal to watch the magic happen!")
    print("==========================================================")

if __name__ == "__main__":
    run_quick_demo()
