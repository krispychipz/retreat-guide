# Retreat Guide

This repository provides a script that aggregates retreat events from multiple dharma center calendars.

## Requirements

- Python 3.8+
- `requests`
- `beautifulsoup4`

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Usage

1. Create a file named `calendar_urls.txt` containing one calendar URL per line. A couple of example entries are included by default.
2. Run the script:

```bash
python parse_sesshin_events.py
```

The script will print dates, info, links, and the source calendar for events that contain the word "retreat" in their title.
