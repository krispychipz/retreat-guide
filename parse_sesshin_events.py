import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict


logger = logging.getLogger(__name__)


def fetch_retreat_events(url: str) -> List[Dict[str, str]]:
    """Fetch events containing 'retreat' from a calendar page."""
    logger.info("Fetching %s", url)
    response = requests.get(url)
    logger.debug("Response status: %s", getattr(response, "status_code", "N/A"))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    cards = soup.select(".card-event")
    logger.debug("Found %d '.card-event' elements", len(cards))
    for event in cards:
        title_elem = event.select_one(".card-title")
        if not title_elem:
            logger.debug("Skipping element with no title")
            continue
        title_text = title_elem.get_text(strip=True)
        logger.debug("Found title: %s", title_text)
        if "retreat" not in title_text.lower():
            logger.debug("Title does not contain 'retreat', skipping")
            continue

        date_elem = event.select_one(".card-date")
        info_elem = event.select_one(".card-description")
        link_elem = event.select_one("a")

        event_data = {
            "title": title_text,
            "date": date_elem.get_text(strip=True) if date_elem else "",
            "info": info_elem.get_text(strip=True) if info_elem else "",
            "link": link_elem["href"] if link_elem and link_elem.has_attr("href") else "",
            "source": url,
        }
        logger.debug("Added event: %s", event_data)
        events.append(event_data)
    logger.info("%d retreat events found", len(events))
    return events


def fetch_all_retreats(urls: List[str]) -> List[Dict[str, str]]:
    all_events = []
    for url in urls:
        logger.info("Processing calendar page: %s", url)
        try:
            all_events.extend(fetch_retreat_events(url))
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
    logger.info("Total events collected: %d", len(all_events))
    return all_events


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse retreat events from SFZC" )
    parser.add_argument("--debug", action="store_true", help="Enable debug loggi ng")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s:%(message)s")

    url = "https://www.sfzc.org/calendar"
    events = fetch_retreat_events(url)
    for event in events:
        print(f"{event['date']} - {event['title']}")
        print(event['info'])
        print(event['link'])
        print(f"Source: {event['source']}")
        print()


if __name__ == "__main__":
    main()
