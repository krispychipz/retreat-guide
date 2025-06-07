from datetime import datetime
from typing import Dict, List

from bs4 import BeautifulSoup

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


def _parse_single_date(text: str) -> datetime:
    """Parse a date string like 'June 1' into a datetime."""
    text = text.strip()
    for fmt in ("%B %d, %Y", "%B %d"):
        try:
            dt = datetime.strptime(text, fmt)
            if "%Y" not in fmt:
                dt = dt.replace(year=datetime.now().year)
            return dt
        except ValueError:
            continue
    # Fallback to current time if parsing fails
    return datetime.now()


def parse_events(html: str, source: str) -> List[RetreatEvent]:
    """Parse retreat events from SFZC HTML snippet and return dataclasses."""
    soup = BeautifulSoup(html, "html.parser")
    events: List[RetreatEvent] = []
    for row in soup.select("tr"):
        title_cell = row.select_one("td.views-field.views-field-title")
        if not title_cell:
            continue
        title_text = title_cell.get_text(strip=True)
        if "retreat" not in title_text.lower():
            continue

        date_cell = row.select_one("td.views-field.views-field-field-dates-1")
        center_cell = row.select_one("td.views-field.views-field-field-practice-center")
        link_elem = title_cell.find("a", href=True)

        date_text = date_cell.get_text(strip=True) if date_cell else ""
        start = _parse_single_date(date_text)

        events.append(
            RetreatEvent(
                title=title_text,
                dates=RetreatDates(start=start, end=start),
                teachers=[],
                location=RetreatLocation(
                    practice_center=center_cell.get_text(strip=True) if center_cell else ""
                ),
                description="",
                link=link_elem["href"] if link_elem else "",
                other={"source": source},
            )
        )
    return events
