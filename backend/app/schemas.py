from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: int
    external_id: str
    source: str
    title: str
    company: str
    location: str
    job_type: str
    salary: str
    description: str
    skills: str
    url: str
    posted_at: str
    scraped_at: datetime
    search_label: str

    model_config = {"from_attributes": True}


class JobsResponse(BaseModel):
    total: int
    jobs: list[JobOut]


class SourceCount(BaseModel):
    source: str
    count: int


class CompanyCount(BaseModel):
    company: str
    count: int


class Fortune100Company(BaseModel):
    rank: int
    name: str
    slug: str
    country: str
    career_url: str
    job_count: int = 0


class SkillCount(BaseModel):
    skill: str
    count: int


class StatsResponse(BaseModel):
    total_jobs: int
    total_companies: int
    total_sources: int
    last_scrape: datetime | None
    by_source: list[SourceCount]
    top_companies: list[CompanyCount]
    top_skills: list[SkillCount]
    recent_jobs: list[JobOut]


class ScrapeResponse(BaseModel):
    status: str
    jobs_added: int
    jobs_updated: int
    duration_seconds: float
    by_source: list[SourceCount]
    errors: list[str]
