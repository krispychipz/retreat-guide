from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import re
from models import RetreatEvent, RetreatDates, RetreatLocation

def parse_retreats(html_path: str) -> List[RetreatEvent]:
    soup = BeautifulSoup(open(html_path, encoding='utf-8'), 'html.parser')
    events: List[RetreatEvent] = []

    for container in soup.find_all('div', class_='irc-retreat-listing-div-text'):
        paras = container.find_all('p', class_='irc-retreat-listing-p')
        if len(paras) < 2:
            continue
        detail_p, desc_p = paras[0], paras[1]

        # Title
        title_parts = [s.get_text(strip=True)
                       for s in detail_p.find_all('strong')
                       if 'RETREAT FULL' not in s.get_text()]
        title = ' '.join(title_parts)

        # Teachers
        teachers = [a.get_text(strip=True)
                    for a in detail_p.find_all('a', href=True)]

        # Raw date text is right after the first <br>
        dates_text = ''
        br = detail_p.find('br')
        if br:
            node = br.next_sibling
            while node and (not isinstance(node, str) or not node.strip()):
                node = node.next_sibling
            if isinstance(node, str):
                # strip off any trailing hours info
                dates_text = node.split('  -  ')[0].strip()

        # Parse date range, e.g. "June 29 to July 13, 2025"
        m = re.match(r'([A-Za-z]+ \d{1,2})(?:,? (\d{4}))? to ([A-Za-z]+ \d{1,2}), (\d{4})',
                     dates_text)
        if m:
            start_str, start_year, end_str, end_year = m.groups()
            year = end_year
            start_year = start_year or year
            start_dt = datetime.strptime(f"{start_str}, {start_year}", "%B %d, %Y")
            end_dt   = datetime.strptime(f"{end_str}, {end_year}", "%B %d, %Y")
            dates = RetreatDates(start=start_dt, end=end_dt)
        else:
            # fallback to None if parse fails
            dates = RetreatDates(start=None, end=None)  # type: ignore

        # Description
        description = desc_p.get_text(strip=True)

        # Registration link: look for a REGISTER link in the list items
        link = ''
        ul = container.find('ul')
        if ul:
            reg = ul.find('a', string=re.compile(r'REGISTER', re.I))
            if reg and reg.has_attr('href'):
                link = reg['href']

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

        events.append(RetreatEvent(
            title=title,
            dates=dates,
            teachers=teachers,
            location=loc,
            description=description,
            link=link,
            other=other
        ))

    return events

# Example usage
if __name__ == '__main__':
    retreats = parse_retreats('/Users/richbae/Downloads/irc.html')
    for r in retreats:
        print(r)
