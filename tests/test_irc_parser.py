import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sites import irc
from models import RetreatDates, RetreatLocation

SAMPLE_HTML = '''
<div class="irc-retreat-listing-div-text">
  <p class="irc-retreat-listing-p">
    <strong>7-Day Retreat</strong> Teacher One, Teacher Two<br>
    June 29 – July 13, 2025 - 10 days
  </p>
  <p class="irc-retreat-listing-p">Join us for an immersive retreat.</p>
  <ul>
    <li><strong>Location:</strong> IRC, Santa Cruz, CA, USA</li>
    <li><a href="https://example.com/reg">REGISTER</a></li>
  </ul>
</div>
'''

def test_parse_events_basic():
    events = irc.parse_events(SAMPLE_HTML, "https://source")
    assert len(events) == 1
    evt = events[0]
    assert evt.title == "7-Day Retreat"
    assert evt.teachers == ["Teacher One", "Teacher Two"]
    assert evt.dates.start == datetime(2025, 6, 29)
    assert evt.dates.end == datetime(2025, 7, 13)
    assert evt.location.practice_center == "IRC"
    assert evt.location.city == "Santa Cruz"
    assert evt.location.region == "CA"
    assert evt.location.country == "USA"
    assert evt.link == "https://example.com/reg"
    assert evt.other.get("source") == "https://source"
