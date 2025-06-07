import logging
from parse_retreat_events import (
    fetch_retreat_events as _fetch_retreat_events,
    fetch_all_retreats as _fetch_all_retreats,
    events_to_xml,
    IRC_URL,
    SPIRITROCK_URL,
    sfzc,
    irc,
    spiritrock,
)

fetch_retreat_events = _fetch_retreat_events
fetch_all_retreats = _fetch_all_retreats


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse retreat events from supported sites")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to fetch (where applicable)")
    parser.add_argument("--site", choices=["sfzc", "irc", "spiritrock"], default="sfzc", help="Which site to parse")
    parser.add_argument("--output", type=str, help="Write events to this XML file")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s:%(message)s")

    if args.site == "sfzc":
        events = fetch_retreat_events(sfzc.BASE_URL, pages=args.pages, parser=sfzc.parse_events)
    elif args.site == "irc":
        events = fetch_retreat_events(IRC_URL, pages=1, parser=irc.parse_events)
    else:
        events = fetch_retreat_events(SPIRITROCK_URL, pages=1, parser=spiritrock.parse_events)

    if args.output:
        xml = events_to_xml(events)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(xml)
        print(f"Wrote {len(events)} events to {args.output}")
    else:
        for event in events:
            print(f"{event.dates.start:%B %d, %Y} - {event.title}")
            print(event.location.practice_center)
            print(event.link)
            print(f"Source: {event.other.get('source', '')}")
            print()


if __name__ == "__main__":
    main()
