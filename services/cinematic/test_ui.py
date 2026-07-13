from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import unittest

class TestJarvisUI(unittest.TestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Try to initialize webdriver, will fail if chrome is not installed locally
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            self.skipTest(f"Skipping UI test because webdriver could not be initialized: {e}")

    def test_homepage_title(self):
        # We assume the Flask app runs locally on port 5000
        try:
            self.driver.get("http://127.0.0.1:5000")
            time.sleep(2)
            # Just checking if the page loads and has a title or body
            body = self.driver.find_element(By.TAG_NAME, "body")
            self.assertIsNotNone(body, "Body should be present on the homepage")
        except Exception as e:
            self.fail(f"Could not load the page: {e}")

    def tearDown(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()

if __name__ == "__main__":
    unittest.main()
