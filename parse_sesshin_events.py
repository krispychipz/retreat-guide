import logging
from typing import Callable, List, Dict

import requests

from sites import sfzc


logger = logging.getLogger(__name__)



def fetch_retreat_events(
    base_url: str,
    pages: int = 3,
    parser: Callable[[str, str], List[Dict[str, str]]] = sfzc.parse_events,
) -> List[Dict[str, str]]:
    """Fetch events containing 'retreat' from an AJAX-powered calendar."""
    all_events = []
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
    parser: Callable[[str, str], List[Dict[str, str]]] = sfzc.parse_events,
) -> List[Dict[str, str]]:
    """Fetch retreat events from multiple base URLs."""
    all_events = []
    for url in urls:
        logger.info("Processing calendar page: %s", url)
        try:
            all_events.extend(fetch_retreat_events(url, pages=pages, parser=parser))
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
    logger.info("Total events collected: %d", len(all_events))
    return all_events


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse retreat events from SFZC")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to fetch")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s:%(message)s")

    events = fetch_retreat_events(sfzc.BASE_URL, pages=args.pages)
    for event in events:
        print(f"{event['date']} - {event['title']}")
        print(event['practice_center'])
        print(event['link'])
        print(f"Source: {event['source']}")
        print()


if __name__ == "__main__":
    main()
