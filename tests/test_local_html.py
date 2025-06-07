import os
from datetime import datetime
from sites import irc, sfzc, spiritrock

BASE = os.path.dirname(__file__)


def test_parse_irc_real_page():
    path = os.path.join(BASE, "irc.html")
    events = irc.parse_retreats(path)
    assert len(events) == 33
    assert any(
        e.title == "2 week Mindfulness of Mind Retreat for Experienced Students"
        and e.dates.start == datetime(2025, 6, 29)
        for e in events
    )


def test_parse_sfzc_real_page():
    path = os.path.join(BASE, "sfzc.html")
    html = open(path, encoding="utf-8").read()
    events = sfzc.parse_events(html, path)
    assert len(events) == 2
    titles = [e.title for e in events]
    assert "Meditation in Recovery Daylong Retreat, GGF 6/15" in titles
    assert (
        "Easeful Body, Peaceful Mind: A 5-day Yoga and Zen Retreat ZMC, 7/1–7/6 – Waitlist Only" in titles
    )


def test_parse_spiritrock_real_page():
    path = os.path.join(BASE, "spiritrock.html")
    events = spiritrock.parse_spiritrock(path)
    assert len(events) == 36
    titles = [e.title for e in events]
    assert any("Winter Solstice Retreat" in t for t in titles)
    assert any("New Year's Insight Meditation Retreat" in t for t in titles)
