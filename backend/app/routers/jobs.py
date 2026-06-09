from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.careers_data import fortune100_company_names
from app.database import get_db
from app.models import Job
from app.schemas import JobOut, JobsResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobsResponse)
def list_jobs(
    source: str | None = None,
    company: str | None = None,
    fortune100: bool = False,
    fortune100_company: str | None = None,
    skill: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if source:
        query = query.filter(Job.source == source)
    if fortune100_company:
        names = fortune100_company_names()
        if fortune100_company not in names:
            return JobsResponse(total=0, jobs=[])
        query = query.filter(Job.source == "careers", Job.company == fortune100_company)
    elif fortune100:
        query = query.filter(Job.source == "careers")
    elif company:
        query = query.filter(Job.company.ilike(f"%{company}%"))
    if skill:
        query = query.filter(Job.skills.ilike(f"%{skill}%"))
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Job.title.ilike(pattern),
                Job.company.ilike(pattern),
                Job.description.ilike(pattern),
                Job.location.ilike(pattern),
            )
        )
    total = query.count()
    jobs = query.order_by(desc(Job.scraped_at)).offset(offset).limit(limit).all()
    return JobsResponse(total=total, jobs=jobs)
