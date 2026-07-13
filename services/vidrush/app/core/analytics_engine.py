import json
import os
from configs.settings import BASE_DIR

class AnalyticsEngine:
    def __init__(self):
        self.log_file = os.path.join(BASE_DIR, "logs", "analytics.json")
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                json.dump([], f)
                
    def log_performance(self, video_id: str, views: int, retention_percent: float, ctr_percent: float):
        entry = {
            "video_id": video_id,
            "views": views,
            "retention": retention_percent,
            "ctr": ctr_percent
        }
        with open(self.log_file, "r") as f:
            data = json.load(f)
        data.append(entry)
        with open(self.log_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Logged performance for {video_id}: CTR {ctr_percent}%")

    def identify_best_hooks(self):
        with open(self.log_file, "r") as f:
            data = json.load(f)
        # Sort by retention and ctr
        best = sorted(data, key=lambda x: x["retention"] * x["ctr"], reverse=True)
        return best[:5]

if __name__ == "__main__":
    ae = AnalyticsEngine()
    ae.log_performance("video_001", 15000, 65.4, 12.1)
    print("Best Performers:", ae.identify_best_hooks())
