import os
import time
import requests
import logging
import uuid
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoProvider:
    def submit_job(self, prompt: str) -> str:
        raise NotImplementedError
        
    def check_status(self, job_id: str) -> dict:
        """Returns dict with status ('PENDING', 'COMPLETED', 'FAILED') and url if complete."""
        raise NotImplementedError

class LumaVideoProvider(VideoProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.lumalabs.ai/dream-machine/v1"

    def submit_job(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"prompt": prompt}
        response = requests.post(f"{self.base_url}/generations", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 429:
            raise Exception("RateLimitExceeded")
            
        response.raise_for_status()
        return response.json()['id']

    def check_status(self, job_id: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        response = requests.get(f"{self.base_url}/generations/{job_id}", headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        status = "PENDING"
        if data.get("state") == "completed":
            status = "COMPLETED"
        elif data.get("state") == "failed":
            status = "FAILED"
            
        return {
            "status": status,
            "url": data.get("assets", {}).get("video")
        }

class VideoGateway:
    def __init__(self):
        self.provider_type = os.getenv("VIDEO_PROVIDER", "mock")
        
        if self.provider_type == "luma":
            api_key = os.getenv("LUMA_API_KEY", "sk-mock-key")
            self.provider = LumaVideoProvider(api_key)
        else:
            self.provider = None

    def submit_with_retry(self, prompt: str, max_retries=3) -> str:
        if self.provider is None:
            raise ValueError(f"No video provider configured. Cannot submit job for prompt: {prompt}")

        retries = 0
        backoff = 2.0

        while retries < max_retries:
            try:
                logger.info(f"VideoGateway: Submitting Job (Attempt {retries + 1}/{max_retries})")
                job_id = self.provider.submit_job(prompt)
                logger.info(f"VideoGateway: Job {job_id} submitted.")
                return job_id
            except Exception as e:
                logger.warning(f"VideoGateway Error: {str(e)}")
                if "RateLimitExceeded" in str(e):
                    time.sleep(backoff)
                    backoff *= 2
                    retries += 1
                else:
                    retries += 1

        logger.error("VideoGateway: Max retries exhausted for submission.")
        return None

    def poll_job(self, job_id: str, max_polling_time=600, poll_interval=10) -> str:
        if self.provider is None:
            raise ValueError(f"No video provider configured. Cannot poll job: {job_id}")

        start_time = time.time()
        while time.time() - start_time < max_polling_time:
            try:
                res = self.provider.check_status(job_id)
                status = res["status"]
                logger.info(f"VideoGateway: Job {job_id} status: {status}")
                
                if status == "COMPLETED":
                    return res["url"]
                elif status == "FAILED":
                    logger.error(f"VideoGateway: Job {job_id} failed on provider side.")
                    return None
            except Exception as e:
                logger.warning(f"VideoGateway Polling Error: {str(e)}")
            
            time.sleep(poll_interval)
            
        logger.error(f"VideoGateway: Job {job_id} timed out after {max_polling_time} seconds.")
        return None

    def download_asset(self, url: str, output_path: str) -> bool:
        if self.provider is None:
            raise ValueError("No video provider configured. Cannot download asset.")

        logger.info(f"VideoGateway: Downloading {url} to {output_path}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        if os.path.getsize(output_path) < 1000:
            raise ValueError("Downloaded video file is corrupt/empty.")
            
        return True
