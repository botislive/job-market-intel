import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.scrapers.base import RawJob, ScrapeResult, default_headers

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "fortune100_careers.json"
MAX_JOBS_PER_COMPANY = 75


def _load_companies() -> list[dict]:
    with DATA_FILE.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload["companies"]


def _label(company: dict) -> str:
    return f"Fortune 100 — {company['name']}"


def _job(
    company: dict,
    external_id: str,
    title: str,
    *,
    location: str = "",
    job_type: str = "",
    salary: str = "",
    description: str = "",
    url: str = "",
    posted_at: str = "",
) -> RawJob:
    return RawJob(
        external_id=f"{company['slug']}:{external_id}",
        source="careers",
        title=title.strip(),
        company=company["name"],
        location=location,
        job_type=job_type,
        salary=salary,
        description=description,
        url=url or company.get("career_url", ""),
        posted_at=posted_at,
        search_label=_label(company),
    )


async def _fetch_workday(client, company: dict, ats: dict) -> list[RawJob]:
    host, tenant, site = ats["host"], ats["tenant"], ats["site"]
    api = f"https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    page_url = f"https://{host}.myworkdayjobs.com/{site}"
    jobs: list[RawJob] = []
    offset = 0
    page_size = 20
    while len(jobs) < MAX_JOBS_PER_COMPANY:
        resp = await client.post(
            api,
            json={"appliedFacets": {}, "limit": page_size, "offset": offset, "searchText": ""},
            headers={**default_headers(), "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        postings = data.get("jobPostings", [])
        if not postings:
            break
        for item in postings:
            path = item.get("externalPath", "")
            job_url = f"{page_url}{path}" if path else page_url
            jobs.append(
                _job(
                    company,
                    path or item.get("title", ""),
                    item.get("title", "Untitled"),
                    location=item.get("locationsText", ""),
                    url=job_url,
                    posted_at=item.get("postedOn", ""),
                )
            )
            if len(jobs) >= MAX_JOBS_PER_COMPANY:
                break
        offset += page_size
        if offset >= data.get("total", 0):
            break
    return jobs


async def _fetch_amazon(client, company: dict) -> list[RawJob]:
    jobs: list[RawJob] = []
    offset = 0
    while len(jobs) < MAX_JOBS_PER_COMPANY:
        resp = await client.get(
            "https://www.amazon.jobs/en/search.json",
            params={"offset": offset, "result_limit": 20},
            headers=default_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("jobs", [])
        if not batch:
            break
        for item in batch:
            job_path = item.get("job_path", "")
            job_id = str(item.get("id_icims") or item.get("id", ""))
            if job_path:
                job_url = (
                    job_path
                    if job_path.startswith("http")
                    else f"https://www.amazon.jobs{job_path}"
                )
            elif job_id:
                job_url = f"https://www.amazon.jobs/en/jobs/{job_id}"
            else:
                job_url = company["career_url"]
            city = item.get("city", "")
            country = item.get("country_code", "")
            location = ", ".join(p for p in (city, country) if p)
            jobs.append(
                _job(
                    company,
                    job_id,
                    item.get("title", "Untitled"),
                    location=location,
                    description=(item.get("description", "") or "")[:4000],
                    url=job_url,
                    posted_at=item.get("posted_date", ""),
                    job_type=item.get("job_category", ""),
                )
            )
            if len(jobs) >= MAX_JOBS_PER_COMPANY:
                break
        offset += len(batch)
        if offset >= min(data.get("hits", 0), MAX_JOBS_PER_COMPANY * 4):
            break
    return jobs


async def _fetch_microsoft(client, company: dict, ats: dict) -> list[RawJob]:
    domain = ats.get("domain", "microsoft.com")
    jobs: list[RawJob] = []
    start = 0
    page_size = 20
    while len(jobs) < MAX_JOBS_PER_COMPANY:
        resp = await client.get(
            "https://apply.careers.microsoft.com/api/pcsx/search",
            params={
                "domain": domain,
                "query": "",
                "location": "",
                "start": start,
                "sortby": 0,
            },
            headers=default_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        positions = data.get("positions", [])
        if not positions:
            break
        for item in positions:
            job_id = str(item.get("id", item.get("displayJobId", "")))
            locations = item.get("locations") or item.get("standardizedLocations") or []
            location = locations[0] if locations else ""
            posted = ""
            if item.get("postedTs"):
                try:
                    posted = datetime.utcfromtimestamp(item["postedTs"]).isoformat()
                except (TypeError, ValueError, OSError):
                    posted = str(item["postedTs"])
            position_url = item.get("positionUrl", "")
            if position_url.startswith("http"):
                job_url = position_url
            elif position_url:
                job_url = f"https://apply.careers.microsoft.com{position_url}"
            else:
                job_url = company["career_url"]
            jobs.append(
                _job(
                    company,
                    job_id,
                    item.get("name", "Untitled"),
                    location=location,
                    url=job_url,
                    posted_at=posted,
                    job_type=item.get("department", ""),
                )
            )
            if len(jobs) >= MAX_JOBS_PER_COMPANY:
                break
        start += page_size
        if start >= data.get("count", 0):
            break
    return jobs


async def _fetch_smartrecruiters(client, company: dict, ats: dict) -> list[RawJob]:
    slug = ats["slug"]
    jobs: list[RawJob] = []
    offset = 0
    while len(jobs) < MAX_JOBS_PER_COMPANY:
        resp = await client.get(
            f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
            params={"offset": offset, "limit": 20},
            headers=default_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("content", [])
        if not batch:
            break
        for item in batch:
            loc = item.get("location", {}) or {}
            location_parts = [loc.get("city"), loc.get("region"), loc.get("country")]
            location = ", ".join(p for p in location_parts if p)
            jobs.append(
                _job(
                    company,
                    str(item.get("id", "")),
                    item.get("name", "Untitled"),
                    location=location,
                    description=(item.get("jobAd", {}) or {}).get("sections", {}).get("jobDescription", {}).get("text", "")[:4000],
                    url=item.get("ref", "") or f"https://careers.smartrecruiters.com/{slug}",
                    posted_at=item.get("releasedDate", ""),
                    job_type=item.get("typeOfEmployment", {}).get("label", "") if isinstance(item.get("typeOfEmployment"), dict) else "",
                )
            )
            if len(jobs) >= MAX_JOBS_PER_COMPANY:
                break
        offset += len(batch)
        if offset >= data.get("totalFound", 0):
            break
    return jobs


async def _fetch_greenhouse(client, company: dict, ats: dict) -> list[RawJob]:
    board = ats["board"]
    resp = await client.get(
        f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs",
        params={"content": "true"},
        headers=default_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    jobs: list[RawJob] = []
    for item in resp.json().get("jobs", [])[:MAX_JOBS_PER_COMPANY]:
        jobs.append(
            _job(
                company,
                str(item.get("id", "")),
                item.get("title", "Untitled"),
                location=item.get("location", {}).get("name", "") if isinstance(item.get("location"), dict) else str(item.get("location", "")),
                description=(item.get("content", "") or "")[:4000],
                url=item.get("absolute_url", company["career_url"]),
                posted_at=item.get("updated_at", ""),
            )
        )
    return jobs


async def _fetch_lever(client, company: dict, ats: dict) -> list[RawJob]:
    slug = ats["slug"]
    resp = await client.get(
        f"https://api.lever.co/v0/postings/{slug}",
        params={"mode": "json"},
        headers=default_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    jobs: list[RawJob] = []
    for item in resp.json()[:MAX_JOBS_PER_COMPANY]:
        location = item.get("categories", {}).get("location", "")
        jobs.append(
            _job(
                company,
                str(item.get("id", "")),
                item.get("text", "Untitled"),
                location=location,
                description=(item.get("descriptionPlain", "") or "")[:4000],
                url=item.get("hostedUrl", company["career_url"]),
                posted_at=str(item.get("createdAt", "")),
                job_type=item.get("categories", {}).get("commitment", ""),
            )
        )
    return jobs


async def _fetch_ashby(client, company: dict, ats: dict) -> list[RawJob]:
    slug = ats["slug"]
    resp = await client.get(
        f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
        headers=default_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    jobs: list[RawJob] = []
    for item in resp.json().get("jobs", [])[:MAX_JOBS_PER_COMPANY]:
        location = item.get("location", "")
        if isinstance(location, dict):
            location = location.get("name", "")
        jobs.append(
            _job(
                company,
                str(item.get("id", "")),
                item.get("title", "Untitled"),
                location=location,
                description=(item.get("descriptionPlain", "") or item.get("description", "") or "")[:4000],
                url=item.get("jobUrl", company["career_url"]),
                posted_at=item.get("publishedAt", ""),
                job_type=item.get("employmentType", ""),
            )
        )
    return jobs


_FETCHERS = {
    "workday": _fetch_workday,
    "amazon": _fetch_amazon,
    "microsoft": _fetch_microsoft,
    "smartrecruiters": _fetch_smartrecruiters,
    "greenhouse": _fetch_greenhouse,
    "lever": _fetch_lever,
    "ashby": _fetch_ashby,
}


class CareerPagesScraper:
    name = "careers"

    async def scrape(self, client) -> ScrapeResult:
        result = ScrapeResult()
        companies = _load_companies()
        delay = settings.careers_request_delay_seconds

        for company in companies:
            ats = company.get("ats")
            if not ats:
                continue
            ats_type = ats.get("type")
            fetcher = _FETCHERS.get(ats_type)
            if not fetcher:
                result.errors.append(f"careers/{company['slug']}: unsupported ATS type {ats_type}")
                continue
            try:
                if ats_type == "amazon":
                    jobs = await fetcher(client, company)
                else:
                    jobs = await fetcher(client, company, ats)
                result.jobs.extend(jobs)
            except Exception as exc:
                result.errors.append(f"careers/{company['slug']}: {exc}")
            await asyncio.sleep(delay)

        return result
