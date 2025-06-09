import logging
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional
import requests
import re

from models import RetreatEvent, RetreatDates, RetreatLocation

ALGOLIA_URL = "https://e6yg7cmgyo-dsn.algolia.net/1/indexes/events/query"
ALGOLIA_HEADERS = {
    "X-Algolia-API-Key": "04e497e32c17a3fc1bd4e4b8b2e45413",
    "X-Algolia-Application-Id": "E6YG7CMGYO",
    "X-Algolia-Agent": "Algolia for JavaScript (4.24.0); Browser (lite)",
}

# Separate headers for fetching event detail pages
DETAIL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

# — helper to strip out HTML from the description —
def strip_html(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text(separator=" ", strip=True)

def fetch_algolia_page(page: int = 0, hits_per_page: int = 100) -> List[dict]:
    """Return a single page of results from the Spirit Rock Algolia index."""
    payload = {"params": f"page={page}&hitsPerPage={hits_per_page}"}
    resp = requests.post(ALGOLIA_URL, json=payload, headers=ALGOLIA_HEADERS)
    resp.raise_for_status()
    return resp.json().get("hits", [])


def fetch_description(url: str) -> str:
    """Fetch the full description from an event detail page."""
    try:
        resp = requests.get(url, headers=DETAIL_HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return ""
    logging.debug("Fetching description from %s", url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Look for a header element mentioning "description" and collect the text
    # from the elements that follow until the next header. This mirrors the
    # layout used on Spirit Rock pages where the description lives below a
    # heading such as "Program Description".
    header = soup.find(
        lambda tag: (
            tag.name in {"h1", "h2", "h3", "h4", "h5", "strong"}
            and "description" in tag.get_text(strip=True).lower()
        )
    )
    logging.debug("Found header for description: %s", header)
    if header:
        parts: List[str] = []
        for sib in header.find_all_next():
            if sib.name in {"h1", "h2", "h3", "h4", "h5"}:
                break
            if sib.name in {"p", "div"}:
                text = sib.get_text(" ", strip=True)
                if text:
                    parts.append(text)
        if parts:
            logging.debug("Collected description parts: %s", parts)
            return " ".join(parts)

    meta_og = soup.find("meta", property="og:description")
    meta_desc = soup.find("meta", attrs={"name": "description"})
    body_div = soup.find(class_="program-description") or soup.find(itemprop="description")

    if meta_og and meta_og.get("content"):
        return meta_og["content"].strip()
    if meta_desc and meta_desc.get("content"):
        return meta_desc["content"].strip()
    if body_div:
        return body_div.get_text(" ", strip=True)

    return ""

def parse_algolia_events(max_pages: int=10) -> List[RetreatEvent]:
    logging.info("Fetching Spirit Rock events from Algolia")
    events: List[RetreatEvent] = []
    for page in range(max_pages):
        hits = fetch_algolia_page(page)
        if not hits:
            break

        for h in hits:
            # 1) Basic fields
            title = h.get("title", "")
            link  = h.get("url", "")

            # 2) Description (strip HTML)
            description = fetch_description(link)
            #description = h.get("shortDescription") or h.get("description", "")

            # 3) Dates (UNIX timestamps → datetime)
            start_ts = h.get("startDate")
            end_ts = h.get("endDate")

            if isinstance(start_ts, (int, float)):
                start_dt = datetime.fromtimestamp(start_ts)
            elif isinstance(start_ts, str):
                try:
                    start_dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                except ValueError:
                    start_dt = None
            else:
                start_dt = None

            if isinstance(end_ts, (int, float)):
                end_dt = datetime.fromtimestamp(end_ts)
            elif isinstance(end_ts, str):
                try:
                    end_dt = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
                except ValueError:
                    end_dt = None
            else:
                end_dt = None
            dates = RetreatDates(start=start_dt, end=end_dt)

            # 4) Teachers
            et = h.get("eventTeachers")
            if et is None:
                et = h.get("teacherNames", [])
                if isinstance(et, list):
                    teachers = [name.strip() for name in et if isinstance(name, str) and name.strip()]
                else:
                    teachers = []
            else:
                teachers = [name.strip() for name in str(et).split(",") if name.strip()]

            # 5) Location information
            location = RetreatLocation()
            location.practice_center = "Spirit Rock Meditation Center"
            location.city = "Woodacre"
            location.region = "CA"
            location.country = "USA"

            # 6) Other metadata
            other = {
                "eventCode":      h.get("eventCode", ""),
                "programType":    h.get("programTypeName", ""),
                "duration":       h.get("duration", ""),
                "credits":        str(h.get("creditCount", "")),
                "postDateString": h.get("postDateString", ""),
            }
            other["address"] = "5000 Sir Francis Drake Blvd Box 169, Woodacre, CA 94973"

            used_keys = {
                "title",
                "url",
                "startDate",
                "endDate",
                "eventTeachers",
                "teacherNames",
                "shortDescription",
                "displayLocation",
                "location",
            }

            for key, val in h.items():
                if key not in used_keys and key not in other and val not in (None, ""):
                    other[key] = val

            events.append(RetreatEvent(
                title=title,
                dates=dates,
                teachers=teachers,
                location=location,
                description=description,
                link=link,
                other=other
            ))
    logging.info("%d retreat events found", len(events))

    return events