from importlib import import_module
from bs4 import BeautifulSoup
from datetime import datetime
import re

from models import RetreatDates

# Import submodules normally
irc = import_module('sites.irc')

# Preserve original function so we can delegate
_original_parse_events = irc.parse_events

def _patched_parse_events(html: str, source: str):
    """Wrap the original parser and ensure teacher names are captured even
    when no <span> tag is present."""
    events = _original_parse_events(html, source)
    try:
        soup = BeautifulSoup(html, 'html.parser')
        containers = soup.find_all('div', class_='irc-retreat-listing-div-text')
        date_re = re.compile(
            r'([A-Za-z]+)\s+(\d{1,2})(?:,?\s*(\d{4}))?\s*(?:to|[-\u2013])\s*(?:([A-Za-z]+)\s+)?(\d{1,2}),?\s*(\d{4})?'
        )
        for evt, cont in zip(events, containers):
            detail_p = cont.find('p', class_='irc-retreat-listing-p')
            if not detail_p:
                continue

            if not getattr(evt, 'teachers', None):
                links = detail_p.find_all('a', href=True)
                evt.teachers = [a.get_text(strip=True) for a in links]

            if evt.dates.start is None:
                br = detail_p.find('br')
                text = ''
                if br:
                    node = br.next_sibling
                    while node and isinstance(node, str) and not node.strip():
                        node = node.next_sibling
                    if node:
                        text = node if isinstance(node, str) else node.get_text(' ', strip=True)
                        text = re.split(r'\s+-\s+', text)[0].strip()
                m = date_re.search(text)
                if m:
                    smonth, sday, syear, emonth, eday, eyear = m.groups()
                    eyear = eyear or syear
                    syear = syear or eyear
                    emonth = emonth or smonth
                    try:
                        start_dt = datetime.strptime(f"{smonth} {sday} {syear}", "%B %d %Y")
                        end_dt = datetime.strptime(f"{emonth} {eday} {eyear}", "%B %d %Y")
                        evt.dates = RetreatDates(start=start_dt, end=end_dt)
                    except Exception:
                        pass
    except Exception:
        pass  # fail silently; rely on original parsing if anything goes wrong
    return events

# Replace parse_events with patched version
irc.parse_events = _patched_parse_events
