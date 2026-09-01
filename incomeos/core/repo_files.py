import os
from dotenv import load_dotenv
from .github_client import GitHubClient

load_dotenv()

class RepoFileFetcher:
    def __init__(self):
        self.client = GitHubClient()
    
    def fetch_all_files(self, owner: str, repo: str, path: str = "") -> list[dict]:
        """Репозиторийн бүх файлыг рекурсивээр татах"""
        files = []
        try:
            contents = self.client.get_repo_contents(owner, repo, path)
            if isinstance(contents, list):
                for item in contents:
                    if item["type"] == "file":
                        files.append({
                            "path": item["path"],
                            "name": item["name"],
                            "size": item.get("size", 0),
                            "extension": os.path.splitext(item["name"])[1].lower()
                        })
                    elif item["type"] == "dir":
                        # Рекурсив дуудлага (гүнзгийрүүлэх)
                        sub_files = self.fetch_all_files(owner, repo, item["path"])
                        files.extend(sub_files)
        except Exception as e:
            print(f"⚠️ Алдаа {path}: {e}")
        return files

# --- Жишээ хэрэглээ ---
if __name__ == "__main__":
    fetcher = RepoFileFetcher()
    files = fetcher.fetch_all_files("bi421", "IncomeOS")
    
    print(f"\n✅ Нийт файл: {len(files)}")
    print("\nЭхний 10 файл:")
    for f in files[:10]:
        print(f"  - {f['path']} ({f['size']} bytes)")
