import urllib.request
import sys
url = "https://api.airforce/imagine2?prompt=iron+man"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        content = response.read()
        print("Success! Bytes:", len(content))
        with open("test.jpg", "wb") as f:
            f.write(content)
except Exception as e:
    print("Error:", e)
