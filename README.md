# Retreat Guide

This repository provides a script that gathers retreat events from the San Francisco Zen Center website.

## Requirements

- Python 3.8+
- `requests`
- `beautifulsoup4`

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Usage

Run the script (it will fetch several pages from the site's AJAX endpoint):

```bash
python parse_sesshin_events.py
```

The script downloads three pages of events by default. Add `--pages` to change
the number of pages or `--debug` to see detailed parsing information:

```bash
python parse_sesshin_events.py --pages 5 --debug
```

The script will print the date, practice center, link, and source URL for events
whose title contains the word "retreat".
