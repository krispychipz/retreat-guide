import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parse_retreat_events import (
    fetch_retreat_events,
    fetch_all_retreats,
    main as parse_main,
)
import json
from models import RetreatEvent, RetreatDates, RetreatLocation

SAMPLE_HTML_RETREAT = '''
<table class="views-table">
<caption>Saturday, Jun 29, 2025</caption>
<tbody>
<tr>
    <td>9:00 am</td>
    <td>Green Gulch</td>
    <td><a href="https://example.com/retreat">3-Day Retreat</a></td>
</tr>
</tbody>
</table>
'''

SAMPLE_HTML_NONE = '''
<table class="views-table">
<caption>Sunday, Jun 30, 2025</caption>
<tbody>
<tr>
    <td>10:00 am</td>
    <td>City Center</td>
    <td><a href="https://example.com/practice">Weekly Practice</a></td>
</tr>
</tbody>
</table>
'''

SAMPLE_JSON_RETREAT = [{"data": SAMPLE_HTML_RETREAT}]
SAMPLE_JSON_NONE = [{"data": SAMPLE_HTML_NONE}]


def test_fetch_retreat_events(monkeypatch):
    class MockResponse:
        def __init__(self, payload):
            self.payload = payload
            self.text = "unused"
        def raise_for_status(self):
            pass
        def json(self):
            return self.payload

    def mock_get(url, **kwargs):
        return MockResponse(SAMPLE_JSON_RETREAT)

    monkeypatch.setattr("requests.get", mock_get)
    events = fetch_retreat_events("https://dummy?page={page}", pages=1)
    assert len(events) == 1
    evt = events[0]
    assert evt.title == "3-Day Retreat"
    assert evt.location.practice_center == "Green Gulch"
    assert evt.other.get("source") == "https://dummy?page=0"


def test_fetch_all_retreats(monkeypatch):
    class MockResponse:
        def __init__(self, payload):
            self.payload = payload
            self.text = "unused"
        def raise_for_status(self):
            pass
        def json(self):
            return self.payload

    responses = {
        "https://one": SAMPLE_JSON_RETREAT,
        "https://two": SAMPLE_JSON_NONE,
    }

    def mock_get(url, **kwargs):
        base = url.split("?")[0]
        return MockResponse(responses[base])

    monkeypatch.setattr("requests.get", mock_get)
    events = fetch_all_retreats(list(responses.keys()), pages=1)
    assert len(events) == 1
    evt = events[0]
    assert evt.location.practice_center == "Green Gulch"
    assert evt.other.get("source") == "https://one"



def test_main_writes_output(tmp_path, monkeypatch):
    def mock_fetch(url, pages=3, parser=None, params=None):
        return [
            RetreatEvent(
                title="3-Day Retreat",
                dates=RetreatDates(start=datetime(2025, 6, 1), end=datetime(2025, 6, 1)),
                teachers=[],
                location=RetreatLocation(practice_center="Green Gulch"),
                description="",
                link="https://example.com/retreat",
                other={"source": url},
            )
        ]

    monkeypatch.setattr("parse_retreat_events.fetch_retreat_events", mock_fetch)
    monkeypatch.setattr(
        "parse_retreat_events.spiritrock.parse_algolia_events",
        lambda: mock_fetch("https://spiritrock"),
    )

    output = tmp_path / "events.json"
    monkeypatch.setattr(sys, "argv", ["prog", "--output", str(output)])
    parse_main()

    contents = json.loads(output.read_text(encoding="utf-8"))
    assert contents[0]["title"] == "3-Day Retreat"
