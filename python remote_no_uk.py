import requests
from pathlib import Path

# ============================================================
# ТАНЫ УР ЧАДВАР
# ============================================================
MY_SKILLS = [
    "python", "fastapi", "postgresql", "docker", "redis",
    "testing", "git", "api", "sql", "data_engineering"
]

# ============================================================
# ХАСАХ ҮГС (Location)
# ============================================================
LOCATION_BLOCKED = [
    "uk", "united kingdom", "london", "england", "britain",
    "manchester", "birmingham", "edinburgh", "glasgow"
]

# ============================================================
# 1. АЖЛЫН БАЙР ТАТАХ
# ============================================================
def fetch_jobs():
    jobs = []
    try:
        r = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
        if r.status_code == 200:
            for item in r.json().get("data", []):
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", "Unknown"),
                    "url": item.get("url", ""),
                    "desc": item.get("description", ""),
                    "raw": str(item)
                })
    except:
        pass
    try:
        r = requests.get("https://remoteok.com/api", timeout=10)
        if r.status_code == 200:
            for item in r.json():
                if isinstance(item, dict) and item.get("position"):
                    jobs.append({
                        "title": item.get("position", ""),
                        "company": item.get("company", "Unknown"),
                        "url": item.get("url", ""),
                        "desc": item.get("description", ""),
                        "raw": str(item)
                    })
    except:
        pass
    return jobs

# ============================================================
# 2. ШҮҮХ (Remote + Location хасах)
# ============================================================
def filter_jobs(jobs):
    good = []
    for job in jobs:
        text = (job["title"] + " " + job["desc"] + " " + job["raw"]).lower()
        
        # 1. Location блок хийх (UK, London гэх мэт)
        blocked_location = False
        for word in LOCATION_BLOCKED:
            if word in text:
                blocked_location = True
                break
        if blocked_location:
            continue
        
        # 2. Remote эсэх шалгах
        remote_keywords = ["remote", "work from anywhere", "fully remote", "home office", "anywhere"]
        is_remote = any(kw in text for kw in remote_keywords)
        if not is_remote:
            continue
        
        # 3. Ур чадвар тохирч байгаа эсэх
        match = [s for s in MY_SKILLS if s in text]
        if len(match) >= 2:
            job["match"] = len(match)
            job["skills"] = match
            good.append(job)
    
    good.sort(key=lambda x: x["match"], reverse=True)
    return good

# ============================================================
# 3. ХАРУУЛАХ
# ============================================================
def main():
    print("\n" + "=" * 60)
    print("  🌍 REMOTE АЖЛУУД (UK-гүй)")
    print("=" * 60)
    
    print("📡 Ажил татаж байна...")
    jobs = fetch_jobs()
    print(f"📥 {len(jobs)} ажил олдлоо")
    
    good = filter_jobs(jobs)
    print(f"✅ {len(good)} ажил remote, UK-гүй, таны ур чадварт тохирч байна\n")
    
    if not good:
        print("😔 Remote тохирсон ажил олдсонгүй.")
        print("📌 Зөвлөмж: Upwork, Wellfound дээр 'Remote Python' гэж хайна уу.")
        return
    
    for i, job in enumerate(good[:10], 1):
        print(f"{i}. {job['title']}")
        print(f"   🏢 {job['company']}")
        print(f"   🔧 Тохирсон ур чадвар: {', '.join(job['skills'])}")
        print(f"   🌐 {job['url']}")
        print()
    
    # Хадгалах
    Path("data").mkdir(exist_ok=True)
    with open("data/remote_no_uk.txt", "w", encoding="utf-8") as f:
        for job in good:
            f.write(f"{job['title']} | {job['company']} | {job['url']}\n")
    print("💾 data/remote_no_uk.txt файлд хадгалагдсан.")
    print("📌 Энэ файлыг нээгээд URL-уудыг дарна уу.")

if __name__ == "__main__":
    main()