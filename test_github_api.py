import os
import urllib.request
import json
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("GITHUB_TOKEN")

# GitHub API-д хандах URL (Жишээ нь: таны өөрийн профайл эсвэл IncomeOS репозитори)
url = "https://api.github.com/repos/bi421/IncomeOS"

req = urllib.request.Request(
    url, 
    headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("✅ GitHub API амжилттай холбогдлоо!")
        print(f"Репозиторийн нэр: {data.get('name')}")
        print(f"Одоогийн одод (stars): {data.get('stargazers_count')}")
        print(f"Үндсэн хэл: {data.get('language')}")
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Алдаа: {e.code} - {e.reason}")
    print("Токен хүчингүй эсвэл эрх хүрэлцэхгүй байна.")
except Exception as e:
    print(f"❌ Алдаа гарлаа: {e}")
