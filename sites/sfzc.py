from datetime import datetime
from typing import List

import logging

from bs4 import BeautifulSoup
import requests
import re

from models import RetreatEvent, RetreatDates, RetreatLocation

logger = logging.getLogger(__name__)

# Base calendar URL for regular page requests
CALENDAR_URL = "https://www.sfzc.org/calendar?page={page}"
# Default headers for requests to event detail pages
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}


def fetch_description(url: str) -> str:
    """Fetch and return a description from an event detail page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to fetch %s: %s", url, exc)
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    meta = soup.find("meta", property="og:description")
    if meta and meta.get("content"):
        return meta["content"].strip()

    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()

    body_div = soup.select_one("div.field--name-body")
    if body_div:
        return body_div.get_text(" ", strip=True)

    return ""

def parse_events(html: str, source: str) -> List[RetreatEvent]:
    """Parse retreat events from SFZC HTML snippet and return dataclasses."""
    logger.debug("Parsing HTML from %s", source)
    soup = BeautifulSoup(html, "html.parser")
    events: List[RetreatEvent] = []

    tables = soup.select("table.views-table")
    logger.debug("Found %d event tables", len(tables))

    for table in tables:
        cap = table.find("caption")
        if not cap:
            logger.debug("Skipping table without caption")
            continue
        date_str = cap.get_text(strip=True)
        try:
            event_day = datetime.strptime(date_str, "%A, %b %d, %Y").date()
        except ValueError:
            logger.debug("Could not parse date '%s'", date_str)
            continue

        for row in table.select("tbody tr"):
            cols = row.find_all("td")
            if len(cols) < 3:
                logger.debug("Row has %d columns, expected 3", len(cols))
                continue

            time_str = cols[0].get_text(strip=True)
            try:
                t = datetime.strptime(time_str, "%I:%M %p").time()
            except ValueError:
                t = None
            start_dt = datetime.combine(event_day, t) if t else None
            dates = RetreatDates(start=start_dt)

            loc_name = cols[1].get_text(strip=True)
            location = RetreatLocation(practice_center=loc_name)

            link_tag = cols[2].find("a")
            title_raw = link_tag.get_text(strip=True) if link_tag else cols[2].get_text(strip=True)
            title = re.sub(r",\s*\d{1,2}/\d{1,2}$", "", title_raw)
            link = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""

            keywords = ["sesshin", "sitting", "zazenkai", "retreat"]
            title_lower = title.lower()

            if not any(kw in title_lower for kw in keywords):
                logger.debug("Skipping non-retreat event: %s", title)
                continue

            description = fetch_description(link) if link else ""

            events.append(
                RetreatEvent(
                    title=title,
                    dates=dates,
                    teachers=[],
                    location=location,
                    description=description,
                    link=link,
                    other={"source": source},
                )
            )

    logger.debug("Parsed %d retreat events from %s", len(events), source)
    return events


def parse_calendar(html_path: str) -> List[RetreatEvent]:
    """Convenience wrapper for local files."""
    with open(html_path, encoding="utf-8") as fh:
        return parse_events(fh.read(), html_path)


if __name__ == "__main__":
    retreats = parse_calendar("sfzc.html")
    for r in retreats:
        print(r)
