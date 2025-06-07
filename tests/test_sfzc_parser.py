import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sites import sfzc
from models import RetreatLocation, RetreatDates

SAMPLE_TEMPLATE = """
<table class="views-table">
<caption>Saturday, Jun 29, 2025</caption>
<tbody>
<tr>
    <td>9:00 am</td>
    <td>{center}</td>
    <td><a href="https://example.com/retreat">Sesshin</a></td>
</tr>
</tbody>
</table>
"""


def parse_single(center: str):
    html = SAMPLE_TEMPLATE.format(center=center)
    events = sfzc.parse_events(html, "https://source")
    assert len(events) == 1
    return events[0]


def test_city_center_address():
    evt = parse_single("City Center")
    assert evt.location.practice_center == "City Center"
    assert evt.location.city == "San Francisco"
    assert evt.location.region == "CA"
    assert evt.location.country == "USA"
    assert evt.other.get("address") == "300 Page St, San Francisco, CA 94102"


def test_green_gulch_address():
    evt = parse_single("Green Gulch")
    assert evt.location.practice_center == "Green Gulch"
    assert evt.location.city == "Muir Beach"
    assert evt.location.region == "CA"
    assert evt.location.country == "USA"
    assert evt.other.get("address") == "1601 Shoreline Hwy, Muir Beach, CA 94965"


def test_tassajara_address():
    evt = parse_single("Tassajara")
    assert evt.location.practice_center == "Tassajara"
    assert evt.location.city == "Carmel Valley"
    assert evt.location.region == "CA"
    assert evt.location.country == "USA"
    assert (
        evt.other.get("address")
        == "39171 Tassajara Road Carmel Valley, CA 93924 Jamesburg"
    )


def test_fetch_description_teachers(monkeypatch):
    sample_detail = """
    <html><head>
        <meta property="og:description" content="An engaging retreat" />
    </head><body>
        <div class="field field--name-field-teachers field--type-entity-reference field--label-inline">
            <div class="field__label">Teachers</div>
            <div class="field__items">
                <div class="field__item"><a href="/teachers/teacher-one">Teacher One</a></div>
                <div class="field__item"><a href="/teachers/teacher-two">Teacher Two</a></div>
            </div>
        </div>

    </body></html>
    """

    class MockResp:
        def __init__(self, text: str):
            self.text = text

        def raise_for_status(self):
            pass

    def mock_get(url, headers=None, timeout=10):  # noqa: D401
        return MockResp(sample_detail)

    monkeypatch.setattr("requests.get", mock_get)

    desc, teachers = sfzc.fetch_description("https://example.com/retreat")
    assert desc == "An engaging retreat"
    assert teachers == ["Teacher One", "Teacher Two"]
