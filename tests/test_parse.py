import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parse_sesshin_events import fetch_sesshin_events

SAMPLE_HTML = '''
<div class="card-event">
    <div class="card-title">Winter Sesshin</div>
    <div class="card-date">January 5</div>
    <div class="card-description">5-day intensive</div>
    <a href="https://example.com/winter">Details</a>
</div>
<div class="card-event">
    <div class="card-title">Weekly Practice</div>
    <div class="card-date">January 6</div>
    <div class="card-description">Regular zazen</div>
    <a href="https://example.com/practice">Details</a>
</div>
'''

def test_fetch_sesshin_events(monkeypatch):
    class MockResponse:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass

    def mock_get(url):
        return MockResponse(SAMPLE_HTML)

    monkeypatch.setattr('requests.get', mock_get)
    events = fetch_sesshin_events('https://sfzc.org/calendar')
    assert len(events) == 1
    event = events[0]
    assert event['title'] == 'Winter Sesshin'
    assert event['link'] == 'https://example.com/winter'

