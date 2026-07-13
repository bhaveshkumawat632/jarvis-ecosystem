import time
import json
import redis
from workers.celery_worker import generate_video_task

# Submit the task to Celery
print("Submitting task to Celery...")
task = generate_video_task.delay("The Secret Code", 10, "1080p")
task_id = task.id
print(f"Task submitted with ID: {task_id}")

# Connect to Redis
r = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

# Monitor status
for _ in range(30):
    # Check Celery meta
    celery_meta_key = f"celery-task-meta-{task_id}"
    celery_meta = r.get(celery_meta_key)
    
    # Check VidRush task_state
    vidrush_state_key = f"task:{task_id}"
    vidrush_state = r.get(vidrush_state_key)
    
    print("---")
    print(f"Celery state: {celery_meta}")
    print(f"VidRush state: {vidrush_state}")
    
    time.sleep(2)
