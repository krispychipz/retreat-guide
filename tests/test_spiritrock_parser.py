import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sites import spiritrock

SAMPLE_DETAIL = """
<html><head>
<meta property="og:description" content="Full retreat description" />
</head><body></body></html>
"""

class MockResp:
    def __init__(self, text: str):
        self.text = text
    def raise_for_status(self):
        pass

def test_fetch_description(monkeypatch):
    def mock_get(url, headers=None, timeout=10):
        return MockResp(SAMPLE_DETAIL)
    monkeypatch.setattr("requests.get", mock_get)
    desc = spiritrock.fetch_description("https://example.com/event")
    assert desc == "Full retreat description"

def test_parse_events_uses_detail(monkeypatch):
    html = """
    <div class='event-wrap'>
      <h2 class='event-title'><a href='https://example.com/event'>My Retreat</a></h2>
      <div class='event-meta-full'></div>
      <div class='event-description'>Short desc</div>
    </div>
    """
    monkeypatch.setattr(spiritrock, "fetch_description", lambda url: "Full retreat description")
    events = spiritrock.parse_events(html, "source")
    assert events[0].description == "Full retreat description"
