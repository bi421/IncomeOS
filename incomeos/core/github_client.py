import os
import urllib.request
import json
from dotenv import load_dotenv

# .env файлыг ачаалах
load_dotenv()

class GitHubClient:
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN олдсонгүй. .env файлыг шалгана уу.")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "IncomeOS-Analyzer"
        }

    def get_repo_info(self, owner: str, repo: str) -> dict:
        """Репозиторийн үндсэн мэдээллийг татах"""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        return self._make_request(url)

    def get_repo_contents(self, owner: str, repo: str, path: str = "") -> list:
        """Репозиторийн доторх файлуудын жагсаалтыг татах (Skill Evidence цуглуулахад хэрэгтэй)"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        return self._make_request(url)

    def _make_request(self, url: str) -> dict | list:
        """API дуудлагыг гүйцэтгэх үндсэн функц"""
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            raise Exception(f"GitHub API алдаа: {e.code} - {e.reason}")
        except Exception as e:
            raise Exception(f"Холболтын алдаа: {e}")

# --- Жишээ хэрэглээ ---
if __name__ == "__main__":
    client = GitHubClient()
    
    # IncomeOS репозиторийн мэдээллийг татах
    info = client.get_repo_info("bi421", "IncomeOS")
    print(f"✅ Репозитори: {info['name']}")
    print(f"✅ Үндсэн хэл: {info['language']}")
    print(f"✅ Хэмжээ: {info['size']} KB")
