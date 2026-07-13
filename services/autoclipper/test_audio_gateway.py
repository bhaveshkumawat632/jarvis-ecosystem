import unittest
from unittest.mock import patch, Mock, mock_open
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.audio_gateway import AudioGateway, OpenAITTSProvider
import requests

class TestAudioGateway(unittest.TestCase):
    @patch('memory.audio_gateway.os.path.getsize')
    @patch('builtins.open', new_callable=mock_open)
    @patch('memory.audio_gateway.requests.post')
    def test_provider_success(self, mock_post, mock_file, mock_getsize):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.iter_content.return_value = [b"dummy_audio_bytes"]
        mock_post.return_value = mock_resp
        
        mock_getsize.return_value = 5000 # Pretend file is 5KB
        
        provider = OpenAITTSProvider("mock-key")
        res = provider.generate_tts("Hello", "alloy", "out.wav")
        self.assertTrue(res)

    @patch('memory.audio_gateway.requests.post')
    def test_provider_rate_limit(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 429
        mock_post.return_value = mock_resp

        provider = OpenAITTSProvider("mock-key")
        with self.assertRaises(Exception) as context:
            provider.generate_tts("Hello", "alloy", "out.wav")
        self.assertTrue("RateLimitExceeded" in str(context.exception))

    @patch('memory.audio_gateway.time.sleep')
    @patch.object(OpenAITTSProvider, 'generate_tts')
    def test_gateway_retry_logic(self, mock_generate, mock_sleep):
        os.environ["AUDIO_PROVIDER"] = "openai"
        gateway = AudioGateway()

        mock_generate.side_effect = [
            Exception("RateLimitExceeded"),
            Exception("RateLimitExceeded"),
            True
        ]

        resp = gateway.generate_with_retry("Hello", "alloy", "out.wav")
        
        self.assertEqual(resp, "out.wav")
        self.assertEqual(mock_generate.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        
        del os.environ["AUDIO_PROVIDER"]

if __name__ == '__main__':
    unittest.main()
