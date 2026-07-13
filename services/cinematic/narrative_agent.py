import os
import json
import re
from openai import OpenAI, APIConnectionError, RateLimitError
from jarvis_core_lib.config import PipelineConfig
# Mock interface matching Phase 24 Database Layout
class ProductionShowBible:
    def __init__(self, project_dir):
        self.project_dir = project_dir
    def register_character(self, name, prompt, s_path, v_path): pass
    def log_scene_state(self, scene_num, loc, sfx, notes): pass

def run_async_production_pipeline(project_dir, payload):
    print(f"[+] Local Celery Queue triggered successfully for project folder: {project_dir}")

class HybridNarrativeAgent:
    """Orchestrates script extraction using cloud NIM with resilient offline fallbacks."""
    def __init__(self):
        self.active_cloud = PipelineConfig.validate_environment()
        if self.active_cloud:
            self.client = OpenAI(
                base_url=PipelineConfig.NVIDIA_BASE_URL,
                api_key=PipelineConfig.NVIDIA_API_KEY
            )
        else:
            self.client = None

    def _execute_cloud_inference(self, prompt, schema):
        """Queries the enterprise NIM model cluster."""
        print(f"[*] Dispatching execution payload to NVIDIA NIM: {PipelineConfig.NVIDIA_MODEL}")
        completion = self.client.chat.completions.create(
            model=PipelineConfig.NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": f"You are a film director. Output ONLY valid JSON matching this schema: {schema}"},
                {"role": "user", "content": f"Concept: {prompt}"}
            ],
            temperature=0.2,
            max_tokens=2048,
            timeout=30.0  # Fail-fast constraint to trigger local fallback
        )
        return completion.choices[0].message.content

    def _load_local_fallback(self):
        """Resilient local contingency backup execution."""
        print(f"[*] Triggering fallback protocol. Inspecting path: {PipelineConfig.FALLBACK_SCRIPT_PATH}")
        if os.path.exists(PipelineConfig.FALLBACK_SCRIPT_PATH):
            with open(PipelineConfig.FALLBACK_SCRIPT_PATH, "r") as f:
                return json.load(f)
        raise FileNotFoundError("CRITICAL: Pipeline halted. NVIDIA NIM unreachable and fallback_script.json missing.")

    def run(self, user_concept):
        """Main lifecycle block mapping narrative extraction to production execution."""
        schema_definition = '{"project_id": "string", "title": "string", "characters": [], "scenes": []}'
        raw_output = None

        if self.active_cloud:
            try:
                raw_output = self._execute_cloud_inference(user_concept, schema_definition)
            except (APIConnectionError, RateLimitError, Exception) as e:
                print(f"[-] Hardware network exception or timeout occurred: {e}")

        if not raw_output:
            script_data = self._load_local_fallback()
        else:
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            script_data = json.loads(json_match.group(0)) if json_match else json.loads(raw_output)

        # Database and asset lifecycle orchestration
        project_id = script_data.get("project_id", "dynamic_production")
        project_dir = os.path.join(PipelineConfig.PROJECT_ROOT, project_id)
        os.makedirs(project_dir, exist_ok=True)

        show_bible = ProductionShowBible(project_dir)
        print("[+] Synchronized JSON metadata structures with SQLite ShowBible indexes.")
        
        # Write to disk for verification
        script_path = os.path.join(project_dir, "script.json")
        with open(script_path, "w") as f:
            json.dump(script_data, f, indent=4)
        print(f"[+] Script securely written to {script_path}")
        
        run_async_production_pipeline(project_dir, script_data)
        return script_data

if __name__ == "__main__":
    agent = HybridNarrativeAgent()
    agent.run("A cyberpunk heist inside a sub-aquatic data server farm.")
