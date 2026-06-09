import asyncio
from collections import Counter
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.models import Job, ScrapeRun
from app.scrapers.arbeitnow import ArbeitnowScraper
from app.scrapers.career_pages import CareerPagesScraper
from app.scrapers.jobicy import JobicyScraper
from app.scrapers.linkedin_guest import LinkedInGuestScraper
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.remotive import RemotiveScraper
from app.scrapers.rss_feeds import RSSFeedScraper
from app.skills import extract_skills, skills_to_string

SCRAPERS = [
    CareerPagesScraper(),
    RemotiveScraper(),
    RemoteOKScraper(),
    ArbeitnowScraper(),
    JobicyScraper(),
    RSSFeedScraper(),
    LinkedInGuestScraper(),
]


def _as_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _upsert_job(db: Session, raw, skills: str) -> tuple[bool, bool]:
    existing = (
        db.query(Job)
        .filter(Job.source == raw.source, Job.external_id == raw.external_id)
        .first()
    )
    if existing:
        existing.title = _as_str(raw.title)
        existing.company = _as_str(raw.company)
        existing.location = _as_str(raw.location)
        existing.job_type = _as_str(raw.job_type)
        existing.salary = _as_str(raw.salary)
        existing.description = _as_str(raw.description)
        existing.skills = skills
        existing.url = _as_str(raw.url)
        existing.posted_at = _as_str(raw.posted_at)
        existing.scraped_at = datetime.utcnow()
        existing.search_label = _as_str(raw.search_label)
        return False, True
    db.add(
        Job(
            external_id=_as_str(raw.external_id),
            source=_as_str(raw.source),
            title=_as_str(raw.title),
            company=_as_str(raw.company),
            location=_as_str(raw.location),
            job_type=_as_str(raw.job_type),
            salary=_as_str(raw.salary),
            description=_as_str(raw.description),
            skills=skills,
            url=_as_str(raw.url),
            posted_at=_as_str(raw.posted_at),
            search_label=_as_str(raw.search_label),
        )
    )
    return True, False


def _apply_scrape_result(
    db: Session,
    result,
    added: int,
    updated: int,
    source_counts: Counter[str],
) -> tuple[int, int]:
    seen_in_batch: set[tuple[str, str]] = set()
    for raw in result.jobs:
        key = (_as_str(raw.source), _as_str(raw.external_id))
        if key in seen_in_batch:
            continue
        seen_in_batch.add(key)
        skills = skills_to_string(
            extract_skills(f"{raw.title} {raw.description} {raw.search_label}")
        )
        is_added, is_updated = _upsert_job(db, raw, skills)
        if is_added:
            added += 1
        elif is_updated:
            updated += 1
        source_counts[raw.source] += 1
    db.commit()
    return added, updated


async def run_careers_scraper(db: Session) -> dict:
    started = datetime.utcnow()
    added = 0
    updated = 0
    all_errors: list[str] = []
    source_counts: Counter[str] = Counter()

    async with httpx.AsyncClient(follow_redirects=True) as client:
        result = await CareerPagesScraper().scrape(client)
        all_errors.extend(result.errors)
        added, updated = _apply_scrape_result(db, result, added, updated, source_counts)

    finished = datetime.utcnow()
    return {
        "status": "completed" if not all_errors else "completed_with_errors",
        "jobs_added": added,
        "jobs_updated": updated,
        "duration_seconds": (finished - started).total_seconds(),
        "by_source": [{"source": k, "count": v} for k, v in source_counts.most_common()],
        "errors": all_errors,
    }


async def run_all_scrapers(db: Session) -> dict:
    run = ScrapeRun(status="running")
    db.add(run)
    db.commit()

    started = datetime.utcnow()
    added = 0
    updated = 0
    all_errors: list[str] = []
    source_counts: Counter[str] = Counter()

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for scraper in SCRAPERS:
            result = await scraper.scrape(client)
            all_errors.extend(result.errors)
            added, updated = _apply_scrape_result(
                db, result, added, updated, source_counts
            )
            await asyncio.sleep(0.5)

    finished = datetime.utcnow()
    run.finished_at = finished
    run.status = "completed" if not all_errors else "completed_with_errors"
    run.jobs_added = added
    run.jobs_updated = updated
    run.errors = "\n".join(all_errors)
    db.commit()

    return {
        "status": run.status,
        "jobs_added": added,
        "jobs_updated": updated,
        "duration_seconds": (finished - started).total_seconds(),
        "by_source": [{"source": k, "count": v} for k, v in source_counts.most_common()],
        "errors": all_errors,
    }
