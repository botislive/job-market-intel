from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, ScrapeRun
from app.schemas import CompanyCount, JobOut, SkillCount, SourceCount, StatsResponse

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    total_companies = db.query(func.count(func.distinct(Job.company))).scalar() or 0
    total_sources = db.query(func.count(func.distinct(Job.source))).scalar() or 0

    by_source_rows = (
        db.query(Job.source, func.count(Job.id))
        .group_by(Job.source)
        .order_by(desc(func.count(Job.id)))
        .all()
    )
    by_source = [SourceCount(source=row[0], count=row[1]) for row in by_source_rows]

    top_companies_rows = (
        db.query(Job.company, func.count(Job.id))
        .filter(Job.company != "Unknown")
        .group_by(Job.company)
        .order_by(desc(func.count(Job.id)))
        .limit(12)
        .all()
    )
    top_companies = [CompanyCount(company=row[0], count=row[1]) for row in top_companies_rows]

    skill_counter: Counter[str] = Counter()
    for (skills_str,) in db.query(Job.skills).filter(Job.skills != "").all():
        for skill in skills_str.split(", "):
            if skill.strip():
                skill_counter[skill.strip()] += 1
    top_skills = [
        SkillCount(skill=k, count=v) for k, v in skill_counter.most_common(15)
    ]

    recent = db.query(Job).order_by(desc(Job.scraped_at)).limit(10).all()
    last_run = db.query(ScrapeRun).order_by(desc(ScrapeRun.started_at)).first()
    last_scrape = last_run.finished_at if last_run and last_run.finished_at else None

    return StatsResponse(
        total_jobs=total_jobs,
        total_companies=total_companies,
        total_sources=total_sources,
        last_scrape=last_scrape,
        by_source=by_source,
        top_companies=top_companies,
        top_skills=top_skills,
        recent_jobs=[JobOut.model_validate(j) for j in recent],
    )
