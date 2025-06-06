import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def fetch_sesshin_events(url: str = "https://www.sfzc.org/calendar") -> List[Dict[str, str]]:
    """Fetch events containing 'sesshin' from the SFZC calendar page."""
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for event in soup.select(".card-event"):
        title_elem = event.select_one(".card-title")
        if not title_elem:
            continue
        title_text = title_elem.get_text(strip=True)
        if "sesshin" not in title_text.lower():
            continue

        date_elem = event.select_one(".card-date")
        info_elem = event.select_one(".card-description")
        link_elem = event.select_one("a")

        events.append({
            "title": title_text,
            "date": date_elem.get_text(strip=True) if date_elem else "",
            "info": info_elem.get_text(strip=True) if info_elem else "",
            "link": link_elem["href"] if link_elem and link_elem.has_attr("href") else "",
        })
    return events


def main() -> None:
    events = fetch_sesshin_events()
    for event in events:
        print(f"{event['date']} - {event['title']}")
        print(event['info'])
        print(event['link'])
        print()


if __name__ == "__main__":
    main()
