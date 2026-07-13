import requests
import time
import json
import sys

API_URL = "http://localhost:8000/api/v1/workflow"

def test_pipeline():
    print("🚀 Triggering E2E video generation via FastAPI...", flush=True)
    try:
        response = requests.post(f"{API_URL}/generate", json={
            "topic": "A super fast 5-second test video",
            "duration": 5,
            "quality": "1080p",
            "style": "reddit_story"
        })
        response.raise_for_status()
        data = response.json()
        task_id = data.get("task_id")
        print(f"✅ Generation triggered! Task ID: {task_id}", flush=True)
    except Exception as e:
        print(f"❌ Failed to trigger generation: {e}")
        return
    
    print("\n📡 Polling status endpoint every 2 seconds...", flush=True)
    for _ in range(90):
        try:
            status_res = requests.get(f"{API_URL}/status/{task_id}")
            status_res.raise_for_status()
            status_data = status_res.json()
            
            state = status_data.get("state")
            meta = status_data.get("metadata", {})
            progress = meta.get("progress", "N/A")
            stage = meta.get("stage", "N/A")
            
            print(f"[{state}] Progress: {progress}% | Stage: {stage}", flush=True)
            
            if state == "COMPLETED" or state == "FAILED":
                if state == "COMPLETED":
                    output = meta.get("output")
                    print(f"\n🎉 SUCCESS! Output file available at: {output}")
                    return True
                else:
                    print(f"\n💀 FAILED: {meta.get('error')}")
                    return False
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            
        time.sleep(2)
    
    print("\n⌛ Timeout reached before task completed.")
    return False

if __name__ == "__main__":
    test_pipeline()
