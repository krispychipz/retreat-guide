import logging
from dataclasses import asdict
from typing import Callable, List

import requests
import xml.etree.ElementTree as ET

from models import RetreatEvent
from sites import sfzc, irc, spiritrock

IRC_URL = "https://www.insightretreatcenter.org/retreats/"
SPIRITROCK_URL = "https://www.spiritrock.org/calendar?programType=retreats"

logger = logging.getLogger(__name__)


def fetch_retreat_events(
    base_url: str,
    pages: int = 3,
    parser: Callable[[str, str], List[RetreatEvent]] = sfzc.parse_events,
) -> List[RetreatEvent]:
    """Fetch events containing 'retreat' from an AJAX-powered calendar."""
    all_events: List[RetreatEvent] = []
    for page in range(pages):
        url = base_url.format(page=page)
        logger.info("Fetching %s", url)
        response = requests.get(url)
        logger.debug("Response status: %s", getattr(response, "status_code", "N/A"))
        response.raise_for_status()

        html = response.text
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, list):
            html = "".join(part.get("data", "") for part in payload if isinstance(part, dict))

        events = parser(html, url)
        all_events.extend(events)

    logger.info("%d retreat events found", len(all_events))
    return all_events


def fetch_all_retreats(
    urls: List[str],
    pages: int = 3,
    parser: Callable[[str, str], List[RetreatEvent]] = sfzc.parse_events,
) -> List[RetreatEvent]:
    """Fetch retreat events from multiple base URLs."""
    all_events: List[RetreatEvent] = []
    for url in urls:
        logger.info("Processing calendar page: %s", url)
        try:
            all_events.extend(fetch_retreat_events(url, pages=pages, parser=parser))
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
    logger.info("Total events collected: %d", len(all_events))
    return all_events


def events_to_xml(events: List[RetreatEvent]) -> str:
    """Convert a list of events to an XML string."""
    root = ET.Element("retreats")
    for event in events:
        retreat_elem = ET.SubElement(root, "retreat")
        data = asdict(event)

        # Flatten dates
        dates = data.pop("dates")
        date_elem = ET.SubElement(retreat_elem, "dates")
        start_elem = ET.SubElement(date_elem, "start")
        start_elem.text = dates["start"].isoformat()
        end_elem = ET.SubElement(date_elem, "end")
        end_elem.text = dates["end"].isoformat()

        # Location
        location = data.pop("location")
        location_elem = ET.SubElement(retreat_elem, "location")
        for key, value in location.items():
            child = ET.SubElement(location_elem, key)
            if value is not None:
                child.text = str(value)

        # Teachers list
        teachers = data.pop("teachers")
        teachers_elem = ET.SubElement(retreat_elem, "teachers")
        for teacher in teachers:
            t_child = ET.SubElement(teachers_elem, "teacher")
            t_child.text = teacher

        # Remaining fields
        for key, value in data.items():
            if isinstance(value, dict):
                sub = ET.SubElement(retreat_elem, key)
                for sub_key, sub_val in value.items():
                    child = ET.SubElement(sub, sub_key)
                    child.text = str(sub_val)
            else:
                child = ET.SubElement(retreat_elem, key)
                child.text = str(value)

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse retreat events from supported sites")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to fetch (where applicable)")
    parser.add_argument("--site", choices=["sfzc", "irc", "spiritrock"], default="sfzc", help="Which site to parse")
    parser.add_argument("--output", type=str, help="Write events to this XML file")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s:%(message)s")

    if args.site == "sfzc":
        events = fetch_retreat_events(sfzc.BASE_URL, pages=args.pages, parser=sfzc.parse_events)
    elif args.site == "irc":
        events = fetch_retreat_events(IRC_URL, pages=1, parser=irc.parse_events)
    else:  # spiritrock
        events = fetch_retreat_events(SPIRITROCK_URL, pages=1, parser=spiritrock.parse_events)

    if args.output:
        xml = events_to_xml(events)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(xml)
        print(f"Wrote {len(events)} events to {args.output}")
    else:
        for event in events:
            print(f"{event.dates.start:%B %d, %Y} - {event.title}")
            print(event.location.practice_center)
            print(event.link)
            print(f"Source: {event.other.get('source', '')}")
            print()


if __name__ == "__main__":
    main()
