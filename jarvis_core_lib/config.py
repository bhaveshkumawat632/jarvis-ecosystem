import os

class PipelineConfig:
    """Handles global configuration and routing flags for Jarvis Universal."""
    # Infrastructure Modes
    USE_NVIDIA_API = os.environ.get("USE_NVIDIA_API", "TRUE").upper() == "TRUE"
    
    # Environment Keys
    NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "NVIDIA_API_KEY_HERE")
    
    # API Configurations
    NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL = "nvidia/nemotron-4-340b-instruct"
    
    # Local Resource Paths
    PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/home/junglee01/jarvis_universal/projects")
    FALLBACK_SCRIPT_PATH = os.path.join(PROJECT_ROOT, "fallback_script.json")

    @classmethod
    def validate_environment(cls):
        """Validates configuration state before booting the pipeline."""
        if cls.USE_NVIDIA_API and cls.NVIDIA_API_KEY == "YOUR_NVIDIA_API_KEY_HERE":
            print("[-] WARNING: NVIDIA_API_KEY contains placeholder. Forcing local fallback mode.")
            return False
        return cls.USE_NVIDIA_API
