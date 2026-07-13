import os
import time
import jwt
import requests

KLING_ACCESS_KEY = "KLING_ACCESS_KEY_HERE"
KLING_SECRET_KEY = "KLING_SECRET_KEY_HERE"

def generate_kling_token():
    headers = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": KLING_ACCESS_KEY,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5
    }
    return jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256", headers=headers)

token = generate_kling_token()
print("Token:", token)

url = "https://api.klingai.com/v1/videos/text2video"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "model": "kling-v1",
    "prompt": "Cinematic 4K film, shallow depth of field, golden hour lighting. A submarine in the deep ocean.",
}
response = requests.post(url, json=payload, headers=headers)
print("Submit Response:", response.status_code, response.text)
