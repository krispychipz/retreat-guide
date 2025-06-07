import logging
from dataclasses import asdict
from typing import Callable, List

import requests
import json

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
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        logger.info("Fetching %s", url)
        response = requests.get(url, headers=headers)
        logger.debug("Response status: %s", getattr(response, "status_code", "N/A"))
        response.raise_for_status()

        html = response.text
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, list):
            html_parts: List[str] = []
            for part in payload:
                if not isinstance(part, dict):
                    continue
                data = part.get("data", "")
                if isinstance(data, list):
                    html_parts.extend(str(item) for item in data if isinstance(item, (str, bytes)))
                else:
                    html_parts.append(str(data))
            html = "".join(html_parts)

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


def events_to_json(events: List[RetreatEvent]) -> str:
    """Convert a list of events to a JSON string."""
    return json.dumps([asdict(event) for event in events], default=str, indent=2)


def fetch_all_sites(pages: int = 3) -> List[RetreatEvent]:
    """Fetch retreat events from all supported centers."""
    events: List[RetreatEvent] = []
    events.extend(fetch_retreat_events(sfzc.BASE_URL, pages=pages, parser=sfzc.parse_events))
    events.extend(fetch_retreat_events(IRC_URL, pages=1, parser=irc.parse_events))
    events.extend(fetch_retreat_events(SPIRITROCK_URL, pages=1, parser=spiritrock.parse_events))
    return events


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse retreat events from supported sites")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to fetch (where applicable)")
    parser.add_argument(
        "--site",
        choices=["sfzc", "irc", "spiritrock", "all"],
        default="all",
        help="Which site to parse",
    )
    parser.add_argument("--output", type=str, help="Write events to this JSON file")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s:%(message)s")

    if args.site == "sfzc":
        events = fetch_retreat_events(sfzc.BASE_URL, pages=args.pages, parser=sfzc.parse_events)
    elif args.site == "irc":
        events = fetch_retreat_events(IRC_URL, pages=1, parser=irc.parse_events)
    elif args.site == "spiritrock":
        events = fetch_retreat_events(SPIRITROCK_URL, pages=1, parser=spiritrock.parse_events)
    else:  # all
        events = fetch_all_sites(pages=args.pages)

    if args.output:
        json_str = events_to_json(events)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(json_str)
        print(f"Wrote {len(events)} events to {args.output}")
    else:
        for event in events:
            start_dt = event.dates.start
            date_str = start_dt.strftime("%B %d, %Y") if start_dt else "Unknown Date"
            print(f"{date_str} - {event.title}")
            print(event.location.practice_center or "")
            print(event.link or "")
            print(f"Source: {event.other.get('source', '')}")
            print()


if __name__ == "__main__":
    main()
