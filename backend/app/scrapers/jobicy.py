from app.scrapers.base import RawJob, ScrapeResult, default_headers


class JobicyScraper:
    name = "jobicy"
    url = "https://jobicy.com/api/v2/remote-jobs"

    async def scrape(self, client) -> ScrapeResult:
        result = ScrapeResult()
        try:
            resp = await client.get(self.url, headers=default_headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("jobs", []):
                job_type = item.get("jobType", "")
                if isinstance(job_type, list):
                    job_type = ", ".join(str(x) for x in job_type)
                salary = item.get("annualSalaryMin", "") or ""
                if isinstance(salary, (int, float)):
                    salary = str(salary)
                result.jobs.append(
                    RawJob(
                        external_id=str(item.get("id", item.get("url", ""))),
                        source=self.name,
                        title=item.get("jobTitle", "").strip(),
                        company=item.get("companyName", "Unknown").strip(),
                        location=item.get("jobGeo", "Remote"),
                        job_type=str(job_type),
                        salary=str(salary),
                        description=item.get("jobDescription", "") or item.get("jobExcerpt", "") or "",
                        url=item.get("url", ""),
                        posted_at=item.get("pubDate", ""),
                        search_label="Remote — Global",
                    )
                )
        except Exception as exc:
            result.errors.append(f"{self.name}: {exc}")
        return result
