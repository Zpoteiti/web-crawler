"""FastAPI server exposing commodity scraping service."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from .services import CommodityService


app = FastAPI()


BASE_REPORT_DIR = Path(__file__).resolve().parent / "reports"


class ScrapeRequest(BaseModel):
    user_id: str
    session_id: str
    scraper_names: Optional[List[str]] = None


@app.post("/scrape")
async def scrape(req: ScrapeRequest):
    """Run commodity scrapers asynchronously for a user session."""
    output_dir = BASE_REPORT_DIR / req.user_id / req.session_id
    service = CommodityService(output_dir=output_dir)

    result = await asyncio.to_thread(service.run_full_analysis, req.scraper_names)

    return {
        "files": result.get("files", {}),
        "summary": result.get("summary", {}),
    }

