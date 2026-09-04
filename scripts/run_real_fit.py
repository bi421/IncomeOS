from incomeos.skills.aggregator import build_master_profile
from incomeos.jobs.ingestion import run_pipeline # Remotive/Arbeitnow татдаг
from incomeos.jobs.requirements import extract_requirements
from incomeos.jobs.fit import evaluate_job_fit, CapabilityLevel, JobRequirement
from incomeos.jobs.models import JobRecord

# 1. Бодит GitHub evidence-ээс профайл бүтээх
master = build_master_profile('data/github_repos')
# master_skill_profile.json -> CapabilityLevel рүү хөрвүүлэх
def to_level(conf: float):
    if conf >= 0.9: return CapabilityLevel.A
    if conf >= 0.70: return CapabilityLevel.B
    return CapabilityLevel.UNKNOWN

real_profile = {
    "capabilities": [
        {"name": k, "skills": [k], "confidence": v["confidence"], "level": to_level(v["confidence"])}
        for k, v in master.items()
    ]
}

# 2. Бодит ажлын зар татах (275 биш, одоо татсан шинэ зар)
jobs: list[JobRecord] = run_pipeline(limit=50) # Remotive + Arbeitnow

# 3. Бодит холболт - requirements + fit
for job in jobs[:10]:
    reqs = extract_requirements(job.description) # requirements.py жинхэнэ гарааны цэг
    # reqs = (JobRequirement("Python", CapabilityLevel.B),...)

    fit = evaluate_job_fit(
        job_id=job.id,
        requirements=reqs,
        profile=real_profile
    )
    print(f"{job.title[:40]} | fit={fit.score:.2f} | {fit.reasons}")
    # reasons дотор яг ямар skill дутуу, alias таарсан эсэх гарна