from datetime import datetime
from typing import Dict, List

from bs4 import BeautifulSoup
import requests
import re

from models import RetreatEvent, RetreatDates, RetreatLocation

# Base endpoint for AJAX requests
BASE_AJAX = "https://www.sfzc.org/views/ajax"

# Default query parameters sent with each request. The page number will be
# inserted at runtime.
DEFAULT_PARAMS: Dict[str, str] = {
    "_wrapper_format": "drupal_ajax",
    "view_name": "events",
    "view_display_id": "default",
    "_drupal_ajax": "1",
}


def fetch_events_page(page: int) -> str:
    """Fetch a single events page from SFZC using the AJAX endpoint."""
    params = DEFAULT_PARAMS.copy()
    params["page"] = str(page)
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ),
    }
    resp = requests.get(BASE_AJAX, params=params, headers=headers)
    resp.raise_for_status()
    return resp.text


def parse_events(html: str, source: str) -> List[RetreatEvent]:
    """Parse retreat events from SFZC HTML snippet and return dataclasses."""
    soup = BeautifulSoup(html, "html.parser")
    events: List[RetreatEvent] = []

    for table in soup.select("table.views-table"):
        cap = table.find("caption")
        if not cap:
            continue
        date_str = cap.get_text(strip=True)
        try:
            event_day = datetime.strptime(date_str, "%A, %b %d, %Y").date()
        except ValueError:
            continue

        for row in table.select("tbody tr"):
            cols = row.find_all("td")
            if len(cols) < 3:
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

            if "retreat" not in title.lower():
                continue

            events.append(
                RetreatEvent(
                    title=title,
                    dates=dates,
                    teachers=[],
                    location=location,
                    description="",
                    link=link,
                    other={"source": source},
                )
            )

    return events


def parse_calendar(html_path: str) -> List[RetreatEvent]:
    """Convenience wrapper for local files."""
    with open(html_path, encoding="utf-8") as fh:
        return parse_events(fh.read(), html_path)


if __name__ == "__main__":
    retreats = parse_calendar("sfzc.html")
    for r in retreats:
        print(r)
