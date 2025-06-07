# Retreat Guide

This repository provides a small tool for gathering retreat events.  Each website
has its own parser module under `sites/`, allowing new sources to be added
easily.  The included example fetches events from the San Francisco Zen Center
website.

## Requirements

- Python 3.8+
- `requests`
- `beautifulsoup4`

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Usage

Run the script (it will fetch several pages from the site's calendar). By default
it prints results to the console.  Pass `--output` to write the collected events
to a JSON file instead of printing them:

```bash
python parse_retreat_events.py
python parse_retreat_events.py --output events.json
```

The script downloads three pages of events by default. Add `--pages` to change
the number of pages or `--debug` to see detailed parsing information. Use
`--site` to choose between `sfzc`, `irc`, or `spiritrock`:

```bash
python parse_retreat_events.py --pages 5 --debug
```

The script will print the date, practice center, link, and source URL for events
whose title contains the word "retreat".

## Data Structures

A set of dataclasses is provided in `models.py` for parsers that need a structured representation of retreat events.
The classes `RetreatEvent`, `RetreatDates`, and `RetreatLocation` can be imported and used across sites.

