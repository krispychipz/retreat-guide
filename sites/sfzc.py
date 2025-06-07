from datetime import datetime
from typing import List, Dict

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


def fetch_description(url: str) -> tuple[str, List[str]]:
    """Fetch description and teacher names from an event detail page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to fetch %s: %s", url, exc)
        return "", []

    soup = BeautifulSoup(response.text, "html.parser")

    description = ""
    meta = soup.find("meta", property="og:description")
    if meta and meta.get("content"):
        description = meta["content"].strip()
    else:
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            description = meta["content"].strip()
        else:
            body_div = soup.select_one("div.field--name-body")
            if body_div:
                description = body_div.get_text(" ", strip=True)

    teachers: List[str] = []
    teacher_el = soup.find(string=re.compile(r"Teachers?:", re.I))
    if teacher_el:
        container = (
            teacher_el.parent.parent
            if getattr(teacher_el, "parent", None)
            and getattr(teacher_el.parent, "parent", None)
            else teacher_el.parent
        )
        container_text = container.get_text(" ", strip=True)
        m = re.search(r"Teachers?:\s*(.*)", container_text, re.I)
        if m:
            teachers_str = m.group(1)
            teachers_str = re.sub(r"\band\b", ",", teachers_str, flags=re.I)
            teachers = [
                t.strip() for t in re.split(r",|/|&", teachers_str) if t.strip()
            ]
        else:
            for a in container.find_all("a"):
                name = a.get_text(strip=True)
                if name:
                    teachers.append(name)

    return description, teachers


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
            other: Dict[str, str] = {"source": source}

            name_lower = loc_name.lower()
            if "city center" in name_lower:
                location.city = "San Francisco"
                location.region = "CA"
                location.country = "USA"
                other["address"] = "300 Page St, San Francisco, CA 94102"
            elif "green gulch" in name_lower:
                location.city = "Muir Beach"
                location.region = "CA"
                location.country = "USA"
                other["address"] = "1601 Shoreline Hwy, Muir Beach, CA 94965"
            elif "tassajara" in name_lower:
                location.city = "Carmel Valley"
                location.region = "CA"
                location.country = "USA"
                other["address"] = (
                    "39171 Tassajara Road Carmel Valley, CA 93924 Jamesburg"
                )

            link_tag = cols[2].find("a")
            title_raw = (
                link_tag.get_text(strip=True)
                if link_tag
                else cols[2].get_text(strip=True)
            )
            title = re.sub(r",\s*\d{1,2}/\d{1,2}$", "", title_raw)
            link = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""

            keywords = ["sesshin", "sitting", "zazenkai", "retreat"]
            title_lower = title.lower()

            if not any(kw in title_lower for kw in keywords):
                logger.debug("Skipping non-retreat event: %s", title)
                continue

            if link:
                description, teachers = fetch_description(link)
            else:
                description, teachers = "", []

            events.append(
                RetreatEvent(
                    title=title,
                    dates=dates,
                    teachers=teachers,
                    location=location,
                    description=description,
                    link=link,
                    other=other,
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
