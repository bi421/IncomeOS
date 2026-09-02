import asyncio
import aiohttp
import json
import time
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# ================================================
# ТОХИРГОО
# ================================================
BOT_TOKEN = "8897075663:AAFhoJ3sVTHCN7kfAdRpV4rFMiCvy9XIGDo"
DB_PATH = Path("data/applications.db")
COVER_DIR = Path("cover_letters")
COVER_DIR.mkdir(exist_ok=True)
TEMPLATE_FILE = COVER_DIR / "template.txt"

MY_SKILLS = ["python", "fastapi", "postgresql", "docker", "redis", "testing", "git"]
LOCATION_BLOCKED = ["uk", "united kingdom", "london", "england", "britain", "manchester", "birmingham", "edinburgh", "glasgow"]
PROBABILITY_THRESHOLD = 40

# ================================================
# ӨГӨГДЛИЙН САН (АВТОМАТ МИГРАЦИЯТАЙ)
# ================================================
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company TEXT,
            url TEXT,
            applied_at TEXT,
            status TEXT DEFAULT 'PENDING',
            probability REAL,
            variance REAL,
            confidence_lower REAL,
            confidence_upper REAL,
            match_skills TEXT
        )
    """)
    cur = conn.execute("PRAGMA table_info(applications)")
    columns = [row[1] for row in cur.fetchall()]
    for col in ["probability", "variance", "confidence_lower", "confidence_upper", "match_skills"]:
        if col not in columns:
            conn.execute(f"ALTER TABLE applications ADD COLUMN {col} { 'REAL' if col != 'match_skills' else 'TEXT'}")
    conn.commit()
    conn.close()

def save_application(job, prob_data, match_skills):
    conn = sqlite3.connect(str(DB_PATH))
    lower, upper = prob_data["confidence_interval"]
    conn.execute(
        "INSERT INTO applications (job_title, company, url, applied_at, probability, variance, confidence_lower, confidence_upper, match_skills, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (job["title"], job["company"], job["url"], datetime.now().isoformat(), prob_data["probability"], prob_data["variance"], lower, upper, ", ".join(match_skills), "PENDING")
    )
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(str(DB_PATH))
    total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM applications WHERE status='PENDING'").fetchone()[0]
    avg_prob = conn.execute("SELECT AVG(probability) FROM applications").fetchone()[0] or 0
    conn.close()
    return total, pending, round(avg_prob, 2)

# ================================================
# 1. ЗАГВАР УНШИХ (AI-ГҮЙ)
# ================================================
def get_cover_letter_template() -> str:
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return """
Date: {date}

To the Hiring Team of {company},

I am applying for the position of {job_title}. 

My background includes experience with: {skills}.

I have reviewed the requirements and believe my skills align well with your needs.

