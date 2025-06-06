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

Run the script (it will fetch several pages from the site's AJAX endpoint). By default
it prints results to the console, but you can also write them to an XML file using
`--output`:

```bash
python parse_sesshin_events.py
python parse_sesshin_events.py --output events.xml
```

The script downloads three pages of events by default. Add `--pages` to change
the number of pages or `--debug` to see detailed parsing information:

```bash
python parse_sesshin_events.py --pages 5 --debug
```

The script will print the date, practice center, link, and source URL for events
whose title contains the word "retreat".
