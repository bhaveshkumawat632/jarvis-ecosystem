import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('/home/junglee01/jarvis_ecosystem')
from tasks.autoclip_worker import process_viral_clip, celery_app

# Run synchronously
celery_app.conf.task_always_eager = True

def run_recovery():
    print("[*] Starting recovery for nightshift_ea1227be")
    process_viral_clip("nightshift_ea1227be", "dummy_url")
    print("[+] Recovery completed")

if __name__ == "__main__":
    run_recovery()
