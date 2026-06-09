from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ScrapeResponse, SourceCount
from app.scrapers import run_all_scrapers, run_careers_scraper

router = APIRouter(prefix="/api", tags=["scrape"])


def _scrape_response(result: dict) -> ScrapeResponse:
    return ScrapeResponse(
        status=result["status"],
        jobs_added=result["jobs_added"],
        jobs_updated=result["jobs_updated"],
        duration_seconds=result["duration_seconds"],
        by_source=[SourceCount(**item) for item in result["by_source"]],
        errors=result["errors"],
    )


@router.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(db: Session = Depends(get_db)):
    return _scrape_response(await run_all_scrapers(db))


@router.post("/scrape/careers", response_model=ScrapeResponse)
async def trigger_careers_scrape(db: Session = Depends(get_db)):
    """Fortune 100 career pages only (~1 min). Run this if the full sync timed out."""
    return _scrape_response(await run_careers_scraper(db))
