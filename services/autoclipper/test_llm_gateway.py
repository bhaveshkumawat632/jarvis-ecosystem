import unittest
from unittest.mock import patch, Mock
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.llm_gateway import LLMGateway, OllamaCloudProvider
import json
import requests

class TestLLMGateway(unittest.TestCase):
    @patch('memory.llm_gateway.requests.post')
    def test_provider_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": '{"success": true}'}
        }
        mock_post.return_value = mock_resp

        provider = OllamaCloudProvider("mock_key", "gpt-oss:120b")
        res = provider.generate("sys", "user")
        self.assertEqual(res, '{"success": true}')

    @patch('memory.llm_gateway.requests.post')
    def test_provider_rate_limit(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 429
        mock_post.return_value = mock_resp

        provider = OllamaCloudProvider("mock_key", "gpt-oss:120b")
        with self.assertRaises(Exception) as context:
            provider.generate("sys", "user")
        self.assertTrue("RateLimitExceeded" in str(context.exception))

    @patch('memory.llm_gateway.time.sleep')
    @patch.object(OllamaCloudProvider, 'generate')
    def test_gateway_retry_logic(self, mock_generate, mock_sleep):
        os.environ["LLM_PROVIDER"] = "ollama"
        os.environ["OLLAMA_API_KEY"] = "mock_key"
        gateway = LLMGateway()

        # Fail twice with RateLimit, succeed on third
        mock_generate.side_effect = [
            Exception("RateLimitExceeded"),
            Exception("RateLimitExceeded"),
            '{"action": "jump", "tension": 5, "is_dialogue": false}'
        ]

        resp = gateway.execute_with_retry("sys", "user", required_keys=["action", "tension"])
        
        self.assertIsNotNone(resp)
        self.assertEqual(resp["action"], "jump")
        self.assertEqual(mock_generate.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        
        del os.environ["LLM_PROVIDER"]
        del os.environ["OLLAMA_API_KEY"]

    @patch.object(OllamaCloudProvider, 'generate')
    def test_gateway_validation_failure(self, mock_generate):
        os.environ["LLM_PROVIDER"] = "ollama"
        os.environ["OLLAMA_API_KEY"] = "mock_key"
        gateway = LLMGateway()

        # Missing 'tension' key repeatedly
        mock_generate.return_value = '{"action": "jump"}'

        resp = gateway.execute_with_retry("sys", "user", required_keys=["action", "tension"], max_retries=2)
        self.assertIsNone(resp) # Should exhaust retries
        self.assertEqual(mock_generate.call_count, 2)

        del os.environ["LLM_PROVIDER"]
        del os.environ["OLLAMA_API_KEY"]

if __name__ == '__main__':
    unittest.main()