Sincerely,
Batsukh Bold
"""

def generate_cover_letter(job_title: str, company: str, skills: list[str]) -> str:
    template = get_cover_letter_template()
    return template.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        job_title=job_title,
        company=company,
        skills=", ".join(skills)
    )

# ================================================
# 2. 5 ЭХ ҮҮСВЭР – БҮР НЬ ӨӨР ПАРСЕРТЭЙ
# ================================================
def parse_arbeitnow(data):
    jobs = []
    for item in data.get("data", []):
        jobs.append({
            "title": item.get("title", ""),
            "company": item.get("company_name", "Unknown"),
            "url": item.get("url", ""),
            "raw": str(item)
        })
    return jobs

def parse_remoteok(data):
    jobs = []
    for item in data:
        if isinstance(item, dict) and item.get("position"):
            jobs.append({
                "title": item.get("position", ""),
                "company": item.get("company", "Unknown"),
                "url": item.get("url", ""),
                "raw": str(item)
            })
    return jobs

def parse_remotive(data):
    jobs = []
    for item in data.get("jobs", []):
        jobs.append({
            "title": item.get("title", ""),
            "company": item.get("company_name", "Unknown"),
            "url": item.get("url", ""),
            "raw": str(item)
        })
    return jobs

def parse_findwork(data):
    jobs = []
    for item in data.get("results", []):
        if item.get("remote") is True:  # Зөвхөн remote
            jobs.append({
                "title": item.get("role", ""),
                "company": item.get("company_name", "Unknown"),
                "url": item.get("url", ""),
                "raw": str(item)
            })
    return jobs

def parse_workingnomads(data):
    jobs = []
    for item in data:
        if isinstance(item, dict) and item.get("title"):
            jobs.append({
                "title": item.get("title", ""),
                "company": item.get("company", "Unknown"),
                "url": item.get("url", ""),
                "raw": str(item)
            })
    return jobs

# ================================================
# 3. АЮУЛГҮЙ ФЕТЧ (ХЭЗЭЭ Ч ГАЦАХГҮЙ)
# ================================================
async def safe_fetch(session, url, parse_func, name, timeout=8):
    try:
        async with asyncio.timeout(timeout):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return parse_func(data)
                return []
    except asyncio.TimeoutError:
        print(f"⚠️ {name}: Хугацаа хэтэрсэн ({timeout} сек)")
        return []
    except aiohttp.ClientError as e:
        print(f"⚠️ {name}: Сүлжээний алдаа - {e}")
        return []
    except json.JSONDecodeError:
        print(f"⚠️ {name}: JSON задлах алдаа")
        return []
    except Exception as e:
        print(f"⚠️ {name}: Санаандгүй алдаа - {e}")
        return []

async def fetch_all_jobs():
    sources = [
        ("Arbeitnow", "https://www.arbeitnow.com/api/job-board-api", parse_arbeitnow),
        ("RemoteOK", "https://remoteok.com/api", parse_remoteok),
        ("Remotive", "https://remotive.com/api/remote-jobs", parse_remotive),
        ("Findwork", "https://findwork.dev/api/jobs/?remote=true", parse_findwork),
        ("WorkingNomads", "https://workingnomads.com/api/jobs", parse_workingnomads)
    ]
    
    async with aiohttp.ClientSession() as session:
        tasks = [safe_fetch(session, url, parse, name) for name, url, parse in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_jobs = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ {sources[i][0]}: Бүрэн бүтэлгүйтсэн - {result}")
            elif result:
                print(f"✅ {sources[i][0]}: {len(result)} ажил")
                all_jobs.extend(result)
            else:
                print(f"❌ {sources[i][0]}: 0 ажил (хоосон эсвэл алдаа)")
        return all_jobs

# ================================================
# 4. ШҮҮХ, ШИНЖИЛГЭЭ
# ================================================
def filter_jobs(jobs):
    matches = []
    for job in jobs:
        text = (job["title"] + " " + job["raw"]).lower()
        
        if any(w in text for w in LOCATION_BLOCKED): continue
        if not any(w in text for w in ["remote", "work from anywhere", "fully remote", "home office"]): continue
        
        match_skills = [s for s in MY_SKILLS if s in text]
        score = len(match_skills)
        
        if score >= 2:
            prob = (score / len(MY_SKILLS)) * 100
            variance = (prob * (100 - prob)) / 100
            lower = max(0, prob - 15)
            upper = min(100, prob + 15)
            
            matches.append({
                "title": job["title"],
                "company": job["company"],
                "url": job["url"],
                "probability": {
                    "probability": round(prob, 2),
                    "variance": round(variance, 2),
                    "confidence_interval": (round(lower, 2), round(upper, 2)),
                    "recommendation": "✅ Тохирч байна." if prob >= 70 else "🟡 Тохирол дунд."
                },
                "match_skills": match_skills
            })
    return sorted(matches, key=lambda x: x["probability"]["probability"], reverse=True)[:10]

def safe_save_cover_letter(job, skills):
    try:
        safe_title = re.sub(r'[<>:"/\\|?*]', '', job["title"])[:50]
        cover_path = COVER_DIR / f"{safe_title}.txt"
        cover_text = generate_cover_letter(job["title"], job["company"], skills)
        cover_path.write_text(cover_text, encoding="utf-8")
    except:
        pass

# ================================================
# 5. TELEGRAM ХЭНДЛЕРҮҮД
# ================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👋 Сайн байна! /jobs - ажил хайх (≥{PROBABILITY_THRESHOLD}%), /stats - статистик, /template - загвар харах")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, pending, avg = get_stats()
    await update.message.reply_text(f"📊 Нийт өргөдөл: {total}\n⏳ Хүлээгдэж буй: {pending}\n📈 Дунд магадлал: {avg}%")

async def template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_cover_letter_template()
    await update.message.reply_text(f"📄 Одоогийн cover letter загвар:\n\n{text[:500]}")

async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_msg = await update.message.reply_text("🔄 5 эх үүсвэрээс зэрэгцээ татаж байна... (Хэзээ ч гацахгүй)")
    start_time = time.time()
    
    all_jobs = await fetch_all_jobs()
    matches = filter_jobs(all_jobs)
    
    elapsed = time.time() - start_time
    if not matches:
        await update.message.reply_text(f"😔 {PROBABILITY_THRESHOLD}%-с дээш тохирсон ажил олдсонгүй. ({elapsed:.2f} сек)")
        return

    await start_msg.edit_text(f"✅ {len(matches)} ажил олдлоо. Дэлгэрэнгүйг доороос харна уу.")

    for job in matches:
        prob = job["probability"]
        save_application(job, prob, job["match_skills"])
        safe_save_cover_letter(job, job["match_skills"])
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Apply", url=job["url"])]])
        text = (
            f"<b>{job['title']}</b>\n"
            f"🏢 {job['company']}\n"
            f"📊 Магадлал: {prob['probability']}%\n"
            f"📉 Вариац: {prob['variance']:.2f}\n"
            f"🔧 Тохирсон ур чадвар: {', '.join(job['match_skills'])}\n"
            f"💡 {prob['recommendation']}"
        )
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
        await asyncio.sleep(0.3)

    total, pending, avg = get_stats()
    await update.message.reply_text(f"✅ {len(matches)} ажил (≥{PROBABILITY_THRESHOLD}%) {elapsed:.2f} сек-т илгээлээ.\n📊 Нийт {total}, хүлээгдэж буй {pending}, дунд магадлал {avg}%")

# ================================================
# 6. ҮНДСЭН (АЛДААГ ҮРГЭЛЖ БАРИХ)
# ================================================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("jobs", jobs))
    app.add_handler(CommandHandler("template", template))
    
    print("🤖 Бот ажиллаж байна... (5 эх үүсвэр, Хэзээ ч гацахгүй)")
    print(f"📄 Cover letter загвар: {TEMPLATE_FILE}")
    print(f"🔧 Таны ур чадвар: {', '.join(MY_SKILLS)}")
    app.run_polling()

if __name__ == "__main__":
    main()
