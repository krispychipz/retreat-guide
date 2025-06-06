import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def fetch_retreat_events(url: str) -> List[Dict[str, str]]:
    """Fetch events containing 'retreat' from a calendar page."""
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for event in soup.select(".card-event"):
        title_elem = event.select_one(".card-title")
        if not title_elem:
            continue
        title_text = title_elem.get_text(strip=True)
        if "retreat" not in title_text.lower():
            continue

        date_elem = event.select_one(".card-date")
        info_elem = event.select_one(".card-description")
        link_elem = event.select_one("a")

        events.append({
            "title": title_text,
            "date": date_elem.get_text(strip=True) if date_elem else "",
            "info": info_elem.get_text(strip=True) if info_elem else "",
            "link": link_elem["href"] if link_elem and link_elem.has_attr("href") else "",
            "source": url,
        })
    return events


def fetch_all_retreats(urls: List[str]) -> List[Dict[str, str]]:
    all_events = []
    for url in urls:
        try:
            all_events.extend(fetch_retreat_events(url))
        except Exception as exc:
            print(f"Failed to fetch {url}: {exc}")
    return all_events


def read_calendar_urls(path: str = "calendar_urls.txt") -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip()]
    except FileNotFoundError:
        print(f"Calendar list file {path} not found.")
        return []


def main() -> None:
    urls = read_calendar_urls()
    events = fetch_all_retreats(urls)
    for event in events:
        print(f"{event['date']} - {event['title']}")
        print(event['info'])
        print(event['link'])
        print(f"Source: {event['source']}")
        print()


if __name__ == "__main__":
    main()
