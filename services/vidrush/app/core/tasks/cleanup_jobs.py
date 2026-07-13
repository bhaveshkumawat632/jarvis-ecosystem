import structlog
import os
import time
import shutil
from configs.settings import TEMP_DIR, OUTPUT_DIR

logger = structlog.get_logger(__name__)

class AutomaticCleanupJob:
    """Prevents storage explosions by aggressively wiping orphaned, temp, and old logs."""
    def __init__(self):
        self.temp_dir = TEMP_DIR
        self.outputs_dir = OUTPUT_DIR
        self.max_temp_age_seconds = 3600  # 1 hour
        self.max_output_age_seconds = 604800 # 7 days
        
    def run_cleanup(self):
        logger.info("cleanup_job_started")
        now = time.time()
        
        # 1. Purge Temp Files
        purged_temp = 0
        if os.path.exists(self.temp_dir):
            for filename in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, filename)
                if os.path.isfile(filepath):
                    if now - os.path.getmtime(filepath) > self.max_temp_age_seconds:
                        os.remove(filepath)
                        purged_temp += 1
                        
        # 2. Purge Old Outputs
        purged_outputs = 0
        if os.path.exists(self.outputs_dir):
            for filename in os.listdir(self.outputs_dir):
                filepath = os.path.join(self.outputs_dir, filename)
                if os.path.isfile(filepath):
                    if now - os.path.getmtime(filepath) > self.max_output_age_seconds:
                        os.remove(filepath)
                        purged_outputs += 1
                        
        logger.info("cleanup_job_completed", temp_files_deleted=purged_temp, old_outputs_deleted=purged_outputs)

cleanup_job = AutomaticCleanupJob()
