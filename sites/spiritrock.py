from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List
import re

from models import RetreatEvent, RetreatDates, RetreatLocation

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

        # 6) Location: Spirit Rock listings often omit location here
        location = RetreatLocation()

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
