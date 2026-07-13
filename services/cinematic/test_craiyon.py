import requests
url = "https://api.craiyon.com/v3"
data = {"prompt": "iron man"}
try:
    response = requests.post(url, json=data, timeout=10)
    print("Craiyon Status:", response.status_code)
except Exception as e:
    print("Craiyon Error:", e)
