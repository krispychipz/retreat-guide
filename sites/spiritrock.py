from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional
import requests
import re

from models import RetreatEvent, RetreatDates, RetreatLocation

ALGOLIA_URL = "https://e6yg7cmgyo-dsn.algolia.net/1/indexes/events/query"
HEADERS = {
    "X-Algolia-API-Key": "04e497e32c17a3fc1bd4e4b8b2e45413",
    "X-Algolia-Application-Id": "E6YG7CMGYO",
    "X-Algolia-Agent": "Algolia for JavaScript (4.24.0); Browser (lite)",
}

# — helper to strip out HTML from the description —
def strip_html(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text(separator=" ", strip=True)

def fetch_algolia_page(page: int = 0, hits_per_page: int = 100) -> List[dict]:
    """Return a single page of results from the Spirit Rock Algolia index."""
    payload = {"params": f"page={page}&hitsPerPage={hits_per_page}"}
    resp = requests.post(ALGOLIA_URL, json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("hits", [])

def parse_algolia_events(max_pages: int=10) -> List[RetreatEvent]:
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
            description = strip_html(h.get("shortDescription"))

            # 3) Dates (UNIX timestamps → datetime)
            start_ts = h.get("startDate")
            end_ts   = h.get("endDate")
            start_dt = datetime.fromtimestamp(start_ts) if isinstance(start_ts, (int, float)) else None
            end_dt   = datetime.fromtimestamp(end_ts)   if isinstance(end_ts,   (int, float)) else None
            dates = RetreatDates(start=start_dt, end=end_dt)

            # 4) Teachers
            et = h.get("eventTeachers", "")
            teachers = [name.strip() for name in et.split(",") if name.strip()]

            # 5) Location (Spirit Rock only gives a displayLocation here)
            loc_str = h.get("displayLocation")
            location = RetreatLocation(practice_center=loc_str)

            # 6) Other metadata
            other = {
                "eventCode":      h.get("eventCode", ""),
                "programType":    h.get("programTypeName", ""),
                "duration":       h.get("duration", ""),
                "credits":        str(h.get("creditCount", "")),
                "postDateString": h.get("postDateString", "")
            }

            events.append(RetreatEvent(
                title=title,
                dates=dates,
                teachers=teachers,
                location=location,
                description=description,
                link=link,
                other=other
            ))

    return events

def parse_events(html: str, source: str) -> List[RetreatEvent]:
    """Parse Spirit Rock retreat listings."""
    soup = BeautifulSoup(html, 'html.parser')
    events: List[RetreatEvent] = []

    for card in soup.select('div.event-wrap'):
        # 1) Title & link
        a = card.select_one('h2.event-title a')
        if not a:
            continue
        title = a.get_text(strip=True)
        link = a['href']

        # 2) Meta block contains date range and teacher links
        meta_txt = card.select_one('.event-meta-full')
        raw_meta = meta_txt.get_text(' ', strip=True) if meta_txt else ''

        # match "June 29 – July 13, 2025" or similar
        m = re.search(r'([A-Za-z]+ \d{1,2},? \d{4}).*?[–-].*?([A-Za-z]+ \d{1,2},? \d{4})', raw_meta)
        if m:
            start_dt = datetime.strptime(m.group(1), "%B %d, %Y")
            end_dt = datetime.strptime(m.group(2), "%B %d, %Y")
            dates = RetreatDates(start=start_dt, end=end_dt)
        else:
            dates = RetreatDates(start=None, end=None)

        # 3) Teachers: gather names from links in meta, skipping register links
        teachers = []
        for link_tag in meta_txt.select('a[href]') if meta_txt else []:
            href = link_tag['href']
            if 'retreat.guru/program' in href:
                continue
            teachers.append(link_tag.get_text(strip=True))

        # 4) Description: the summary paragraph or div
        desc_div = card.select_one('.event-description, .event-summary')
        description = desc_div.get_text(' ', strip=True) if desc_div else ''

        # 5) Other info: status or credits from the card-meta if present
        other: Dict[str, str] = {}
        if meta_txt:
            text = meta_txt.get_text(' ', strip=True)
            if 'Full' in text:
                other['Status'] = text

        # 6) Location
        location = RetreatLocation()
        location.practice_center = "Spirit Rock Meditation Center"
        location.city = "Woodacre"
        location.region = "CA"
        location.country = "USA"
        other["address"] = "5000 Sir Francis Drake Blvd Box 169, Woodacre, CA 94973"

        events.append(RetreatEvent(
            title=title,
            dates=dates,
            teachers=teachers,
            location=location,
            description=description,
            link=link,
            other={"source": source, **other}
        ))

    return events


def parse_spiritrock(html_path: str) -> List[RetreatEvent]:
    """Convenience wrapper for local files."""
    with open(html_path, encoding='utf-8') as fh:
        return parse_events(fh.read(), html_path)


if __name__ == '__main__':
    retreats = parse_spiritrock('spiritrock.html')
    for evt in retreats:
        print(evt)
