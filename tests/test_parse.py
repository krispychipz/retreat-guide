import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parse_sesshin_events import fetch_retreat_events, fetch_all_retreats

SAMPLE_HTML_RETREAT = '''
<div class="card-event">
    <div class="card-title">3-Day Retreat</div>
    <div class="card-date">June 1</div>
    <div class="card-description">Meditation intensive.</div>
    <a href="https://example.com/retreat">Details</a>
</div>
'''

SAMPLE_HTML_NONE = '''
<div class="card-event">
    <div class="card-title">Weekly Practice</div>
    <div class="card-date">June 2</div>
    <div class="card-description">Regular sitting</div>
    <a href="https://example.com/practice">Details</a>
</div>
'''


def test_fetch_retreat_events(monkeypatch):
    class MockResponse:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass

    def mock_get(url):
        return MockResponse(SAMPLE_HTML_RETREAT)

    monkeypatch.setattr("requests.get", mock_get)
    events = fetch_retreat_events("https://dummy")
    assert len(events) == 1
    assert events[0]["title"] == "3-Day Retreat"
    assert events[0]["source"] == "https://dummy"


def test_fetch_all_retreats(monkeypatch):
    class MockResponse:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass

    responses = {
        "https://one": SAMPLE_HTML_RETREAT,
        "https://two": SAMPLE_HTML_NONE,
    }

    def mock_get(url):
        return MockResponse(responses[url])

    monkeypatch.setattr("requests.get", mock_get)
    events = fetch_all_retreats(list(responses.keys()))
    assert len(events) == 1
    assert events[0]["source"] == "https://one"

