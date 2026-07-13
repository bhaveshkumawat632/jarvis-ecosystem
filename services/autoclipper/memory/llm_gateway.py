import os
import json
import time
import requests
import logging

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMProvider:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

class OpenAILikeProvider(LLMProvider):
    def __init__(self, base_url: str, api_key: str, model_name: str):
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }
        
        response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 429:
            raise Exception("RateLimitExceeded")
            
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']


class OllamaCloudProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.base_url = "https://ollama.com/api"
        self.model_name = model_name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        
        response = requests.post(f"{self.base_url}/chat", headers=headers, json=payload, timeout=60)
        
        if response.status_code == 429:
            raise Exception("RateLimitExceeded")
            
        response.raise_for_status()
        data = response.json()
        return data['message']['content']


class LLMGateway:
    def __init__(self):
        self.provider_type = os.getenv("LLM_PROVIDER", "ollama")
        
        if self.provider_type == "openai":
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is missing")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.provider = OpenAILikeProvider(base_url, api_key, model)
        elif self.provider_type == "nim":
            base_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
            api_key = os.getenv("NIM_API_KEY")
            if not api_key:
                raise ValueError("NIM_API_KEY is missing")
            model = os.getenv("NIM_MODEL", "meta/llama3-70b-instruct")
            self.provider = OpenAILikeProvider(base_url, api_key, model)
        elif self.provider_type == "ollama":
            api_key = os.getenv("OLLAMA_API_KEY")
            if not api_key:
                raise ValueError("OLLAMA_API_KEY is missing")
            model = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")
            self.provider = OllamaCloudProvider(api_key, model)
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {self.provider_type}")

    def execute_with_retry(self, system_prompt: str, user_prompt: str, max_retries=3, required_keys=None):
        if self.provider is None:
            raise Exception("No provider configured.")

        retries = 0
        backoff = 1.0

        while retries < max_retries:
            try:
                logger.info(f"LLMGateway: Making request to {self.provider_type} (Attempt {retries + 1}/{max_retries})")
                raw_response = self.provider.generate(system_prompt, user_prompt)
                
                if raw_response.startswith("```json"):
                    raw_response = raw_response[7:]
                    if raw_response.endswith("```"):
                        raw_response = raw_response[:-3]
                raw_response = raw_response.strip("` \n")
                
                parsed_json = json.loads(raw_response)
                
                if required_keys:
                    missing_keys = [k for k in required_keys if k not in parsed_json]
                    if missing_keys:
                        raise ValueError(f"Malformed JSON: Missing keys {missing_keys}")
                        
                logger.info("LLMGateway: Request successful and validated.")
                return parsed_json
                
            except Exception as e:
                logger.warning(f"LLMGateway Error with {self.provider_type}: {str(e)}")
                if "RateLimitExceeded" in str(e):
                    time.sleep(backoff)
                    backoff *= 2
                    retries += 1
                elif isinstance(e, json.JSONDecodeError) or isinstance(e, ValueError):
                    retries += 1
                else:
                    retries += 1

        # FALLBACK MECHANISM to NVIDIA if Ollama fails
        if self.provider_type == "ollama":
            import config
            if hasattr(config, 'NIM_API_KEY') and config.NIM_API_KEY:
                logger.error("Ollama exhausted all retries. Falling back to NVIDIA NIM API...")
                self.provider_type = "nim"
                base_url = "https://integrate.api.nvidia.com/v1"
                self.provider = OpenAILikeProvider(base_url, config.NIM_API_KEY, config.NIM_MODEL)
                return self.execute_with_retry(system_prompt, user_prompt, max_retries, required_keys)

        logger.error("LLMGateway: Max retries exhausted across all available providers.")
        return None
