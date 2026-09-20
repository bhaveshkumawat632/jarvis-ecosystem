import os
import requests
import json

class LLMRouter:
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.nvidia_key = os.environ.get("NVIDIA_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")

    def generate_completion(self, system_prompt, user_prompt, response_format=None):
        # Priority-ordered list of API endpoints, models, and keys
        attempts = [
            # 1. Groq (Fastest, very high limits for free users)
            ("groq", "https://api.groq.com/openai/v1/chat/completions", "llama3-8b-8192", self.groq_key),
            
            # 2. Nvidia NIM (Excellent backups, large capacity)
            ("nvidia", "https://integrate.api.nvidia.com/v1/chat/completions", "nvidia/nemotron-4-340b-instruct", self.nvidia_key),
            
            # 3. OpenRouter - Llama 3.3 70B (High quality free model)
            ("openrouter", "https://openrouter.ai/api/v1/chat/completions", "meta-llama/llama-3.3-70b-instruct:free", self.openrouter_key),
            
            # 4. OpenRouter - Llama 3.2 3B (Fast fallback model)
            ("openrouter", "https://openrouter.ai/api/v1/chat/completions", "meta-llama/llama-3.2-3b-instruct:free", self.openrouter_key),
            
            # 5. OpenRouter - Qwen 2.5 Coder (Great for structural/logic tasks)
            ("openrouter", "https://openrouter.ai/api/v1/chat/completions", "qwen/qwen3-coder:free", self.openrouter_key),
        ]

        for provider, url, model, key in attempts:
            if not key or key.endswith("_HERE") or len(key) < 10:
                print(f"[-] [LLM Router] Skipping {provider} ({model}) due to missing or invalid key.")
                continue

            print(f"🔄 [LLM Router] Attempting completion via {provider} using {model}...")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            }

            # OpenRouter requires extra headers to identify the app
            if provider == "openrouter":
                headers["HTTP-Referer"] = "https://github.com/bhaveshkumawat632/jarvis-ecosystem"
                headers["X-Title"] = "Jarvis Cinematic Failover Engine"

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            if response_format:
                payload["response_format"] = response_format

            try:
                # Add reasonable timeout to fail fast if upstream is down or heavily loaded
                r = requests.post(url, headers=headers, json=payload, timeout=25)
                if r.status_code == 200:
                    result = r.json()
                    content = result['choices'][0]['message']['content'].strip()
                    print(f"✅ [LLM Router] Success with {provider} ({model})!")
                    return content
                else:
                    print(f"⚠️ [LLM Router] {provider} returned HTTP {r.status_code}: {r.text[:150]}")
            except Exception as e:
                print(f"⚠️ [LLM Router] Connection to {provider} failed: {e}")
        
        raise RuntimeError("❌ All LLM providers exhausted. Execution halted.")
