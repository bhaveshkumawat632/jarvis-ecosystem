import os
import json
import logging
from config import OLLAMA_API_KEY
from memory.llm_gateway import OllamaCloudProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_llm():
    print("=======================================")
    print("[*] Testing Live LLM Gateway")
    print("=======================================")
    try:
        provider = OllamaCloudProvider(api_key=OLLAMA_API_KEY, model_name="gpt-oss:120b")
        sys_prompt = "You are a professional screenwriter. Return JSON with 'genre' and 'action' descriptions."
        user_msg = "Create a 30-second cinematic sci-fi scene about a lone explorer discovering an abandoned alien city."
        
        response = provider.generate(sys_prompt, user_msg)
        print("RAW RESPONSE:")
        print(response)
        
        print("\n[+] Verification:")
        print("Provider: Ollama Cloud")
        print("Model: gpt-oss:120b")
        
    except Exception as e:
        print(f"Failed to verify LLM: {e}")

if __name__ == "__main__":
    verify_llm()
