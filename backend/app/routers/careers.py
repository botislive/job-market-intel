from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.careers_data import load_fortune100_companies
from app.database import get_db
from app.models import Job
from app.schemas import Fortune100Company

router = APIRouter(prefix="/api/careers", tags=["careers"])


@router.get("/companies", response_model=list[Fortune100Company])
def list_fortune100_companies(db: Session = Depends(get_db)):
    counts = dict(
        db.query(Job.company, func.count(Job.id))
        .filter(Job.source == "careers")
        .group_by(Job.company)
        .all()
    )
    return [
        Fortune100Company(
            rank=c["rank"],
            name=c["name"],
            slug=c["slug"],
            country=c["country"],
            career_url=c["career_url"],
            job_count=counts.get(c["name"], 0),
        )
        for c in load_fortune100_companies()
    ]
