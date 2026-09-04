import sys, pathlib, json
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from incomeos.jobs.fit import evaluate_job_fit, CapabilityLevel, JobRequirement
from incomeos.jobs.requirements import extract_requirements, SKILL_ALIASES

profile_path = ROOT / "data" / "profile" / "master_skill_profile.json"
with open(profile_path, encoding="utf-8") as f:
    raw = json.load(f)

skills_list = raw.get("skills", [])

def to_level(conf: float, verified: int = 0):
    if verified > 0:
        if conf >= 0.90: return CapabilityLevel.A
        if conf >= 0.70: return CapabilityLevel.B
    else:
        if conf >= 0.80: return CapabilityLevel.A
        if conf >= 0.60: return CapabilityLevel.B
    return CapabilityLevel.UNKNOWN

real_profile = {
    "capabilities": [
        {"name": s["name"], "skills": [s["name"]], "confidence": float(s["confidence"]), "level": to_level(float(s["confidence"]), s.get("verified_evidence_count",0)), "verified_count": s.get("verified_evidence_count",0)}
        for s in skills_list
    ]
}

print("=== REAL PROFILE (HONEST) ===")
for c in real_profile["capabilities"]:
    print(f"{c['name']:20s} conf={c['confidence']:.2f} -> {c['level'].value}")

tests = [
    "Required Skills: Python, Testing, Docker. Preferred: AWS",
    "Required Skills & Experiences: C++ and CMake build system for quant trading. Nice to have: Linux",
    "Required: Data Engineering, Data Pipeline, Python, SQL. Preferred: Pandas, Docker"
]

for desc in tests:
    required, preferred = extract_requirements(description=desc, available_skills=tuple(SKILL_ALIASES.keys()))
    req_objs = tuple(JobRequirement(name, CapabilityLevel.B) for name in required)
    fit = evaluate_job_fit(job_id="real", requirements=req_objs, profile=real_profile)
    # Энд fit_score гэж зөв дуудна
    print(f"\n--- DESC: {desc}")
    print(f"  required={required}")
    print(f"  FIT SCORE = {fit.fit_score:.3f}")
    print(f"  matched={fit.matched_requirements}")
    print(f"  missing={fit.missing_requirements}")
    print(f"  reasons={fit.reasons}")