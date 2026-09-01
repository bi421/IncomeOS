from dataclasses import dataclass
from typing import Dict, List

@dataclass
class OpportunityArchetype:
    title: str
    description: str
    required_skills: Dict[str, int]
    next_actions: List[str]

class OpportunityMatcher:
    def __init__(self):
        self.archetypes = [
            OpportunityArchetype(
                title="Modern Full-Stack Web Developer (TypeScript/React)",
                description="TypeScript, React/Next.js, Prisma дээр суурилсан орчин үеийн веб автоматжуулалтын шийдэл.",
                required_skills={
                    "TypeScript": 30,
                    "React / Next.js": 5,
                    "Node.js": 3,
                    "Prisma / ORM": 1,
                    "Testing": 10
                },
                next_actions=[
                    "reelautofly төслийг портфолио болгон, Next.js + Prisma case study бичих",
                    "Vercel эсвэл Railway дээр deploy хийж, live demo бэлдэх",
                    "TypeScript + React чиглэлийн Remote/Freelance ажлын заруудыг хайх"
                ]
            ),
            OpportunityArchetype(
                title="Senior Python Backend Engineer",
                description="Өндөр ачаалалтай, тестлэгдсэн Python системүүд бүтээх.",
                required_skills={"Python": 500, "Testing": 100, "Docker": 5},
                next_actions=[
                    "Python/Docker багцтай Senior Backend ажлын заруудыг хайх",
                    "ResearchOS болон IncomeOS төслүүдээ портфолио болгон эмхэтгэх",
                    "System Design болон Testing архитектур дээр ярилцлагад бэлдэх"
                ]
            ),
            OpportunityArchetype(
                title="C++ / Systems Performance Developer",
                description="Өндөр гүйцэтгэл шаардсан C++ систем, алгоритм боловсруулах.",
                required_skills={"C++": 100, "CMake": 5, "Testing": 50},
                next_actions=[
                    "CMake болон C++ testing (GTest/pytest) туршлагаа тодотгох",
                    "High-frequency trading эсвэл data processing төслүүд рүү чиглэх",
                    "trader репозиторигийн гүйцэтгэлийн (performance) хэсгийг онцлох"
                ]
            ),
            OpportunityArchetype(
                title="Data Engineering & Automation Specialist",
                description="Өгөгдлийн pipeline, автоматжуулалт, ROI хяналтын систем.",
                required_skills={"Python": 200, "Data Engineering": 20, "Docker": 10},
                next_actions=[
                    "fb-planner-audit болон true-roas-complete төслүүдийг case study болгох",
                    "ETL pipeline, web scraping automation чиглэлийн freelance төсөл хайх",
                    "Docker контейнерчилэлтийн мэдлэгээ гүнзгийрүүлэх"
                ]
            ),
            OpportunityArchetype(
                title="Full-Stack Automation Builder",
                description="Эхнээс нь дуустал (End-to-end) автоматжуулалтын шийдэл (Python + Web).",
                required_skills={"Python": 300, "TypeScript": 20, "Testing": 50},
                next_actions=[
                    "Python backend + TypeScript frontend бүхий төслүүдэд чиглэх",
                    "End-to-end testing болон CI/CD pipeline тохируулах",
                    "reelautofly болон IncomeOS-ийг нэгтгэсэн automation demo бэлдэх"
                ]
            )
        ]

    def match_opportunities(self, profile: Dict[str, int]) -> List[Dict]:
        results = []
        
        for archetype in self.archetypes:
            matched_skills = []
            missing_skills = []
            total_score = 0
            max_possible_score = 0
            
            for skill, min_req in archetype.required_skills.items():
                max_possible_score += min_req
                actual_evidence = profile.get(skill, 0)
                
                if actual_evidence >= min_req:
                    matched_skills.append(f"{skill} ✅ ({actual_evidence})")
                    total_score += min_req
                elif actual_evidence > 0:
                    matched_skills.append(f"{skill} ⚠️ ({actual_evidence}/{min_req})")
                    total_score += actual_evidence
                else:
                    missing_skills.append(f"{skill} ❌ (0/{min_req})")
            
            match_percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
            
            results.append({
                "title": archetype.title,
                "description": archetype.description,
                "match_percentage": round(match_percentage, 1),
                "matched": matched_skills,
                "missing": missing_skills,
                "next_actions": archetype.next_actions
            })
        
        return sorted(results, key=lambda x: x["match_percentage"], reverse=True)
