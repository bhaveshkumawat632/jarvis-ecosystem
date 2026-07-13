import unittest
import os
from jarvis_core_lib.config import PipelineConfig
from narrative_agent import HybridNarrativeAgent

class TestHybridPipelineArchitecture(unittest.TestCase):
    def setUp(self):
        """Setup workspace variables for execution testing."""
        PipelineConfig.PROJECT_ROOT = "./test_workspace"
        PipelineConfig.FALLBACK_SCRIPT_PATH = "./test_workspace/fallback_script.json"
        os.makedirs(PipelineConfig.PROJECT_ROOT, exist_ok=True)
        
        # Write dummy fallback script
        self.dummy_payload = {"project_id": "test_fallback", "title": "Fallback Active"}
        with open(PipelineConfig.FALLBACK_SCRIPT_PATH, "w") as f:
            import json
            json.dump(self.dummy_payload, f)

    def test_fallback_activation_on_invalid_key(self):
        """Verifies system drops gracefully to local files if API configuration is incomplete."""
        PipelineConfig.NVIDIA_API_KEY = "YOUR_NVIDIA_API_KEY_HERE"
        agent = HybridNarrativeAgent()
        self.assertFalse(agent.active_cloud)
        
        resulting_data = agent.run("Test concept execution")
        self.assertEqual(resulting_data["project_id"], "test_fallback")

    def tearDown(self):
        """Clean up generated test file structures."""
        import shutil
        if os.path.exists(PipelineConfig.PROJECT_ROOT):
            shutil.rmtree(PipelineConfig.PROJECT_ROOT)

if __name__ == "__main__":
    unittest.main()
