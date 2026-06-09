#!/usr/bin/env python3
"""Scrape Fortune 100 career pages only."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import SessionLocal, init_db
from app.scrapers.runner import run_careers_scraper


async def main():
    init_db()
    db = SessionLocal()
    try:
        result = await run_careers_scraper(db)
        print(f"Status: {result['status']}")
        print(f"Added: {result['jobs_added']}, Updated: {result['jobs_updated']}")
        print(f"Duration: {result['duration_seconds']:.1f}s")
        for item in result["by_source"]:
            print(f"  {item['source']}: {item['count']}")
        if result["errors"]:
            print("Errors:")
            for err in result["errors"]:
                print(f"  - {err}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
