import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sites import spiritrock

SAMPLE_HIT = {
    "title": "Weeklong Retreat",
    "url": "https://example.com/retreat",
    "startDate": "2025-06-29T15:00:00Z",
    "endDate": "2025-07-06T15:00:00Z",
    "teacherNames": ["Teacher One", "Teacher Two"],
    "description": "An engaging retreat",
    "location": {
        "centerName": "Spirit Rock",
        "city": "Woodacre",
        "region": "CA",
        "country": "USA",
    },
    "extra": "value",
}


def test_parse_algolia_events(monkeypatch):
    def mock_fetch(page=0, hits_per_page=100):
        if page == 0:
            return [SAMPLE_HIT]
        return []

    monkeypatch.setattr(spiritrock, "fetch_algolia_page", mock_fetch)

    events = spiritrock.parse_algolia_events(max_pages=2)
    assert len(events) == 1
    evt = events[0]
    assert evt.title == "Weeklong Retreat"
    assert evt.teachers == ["Teacher One", "Teacher Two"]
    assert evt.dates.start == datetime(2025, 6, 29, 15, 0, tzinfo=timezone.utc)
    assert evt.dates.end == datetime(2025, 7, 6, 15, 0, tzinfo=timezone.utc)
    assert evt.location.city == "Woodacre"
    assert evt.other.get("extra") == "value"
