from app.scrapers.base import RawJob, ScrapeResult, default_headers


class RemotiveScraper:
    name = "remotive"
    url = "https://remotive.com/api/remote-jobs"

    async def scrape(self, client) -> ScrapeResult:
        result = ScrapeResult()
        try:
            resp = await client.get(self.url, headers=default_headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("jobs", []):
                result.jobs.append(
                    RawJob(
                        external_id=str(item.get("id", item.get("url", ""))),
                        source=self.name,
                        title=item.get("title", "").strip(),
                        company=item.get("company_name", "Unknown").strip(),
                        location=item.get("candidate_required_location", "Remote"),
                        job_type=item.get("job_type", ""),
                        salary=item.get("salary", "") or "",
                        description=item.get("description", "") or "",
                        url=item.get("url", ""),
                        posted_at=item.get("publication_date", ""),
                        search_label="Remote — Global",
                    )
                )
        except Exception as exc:
            result.errors.append(f"{self.name}: {exc}")
        return result
