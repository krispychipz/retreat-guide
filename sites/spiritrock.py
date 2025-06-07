from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import re

from models import RetreatEvent, RetreatDates, RetreatLocation

@dataclass
class RetreatDates:
    """Date range for a retreat."""
    start: Optional[datetime]
    end: Optional[datetime]

@dataclass
class RetreatLocation:
    """Detailed retreat location information."""
    practice_center: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

@dataclass
class RetreatEvent:
    """Unified representation of a retreat event."""
    title: str
    dates: RetreatDates
    teachers: List[str]
    location: RetreatLocation
    description: str
    link: str
    other: Dict[str, str] = field(default_factory=dict)

def parse_spiritrock(html_path: str) -> List[RetreatEvent]:
    soup = BeautifulSoup(open(html_path, encoding='utf-8'), 'html.parser')
    events: List[RetreatEvent] = []

    for card in soup.find_all('div', class_='event-card'):
        # 1) Title & link
        a = card.select_one('h2.event-title a')
        if not a:
            continue
        title = a.get_text(strip=True)
        link  = a['href']

        # 2) Dates: container with class "flex flex-row w-full mb-4 event-headline"
        headline = card.select_one('div.event-headline')
        raw_dates = headline.get_text(' ', strip=True) if headline else ''
        # match "June 29, 2025 – July 13, 2025"
        m = re.search(r'([A-Za-z]+ \d{1,2}, \d{4})\s*[–-]\s*([A-Za-z]+ \d{1,2}, \d{4})', raw_dates)
        if m:
            start_dt = datetime.strptime(m.group(1), "%B %d, %Y")
            end_dt   = datetime.strptime(m.group(2), "%B %d, %Y")
            dates = RetreatDates(start=start_dt, end=end_dt)
        else:
            dates = RetreatDates(start=None, end=None)

        # 3) Teachers: div with class ending in "teacher-names-only"
        teacher_div = card.find('div', class_='teacher-names-only')
        teachers = []
        if teacher_div:
            # split on commas, strip whitespace
            for name in teacher_div.get_text(strip=True).split(','):
                name = name.strip()
                if name:
                    teachers.append(name)

        # 4) Description: the summary paragraph or div
        desc_div = card.select_one('.event-description, .event-summary')
        description = desc_div.get_text(' ', strip=True) if desc_div else ''

        # 5) Other info: status or credits from the card-meta if present
        other: Dict[str, str] = {}
        meta = card.select_one('.event-meta-full')
        if meta:
            text = meta.get_text(' ', strip=True)
            # example: look for "Status: Full" or "Waitlist open"
            if 'Full' in text:
                other['Status'] = text

        # 6) Location: Spirit Rock listings often omit location here
        location = RetreatLocation()

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

# usage
if __name__ == '__main__':
    retreats = parse_spiritrock('spiritrock.html')
    for evt in retreats:
        print(evt)
