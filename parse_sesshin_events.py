import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict


logger = logging.getLogger(__name__)


def _parse_events(html: str, source: str) -> List[Dict[str, str]]:
    """Parse retreat events from a block of HTML."""
    soup = BeautifulSoup(html, "html.parser")

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
            "source": source,
        }
        logger.debug("Added event: %s", event_data)
        events.append(event_data)
    return events


def fetch_retreat_events(base_url: str, pages: int = 3) -> List[Dict[str, str]]:
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

        events = _parse_events(html, url)
        all_events.extend(events)

    logger.info("%d retreat events found", len(all_events))
    return all_events


def fetch_all_retreats(urls: List[str], pages: int = 3) -> List[Dict[str, str]]:
    """Fetch retreat events from multiple base URLs."""
    all_events = []
    for url in urls:
        logger.info("Processing calendar page: %s", url)
        try:
            all_events.extend(fetch_retreat_events(url, pages=pages))
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

    url = (
        "https://www.sfzc.org/views/ajax?_wrapper_format=drupal_ajax&view_name=events"
        "&view_display_id=default&view_args=&view_path=%2Fnode%2F186&view_base_path="
        "&view_dom_id=56888d420fb7e34a8182ad455f7f35d6ea8af1488c062d10fbeb38f056c886d7"
        "&pager_element=0&page={page}&_drupal_ajax=1"
        "&ajax_page_state%5Btheme%5D=sfzc&ajax_page_state%5Btheme_token%5D="
        "&ajax_page_state%5Blibraries%5D=eJxlz1FuwyAMBuALETgSMuBQNoMjG9Zlpx9dtLVLXiz8Yf2yA3PXLrD5ACKF3cpSTThrJg5Ai_adSsvX_6nveuXGCV-UShCQ3f2JiSzoIteNG7au9pywLEEQUpRRg8nMmdB3yC7Pcu4tvMHnf6xmA4E8827qkowNyD7FjraNQEVvmIyuX3EeP5c4nqeLtXS8l4QeCKW70ko3umvH6gIomh58xQwV27jCIwTVfBS8q_uptnIahAf50tZHIHqNwkTHyPKry6Hfd5anxQ"
    )
    events = fetch_retreat_events(url, pages=args.pages)
    for event in events:
        print(f"{event['date']} - {event['title']}")
        print(event['info'])
        print(event['link'])
        print(f"Source: {event['source']}")
        print()


if __name__ == "__main__":
    main()
