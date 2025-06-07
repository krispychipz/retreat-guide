from bs4 import BeautifulSoup, NavigableString
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

        # Teachers appear as links immediately following the title
        teachers: List[str] = []
        br_after_teachers = None
        span = detail_p.find('span')
        if span:
            teachers = [a.get_text(strip=True) for a in span.find_all('a', href=True)]
            br_after_teachers = span.find_next('br')
        logger.debug("Teachers parsed: %s", teachers)

        # Raw date text is right after the first <br>
        dates = ''
        dates_text = ''
        br = br_after_teachers
        if br:
            for el in br.next_elements:
                #logger.debug("next element: %s", el)
                if isinstance(el, NavigableString) and el.strip():
                    dates_text = el.strip()
                    break
        logger.debug("Dates text: %s", dates_text)
        
        # Parse date range, e.g. "June 1 to 8, 2025" or "October 31 – November 15, 2025"
        m = re.search(
            r'([A-Za-z]+)\s+(\d{1,2})(?:,?\s*(\d{4}))?\s*(?:to|[-\u2013])\s*(?:([A-Za-z]+)\s+)?(\d{1,2}),?\s*(\d{4})?',
            dates_text,
        )
        if m:
            smonth, sday, syear, emonth, eday, eyear = m.groups()
            eyear = eyear or syear
            syear = syear or eyear
            emonth = emonth or smonth
            start_dt = datetime.strptime(f"{smonth} {sday} {syear}", "%B %d %Y")
            end_dt = datetime.strptime(f"{emonth} {eday} {eyear}", "%B %d %Y")
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

        # Override with known Insight Retreat Center location details
        loc.practice_center = "Insight Retreat Center"
        loc.city = "Santa Cruz"
        loc.region = "CA"
        loc.country = "USA"
        other["address"] = "1906 Glen Canyon Rd, Santa Cruz, CA 95060"

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
