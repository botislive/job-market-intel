from app.scrapers.base import RawJob, ScrapeResult, default_headers


class ArbeitnowScraper:
    name = "arbeitnow"
    url = "https://www.arbeitnow.com/api/job-board-api"

    async def scrape(self, client) -> ScrapeResult:
        result = ScrapeResult()
        try:
            resp = await client.get(self.url, headers=default_headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("data", []):
                slug = item.get("slug", "")
                job_types = item.get("job_types") or []
                job_type = ""
                if job_types:
                    first = job_types[0]
                    job_type = first.get("name", "") if isinstance(first, dict) else str(first)
                result.jobs.append(
                    RawJob(
                        external_id=slug or str(item.get("url", "")),
                        source=self.name,
                        title=item.get("title", "").strip(),
                        company=item.get("company_name", "Unknown").strip(),
                        location=item.get("location", "") or "Europe / Remote",
                        job_type=job_type,
                        salary="",
                        description=item.get("description", "") or "",
                        url=item.get("url", ""),
                        posted_at=item.get("created_at", ""),
                        search_label="Europe / Remote",
                    )
                )
        except Exception as exc:
            result.errors.append(f"{self.name}: {exc}")
        return result
