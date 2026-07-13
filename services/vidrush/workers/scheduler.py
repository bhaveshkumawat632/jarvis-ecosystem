from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

class VidRushScheduler:
    def __init__(self):
        self.scheduler = BlockingScheduler()
        
    def add_job(self, topic, run_time=None):
        def generate_job():
            print(f"[{datetime.now()}] Starting scheduled generation for: {topic}")
            # Import Orchestrator dynamically to avoid circular dependencies
            from app.core.orchestrator import Orchestrator
            orch = Orchestrator()
            orch.run_full_pipeline(topic, 8, "1080p")
            
        if run_time:
            self.scheduler.add_job(generate_job, 'date', run_date=run_time)
        else:
            self.scheduler.add_job(generate_job, 'interval', hours=24) # Daily batch
            
    def start(self):
        print("Starting Scheduler...")
        self.scheduler.start()

if __name__ == "__main__":
    s = VidRushScheduler()
    # s.add_job("Interesting Space Facts")
    print("Scheduler initialized.")
