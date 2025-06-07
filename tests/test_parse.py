import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parse_retreat_events import (
    fetch_retreat_events,
    fetch_all_retreats,
    events_to_xml,
    main as parse_main,
)
from models import RetreatEvent, RetreatDates, RetreatLocation

SAMPLE_HTML_RETREAT = '''
<table>
<tr>
    <td class="views-field views-field-title">
        <a href="https://example.com/retreat">3-Day Retreat</a>
    </td>
    <td class="views-field views-field-field-dates-1">June 1</td>
    <td class="views-field views-field-field-practice-center">Green Gulch</td>
</tr>
</table>
'''

SAMPLE_HTML_NONE = '''
<table>
<tr>
    <td class="views-field views-field-title">
        <a href="https://example.com/practice">Weekly Practice</a>
    </td>
    <td class="views-field views-field-field-dates-1">June 2</td>
    <td class="views-field views-field-field-practice-center">City Center</td>
</tr>
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

    def mock_get(url):
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

    def mock_get(url):
        base = url.split("?")[0]
        return MockResponse(responses[base])

    monkeypatch.setattr("requests.get", mock_get)
    events = fetch_all_retreats(list(responses.keys()), pages=1)
    assert len(events) == 1
    evt = events[0]
    assert evt.location.practice_center == "Green Gulch"
    assert evt.other.get("source") == "https://one"


def test_events_to_xml():
    events = [
        RetreatEvent(
            title="3-Day Retreat",
            dates=RetreatDates(start=datetime(2025, 6, 1), end=datetime(2025, 6, 1)),
            teachers=[],
            location=RetreatLocation(practice_center="Green Gulch"),
            description="",
            link="https://example.com/retreat",
            other={"source": "https://dummy?page=0"},
        )
    ]
    xml = events_to_xml(events)
    assert "<retreats>" in xml
    assert "<title>3-Day Retreat</title>" in xml


def test_main_writes_output(tmp_path, monkeypatch):
    def mock_fetch(url, pages=3, parser=None):
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

    output = tmp_path / "events.xml"
    monkeypatch.setattr(sys, "argv", ["prog", "--output", str(output)])
    parse_main()

    contents = output.read_text(encoding="utf-8")
    assert "<retreats>" in contents


def test_events_to_xml_handles_missing_dates():
    events = [
        RetreatEvent(
            title="TBD",
            dates=RetreatDates(),
            teachers=[],
            location=RetreatLocation(),
            description="",
            link="",
            other={},
        )
    ]
    xml = events_to_xml(events)
    assert "<start />" in xml
    assert "<end />" in xml


def test_main_prints_without_dates(monkeypatch, capsys):
    def mock_fetch(url, pages=3, parser=None):
        return [
            RetreatEvent(
                title="Retreat",
                dates=RetreatDates(),
                teachers=[],
                location=RetreatLocation(practice_center="Center"),
                description="",
                link="http://example.com",
                other={"source": url},
            )
        ]

    monkeypatch.setattr("parse_retreat_events.fetch_retreat_events", mock_fetch)

    monkeypatch.setattr(sys, "argv", ["prog", "--site", "sfzc"])
    parse_main()
    captured = capsys.readouterr()
    assert "Unknown Date" in captured.out
