import asyncio
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.config import settings
from app.scrapers.base import RawJob, ScrapeResult, default_headers

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"


def _extract_job_id(url: str) -> str | None:
    match = re.search(r"jobs/view/[^/]+-(\d+)", url)
    return match.group(1) if match else None


def _parse_search_cards(html: str, label: str) -> list[RawJob]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[RawJob] = []
    for card in soup.select("div.base-card, li div.base-search-card"):
        link = card.select_one("a.base-card__full-link, a[class*='full-link']")
        if not link or not link.get("href"):
            continue
        href = link["href"].split("?")[0]
        job_id = _extract_job_id(href)
        if not job_id:
            continue
        title_el = card.select_one("[class*='title'], h3")
        company_el = card.select_one("[class*='subtitle'], h4")
        location_el = card.select_one("[class*='location'], span[class*='location']")
        time_el = card.select_one("time, [class*='listdate']")
        title = title_el.get_text(strip=True) if title_el else "Untitled"
        company = company_el.get_text(strip=True) if company_el else "Unknown"
        location = location_el.get_text(strip=True) if location_el else ""
        posted = time_el.get("datetime", "") if time_el and time_el.get("datetime") else (
            time_el.get_text(strip=True) if time_el else ""
        )
        jobs.append(
            RawJob(
                external_id=job_id,
                source="linkedin",
                title=title,
                company=company,
                location=location,
                url=urljoin("https://www.linkedin.com", href),
                posted_at=posted,
                search_label=label,
            )
        )
    return jobs


def _parse_detail_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    desc_el = soup.select_one(
        "div.show-more-less-html__markup, "
        "div.description__text, "
        "[class*='description'] section div"
    )
    criteria = soup.select("[class*='job-criteria'] li, .description__job-criteria-item")
    extra = " | ".join(c.get_text(" ", strip=True) for c in criteria[:6])
    description = ""
    if desc_el:
        description = desc_el.get_text("\n", strip=True)
    if extra:
        description = f"{description}\n{extra}".strip()
    job_type = ""
    for item in criteria:
        text = item.get_text(" ", strip=True)
        if any(k in text.lower() for k in ("full-time", "contract", "part-time", "temporary")):
            job_type = text
            break
    return description[:8000], job_type


class LinkedInGuestScraper:
    name = "linkedin"

    async def scrape(self, client) -> ScrapeResult:
        result = ScrapeResult()
        seen_ids: set[str] = set()

        for search in settings.linkedin_searches:
            label = search.get("label", search["keywords"])
            for page in range(settings.linkedin_max_pages):
                params = {
                    "keywords": search["keywords"],
                    "location": search["location"],
                    "start": page * 25,
                    "f_TPR": "r604800",
                }
                for key in ("f_WT", "f_JT", "f_E"):
                    if key in search:
                        params[key] = search[key]
                try:
                    resp = await client.get(
                        SEARCH_URL,
                        params=params,
                        headers=default_headers(),
                        timeout=30,
                    )
                    resp.raise_for_status()
                    page_jobs = _parse_search_cards(resp.text, label)
                    if not page_jobs:
                        break
                    for job in page_jobs:
                        if job.external_id not in seen_ids:
                            seen_ids.add(job.external_id)
                            result.jobs.append(job)
                    await asyncio.sleep(settings.request_delay_seconds)
                except Exception as exc:
                    result.errors.append(f"linkedin search '{label}' page {page}: {exc}")
                    break

        for job in result.jobs[:40]:
            try:
                resp = await client.get(
                    DETAIL_URL.format(job_id=job.external_id),
                    headers=default_headers(),
                    timeout=30,
                )
                if resp.status_code == 200:
                    desc, job_type = _parse_detail_html(resp.text)
                    job.description = desc
                    job.job_type = job_type
                await asyncio.sleep(settings.request_delay_seconds)
            except Exception as exc:
                result.errors.append(f"linkedin detail {job.external_id}: {exc}")

        return result
