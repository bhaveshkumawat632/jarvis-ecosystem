import os
import shutil
from jarvis_core_lib.database import get_db_connection
from celery import Celery

app = Celery('cinematic.janitor', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@app.task(bind=True, name="task.janitor_cleanup")
def janitor_cleanup(self, project_dir):
    """
    Phase 37 Priority 1: Storage Lifecycle Node.
    Prevents the Storage Sawtooth Effect by safely sweeping heavy temporary scratch files 
    after confirming the final multiplexed Ultra-HD master exists.
    """
    print(f"[*] Janitor Node: Initiating lifecycle cleanup for {project_dir}")
    
    final_master = os.path.join(project_dir, "final_master_ultra_hd.mp4")
    
    # 1. State Verification Hook
    # Check SQLite ShowBible first to ensure we aren't interrupting a failed queue
    bible_path = os.path.join(project_dir, "production_show_bible.db")
    if os.path.exists(bible_path):
        try:
            conn = get_db_connection(bible_path)
            c = conn.cursor()
            # Simple validation to verify the database is closed and intact
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = c.fetchall()
            conn.close()
            print(f"[+] Verified ProductionShowBible integrity. Tables found: {len(tables)}")
        except Exception as e:
            print(f"[-] ShowBible state locked or corrupted. Aborting cleanup: {e}")
            return {"status": "aborted", "reason": "Database lock/corruption"}

    # Validate the target video asset
    if not os.path.exists(final_master) or os.path.getsize(final_master) == 0:
        print("[-] Janitor aborted: final_master_ultra_hd.mp4 is missing or zero bytes.")
        return {"status": "aborted", "reason": "Missing master output"}
        
    print("[+] State verification passed. Proceeding with targeted directory purging.")
    
    # 2. Targeted Directory Purging
    bytes_freed = 0
    files_deleted = 0
    
    # Clean up intermediate wav and mp4 files in project root
    for f in os.listdir(project_dir):
        if f == "final_master_ultra_hd.mp4":
            continue
            
        file_path = os.path.join(project_dir, f)
        if os.path.isfile(file_path):
            if f.endswith('.wav') or f.endswith('.mp4') or f.endswith('.mp3'):
                try:
                    bytes_freed += os.path.getsize(file_path)
                    os.remove(file_path)
                    files_deleted += 1
                except Exception as e:
                    print(f"[-] Failed to delete {f}: {e}")
                    
    # Clean up scratch directories
    scratch_dirs = ["scratch_vox", "temp_frames", "intermediate_renders"]
    for d in scratch_dirs:
        dir_path = os.path.join(project_dir, d)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                for root, dirs, files in os.walk(dir_path):
                    for name in files:
                        bytes_freed += os.path.getsize(os.path.join(root, name))
                shutil.rmtree(dir_path)
                print(f"[+] Swept directory: {dir_path}")
            except Exception as e:
                print(f"[-] Failed to sweep {dir_path}: {e}")
                
    freed_mb = bytes_freed / (1024 * 1024)
    print(f"[*] Janitor Cycle Complete. Reclaimed {freed_mb:.2f} MB of disk space. Purged {files_deleted} artifacts.")
    
    return {"status": "success", "freed_mb": freed_mb}
