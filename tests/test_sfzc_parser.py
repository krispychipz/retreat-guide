import sys
import os
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sites import sfzc

SAMPLE_HTML = '''
<table class="views-table">
<caption>Saturday, Jun 29, 2025</caption>
<tbody>
<tr>
    <td>9:00 am</td>
    <td>City Center</td>
    <td><a href="https://example.com/event">One-Day Sesshin</a></td>
</tr>
</tbody>
</table>
'''

DETAIL_HTML = '<meta property="og:description" content="Join us for an intensive sesshin." />'

def test_parse_event_fetches_description(monkeypatch):
    mock_resp = Mock()
    mock_resp.text = DETAIL_HTML
    mock_resp.raise_for_status = Mock()
    monkeypatch.setattr(sfzc.requests, "get", Mock(return_value=mock_resp))

    events = sfzc.parse_events(SAMPLE_HTML, "https://source")
    assert len(events) == 1
    evt = events[0]
    assert evt.link == "https://example.com/event"
    assert evt.description == "Join us for an intensive sesshin."

