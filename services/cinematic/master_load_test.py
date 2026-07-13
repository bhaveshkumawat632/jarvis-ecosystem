import time
import random
from locust import HttpUser, task, between, LoadTestShape

# To simulate geographical diversity, we can inject diverse IP headers
GEO_IPS = [
    "203.0.113.1",   # Asia
    "198.51.100.1",  # North America
    "81.2.69.142",   # Europe
    "177.0.0.1",     # South America
    "102.164.0.0",   # Africa
    "1.1.1.1"        # Oceania
]

def get_geo_headers():
    return {
        "X-Forwarded-For": random.choice(GEO_IPS),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

class Tier1BasicUser(HttpUser):
    """
    Tier 1 (Basic) User: High Volume, Low Complexity.
    Simulates checking project lists and viewing static progress.
    """
    weight = 3
    wait_time = between(1, 3) # Very active, high volume

    @task
    def check_projects(self):
        self.client.get("/api/projects", headers=get_geo_headers(), name="Tier1_GetProjects")

class Tier2StudioUser(HttpUser):
    """
    Tier 2 (Studio) User: High Complexity.
    Simulates POST requests to generate videos (requiring heavy processing).
    """
    weight = 2
    wait_time = between(10, 20) # Lower volume, high complexity payload

    @task
    def create_complex_project(self):
        payload = {
            "idea": "A high-fidelity cinematic scene of a futuristic city with flying cars.",
            "music_mood": "cinematic"
        }
        with self.client.post("/api/projects", json=payload, headers=get_geo_headers(), catch_response=True, name="Tier2_CreateProject") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure("Failed to create studio project")

class EnterpriseUser(HttpUser):
    """
    Enterprise API User: High Security Overhead.
    Simulates requests passing strict authorization headers.
    """
    weight = 1
    wait_time = between(5, 10)

    @task
    def enterprise_secure_call(self):
        headers = get_geo_headers()
        # Adding mock enterprise security headers
        headers.update({
            "Authorization": "Bearer ENTP-SECURE-TOKEN-999",
            "X-Enterprise-Client": "CorpX"
        })
        self.client.get("/api/projects", headers=headers, name="Enterprise_GetProjects_Secure")

class EmergencyOverrideUser(HttpUser):
    """
    Emergency Manual Override User: Forces fallback/local components.
    Simulates invalid tokens or forced fallback flags to trigger local processing.
    """
    weight = 4
    wait_time = between(8, 15)

    @task
    def trigger_fallback_generation(self):
        payload = {
            "idea": "Emergency manual override task",
            "hf_token": "INVALID_TOKEN_FORCE_FALLBACK", # Forces local components/fallback
            "replicate_key": "INVALID_KEY" 
        }
        headers = get_geo_headers()
        headers["X-Emergency-Override"] = "true"
        
        with self.client.post("/api/projects", json=payload, headers=headers, catch_response=True, name="Emergency_Fallback_Trigger") as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure("Failed to trigger emergency override")


# To run this script for 1 hour with exactly 10 users:
# locust -f master_load_test.py --headless -u 10 -r 10 --run-time 1h --host http://127.0.0.1:5000
