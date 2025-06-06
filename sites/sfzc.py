from typing import List, Dict
from bs4 import BeautifulSoup

# Default AJAX endpoint for SFZC retreat events
BASE_URL = (
    "https://www.sfzc.org/views/ajax?_wrapper_format=drupal_ajax&view_name=events"
    "&view_display_id=default&view_args=&view_path=%2Fnode%2F186&view_base_path="
    "&view_dom_id=56888d420fb7e34a8182ad455f7f35d6ea8af1488c062d10fbeb38f056c886d7"
    "&pager_element=0&page={page}&_drupal_ajax=1"
    "&ajax_page_state%5Btheme%5D=sfzc&ajax_page_state%5Btheme_token%5D="
    "&ajax_page_state%5Blibraries%5D=eJxlz1FuwyAMBuALETgSMuBQNoMjG9Zlpx9dtLVLXiz8Yf2yA3PXLrD5ACKF3cpSTThrJg5Ai_adSsvX_6nveuXGCV-UShCQ3f2JiSzoIteNG7au9pywLEEQUpRRg8nMmdB3yC7Pcu4tvMHnf6xmA4E8827qkowNyD7FjraNQEVvmIyuX3EeP5c4nqeLtXS8l4QeCKW70ko3umvH6gIomh58xQwV27jCIwTVfBS8q_uptnIahAf50tZHIHqNwkTHyPKry6Hfd5anxQ"
)


def parse_events(html: str, source: str) -> List[Dict[str, str]]:
    """Parse retreat events from SFZC HTML snippet."""
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for row in soup.select("tr"):
        title_cell = row.select_one("td.views-field.views-field-title")
        if not title_cell:
            continue
        title_text = title_cell.get_text(strip=True)
        if "retreat" not in title_text.lower():
            continue

        date_cell = row.select_one("td.views-field.views-field-field-dates-1")
        center_cell = row.select_one("td.views-field.views-field-field-practice-center")
        link_elem = title_cell.find("a", href=True)
        events.append(
            {
                "title": title_text,
                "date": date_cell.get_text(strip=True) if date_cell else "",
                "practice_center": center_cell.get_text(strip=True) if center_cell else "",
                "link": link_elem["href"] if link_elem else "",
                "source": source,
            }
        )
    return events
