import unittest
from unittest.mock import patch, Mock
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.video_gateway import VideoGateway, LumaVideoProvider
import requests

class TestVideoGateway(unittest.TestCase):
    @patch('memory.video_gateway.requests.post')
    def test_provider_submit_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "12345"}
        mock_post.return_value = mock_resp
        
        provider = LumaVideoProvider("mock-key")
        res = provider.submit_job("Hello")
        self.assertEqual(res, "12345")

    @patch('memory.video_gateway.requests.get')
    def test_provider_polling(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"state": "completed", "assets": {"video": "http://dl"}}
        mock_get.return_value = mock_resp

        provider = LumaVideoProvider("mock-key")
        res = provider.check_status("12345")
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["url"], "http://dl")

if __name__ == '__main__':
    unittest.main()
