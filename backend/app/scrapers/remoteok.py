from app.scrapers.base import RawJob, ScrapeResult, default_headers


class RemoteOKScraper:
    name = "remoteok"
    url = "https://remoteok.com/api"

    async def scrape(self, client) -> ScrapeResult:
        result = ScrapeResult()
        try:
            resp = await client.get(self.url, headers=default_headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data:
                if not isinstance(item, dict) or "id" not in item:
                    continue
                tags = ", ".join(item.get("tags") or [])
                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                salary = ""
                if salary_min or salary_max:
                    salary = f"${salary_min or '?'} - ${salary_max or '?'}"
                result.jobs.append(
                    RawJob(
                        external_id=str(item["id"]),
                        source=self.name,
                        title=item.get("position", "").strip(),
                        company=item.get("company", "Unknown").strip(),
                        location=item.get("location", "Remote"),
                        job_type="",
                        salary=salary,
                        description=item.get("description", "") or tags,
                        url=item.get("url") or f"https://remoteok.com/remote-jobs/{item['id']}",
                        posted_at=item.get("date", ""),
                        search_label="Remote — Global",
                    )
                )
        except Exception as exc:
            result.errors.append(f"{self.name}: {exc}")
        return result
