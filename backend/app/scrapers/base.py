from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.config import settings
from app.skills import extract_skills, skills_to_string


@dataclass
class RawJob:
    external_id: str
    source: str
    title: str
    company: str = "Unknown"
    location: str = ""
    job_type: str = ""
    salary: str = ""
    description: str = ""
    url: str = ""
    posted_at: str = ""
    search_label: str = ""


@dataclass
class ScrapeResult:
    jobs: list[RawJob] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class Scraper(Protocol):
    name: str

    async def scrape(self, client: httpx.AsyncClient) -> ScrapeResult: ...


def enrich_job(job: RawJob) -> RawJob:
    text = f"{job.title} {job.description}"
    job_skills = extract_skills(text)
    if job_skills:
        object.__setattr__(job, "description", job.description)  # noqa: B018
    return job


def with_skills(job: RawJob) -> tuple[RawJob, str]:
    skills = extract_skills(f"{job.title} {job.description} {job.search_label}")
    return job, skills_to_string(skills)


def default_headers() -> dict[str, str]:
    return {"User-Agent": settings.user_agent, "Accept-Language": "en-US,en;q=0.9"}
