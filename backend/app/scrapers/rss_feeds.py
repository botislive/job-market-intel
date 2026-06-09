import hashlib

import feedparser

from app.scrapers.base import RawJob, ScrapeResult, default_headers

RSS_SOURCES = [
    {
        "name": "weworkremotely",
        "url": "https://weworkremotely.com/remote-jobs.rss",
        "label": "Remote — WWR",
    },
    {
        "name": "weworkremotely_dev",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "label": "Remote — WWR Dev",
    },
    {
        "name": "himalayas",
        "url": "https://himalayas.app/jobs/rss",
        "label": "Remote — Himalayas",
    },
    {
        "name": "jobicy_rss",
        "url": "https://jobicy.com/?feed=job_feed",
        "label": "Remote — Jobicy RSS",
    },
]


def _parse_feed(content: str, source_name: str, label: str) -> list[RawJob]:
    feed = feedparser.parse(content)
    jobs: list[RawJob] = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        if not title or not link:
            continue
        external_id = hashlib.md5(link.encode()).hexdigest()
        company = "Unknown"
        if " — " in title:
            parts = title.rsplit(" — ", 1)
            if len(parts) == 2:
                title, company = parts[0].strip(), parts[1].strip()
        description = entry.get("summary", "") or entry.get("description", "") or ""
        location = "Remote"
        if hasattr(entry, "tags"):
            for tag in entry.tags:
                if tag.get("term"):
                    location = tag["term"]
                    break
        jobs.append(
            RawJob(
                external_id=external_id,
                source=source_name,
                title=title,
                company=company,
                location=location,
                description=description,
                url=link,
                posted_at=entry.get("published", "") or entry.get("updated", ""),
                search_label=label,
            )
        )
    return jobs


class RSSFeedScraper:
    name = "rss_feeds"

    async def scrape(self, client) -> ScrapeResult:
        result = ScrapeResult()
        for source in RSS_SOURCES:
            try:
                resp = await client.get(
                    source["url"],
                    headers={
                        **default_headers(),
                        "Accept": "application/rss+xml, application/xml, text/xml, */*",
                        "Referer": source["url"],
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                jobs = _parse_feed(resp.text, source["name"], source["label"])
                result.jobs.extend(jobs)
            except Exception as exc:
                result.errors.append(f"{source['name']}: {exc}")
        return result
