from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List
import logging
import re

from models import RetreatEvent, RetreatDates, RetreatLocation

logger = logging.getLogger(__name__)

def parse_events(html: str, source: str) -> List[RetreatEvent]:
    """Parse retreats from an IRC HTML page."""
    logger.debug("Starting IRC parsing")
    soup = BeautifulSoup(html, 'html.parser')
    events: List[RetreatEvent] = []

    for container in soup.find_all('div', class_='irc-retreat-listing-div-text'):
        logger.debug("New retreat container: %s", container.get_text(strip=True)[:60])
        paras = container.find_all('p', class_='irc-retreat-listing-p')
        if len(paras) < 2:
            continue
        detail_p, desc_p = paras[0], paras[1]

        # Title
        title_parts = [s.get_text(strip=True)
                       for s in detail_p.find_all('strong')
                       if 'RETREAT FULL' not in s.get_text()]
        title = ' '.join(title_parts)
        logger.debug("Parsed title: %s", title)

        # Teachers
        teachers = [a.get_text(strip=True)
                    for a in detail_p.find_all('a', href=True)]
        logger.debug("Teachers from links: %s", teachers)
        # Some teacher names may appear as plain text after the title
        first_strong = detail_p.find('strong')
        if first_strong:
            node = first_strong.next_sibling
            teacher_txt = ""
            while node and getattr(node, 'name', None) != 'br':
                if isinstance(node, str):
                    teacher_txt += node
                else:
                    teacher_txt += node.get_text(" ", strip=True)
                node = node.next_sibling
            teacher_txt = teacher_txt.strip(" ,\u2013-")
            if teacher_txt:
                teachers.extend(
                    [t.strip() for t in re.split(r",| and |/", teacher_txt) if t.strip()]
                )
        logger.debug("All teachers: %s", teachers)

        # Raw date text is right after the first <br>
        dates_text = ''
        br = detail_p.find('br')
        if br:
            node = br.next_sibling
            while node and isinstance(node, str) and not node.strip():
                node = node.next_sibling
            if node:
                if isinstance(node, str):
                    text = node
                else:
                    text = node.get_text(' ', strip=True)
                dates_text = re.split(r'\s+-\s+', text)[0].strip()
        logger.debug("Dates text: %s", dates_text)

        # Parse date range, e.g. "June 29 to July 13, 2025" or "June 29 – July 13, 2025"
        m = re.search(
            r'([A-Za-z]+ \d{1,2})(?:,? (\d{4}))?\s*(?:to|[-\u2013])\s*([A-Za-z]+ \d{1,2})(?:,? (\d{4}))?',
            dates_text,
        )
        if m:
            start_str, start_year, end_str, end_year = m.groups()
            end_year = end_year or start_year
            start_year = start_year or end_year
            start_dt = datetime.strptime(f"{start_str}, {start_year}", "%B %d, %Y")
            end_dt = datetime.strptime(f"{end_str}, {end_year}", "%B %d, %Y")
            dates = RetreatDates(start=start_dt, end=end_dt)
        else:
            # fallback to None if parse fails
            dates = RetreatDates(start=None, end=None)  # type: ignore
        logger.debug("Parsed dates: %s", dates)

        # Description
        description = desc_p.get_text(strip=True)
        logger.debug("Description: %s", description[:60])

        # Registration link: look for a REGISTER link in the list items
        link = ''
        ul = container.find('ul')
        if ul:
            reg = ul.find('a', string=re.compile(r'REGISTER', re.I))
            if reg and reg.has_attr('href'):
                link = reg['href']
        logger.debug("Registration link: %s", link)

        # Other info dictionary
        other: Dict[str, str] = {}
        if ul:
            for li in ul.find_all('li'):
                lbl = li.find('strong')
                if not lbl:
                    continue
                key = lbl.get_text(strip=True).rstrip(':')
                val = li.get_text(' ', strip=True)
                val = re.sub(r'^' + re.escape(key) + r':\s*', '', val)
                other[key] = val
        logger.debug("Other fields: %s", other)

        # Location fields (if present in other, under key "Location")
        loc = RetreatLocation()
        if 'Location' in other:
            parts = [p.strip() for p in other.pop('Location').split(',')]
            if parts:
                loc.practice_center = parts[0]
            if len(parts) > 1:
                loc.city = parts[1]
            if len(parts) > 2:
                loc.region = parts[2]
            if len(parts) > 3:
                loc.country = parts[3]
        logger.debug("Location: %s", loc)

        events.append(RetreatEvent(
            title=title,
            dates=dates,
            teachers=teachers,
            location=loc,
            description=description,
            link=link,
            other={"source": source, **other}
        ))
        logger.debug("Added event: %s", title)

    logger.debug("Total events parsed: %d", len(events))
    return events


def parse_retreats(html_path: str) -> List[RetreatEvent]:
    """Convenience wrapper around :func:`parse_events` for local files."""
    with open(html_path, encoding='utf-8') as fh:
        return parse_events(fh.read(), html_path)


if __name__ == '__main__':
    retreats = parse_retreats('/Users/richbae/Downloads/irc.html')
    for r in retreats:
        print(r)
