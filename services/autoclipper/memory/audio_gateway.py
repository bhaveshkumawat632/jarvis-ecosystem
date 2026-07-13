import os
import time
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioProvider:
    def generate_tts(self, text: str, voice_id: str, output_path: str) -> bool:
        raise NotImplementedError

class OpenAITTSProvider(AudioProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/audio/speech"

    def generate_tts(self, text: str, voice_id: str, output_path: str) -> bool:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # default voice_id to alloy if not provided correctly
        if not voice_id:
            voice_id = "alloy"
            
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice_id
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, stream=True, timeout=30)
        
        if response.status_code == 429:
            raise Exception("RateLimitExceeded")
            
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # Simple file validation
        if os.path.getsize(output_path) < 1000:
            raise ValueError("Generated audio file is too small/corrupt.")
            
        return True

class AudioGateway:
    def __init__(self):
        self.provider_type = os.getenv("AUDIO_PROVIDER", "mock")
        
        if self.provider_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "sk-mock-key")
            self.provider = OpenAITTSProvider(api_key)
        else:
            self.provider = None

    def generate_with_retry(self, text: str, voice_id: str, output_path: str, max_retries=3):
        if self.provider is None:
            raise ValueError(f"No audio provider configured. Cannot generate audio for: {text}")

        retries = 0
        backoff = 1.0

        while retries < max_retries:
            try:
                logger.info(f"AudioGateway: Requesting TTS (Attempt {retries + 1}/{max_retries})")
                success = self.provider.generate_tts(text, voice_id, output_path)
                
                if success:
                    logger.info("AudioGateway: Generation successful and saved to disk.")
                    return output_path
                    
            except Exception as e:
                logger.warning(f"AudioGateway Error: {str(e)}")
                if "RateLimitExceeded" in str(e):
                    time.sleep(backoff)
                    backoff *= 2
                    retries += 1
                else:
                    retries += 1

        logger.error("AudioGateway: Max retries exhausted.")
        return None
